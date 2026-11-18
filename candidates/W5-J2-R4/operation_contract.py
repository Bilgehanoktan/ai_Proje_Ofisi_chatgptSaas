"""R4 owner-review contract. No T1 writer, claim issuer, grant or authority.
New operation names/roles are proposals, NOT additions to the canonical enum.
"""
from dataclasses import dataclass, field, asdict
from hashlib import sha256
import json
from membership_review import BINDING, SCOPE, _shape, _binding_ok, _keys, _token, _pin, _uint

RUN_SCOPE = SCOPE + ('plan_revision','task_id','run_id','agent_instance_id','principal_id')
BASE = ('HEAD','MUTATION','FENCE','EVENT','OUTBOX','AUDIT')
EXTRA = {
    'ALLOCATE': ('BUDGET','POOL','MEMBERSHIP','RECEIPT'),
    'CONSUME': ('BUDGET','MEMBERSHIP','RECEIPT'),
    'USAGE': ('BUDGET','MEMBERSHIP','RECEIPT'),
    'RECONCILE': ('BUDGET','MEMBERSHIP','RECEIPT'),
    'UNKNOWN': ('BUDGET','MEMBERSHIP','QUARANTINE'),
    'CLOSE_PARTIAL': ('LEASE','BUDGET','POOL','TERMINAL_REMAINDER'),
}
LOCKS = ('ROOT','WITNESS','MEMORY','COMPANY_STREAM','RUN','LEASE','BUDGET','POOL','MEMBERSHIP')
ORDER = ('HEAD','LEASE','BUDGET','POOL','MEMBERSHIP','RECEIPT','QUARANTINE','TERMINAL_REMAINDER','MUTATION','FENCE','EVENT','OUTBOX','AUDIT')


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')


def digest(value): return sha256(canonical(value)).hexdigest()


def economic_keys(binding):
    if not _shape(binding,BINDING) or not _binding_ok(binding): raise ValueError('BINDING_HOLD')
    # Existing R1/W5-H equality identities; domain-separated comparison hashes only.
    # Ignore attempt, route, effect, tx for uniqueness; never reset them on retry.
    return tuple(digest(['w5-j2-r4-economic-key-v1',k]) for k in _keys(binding))


def run_scope_pin(binding):
    # Original D0IntentJournal scope hash shape, not a new root or parent claim.
    if not _shape(binding,BINDING) or not _binding_ok(binding): raise ValueError('BINDING_HOLD')
    return digest({k:binding[k] for k in RUN_SCOPE})


@dataclass(frozen=True)
class ParentObservation:
    scope_sha: str
    parent_claim_pin: str  # must come from owner; cannot be derived from an invocation
    record_sha: str
    key_sha: str
    recovery_epoch: int
    lease_digest: str
    grant_digest: str
    expires_tick: int


@dataclass(frozen=True)
class OperationPlan:
    phase: str
    scope_sha: str
    subject_pin: str
    parent: ParentObservation
    binding_pin: str
    economic_keys: tuple
    phase_key: str
    tx: str
    request_digest: str
    head_before: int
    budget_before: int
    observed_tick: int
    roles: tuple
    locks: tuple = field(default=LOCKS,init=False)
    decision: str = field(default='HOLD',init=False)
    commit_allowed: bool = field(default=False,init=False)
    provider_call_allowed: bool = field(default=False,init=False)
    retry_allowed: bool = field(default=False,init=False)
    spend_allowed: bool = field(default=False,init=False)
    settlement_allowed: bool = field(default=False,init=False)


def _roles(phase):
    if type(phase) is not str or phase not in EXTRA: raise ValueError('PHASE_HOLD')
    return tuple(r for r in ORDER if r in BASE+EXTRA[phase])


def plan_operation(binding,parent,phase,tx,request_digest,head_before,budget_before,now_tick,*,terminal_subject=None):
    """Build a proposed mandatory write-set. Parent reference must be supplied, not minted.
    A matching reference cannot establish protected custody or expiry through COMMIT.
    CLOSE_PARTIAL uses a stable run-level closure identity, not an arbitrary member key.
    For that phase a binding is a scoped anchor; full run history must be reviewed by owner.
    """
    keys=economic_keys(binding); scope=run_scope_pin(binding); roles=_roles(phase)
    if (type(parent) is not ParentObservation or parent.scope_sha!=scope or
        not all(_pin(x) for x in (parent.parent_claim_pin,parent.record_sha,parent.key_sha,parent.lease_digest,parent.grant_digest)) or
        not all(_uint(x) for x in (parent.recovery_epoch,parent.expires_tick,now_tick,head_before,budget_before)) or
        parent.recovery_epoch==0 or parent.recovery_epoch!=binding['witness_epoch'] or
        now_tick>=parent.expires_tick or max(head_before,budget_before)>=2**63-1 or
        not _token(tx) or tx==binding['admission_tx'] or not _pin(request_digest) or
        request_digest==binding['admission_request_digest']): raise ValueError('PARENT_OR_COMMAND_HOLD')
    if phase=='ALLOCATE' and (tx!=binding['reservation_tx'] or budget_before+1!=binding['reservation_budget_revision']):
        raise ValueError('ALLOCATION_REFERENCE_HOLD')
    if phase!='ALLOCATE' and tx==binding['reservation_tx']: raise ValueError('RESERVATION_TX_ALIAS_HOLD')
    if phase=='CLOSE_PARTIAL':
        if terminal_subject!=scope: raise ValueError('TERMINAL_SCOPE_HOLD')
        subject=scope; identity=(); phase_key=digest(['w5-j2-r4-terminal-v1',scope])
    else:
        if terminal_subject is not None: raise ValueError('UNEXPECTED_TERMINAL_HOLD')
        subject=binding['membership_pin']; identity=keys
        # Owner must enforce unique aliases AND unique per-member phase across restores.
        phase_key=digest(['w5-j2-r4-phase-v1',keys[1],phase])
    return OperationPlan(phase,scope,subject,parent,digest(binding),identity,phase_key,tx,request_digest,
                         head_before,budget_before,now_tick,roles)


@dataclass(frozen=True)
class RoleObservation:
    role: str
    record_id: str
    transaction_ref: str
    request_digest: str
    scope_sha: str
    phase_key: str
    head_before: int
    head_after: int
    budget_before: int
    budget_after: int


@dataclass(frozen=True)
class Review:
    reason: str
    structural_match: bool=False
    decision: str=field(default='HOLD',init=False)
    commit_allowed: bool=field(default=False,init=False)
    provider_call_allowed: bool=field(default=False,init=False)
    retry_allowed: bool=field(default=False,init=False)
    settlement_allowed: bool=field(default=False,init=False)


def plan_digest(plan):
    if type(plan) is not OperationPlan: raise ValueError("PLAN_SHAPE_HOLD")
    return digest(["w5-j2-r4-operation-plan-v1",asdict(plan)])


def inspect_operation(plan,binding,expected_plan_pin,rows,latest_parent,now_tick):
    """Check prospective write-set shape, not DB readback or D5 protected reader.
    Caller-supplied parent/rows may be forged. A match stays HOLD.
    """
    try:
        if (type(plan) is not OperationPlan or plan.roles!=_roles(plan.phase) or plan.locks!=LOCKS or
            type(latest_parent) is not ParentObservation or latest_parent!=plan.parent or
            not _uint(now_tick) or not _uint(plan.observed_tick) or now_tick<plan.observed_tick or now_tick>=plan.parent.expires_tick or
            not all(_pin(x) for x in (plan.scope_sha,plan.subject_pin,plan.phase_key,plan.binding_pin,plan.request_digest)) or
            not _token(plan.tx) or not all(_uint(x) and x<2**63-1 for x in (plan.head_before,plan.budget_before))):
            return Review('PARENT_OR_PLAN_DRIFT_HOLD')
        rebuilt=plan_operation(binding,plan.parent,plan.phase,plan.tx,plan.request_digest,plan.head_before,plan.budget_before,plan.observed_tick,
                               terminal_subject=plan.scope_sha if plan.phase=='CLOSE_PARTIAL' else None)
        if plan!=rebuilt or not _pin(expected_plan_pin) or plan_digest(plan)!=expected_plan_pin:
            return Review('PLAN_BINDING_HOLD')
        if type(rows) is not tuple or len(rows)!=len(plan.roles): return Review('WRITE_SET_INCOMPLETE_HOLD')
        ids=set()
        for role,r in zip(plan.roles,rows):
            if (type(r) is not RoleObservation or r.role!=role or not _token(r.record_id) or r.record_id in ids or
                (r.transaction_ref,r.request_digest,r.scope_sha,r.phase_key)!=(plan.tx,plan.request_digest,plan.scope_sha,plan.phase_key) or
                not all(_uint(x) for x in (r.head_before,r.head_after,r.budget_before,r.budget_after)) or
                (r.head_before,r.head_after,r.budget_before,r.budget_after)!=(plan.head_before,plan.head_before+1,plan.budget_before,plan.budget_before+1)):
                return Review('WRITE_SET_BINDING_HOLD')
            ids.add(r.record_id)
        return Review('D0_OPERATION_SHAPE_MATCH_OWNER_CUSTODY_HOLD',True)
    except (ValueError,KeyError,TypeError,AttributeError,OverflowError): return Review('OPERATION_SHAPE_HOLD')


def inspect_aliases(binding,retained):
    """Stable alias collision test, never proves absence in persistent storage."""
    try:
        keys=set(economic_keys(binding))
        if type(retained) is not tuple or len(retained)>4096: return Review('ALIAS_HISTORY_SHAPE_HOLD')
        if any(keys.intersection(economic_keys(row)) for row in retained): return Review('ECONOMIC_ALIAS_HOLD')
        return Review('ECONOMIC_ABSENCE_UNPROVEN_HOLD')
    except (ValueError,TypeError,KeyError,AttributeError): return Review('ALIAS_HISTORY_SHAPE_HOLD')
