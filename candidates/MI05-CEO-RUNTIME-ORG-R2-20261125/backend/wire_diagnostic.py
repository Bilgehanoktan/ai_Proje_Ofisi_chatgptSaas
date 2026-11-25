"""Test-only fixture transport. The persisted Runtime reader is NOT executed here."""
from plan_slice import app
from pathlib import Path
from fastapi.responses import Response
from app.core.development_review.lifecycle_prefix_wire import prefix_wire
from app.core.development_review.shared_snapshot import build_shared_replay
@app.get('/demo/v1/lifecycle/shared-snapshot')
def fixture_replay():
    text=build_shared_replay(prefix_wire(4))
    if (Path(__file__).parent/'tamper_runtime').exists():
        text=text.replace('"agent_instance_id":"demo-agent"','"agent_instance_id":"other"',1)
    return Response(text,media_type='text/event-stream',headers={'Cache-Control':'no-store'})
