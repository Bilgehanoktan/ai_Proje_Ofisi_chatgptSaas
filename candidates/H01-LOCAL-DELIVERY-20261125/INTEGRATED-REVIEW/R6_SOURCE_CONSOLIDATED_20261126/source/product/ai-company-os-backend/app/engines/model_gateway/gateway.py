"""No provider adapter may perform calls in the D0 source candidate."""
from .fallback import ModelReview


class DisabledModelGateway:
    def invoke(self, request: object) -> ModelReview:
        return ModelReview('MODEL_EGRESS_DISABLED')
