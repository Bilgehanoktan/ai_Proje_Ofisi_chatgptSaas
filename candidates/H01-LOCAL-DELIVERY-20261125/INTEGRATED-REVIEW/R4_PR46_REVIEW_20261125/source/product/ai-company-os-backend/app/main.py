"""0160 compatibility facade; ASGI entrypoint remains app.main:app."""
from app.api.demo import (
    app,
    FIXTURE,
    demo_snapshot,
    status,
    catalog,
    authority,
    core_preview,
    plan_projection,
    authority_projection,
    preview_plan,
    canonical_plan,
    GraphError,
    replay_preview,
    validate_layout
)

__all__ = ["app", "FIXTURE", "demo_snapshot", "status", "catalog", "authority", "core_preview", "plan_projection", "authority_projection", "preview_plan", "canonical_plan", "GraphError", "replay_preview", "validate_layout"]
