"""0160 compatibility facade; implementation at app.core.policy.denial."""
from app.core.policy.denial import (
    EffectRequest,
    Denial,
    deny_effect
)

__all__ = ["EffectRequest", "Denial", "deny_effect"]
