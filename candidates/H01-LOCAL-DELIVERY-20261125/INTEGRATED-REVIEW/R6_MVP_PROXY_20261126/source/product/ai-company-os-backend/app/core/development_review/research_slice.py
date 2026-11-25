"""0224 fixed Research vertical slice: read-only D0 evidence, never a second engine.
Caller owns one consistent read-only T1 snapshot and separately retained fixture
pins. The local archive/journal are separate stores, not an atomic cross-store
snapshot or independent custody. No API, live placement, execution or release.
"""
from dataclasses import dataclass, field, replace
from app.core.agent_runtime.lifecycle import RunState, token
from app.core.agent_runtime.scheduler_review import inspect_pinned_schedule
from app.core.orchestrator.engine import canonical_plan

RESEARCH_REVISION = 'sha256:6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9'
ROOT = 'plan'
_PREFIX = (RunState.QUEUED, RunState.ADMITTED, RunState.RUNNING, RunState.VERIFYING)


@dataclass(frozen=True)
class ResearchRosterReview:
    reason: str
    structural_match: bool = False
    ready: tuple[str, ...] = ()
    root_state: str | None = None
    root_version: int | None = None
    decision: str = field(default='HOLD', init=False)
    dispatch_allowed: bool = field(default=False, init=False)


def review_research_roster(plan, expected_revision, project_id, initial, observations):
    """Pure identity/prefix preflight; does not read DB or bind an actual project."""
    try:
        projection = canonical_plan(plan)
        if (expected_revision != RESEARCH_REVISION or projection['revision'] != expected_revision
                or not token(project_id) or not project_id.startswith('demo-')):
            raise ValueError('D0_RESEARCH_PLAN_PIN_HOLD')
        schedule = inspect_pinned_schedule(plan, observations, initial)
        if any(r.version != 0 or r.attempt != 0 for r in initial):
            raise ValueError('D0_RESEARCH_INITIAL_HOLD')
        root = next(r for r in observations if r.scope.task_id == ROOT)
        if (root.state not in _PREFIX or root.version != _PREFIX.index(root.state)
                or any(r.state is not RunState.QUEUED or r.version != 0
                       for r in observations if r.scope.task_id != ROOT)):
            raise ValueError('D0_RESEARCH_PREFIX_HOLD')
        if schedule.ready != ((ROOT,) if root.state is RunState.QUEUED else ()):
            raise ValueError('D0_RESEARCH_READY_HOLD')
        return ResearchRosterReview('D0_RESEARCH_ROSTER_REFERENCE_ONLY', True, schedule.ready,
                                    root.state.value, root.version)
    except (ValueError, TypeError, AttributeError, KeyError, StopIteration, OverflowError, RecursionError):
        return ResearchRosterReview('D0_RESEARCH_ROSTER_HOLD')


def inspect_research_company_roster(cursor, plan, expected_revision, project_id, initial,
                                    members, pool, events):
    """Exact company membership/ordering on caller's read-only T1 cursor.

    Company match alone is NOT lifecycle proof. The plan-history reader must
    still reconcile the state machine and all retained commands on this cursor.
    """
    from app.core.event_store.company_coordination import Member, CompanyReview, inspect_company
    try:
        pre = review_research_roster(plan, expected_revision, project_id, initial, initial)
        if not pre.structural_match or type(members) is not tuple:
            raise ValueError('D0_RESEARCH_ROSTER_HOLD')
        expected = tuple(Member(project_id, r.scope.plan_revision, r.scope.task_id, r.scope.run_id,
                                r.scope.agent_instance_id, r.scope.principal_id, r.version) for r in initial)
        if (len(members) != len(expected) or not all(type(m) is Member for m in members)
                or set(members) != set(expected)):
            raise ValueError('D0_RESEARCH_MEMBERSHIP_HOLD')
        return inspect_company(cursor, members, pool, events)
    except Exception:
        return CompanyReview('D0_RESEARCH_COMPANY_ROSTER_HOLD')


@dataclass(frozen=True)
class ResearchResultEvidence:
    """Exact 0221 inputs retained at the historical execution boundary."""
    context: object
    registry: tuple
    witness: object
    witness_binding: str
    company: object
    company_binding: str
    result: object
    result_reader: object
    clock: object
    raw: bytes = field(repr=False)
    journal: object = field(repr=False)


@dataclass(frozen=True)
class ResearchSliceReview:
    reason: str
    structural_match: bool = False
    project_id: str | None = None
    plan_revision: str | None = None
    root_run_id: str | None = None
    root_state: str | None = None
    root_version: int | None = None
    event_count: int | None = None
    evidence_sha: str | None = None
    tasks: tuple = ()
    qa_status: str = field(default='DEPENDENCY_HOLD', init=False)
    iv_status: str = field(default='INDEPENDENT_RECEIPT_HOLD', init=False)
    release_status: str = field(default='H01_HOLD', init=False)
    world_id: None = field(default=None, init=False)
    decision: str = field(default='HOLD', init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    provider_called: bool = field(default=False, init=False)
    tool_called: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    release_ready: bool = field(default=False, init=False)
    independent_verified: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)
    freshness: str = field(default='HISTORICAL_SAMPLE', init=False)


def inspect_research_slice(cursor, plan, expected_revision, project_id, pins, members,
                           pool, events, anchor, *, evidence=None):
    """Exact single-project root prefix using original plan/company readbacks.

    All T1 reads must share caller's consistent snapshot. Result linkage requires
    the existing hash-only archive and local HISTORICAL intent receipt, not just
    a VERIFYING head. UNKNOWN/PENDING never authorize retry. No cross-store
    atomicity, independent signature or current lease/skill assignment is proven.
    """
    from app.core.event_store.plan_history_review import RunHistoryPin, inspect_plan_history
    from app.core.event_store.company_coordination import Pool, Allocation
    from app.core.event_store.history_readback import OrdinaryPin
    from app.core.transaction.postgres_admission_mapping import valid_budget
    from app.core.transaction.postgres_transition_mapping import transaction_ref
    from app.core.transaction.fenced_transition import (CompanyTransitionContext, SampleResultPin,
        D0IntentJournal, resolve_result_binding, intent_pin)
    try:
        if (type(pins) is not tuple or type(members) is not tuple or type(events) is not tuple
                or not all(type(p) is RunHistoryPin for p in pins) or type(pool) is not Pool
                or not valid_budget(anchor) or anchor.outstanding_minor or anchor.recognized_cost_minor
                or anchor.unknown_cost or (pool.budget_id, pool.currency, pool.limit_minor, pool.revision,
                    pool.policy_epoch, pool.witness_epoch, pool.source_digest) != (anchor.budget_id,
                    anchor.currency, anchor.limit_minor, anchor.revision, anchor.policy_epoch,
                    anchor.witness_epoch, anchor.source_digest)
                or pool.allocations != (Allocation(project_id, pool.limit_minor),)):
            raise ValueError('D0_RESEARCH_INPUT_HOLD')
        initial = tuple(p.initial for p in pins)
        company = inspect_research_company_roster(cursor, plan, expected_revision, project_id,
                                                   initial, members, pool, events)
        if not company.structural_match:
            raise ValueError('D0_RESEARCH_MEMBERSHIP_HOLD')
        history = inspect_plan_history(cursor, plan, expected_revision, pins, exclusive_budget_anchors=(anchor,))
        if (not history.structural_match or not history.budget_reconciled or not company.structural_match
                or history.event_count != len(events) or company.event_count != len(events)):
            raise ValueError('D0_RESEARCH_SNAPSHOT_HOLD')
        by_task = {t.task_id: t for t in history.tasks}
        observed = tuple(replace(r, state=RunState(by_task[r.scope.task_id].state),
                                 version=by_task[r.scope.task_id].version) for r in initial)
        roster = review_research_roster(plan, expected_revision, project_id, initial, observed)
        if not roster.structural_match or roster.root_version != len(events):
            raise ValueError('D0_RESEARCH_PREFIX_HOLD')
        root = next(p for p in pins if p.initial.scope.task_id == ROOT)
        for p in pins:
            if p is not root and (p.admission is not None or p.commands):
                raise ValueError('D0_RESEARCH_DEPENDENT_HOLD')
        # Require the exact admission -> ordinary RUNNING -> ordinary VERIFYING prefix.
        commands = root.commands
        if (len(commands) != max(0, len(events)-1) or
                (root.admission is None) != (not events) or
                any(type(c) is not OrdinaryPin or c.target is not _PREFIX[i+2]
                    for i, c in enumerate(commands))):
            raise ValueError('D0_RESEARCH_COMMAND_HOLD')
        intents = () if not events else (root.admission.intent, *(c.intent for c in commands))
        for i, (event, intent) in enumerate(zip(events, intents)):
            if ((event.project_id, event.run_id, event.version, event.transaction_ref,
                 event.request_digest, event.kind) != (project_id, root.initial.scope.run_id, i+1,
                 transaction_ref(intent), intent.request_digest,
                 'D0_RUN_ADMISSION' if i == 0 else 'D0_RUN_TRANSITION')):
                raise ValueError('D0_RESEARCH_EVENT_LINK_HOLD')
        digest = None
        if evidence is not None:
            if (type(evidence) is not ResearchResultEvidence or roster.root_state != 'VERIFYING'
                    or type(evidence.result) is not SampleResultPin or type(evidence.journal) is not D0IntentJournal
                    or type(evidence.company) is not CompanyTransitionContext):
                raise ValueError('D0_RESEARCH_RESULT_SHAPE_HOLD')
            last = commands[-1]
            c = evidence.company
            if (c.admission != root.admission or c.members != members or c.pool != pool
                    or c.history != events[:-1] or c.event != events[-1]
                    or evidence.context.invocation.run != last.before
                    or evidence.context.invocation.lease != last.lease):
                raise ValueError('D0_RESEARCH_RESULT_LINK_HOLD')
            binding = resolve_result_binding(last.intent, evidence.context, evidence.registry,
                evidence.witness, evidence.witness_binding, c, evidence.company_binding,
                evidence.result, evidence.result_reader, evidence.clock, evidence.raw)
            receipt = evidence.journal.inspect(last.intent, intent_pin(last.intent, binding))
            if receipt.status != 'HISTORICAL' or not receipt.historical_match:
                raise ValueError('D0_RESEARCH_RESULT_QUARANTINE_HOLD')
            digest = evidence.result.evidence_sha
        return ResearchSliceReview('D0_RESEARCH_ROOT_RESULT_EVIDENCE_ONLY' if digest else
            'D0_RESEARCH_PREFIX_ONLY_RESULT_NOT_PROVEN', True, project_id, expected_revision,
            root.initial.scope.run_id, roster.root_state, roster.root_version, len(events), digest, history.tasks)
    except Exception:
        return ResearchSliceReview('D0_RESEARCH_SLICE_HOLD')
