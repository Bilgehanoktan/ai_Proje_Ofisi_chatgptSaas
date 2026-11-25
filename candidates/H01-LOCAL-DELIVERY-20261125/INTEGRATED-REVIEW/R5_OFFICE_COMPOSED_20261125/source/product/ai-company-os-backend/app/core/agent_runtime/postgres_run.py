"""0193 D0 candidate run-head repository. No connection, commit, or authority."""
from app.core.agent_runtime.lifecycle import RunObservation, RunState, valid_scope, uint

_SCOPE = ("tenant_id", "company_id", "environment_id", "plan_revision", "task_id",
          "run_id", "agent_instance_id", "principal_id")
_WHERE = " AND ".join(f"{name}=%s" for name in _SCOPE)
_TABLE = "t1_candidate.run_heads"


def _scope_values(scope):
    if not valid_scope(scope):
        raise ValueError("RUN_SCOPE_INVALID")
    return tuple(getattr(scope, key) for key in _SCOPE)


def _observation(scope, row):
    if row is None:
        raise ValueError("RUN_HEAD_NOT_FOUND")
    state, version, attempt = row
    if not uint(version) or not uint(attempt):
        raise ValueError("RUN_HEAD_INVALID")
    return RunObservation(scope, RunState(state), version, attempt)


class PostgresRunRepository:
    """Use an existing T1 cursor; caller owns transaction and authority checks.

    Requires explicit R03 mapping integration. No automatic schema setup.
    """
    def lock(self, cursor, scope):
        cursor.execute(f"SELECT state, version, attempt FROM {_TABLE} WHERE {_WHERE} FOR UPDATE",
                       _scope_values(scope))
        return _observation(scope, cursor.fetchone())

    def read(self, cursor, scope):
        cursor.execute(f"SELECT state, version, attempt FROM {_TABLE} WHERE {_WHERE}",
                       _scope_values(scope))
        return _observation(scope, cursor.fetchone())

    def advance(self, cursor, before, target):
        # SQL is deliberately limited to the same non-special transition edges;
        # authorization and intent validation remain the coordinator's responsibility.
        from app.core.agent_runtime.lifecycle import EDGES
        if (not isinstance(before, RunObservation) or not isinstance(before.state, RunState)
                or not isinstance(target, RunState) or target not in (
                    RunState.PLANNING, RunState.RUNNING, RunState.VERIFYING)
                or before.state == RunState.WAITING_APPROVAL
                or target not in EDGES.get(before.state, ())
                or not uint(before.version) or before.version == 2**63-1
                or not uint(before.attempt)):
            raise ValueError("RUN_HEAD_EDGE_INVALID")
        scope_values = _scope_values(before.scope)
        cursor.execute(f"UPDATE {_TABLE} SET state=%s, version=version+1 WHERE {_WHERE} "
                       "AND state=%s AND version=%s AND attempt=%s RETURNING state, version, attempt",
                       (target.value, *scope_values, before.state.value, before.version, before.attempt))
        row = cursor.fetchone()
        if row is None:
            raise ValueError("RUN_HEAD_CAS_MISMATCH")
        after = _observation(before.scope, row)
        if after != RunObservation(before.scope, target, before.version+1, before.attempt):
            raise ValueError("RUN_HEAD_POSTIMAGE_MISMATCH")
        return after
