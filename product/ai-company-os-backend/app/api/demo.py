"""D0 synthetic source candidate. No runtime, external calls, or mutating routes."""
from pathlib import Path
from hashlib import sha256
import json
from fastapi import FastAPI, HTTPException

app = FastAPI(title="AI Company OS — D0 demo only", docs_url=None, redoc_url=None, openapi_url=None)
FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "office.snapshot.json"

@app.get("/demo/v1/office/worlds/{world_id}/snapshot")
def demo_snapshot(world_id: str):
    if world_id != "demo-world":
        raise HTTPException(status_code=404, detail="Demo world not found")
    return json.loads(FIXTURE.read_text(encoding="utf-8"))

@app.get("/demo/v1/status")
def status():
    return {"mode":"D0_SAMPLE_NO_RUNTIME","security_acceptance":"HOLD","release_ready":False,"real_test":"NOT_RUN"}


from app.demo_policy import authority_projection

@app.get("/demo/v1/catalog")
def catalog():
    return json.loads((FIXTURE.parent / "company.catalog.json").read_text(encoding="utf-8"))

@app.get("/demo/v1/authority")
def authority():
    return authority_projection()


from app.core.orchestrator.engine import preview_plan, canonical_plan
from app.core.task_engine.dag import GraphError
from app.core.event_store.ledger import replay_preview
from app.engines.office_engine.layout import validate_layout

@app.get("/demo/v1/core/preview")
def core_preview():
    sample = json.loads((FIXTURE.parent / "core.preview.json").read_text(encoding="utf-8"))
    validate_layout(sample["layout"])
    return {"sample": sample, "plan_preview": preview_plan(sample["plan"]),
            "event_preview": replay_preview(sample["events"], sample["layout"])}


# These exact D0 file pins match the canonical product SOURCE_MANIFEST.
# A content digest is not a signature, IAM grant, runtime receipt or release proof.
_CORE_PLAN_FILES = {
    "core.preview.json": (8418, "3f06282142ca685f21cce6a83ebb6341fe3b8c470027b912662c6d879f15256b"),
    "core.plan.projection.json": (2462, "e564bed4f4edfb5dd94488b08cbba3205b6f018491fadd8d200d884a85e1f4bb"),
}


def _pinned_plan_json(name):
    expected_size, expected_digest = _CORE_PLAN_FILES[name]
    with (FIXTURE.parent / name).open("rb") as file:
        raw = file.read(expected_size + 1)
    if len(raw) != expected_size or sha256(raw).hexdigest() != expected_digest:
        raise ValueError("D0_PLAN_SOURCE_PIN_HOLD")
    return json.loads(raw.decode("utf-8"))


def _canonical_plan_wire(value):
    """Type-sensitive JSON comparison; Python dict equality conflates bool and int."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


@app.get("/demo/v1/core/plan-projection")
def plan_projection():
    """Read the existing fixed compiler output, never synthesize real authority."""
    headers = {"Cache-Control": "no-store"}
    from fastapi.responses import JSONResponse
    try:
        sample = _pinned_plan_json("core.preview.json")
        result = canonical_plan(sample["plan"])
        expected = _pinned_plan_json("core.plan.projection.json")
        if _canonical_plan_wire(result) != _canonical_plan_wire(expected):
            raise ValueError("D0_PLAN_RESPONSE_DRIFT_HOLD")
        return JSONResponse(result, headers=headers)
    except GraphError as exc:
        return JSONResponse(
            {"detail": {"mode": "D0_PLAN_HOLD", "reason": str(exc), "dispatch_allowed": False}},
            status_code=409, headers=headers,
        )
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return JSONResponse(
            {"mode": "D0_PLAN_READBACK_HOLD"}, status_code=503, headers=headers,
        )


from fastapi.responses import JSONResponse
from app.api.mvp_diagnostics import inspect_mvp

@app.get("/demo/v1/mvp/diagnostics")
def mvp_diagnostics():
    # Fixed local fixture only. Never accepts tenant, model or action input.
    try:
        sample = json.loads((FIXTURE.parent / "core.preview.json").read_text(encoding="utf-8"))
        validate_layout(sample["layout"])
        return JSONResponse(inspect_mvp(sample), headers={"Cache-Control": "no-store"})
    except (GraphError, ValueError, KeyError, TypeError, StopIteration, OSError) as exc:
        raise HTTPException(status_code=409, detail={"mode": "D0_READBACK_HOLD"}) from exc


from app.api.outbox_projection import router as outbox_projection_router
app.include_router(outbox_projection_router)


from app.api.admission_projection import router as admission_projection_router
app.include_router(admission_projection_router)


from app.api.office_workbench_projection import router as office_workbench_projection_router
app.include_router(office_workbench_projection_router)


from app.api.task_budget_projection import router as task_budget_projection_router
app.include_router(task_budget_projection_router)


from app.api.lifecycle_projection import router as lifecycle_projection_router
app.include_router(lifecycle_projection_router)


from app.api.lifecycle_prefix_projection import router as lifecycle_prefix_projection_router
app.include_router(lifecycle_prefix_projection_router)
