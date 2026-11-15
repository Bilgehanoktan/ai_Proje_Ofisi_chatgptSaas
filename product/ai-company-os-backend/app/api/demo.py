"""D0 synthetic source candidate. No runtime, external calls, or mutating routes."""
from pathlib import Path
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


@app.get("/demo/v1/core/plan-projection")
def plan_projection():
    # Fixed synthetic fixture only; no user input or writes.
    sample = json.loads((FIXTURE.parent / "core.preview.json").read_text(encoding="utf-8"))
    try:
        return canonical_plan(sample["plan"])
    except GraphError as exc:
        raise HTTPException(status_code=409, detail={"mode": "D0_PLAN_HOLD", "reason": str(exc), "dispatch_allowed": False}) from exc


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
