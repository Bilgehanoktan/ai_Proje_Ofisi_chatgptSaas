"""0160 compatibility facade; implementation at app.core.policy.witness_review."""
from app.core.policy.witness_review import (
    WitnessSample,
    WitnessReview,
    valid_witness,
    inspect_witness,
    RestoreObservation,
    RestoreReview,
    inspect_restore
)

__all__ = ["WitnessSample", "WitnessReview", "valid_witness", "inspect_witness", "RestoreObservation", "RestoreReview", "inspect_restore"]
