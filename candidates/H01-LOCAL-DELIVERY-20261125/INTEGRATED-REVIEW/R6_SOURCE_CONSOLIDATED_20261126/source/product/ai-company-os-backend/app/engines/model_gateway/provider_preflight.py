"""W5-E: offline provider preparation; no transport, credentials or invocation."""
from dataclasses import dataclass, field
from .provider_contract import ProviderKind
from .invocation_route_binding import inspect_invocation_route
from .durable_receipt_adapter import inspect_owner_snapshot


@dataclass(frozen=True)
class ProviderPreflightReview:
    reason: str
    invocation_pin: str | None = None
    owner_snapshot_pin: str | None = None
    decision: str = field(default="HOLD", init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    selected_model: None = field(default=None, init=False)
    actual_tokens: None = field(default=None, init=False)
    actual_cost_minor: None = field(default=None, init=False)


def inspect_provider_preflight(ctx,snapshot,reference,budget_reference,expected_pin):
    route=inspect_invocation_route(ctx)
    if route.binding is None:
        return ProviderPreflightReview(route.reason)
    if ctx.envelope.request.provider is not ProviderKind.SAMPLE:
        return ProviderPreflightReview("PROVIDER_EGRESS_HOLD")
    owner=inspect_owner_snapshot(ctx,snapshot,reference,budget_reference,expected_pin)
    if owner.snapshot_pin is None:
        return ProviderPreflightReview(owner.reason)
    # Pre-call stage only: an observed usage, reconciliation or unknown outcome
    # cannot be reused as a fresh reservation or automatic retry.
    rb=snapshot.readback
    if rb.usage is not None or rb.reconciliation is not None or rb.outcome_unknown:
        return ProviderPreflightReview("PROVIDER_REPLAY_OR_OUTCOME_HOLD")
    if rb.reservation is None or owner.receipt.reason!="USAGE_MISSING_HOLD":
        return ProviderPreflightReview("PROVIDER_RESERVATION_HOLD")
    return ProviderPreflightReview("D0_PROVIDER_PREFLIGHT_MATCH_ONLY",route.binding.invocation_pin,owner.snapshot_pin)
