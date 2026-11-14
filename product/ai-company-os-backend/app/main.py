"""D0 synthetic source candidate. No runtime, external calls, or mutating routes."""
from pathlib import Path
import json
from fastapi import FastAPI, HTTPException

app = FastAPI(title="AI Company OS — D0 demo only", docs_url=None, redoc_url=None, openapi_url=None)
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "office.snapshot.json"

@app.get("/demo/v1/office/worlds/{world_id}/snapshot")
def demo_snapshot(world_id: str):
    if world_id != "demo-world":
        raise HTTPException(status_code=404, detail="Demo world not found")
    return json.loads(FIXTURE.read_text(encoding="utf-8"))

@app.get("/demo/v1/status")
def status():
    return {"mode":"D0_SAMPLE_NO_RUNTIME","security_acceptance":"HOLD","release_ready":False,"real_test":"NOT_RUN"}


from .demo_policy import authority_projection

@app.get("/demo/v1/catalog")
def catalog():
    return json.loads((FIXTURE.parent / "company.catalog.json").read_text(encoding="utf-8"))

@app.get("/demo/v1/authority")
def authority():
    return authority_projection()


from .core.orchestrator import preview_plan, canonical_plan
from .core.dag import GraphError
from .core.event_store import replay_preview
from .core.office import validate_layout

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
