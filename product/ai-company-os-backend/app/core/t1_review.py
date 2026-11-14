"""R03 D0 logical write-set inspection. No DB, SQL, real commit, or provider call.
Physical four/five/seven mapping remains HOLD. These names are logical roles only.
"""
from dataclasses import dataclass
from enum import Enum
import re
from .runtime_preview import Scope, LeaseObservation, ClockSample, valid_scope, token, uint, inspect_lease


class Operation(str, Enum):
    ADMISSION = 'ADMISSION'
    STATE_MUTATION = 'STATE_MUTATION'
    TERMINAL = 'TERMINAL'


BASE_ROLES = frozenset({'HEAD', 'MUTATION', 'FENCE', 'EVENT', 'OUTBOX', 'AUDIT'})
REQUIRED = {
    Operation.ADMISSION: BASE_ROLES | {'ADMISSION', 'LEASE', 'BUDGET'},
    Operation.STATE_MUTATION: BASE_ROLES,
    Operation.TERMINAL: BASE_ROLES | {'LEASE', 'BUDGET'},
}


def digest_ok(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


@dataclass(frozen=True)
class LogicalIntent:
    scope: Scope
    operation: Operation
    expected_version: int
    request_digest: str
    effect_key: str
    idempotency_key: str
    grant_ref: str
    lease_ref: str
    budget_ref: str | None
    policy_epoch: int
    witness_epoch: int
    lease_or_budget_changes: bool = False


@dataclass(frozen=True)
class RoleObservation:
    role: str
    record_id: str
    scope: Scope
    request_digest: str
    transaction_ref: str
    expected_version: int
    policy_epoch: int
    witness_epoch: int


@dataclass(frozen=True)
class T1Review:
    reason: str
    structural_match: bool = False
    missing_roles: tuple[str, ...] = ()
    decision: str = 'HOLD'
    committed: bool = False
    commit_allowed: bool = False
    dispatch_allowed: bool = False
    physical_mapping: str = 'PHYSICAL_MAPPING_HOLD'
    committed_version: int | None = None


def valid_intent(i: object) -> bool:
    return (isinstance(i, LogicalIntent) and valid_scope(i.scope) and isinstance(i.operation, Operation)
            and uint(i.expected_version) and i.expected_version < 2**63-1 and digest_ok(i.request_digest)
            and all(token(v) for v in (i.effect_key, i.idempotency_key, i.grant_ref, i.lease_ref))
            and (i.budget_ref is None or token(i.budget_ref)) and uint(i.policy_epoch) and uint(i.witness_epoch)
            and type(i.lease_or_budget_changes) is bool)


def required_roles(i: LogicalIntent) -> frozenset[str]:
    return REQUIRED[i.operation] | ({'LEASE', 'BUDGET'} if i.lease_or_budget_changes else set())


def inspect_write_set(i: LogicalIntent, rows: tuple[RoleObservation, ...], head_version: int,
                      lease: LeaseObservation | None, reference: LeaseObservation | None,
                      clock: ClockSample | None) -> T1Review:
    """Check synthetic proposal completeness, not physical readback or transactional proof."""
    if not valid_intent(i) or not uint(head_version) or not isinstance(rows, tuple) or len(rows) > 9:
        return T1Review('INTENT_OR_ROWS_INVALID', decision='DENY')
    if head_version != i.expected_version:
        return T1Review('CAS_VERSION_MISMATCH')
    needed = required_roles(i)
    if 'BUDGET' in needed and not i.budget_ref:
        return T1Review('BUDGET_REFERENCE_MISSING')
    if not isinstance(lease, LeaseObservation) or lease.scope != i.scope or lease.lease_id != i.lease_ref or lease.grant_id != i.grant_ref or (lease.policy_epoch, lease.witness_epoch) != (i.policy_epoch, i.witness_epoch):
        return T1Review('LEASE_INTENT_BINDING_MISMATCH', decision='DENY')
    freshness = inspect_lease(lease, reference, clock)
    if freshness.freshness != 'FRESH':
        return T1Review(freshness.reason, decision=freshness.decision)
    seen, ids, tx = set(), set(), set()
    for r in rows:
        if not isinstance(r, RoleObservation) or not isinstance(r.role, str) or r.role not in needed or not token(r.record_id) or not token(r.transaction_ref):
            return T1Review('ROLE_ENVELOPE_INVALID', decision='DENY')
        if r.role in seen or r.record_id in ids:
            return T1Review('DUPLICATE_ROLE_OR_RECORD', decision='DENY')
        if (r.scope != i.scope or r.request_digest != i.request_digest or not uint(r.expected_version) or r.expected_version != i.expected_version
                or not uint(r.policy_epoch) or not uint(r.witness_epoch) or (r.policy_epoch, r.witness_epoch) != (i.policy_epoch, i.witness_epoch)):
            return T1Review('ROLE_SCOPE_DIGEST_VERSION_EPOCH_MISMATCH', decision='DENY')
        seen.add(r.role); ids.add(r.record_id); tx.add(r.transaction_ref)
    missing = tuple(sorted(needed - seen))
    if missing:
        return T1Review('WRITE_SET_INCOMPLETE', missing_roles=missing)
    if len(tx) != 1:
        return T1Review('TRANSACTION_REFERENCE_MISMATCH', decision='DENY')
    return T1Review('T1_ATOMICITY_NOT_PROVEN', structural_match=True)


class DisabledT1Coordinator:
    """Never creates a commit receipt, even for complete caller-supplied observations."""
    def commit(self, intent: LogicalIntent) -> T1Review:
        return T1Review('T1_DISABLED_NO_DEV_NO_F3', decision='DENY')
