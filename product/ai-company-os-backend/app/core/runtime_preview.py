"""R01/D07: pure, synthetic inspection only. No authority, clock, IO or state writer."""
from dataclasses import dataclass
from enum import Enum
import re


class RunState(str, Enum):
    CREATED = 'CREATED'
    QUEUED = 'QUEUED'
    ADMITTED = 'ADMITTED'
    PLANNING = 'PLANNING'
    RUNNING = 'RUNNING'
    WAITING_APPROVAL = 'WAITING_APPROVAL'
    VERIFYING = 'VERIFYING'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'
    TIMED_OUT = 'TIMED_OUT'


TERMINAL = frozenset({RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED, RunState.TIMED_OUT})
SYNTHETIC_TENANT = 'synthetic-tenant'
SYNTHETIC_ENV = 'A0_SAMPLE_ONLY'


def token(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value) is not None


def uint(value: object) -> bool:
    return type(value) is int and 0 <= value <= 2**63 - 1


@dataclass(frozen=True)
class Scope:
    tenant_id: str
    company_id: str
    environment_id: str
    plan_revision: str
    task_id: str
    run_id: str
    agent_instance_id: str
    principal_id: str


def valid_scope(s: object) -> bool:
    return (isinstance(s, Scope) and s.tenant_id == SYNTHETIC_TENANT
            and s.environment_id == SYNTHETIC_ENV and s.company_id == 'synthetic-company'
            and isinstance(s.plan_revision, str)
            and re.fullmatch(r'sha256:[0-9a-f]{64}', s.plan_revision) is not None
            and all(token(v) and v.startswith('demo-') for v in (s.run_id, s.agent_instance_id, s.principal_id))
            and token(s.task_id))


@dataclass(frozen=True)
class LeaseObservation:
    scope: Scope
    lease_id: str
    grant_id: str
    lease_version: int
    heartbeat_revision: int
    fence: int
    policy_epoch: int
    witness_epoch: int
    expires_tick: int
    heartbeat_tick: int


@dataclass(frozen=True)
class ClockSample:
    now_tick: int
    policy_epoch: int
    witness_epoch: int
    max_heartbeat_age: int


@dataclass(frozen=True)
class Inspection:
    freshness: str
    reason: str
    decision: str = 'HOLD'
    dispatch_allowed: bool = False


def valid_lease(l: object) -> bool:
    return (isinstance(l, LeaseObservation) and valid_scope(l.scope)
            and token(l.lease_id) and token(l.grant_id)
            and all(uint(v) for v in (l.lease_version, l.heartbeat_revision, l.fence,
                    l.policy_epoch, l.witness_epoch, l.expires_tick, l.heartbeat_tick))
            and l.lease_version > 0 and l.fence > 0 and l.heartbeat_tick < l.expires_tick)


def inspect_lease(sample: LeaseObservation | None, expected: LeaseObservation | None,
                  clock: ClockSample | None) -> Inspection:
    """Expected is an independent *synthetic* reference, never a real authority."""
    if not valid_lease(sample) or not valid_lease(expected):
        return Inspection('UNKNOWN', 'LEASE_REFERENCE_INVALID_OR_MISSING')
    if not isinstance(clock, ClockSample) or not all(uint(v) for v in (
            clock.now_tick, clock.policy_epoch, clock.witness_epoch, clock.max_heartbeat_age)) or clock.max_heartbeat_age == 0:
        return Inspection('UNKNOWN', 'CLOCK_SAMPLE_INVALID')
    if sample.scope != expected.scope:
        return Inspection('UNKNOWN', 'LEASE_SCOPE_MISMATCH', 'DENY')
    if sample != expected:
        return Inspection('STALE', 'LEASE_REFERENCE_MISMATCH')
    if expected.witness_epoch != clock.witness_epoch:
        return Inspection('STALE', 'ERR_WA_EPOCH_STALE', 'DENY')
    if expected.policy_epoch != clock.policy_epoch:
        return Inspection('STALE', 'ERR_POLICY_EPOCH_STALE', 'DENY')
    if clock.now_tick >= expected.expires_tick:
        return Inspection('STALE', 'LEASE_EXPIRED')
    if clock.now_tick < expected.heartbeat_tick:
        return Inspection('UNKNOWN', 'HEARTBEAT_IN_FUTURE')
    if clock.now_tick - expected.heartbeat_tick > clock.max_heartbeat_age:
        return Inspection('STALE', 'HEARTBEAT_STALE')
    return Inspection('FRESH', 'D0_REFERENCE_MATCH_ONLY')


@dataclass(frozen=True)
class RunObservation:
    scope: Scope
    state: RunState
    version: int
    attempt: int


# Candidate topology, not normative or an executable scheduler. Terminal states cannot be reopened.
EDGES = {
    RunState.CREATED: frozenset({RunState.QUEUED, RunState.CANCELLED}),
    RunState.QUEUED: frozenset({RunState.ADMITTED, RunState.CANCELLED, RunState.TIMED_OUT}),
    RunState.ADMITTED: frozenset({RunState.PLANNING, RunState.RUNNING, RunState.CANCELLED, RunState.TIMED_OUT}),
    RunState.PLANNING: frozenset({RunState.RUNNING, RunState.CANCELLED, RunState.FAILED, RunState.TIMED_OUT}),
    RunState.RUNNING: frozenset({RunState.WAITING_APPROVAL, RunState.VERIFYING, RunState.FAILED, RunState.CANCELLED, RunState.TIMED_OUT}),
    RunState.WAITING_APPROVAL: frozenset({RunState.RUNNING, RunState.CANCELLED, RunState.TIMED_OUT}),
    RunState.VERIFYING: frozenset({RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED, RunState.TIMED_OUT}),
}


@dataclass(frozen=True)
class TransitionPreview:
    structural_edge: bool
    reason: str
    decision: str = 'HOLD'
    commit_allowed: bool = False
    dispatch_allowed: bool = False
    next_version: int | None = None


def inspect_transition(run: RunObservation, target: RunState, expected_version: int,
                       lease: LeaseObservation | None, reference: LeaseObservation | None,
                       clock: ClockSample | None, outcome_unknown: bool = False) -> TransitionPreview:
    """Returns diagnostics, never a new canonical RunState or an executable intent."""
    if (not isinstance(run, RunObservation) or not valid_scope(run.scope)
            or not isinstance(run.state, RunState) or not isinstance(target, RunState)
            or not uint(run.version) or not uint(run.attempt) or not uint(expected_version)
            or type(outcome_unknown) is not bool):
        return TransitionPreview(False, 'RUN_ENVELOPE_INVALID', 'DENY')
    if run.version != expected_version or run.version == 2**63-1:
        return TransitionPreview(False, 'CAS_VERSION_MISMATCH_OR_EXHAUSTED')
    edge = target in EDGES.get(run.state, frozenset())
    if not edge:
        return TransitionPreview(False, 'RUN_EDGE_INVALID', 'DENY')
    if outcome_unknown:
        return TransitionPreview(True, 'ERR_PROVIDER_RESULT_UNKNOWN')
    if target == RunState.CANCELLED:
        return TransitionPreview(True, 'STOP_REQUEST_REQUIRES_AUTHORITY_AND_T1')
    if target == RunState.SUCCEEDED:
        return TransitionPreview(True, 'INDEPENDENT_RECEIPT_AND_T1_REQUIRED')
    if not valid_lease(lease) or lease.scope != run.scope:
        return TransitionPreview(True, 'RUN_LEASE_BINDING_MISSING')
    observation = inspect_lease(lease, reference, clock)
    if observation.freshness != 'FRESH':
        return TransitionPreview(True, observation.reason, observation.decision)
    return TransitionPreview(True, 'T1_ATOMICITY_NOT_PROVEN')


def inspect_renewal(sample: LeaseObservation | None, expected: LeaseObservation | None,
                    clock: ClockSample | None) -> Inspection:
    result = inspect_lease(sample, expected, clock)
    if result.freshness != 'FRESH':
        return result
    return Inspection('FRESH', 'LIVE_GRANT_WA_AND_CAS_REQUIRED')
