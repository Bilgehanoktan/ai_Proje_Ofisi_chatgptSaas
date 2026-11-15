"""D0 ordinary-transition mapping; explicit synthetic lease/clock, no real grant.
Only six base roles, no admission, terminal, renewal, budget or default wiring.
"""
from dataclasses import asdict, replace
from hashlib import sha256
import json
from app.core.agent_runtime.lifecycle import LeaseObservation, inspect_lease, valid_lease
from app.core.agent_runtime.postgres_run import PostgresRunRepository
from app.core.agent_runtime.transition_command import validate_transition
from app.core.event_store.postgres_write import append_event, insert_outbox, reserve_fence
from app.core.transaction.port import CommitReceipt
from app.core.transaction.review import BASE_ROLES, Operation, valid_intent, required_roles

_KEY = 'tenant_id=%s AND company_id=%s AND environment_id=%s AND run_id=%s'
_LEASE_FIELDS = ('lease_id','grant_id','lease_version','heartbeat_revision','fence',
                 'policy_epoch','witness_epoch','expires_tick','heartbeat_tick')

def _key(i):
    s = i.scope
    return (s.tenant_id, s.company_id, s.environment_id, s.run_id)

def transaction_ref(i):
    return 'd0-tx-' + sha256(json.dumps(asdict(i), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def lease_digest(lease):
    if not valid_lease(lease):
        raise ValueError("D0_LEASE_REFERENCE_INVALID")
    return sha256(json.dumps(asdict(lease), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def _one(cursor, sql, params):
    cursor.execute(sql, params)
    row = cursor.fetchone()
    if row is not None and cursor.fetchone() is not None:
        raise ValueError('D0_READBACK_NOT_UNIQUE')
    return row

def _lease(cursor, i, lock=False):
    sql = ('SELECT plan_revision,task_id,agent_instance_id,principal_id,' + ','.join(_LEASE_FIELDS)
           + ' FROM t1_candidate.run_leases WHERE ' + _KEY + (' FOR UPDATE' if lock else ''))
    row = _one(cursor, sql, _key(i))
    s = i.scope
    if row is None or tuple(row[:4]) != (s.plan_revision,s.task_id,s.agent_instance_id,s.principal_id):
        raise ValueError('D0_LEASE_SCOPE_HOLD')
    return LeaseObservation(s, *row[4:])

class D0PostgresTransitionMapping:
    """Single-use transaction mapping. Caller supplies synthetic reference and clock.
    Never install in production or infer actual authority from a D0 receipt.
    """
    def __init__(self, lease_reference, clock):
        self.reference = lease_reference
        self.clock = clock
        self.runs = PostgresRunRepository()
        self.intent = None
        self.before = None
        self.target = None
        self.written = set()
        self.verified = False
        self.last_tick = None

    def _check_lease(self, cursor, i):
        lease = _lease(cursor, i, lock=True)
        if (lease.lease_id,lease.grant_id,lease.policy_epoch,lease.witness_epoch) != (
                i.lease_ref,i.grant_ref,i.policy_epoch,i.witness_epoch):
            raise ValueError('D0_LEASE_INTENT_HOLD')
        clock = self.clock()
        check = inspect_lease(lease, self.reference, clock)
        if check.freshness != 'FRESH':
            raise ValueError(check.reason)
        if self.last_tick is not None and clock.now_tick < self.last_tick:
            raise ValueError("D0_CLOCK_REGRESSION_HOLD")
        self.last_tick = clock.now_tick
        return lease

    def lock_and_validate(self, cursor, i):
        if (self.intent is not None or not valid_intent(i) or i.operation != Operation.STATE_MUTATION
                or required_roles(i) != BASE_ROLES or i.budget_ref is not None):
            raise PermissionError('D0_ORDINARY_TRANSITION_ONLY')
        self.intent = i
        self.before = self.runs.lock(cursor, i.scope)
        if self.before.version != i.expected_version:
            raise ValueError('D0_HEAD_CAS_HOLD')
        self._check_lease(cursor, i)

    def lock_transition(self, cursor, i):
        if self.intent != i:
            raise ValueError('D0_INTENT_HOLD')
        return self.before

    def write_role(self, cursor, role, i):
        raise PermissionError('D0_TRANSITION_COMMAND_REQUIRED')

    def write_transition_role(self, cursor, role, i, before, target):
        if (self.intent != i or before != self.before or role not in BASE_ROLES or role in self.written
                or self.verified or (self.target is not None and self.target != target)):
            raise ValueError('D0_WRITE_ROLE_HOLD')
        validate_transition(before, target, i)
        self.target = target
        tx = transaction_ref(i)
        k = _key(i)
        v = before.version + 1
        if role == 'HEAD':
            self.runs.advance(cursor, before, target)
        elif role == 'MUTATION':
            cursor.execute('INSERT INTO t1_candidate.run_mutations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                           (*k,v,tx,i.request_digest,before.state.value,target.value,before.attempt))
        elif role == 'FENCE':
            reserve_fence(cursor, i)
        elif role == 'EVENT':
            append_event(cursor, i, tx, 'D0_RUN_TRANSITION')
        elif role == 'OUTBOX':
            insert_outbox(cursor, i, tx)
        elif role == 'AUDIT':
            cursor.execute('INSERT INTO t1_candidate.run_audit (tenant_id,company_id,environment_id,run_id,version,transaction_ref,request_digest,effect_key,idempotency_key,grant_ref,lease_ref,policy_epoch,witness_epoch,lease_fence,lease_digest) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                           (*k,v,tx,i.request_digest,i.effect_key,i.idempotency_key,i.grant_ref,i.lease_ref,
                            i.policy_epoch,i.witness_epoch,self.reference.fence,lease_digest(self.reference)))
        self.written.add(role)

    def read_transition(self, cursor, i):
        if self.intent != i:
            raise ValueError('D0_INTENT_HOLD')
        return self.runs.read(cursor, i.scope)

    def verify_write_set(self, cursor, i, roles):
        if self.intent != i or self.written != BASE_ROLES or roles != BASE_ROLES or self.verified:
            raise ValueError('D0_WRITE_SET_INCOMPLETE')
        self._check_lease(cursor, i)
        verify_transition_rows(cursor, i, self.before, self.target, self.reference)
        self.verified = True
        return CommitReceipt(transaction_ref(i), i.expected_version+1, i.request_digest)

def verify_transition_rows(cursor, i, before, target, lease_reference):
    """Exact D0 row comparisons. Requires a single consistent transaction snapshot."""
    validate_transition(before, target, i)
    if (not valid_lease(lease_reference) or lease_reference.scope != i.scope
            or (lease_reference.lease_id,lease_reference.grant_id,lease_reference.policy_epoch,lease_reference.witness_epoch)
            != (i.lease_ref,i.grant_ref,i.policy_epoch,i.witness_epoch)):
        raise ValueError("D0_LEASE_REFERENCE_INVALID")
    tx, k, v = transaction_ref(i), _key(i), i.expected_version+1
    suffix = ' WHERE ' + _KEY + ' AND version=%s'
    checks = (
        ('SELECT transaction_ref,request_digest,before_state,after_state,attempt FROM t1_candidate.run_mutations'+suffix,
         (*k,v),(tx,i.request_digest,before.state.value,target.value,before.attempt)),
        ('SELECT event_id,event_type,request_digest FROM t1_candidate.events'+suffix,
         (*k,v),(tx,'D0_RUN_TRANSITION',i.request_digest)),
        ('SELECT event_id,request_digest FROM t1_candidate.outbox WHERE '+_KEY+' AND event_id=%s',
         (*k,tx),(tx,i.request_digest)),
        ('SELECT effect_key,idempotency_key,request_digest FROM t1_candidate.fences WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND (effect_key=%s OR idempotency_key=%s)',
         (*k[:3],i.effect_key,i.idempotency_key),(i.effect_key,i.idempotency_key,i.request_digest)),
        ('SELECT transaction_ref,request_digest,effect_key,idempotency_key,grant_ref,lease_ref,policy_epoch,witness_epoch,lease_fence,lease_digest FROM t1_candidate.run_audit'+suffix,
         (*k,v),(tx,i.request_digest,i.effect_key,i.idempotency_key,i.grant_ref,i.lease_ref,i.policy_epoch,i.witness_epoch,lease_reference.fence,lease_digest(lease_reference))),
    )
    for sql, params, expected in checks:
        row = _one(cursor, sql, params)
        if row is None or tuple(row) != expected:
            raise ValueError('D0_WRITE_SET_READBACK_HOLD')
    after = PostgresRunRepository().read(cursor, i.scope)
    if after != replace(before, state=target, version=v):
        raise ValueError('D0_HEAD_READBACK_HOLD')
