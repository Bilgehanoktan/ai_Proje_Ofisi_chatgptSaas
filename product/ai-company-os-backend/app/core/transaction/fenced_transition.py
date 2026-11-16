"""0210 D0 local fence and durable intent quarantine; never an effect grant.

Only disposable SQLite witness/memory stores and explicit original T1 mapping.
SQLite writer locks serialize *cooperating local writers* across T1 COMMIT.
Not a distributed transaction, independent custody, or provider authorization.
"""
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3

from app.core.agent_runtime.lifecycle import RunState, valid_scope
from app.core.agent_runtime.memory_witness import (
    MemoryWitnessReader, D0MemoryWitnessStore, _connect as witness_connect,
)
from app.engines.memory_engine.snapshot_store import _connect as memory_connect
from app.core.transaction.postgres_transition_mapping import (
    D0PostgresTransitionMapping, transaction_ref, _lease,
)
from app.core.transaction.port import LogicalT1Coordinator, CommitReceipt
from app.core.transaction.postgres_session import postgres_transaction
from app.core.transaction.witnessed_mapping import WitnessedTransitionMapping, binding_digest
from app.core.transaction.review import valid_intent, digest_ok, Operation
from app.core.transaction.postgres_lifecycle_mapping import AdmissionBinding, D0AdmissionBoundTransitionMapping
from app.core.event_store.company_coordination import (
    Member, Pool, CompanyEvent, CompanyCoordinatedMapping, SCOPE, _roster, _replay,
)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def _digest(value):
    return sha256(_canonical(value)).hexdigest()


def _path(path):
    p = Path(os.path.abspath(path))
    if not p.name.endswith('.intent.sqlite') or p.resolve() != p or any(x.is_symlink() for x in (p, *p.parents)):
        raise ValueError('D0_INTENT_PATH_HOLD')
    return p


def _db(path, mode):
    db = sqlite3.connect(_path(path).as_uri()+'?mode='+mode, uri=True, timeout=2, isolation_level=None)
    try:
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('PRAGMA foreign_keys=ON')
        if mode == 'ro':
            db.execute('PRAGMA query_only=ON')
        return db
    except BaseException:
        db.close()
        raise


@dataclass(frozen=True)
class IntentPin:
    binding: str
    scope_sha: str
    transaction_ref: str
    request_digest: str
    expected_version: int


@dataclass(frozen=True)
class FenceReview:
    reason: str
    status: str = 'HOLD'
    historical_match: bool = False
    decision: str = field(default='HOLD', init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    independent_verified: bool = field(default=False, init=False)


def intent_pin(intent, binding):
    if not valid_intent(intent) or not digest_ok(binding) or not valid_scope(intent.scope):
        raise ValueError('D0_INTENT_BINDING_HOLD')
    return IntentPin(binding, _digest(asdict(intent.scope)), transaction_ref(intent),
                     intent.request_digest, intent.expected_version)


class D0IntentJournal:
    """Append-only local journal. One attempt per exact run scope, no automatic retry.

    PENDING is committed before T1. UNKNOWN or absent outcome is quarantine.
    HISTORICAL is a local receipt observation, not authorization or independent proof.
    """
    def __init__(self, path):
        self.path = _path(path)

    @classmethod
    def create(cls, path):
        p = _path(path)
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with closing(_db(p, 'rw')) as db:
            db.execute('CREATE TABLE intents(binding TEXT PRIMARY KEY,scope_sha TEXT NOT NULL UNIQUE,tx TEXT NOT NULL UNIQUE,request_digest TEXT NOT NULL,version INTEGER NOT NULL,body BLOB NOT NULL)')
            db.execute("CREATE TABLE outcomes(binding TEXT PRIMARY KEY REFERENCES intents(binding),status TEXT NOT NULL CHECK(status IN ('UNKNOWN','HISTORICAL')),receipt BLOB)")
            for table in ('intents', 'outcomes'):
                for op in ('UPDATE', 'DELETE'):
                    db.execute(f"CREATE TRIGGER {table}_no_{op.lower()} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append only'); END")
                db.execute(f"CREATE TRIGGER {table}_no_replace BEFORE INSERT ON {table} WHEN EXISTS(SELECT 1 FROM {table} WHERE binding=NEW.binding) BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER intents_no_scope_replace BEFORE INSERT ON intents WHEN EXISTS(SELECT 1 FROM intents WHERE scope_sha=NEW.scope_sha OR tx=NEW.tx) BEGIN SELECT RAISE(ABORT,'append only'); END")
        return cls(p)

    def stage(self, intent, binding):
        pin = intent_pin(intent, binding)
        with closing(_db(self.path, 'rw')) as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                if db.execute('SELECT 1 FROM intents WHERE scope_sha=? OR binding=? OR tx=?',
                              (pin.scope_sha, pin.binding, pin.transaction_ref)).fetchone() is not None:
                    raise ValueError('D0_INTENT_ALREADY_STAGED_HOLD')
                db.execute('INSERT INTO intents VALUES (?,?,?,?,?,?)',
                           (pin.binding, pin.scope_sha, pin.transaction_ref, pin.request_digest,
                            pin.expected_version, _canonical(asdict(intent))))
                db.execute('COMMIT')
            except BaseException:
                if db.in_transaction:
                    db.execute('ROLLBACK')
                raise
        return pin

    def _check(self, db, intent, pin):
        expected = (pin.scope_sha, pin.transaction_ref, pin.request_digest,
                    pin.expected_version, _canonical(asdict(intent)))
        row = db.execute('SELECT scope_sha,tx,request_digest,version,body FROM intents WHERE binding=?',
                         (pin.binding,)).fetchone()
        if row != expected or pin != intent_pin(intent, pin.binding):
            raise ValueError('D0_INTENT_READBACK_HOLD')

    def _record(self, intent, pin, receipt=None):
        if receipt is not None and (type(receipt) is not CommitReceipt or
                (receipt.transaction_ref, receipt.request_digest, receipt.committed_version) !=
                (pin.transaction_ref, pin.request_digest, pin.expected_version+1)):
            raise ValueError('D0_INTENT_RECEIPT_HOLD')
        status = 'UNKNOWN' if receipt is None else 'HISTORICAL'
        with closing(_db(self.path, 'rw')) as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                self._check(db, intent, pin)
                db.execute('INSERT INTO outcomes VALUES (?,?,?)',
                           (pin.binding, status, None if receipt is None else _canonical(asdict(receipt))))
                db.execute('COMMIT')
            except BaseException:
                if db.in_transaction:
                    db.execute('ROLLBACK')
                raise

    def inspect(self, intent, pin):
        try:
            with closing(_db(self.path, 'ro')) as db:
                db.execute('BEGIN')
                self._check(db, intent, pin)
                row = db.execute('SELECT status,receipt FROM outcomes WHERE binding=?', (pin.binding,)).fetchone()
            if row is None:
                return FenceReview('D0_INTENT_PENDING_QUARANTINE', 'PENDING')
            if row == ('UNKNOWN', None):
                return FenceReview('D0_INTENT_UNKNOWN_QUARANTINE', 'UNKNOWN')
            expected = CommitReceipt(pin.transaction_ref, pin.expected_version+1, pin.request_digest)
            if row == ('HISTORICAL', _canonical(asdict(expected))):
                return FenceReview('D0_INTENT_HISTORICAL_RECEIPT_ONLY', 'HISTORICAL', True)
        except (OSError, sqlite3.Error, ValueError, AttributeError, TypeError):
            pass
        return FenceReview('D0_INTENT_READBACK_HOLD')


@contextmanager
def local_revocation_fence(memory_path, reader, journal):
    """Fixed order: witness writer reservation then memory writer reservation.

    Both held until the original coordinator has returned from COMMIT/close.
    Does not lock an external trust root, clock, filesystem replacement or provider.
    """
    if type(reader) not in (MemoryWitnessReader, D0MemoryWitnessStore) or type(journal) is not D0IntentJournal:
        raise ValueError('D0_FENCE_ADAPTER_HOLD')
    paths = (memory_path, reader.path, journal.path)
    if any(os.path.samefile(a, b) for n, a in enumerate(paths) for b in paths[n+1:]):
        raise ValueError('D0_FENCE_SEPARATION_HOLD')
    with closing(witness_connect(reader.path, 'rw')) as w, closing(memory_connect(memory_path, 'rw')) as m:
        w.execute('BEGIN IMMEDIATE')
        m.execute('BEGIN IMMEDIATE')
        try:
            yield
        finally:
            # No writes in these transactions. Close also releases on failure.
            for db in (m, w):
                if db.in_transaction:
                    db.execute('ROLLBACK')


@dataclass(frozen=True)
class CompanyTransitionContext:
    """D0 candidate inputs for the existing company/admission mapping."""
    admission: AdmissionBinding
    members: tuple[Member, ...]
    pool: Pool
    history: tuple[CompanyEvent, ...]
    event: CompanyEvent


def company_transition_binding(intent, witness_binding, company):
    """Separate v1 binding profile; preserve historical witness/transaction hashes."""
    if (not valid_intent(intent) or not digest_ok(witness_binding)
            or type(company) is not CompanyTransitionContext
            or type(company.admission) is not AdmissionBinding
            or not valid_intent(company.admission.intent)
            or company.admission.intent.operation is not Operation.ADMISSION
            or company.admission.intent.scope != intent.scope
            or type(company.pool) is not Pool or type(company.event) is not CompanyEvent
            or type(company.history) is not tuple):
        raise ValueError('D0_COMPANY_FENCE_BINDING_HOLD')
    e = company.event
    s = intent.scope
    member = _roster(company.members).get(s.run_id)
    if (member is None or (s.tenant_id,s.company_id,s.environment_id) != SCOPE
            or (member.plan_revision,member.task_id,member.agent_instance_id,member.principal_id)
                != (s.plan_revision,s.task_id,s.agent_instance_id,s.principal_id)
            or (e.project_id,e.run_id,e.kind,e.version,e.transaction_ref,e.request_digest)
                != (member.project_id,s.run_id,'D0_RUN_TRANSITION',intent.expected_version+1,
                    transaction_ref(intent),intent.request_digest)
            or intent.operation is not Operation.STATE_MUTATION or intent.lease_or_budget_changes
            or intent.budget_ref is not None
            or (intent.policy_epoch,intent.witness_epoch) != (company.pool.policy_epoch,company.pool.witness_epoch)
            or company.admission.intent.budget_ref != company.pool.budget_id):
        raise ValueError('D0_COMPANY_FENCE_BINDING_HOLD')
    _replay(company.members,company.pool,company.history+(e,))
    # This is a caller-pinned D0 observation, not an independently authenticated grant.
    return _digest(['aicos-d0-company-witness-fence-v1',witness_binding,asdict(company)])


def resolve_fence_binding(intent, witness_binding, company, expected_company_binding):
    """No silent fallback for a partially supplied company profile."""
    if company is None and expected_company_binding is None:
        return witness_binding
    if (not digest_ok(expected_company_binding)
            or company_transition_binding(intent,witness_binding,company) != expected_company_binding):
        raise ValueError('D0_COMPANY_FENCE_PIN_HOLD')
    return expected_company_binding


def execute_fenced_transition(intent, context, registry, witness, expected_binding,
                              memory_path, reader, public_key, raw, journal, connect,
                              clock, latest, *, company=None, expected_company_binding=None):
    """Explicit local D0 RUNNING->VERIFYING; no generic mutation or real effect.

    connect, clock and latest are trusted fixture dependencies, not independent proof.
    Failure after stage leaves durable quarantine; no automatic compensation or retry.
    """
    if type(journal) is not D0IntentJournal or binding_digest(intent, context, registry, witness) != expected_binding:
        raise ValueError('D0_FENCE_BINDING_HOLD')
    fence_binding = resolve_fence_binding(intent, expected_binding, company, expected_company_binding)
    pin = journal.stage(intent, fence_binding)
    try:
        with local_revocation_fence(memory_path, reader, journal):
            mapping = (D0PostgresTransitionMapping(context.invocation.lease, clock) if company is None
                       else D0AdmissionBoundTransitionMapping(company.admission, context.invocation.lease, clock))
            guard = WitnessedTransitionMapping(mapping, context, registry, witness, expected_binding,
                memory_path, reader, public_key, raw, lambda c: (_lease(c, intent, lock=True), clock(), latest()))
            if company is not None:
                # Company lock first; the same cursor then checks admission, lease, witness,
                # ordinary T1 roles and exact company postimage before COMMIT.
                guard = CompanyCoordinatedMapping(guard, company.members, company.pool, company.history, company.event)
            coordinator = LogicalT1Coordinator(lambda: postgres_transaction(connect, guard))
            receipt = coordinator.commit_transition(intent, context.invocation.run, RunState.VERIFYING)
        journal._record(intent, pin, receipt)
    except BaseException:
        # Even if writing UNKNOWN fails, PENDING remains a quarantine.
        try:
            journal._record(intent, pin)
        except Exception:
            pass
        raise
    return journal.inspect(intent, pin)
