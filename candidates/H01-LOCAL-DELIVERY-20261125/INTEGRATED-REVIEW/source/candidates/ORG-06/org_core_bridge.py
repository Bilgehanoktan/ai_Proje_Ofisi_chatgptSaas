"""ORG-06: historical Research-to-organization join, never an authority or HTTP API.

Only the existing Core readback and R3 SQLite store are used. The caller owns
one consistent, read-only Core cursor and retained pins. The separate ORG
snapshot is historical too; cross-store atomicity/current identity is NOT proven.
"""
from contextlib import closing
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BindingReview:
    reason: str
    structural_match: bool = False
    org_revision: str | None = None
    plan_revision: str | None = None
    project_id: str | None = None
    task_id: str | None = None
    seat_id: str | None = None
    role: str | None = None
    decision: str = field(default='HOLD', init=False)
    freshness: str = field(default='HISTORICAL_SAMPLE', init=False)
    authoritative: bool = field(default=False, init=False)
    runtime_binding: None = field(default=None, init=False)
    geometry_join: str = field(default='HOLD', init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    release_ready: bool = field(default=False, init=False)


class Hold(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise Hold(reason)


def _dependencies():
    # The actual pinned checkout is required; no substitute Runtime or IAM.
    from app.core.development_review.research_slice import inspect_research_slice, ResearchSliceReview
    from app.core.agent_runtime.lifecycle import valid_scope, uint
    from app.core.event_store.company_coordination import Member, SCOPE
    from app.core.event_store.plan_history_review import RunHistoryPin, TaskHistory
    from durable_ops import OperationsStore, check_pin
    from integration_guard import ReviewPin, inspect_runtime, token, hex_digest
    return (inspect_research_slice, ResearchSliceReview, valid_scope, uint, Member, SCOPE,
            RunHistoryPin, TaskHistory, OperationsStore, check_pin, ReviewPin, inspect_runtime, token, hex_digest)


def review_research_binding(cursor, *, plan, expected_revision, project_id, pins, members,
                            pool, events, anchor, store, org_head, history_pin,
                            task_id, seat_id, evidence=None):
    """Internal D0 readback; no public inputs or automatic handoff/assignment.

    Core verifies the persisted Research roster, task history and company
    membership. R3 separately verifies its immutable staffing/team/history.
    Both must match the exact same canonical scope, project, task and role.
    A structural match cannot authorize any mutation, placement or dispatch.
    """
    try:
        (inspect_core, CoreReview, valid_scope, uint, Member, core_scope, RunPin,
         TaskHistory, OpsStore, check_pin, ReviewPin, inspect_org, token, hex_digest) = _dependencies()
        require(type(store) is OpsStore and store._key == core_scope, 'ORG_SCOPE_HOLD')
        token(task_id); token(seat_id); token(project_id); hex_digest(org_head); check_pin(history_pin)
        require(type(pins) is tuple and type(members) is tuple, 'CORE_REFERENCE_HOLD')
        require(all(type(p) is RunPin for p in pins) and all(type(m) is Member for m in members), 'CORE_REFERENCE_HOLD')
        core = inspect_core(cursor, plan, expected_revision, project_id, pins, members,
                            pool, events, anchor, evidence=evidence)
        require(type(core) is CoreReview and core.structural_match is True and core.decision == 'HOLD'
                and core.freshness == 'HISTORICAL_SAMPLE' and core.dispatch_allowed is False
                and core.project_id == project_id and core.plan_revision == expected_revision,
                'CORE_READBACK_HOLD')
        require(type(core.tasks) is tuple and all(type(t) is TaskHistory for t in core.tasks), 'TASK_READBACK_HOLD')
        tasks = [t for t in core.tasks if t.task_id == task_id]
        runs = [p.initial for p in pins if p.initial.scope.task_id == task_id]
        roster = [m for m in members if m.task_id == task_id]
        require(len(tasks) == len(runs) == len(roster) == 1, 'TASK_MEMBERSHIP_HOLD')
        task, initial, member = tasks[0], runs[0], roster[0]
        scope = initial.scope
        require(valid_scope(scope) and (scope.tenant_id, scope.company_id, scope.environment_id) == core_scope
                and scope.plan_revision == expected_revision and scope.task_id == task_id,
                'CORE_SCOPE_HOLD')
        require(member.row() == (project_id, scope.plan_revision, scope.task_id, scope.run_id,
                                 scope.agent_instance_id, scope.principal_id, initial.version), 'CORE_MEMBER_HOLD')
        require(uint(task.version) and uint(initial.version) and task.version >= initial.version
                and task.role in ('orchestrator', 'research', 'engineer', 'qa'), 'TASK_ROLE_HOLD')
        # Existing R3 query-only transaction, not R5 PostgreSQL or Core's transaction.
        with closing(store._connect()) as db:
            db.execute('BEGIN')
            require(store._head(db) == org_head, 'ORG_HEAD_HOLD')
            staffing = store._read(db, org_head)[0]
            team = store._team(db, org_head, project_id, staffing)
            actual, _ = store._history(db, org_head, team, staffing)
            require(actual == history_pin and seat_id in team.members, 'ORG_TEAM_HISTORY_HOLD')
            revision = staffing.revision()
            observed = ReviewPin(*core_scope, revision, member.project_id, member.plan_revision,
                                 member.task_id, member.run_id, member.agent_instance_id, member.principal_id, task.role)
            expected = ReviewPin(*core_scope, revision, project_id, scope.plan_revision,
                                 scope.task_id, scope.run_id, scope.agent_instance_id, scope.principal_id, task.role)
            result = inspect_org(staffing, seat_id, observed, expected)
            require(result.get('structural_match') is True and result.get('decision') == 'HOLD'
                    and result.get('dispatch_allowed') is False and result.get('binding_created') is False
                    and result.get('authority') is False and all(result.get(k) is None for k in
                        ('agent_instance_id', 'principal_id', 'run_id')),
                    'ORG_BINDING_HOLD')
        # No identity, live state, credential, grant or geometry leaves this review.
        return BindingReview('D0_HISTORICAL_REFERENCE_MATCH_ONLY', True, org_head,
                             expected_revision, project_id, task_id, seat_id, task.role)
    except Hold as exc:
        return BindingReview(str(exc))
    except Exception:
        return BindingReview('REFERENCE_UNAVAILABLE_HOLD')
