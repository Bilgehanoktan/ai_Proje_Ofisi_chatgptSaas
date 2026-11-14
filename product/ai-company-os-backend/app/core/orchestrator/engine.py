"""Pure D0 plan compiler. No dispatch, task writes, workers or external I/O."""
import hashlib
import json
from app.core.task_engine.dag import Task, GraphError, valid_id, topological_waves, validate_release_boundary
from app.core.policy.denial import EffectRequest, deny_effect

SCOPE = {"tenant_id": "synthetic-tenant", "environment_id": "A0_SAMPLE_ONLY"}


def parse_plan(plan: dict) -> tuple[Task, ...]:
    if not isinstance(plan, dict) or set(plan) != {"id", "worktype", "tasks"} or not valid_id(plan.get("id")):
        raise GraphError("PLAN_ENVELOPE_INVALID")
    if plan["worktype"] != "RESEARCH":
        raise GraphError("UNSUPPORTED_DEMO_WORKTYPE")
    raw = plan["tasks"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= 100:
        raise GraphError("TASK_COUNT_INVALID")
    tasks = []
    for row in raw:
        if not isinstance(row, dict) or set(row) != {"id", "label", "role", "depends_on"} or not isinstance(row["depends_on"], list):
            raise GraphError("TASK_ENVELOPE_INVALID")
        tasks.append(Task(row["id"], row["label"], row["role"], tuple(row["depends_on"])))
    result = tuple(tasks)
    validate_release_boundary(result)
    return result


def canonical_plan(plan: dict) -> dict:
    """Validated projection; digest binds content, not signature or admission evidence."""
    tasks = parse_plan(plan)
    waves = topological_waves(tasks)
    body = {"schema_version": "core.plan.projection.v1-D0", "scope": dict(SCOPE),
            "plan_id": plan["id"], "worktype": plan["worktype"],
            "tasks": [{"id": t.id, "label": t.label, "role": t.role,
                       "depends_on": sorted(t.depends_on), "state": "HOLD", "run_id": None}
                      for t in sorted(tasks, key=lambda t: t.id)],
            "waves": [list(w) for w in waves],
            "edges": [{"from": d, "to": t.id} for t in sorted(tasks, key=lambda t: t.id)
                      for d in sorted(t.depends_on)],
            "validation": "VALIDATED_D0_GRAPH", "admission": "DENY",
            "dispatch_allowed": False, "release_ready": False, "real_run_count": None}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return {**body, "digest": digest, "revision": "sha256:" + digest}


def preview_plan(plan: dict) -> dict:
    """Original v0 wire format retained; canonical compiler is the graph authority."""
    projection = canonical_plan(plan)
    denial = deny_effect(EffectRequest("synthetic-tenant", "A0_SAMPLE_ONLY", "RUN_ADMISSION"))
    by_id = {t["id"]: t for t in projection["tasks"]}
    return {"plan_id": projection["plan_id"], "mode": "D0_PLAN_PREVIEW", "waves": projection["waves"],
            "tasks": [{"id": t["id"], "role": by_id[t["id"]]["role"], "state": "HOLD", "run_id": None}
                      for t in plan["tasks"]],
            "admission": denial.decision, "reasons": list(denial.reasons), "dispatch_allowed": False,
            "real_run_count": None, "release_ready": False}
