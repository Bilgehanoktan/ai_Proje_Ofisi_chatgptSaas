"""0160 compatibility facade; implementation at app.core.agent_runtime.lifecycle."""
from app.core.agent_runtime.lifecycle import (
    RunState,
    TERMINAL,
    SYNTHETIC_TENANT,
    SYNTHETIC_ENV,
    token,
    uint,
    Scope,
    valid_scope,
    LeaseObservation,
    ClockSample,
    Inspection,
    valid_lease,
    inspect_lease,
    RunObservation,
    EDGES,
    TransitionPreview,
    inspect_transition,
    inspect_renewal
)

__all__ = ["RunState", "TERMINAL", "SYNTHETIC_TENANT", "SYNTHETIC_ENV", "token", "uint", "Scope", "valid_scope", "LeaseObservation", "ClockSample", "Inspection", "valid_lease", "inspect_lease", "RunObservation", "EDGES", "TransitionPreview", "inspect_transition", "inspect_renewal"]
