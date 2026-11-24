"""W5-F: pure Runtime-side observation bridge, not runtime wiring or transition."""
from dataclasses import dataclass, field, replace
from app.core.agent_runtime.lifecycle import RunObservation, LeaseObservation, ClockSample
from .invocation_route_binding import InvocationRouteContext
from .provider_preflight import inspect_provider_preflight


@dataclass(frozen=True)
class RuntimeModelReview:
    reason: str
    invocation_pin: str | None = None
    decision: str = field(default="HOLD", init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    transition_allowed: bool = field(default=False, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)


def inspect_runtime_model(ctx,current_run,current_lease,clock,snapshot,reference,budget_reference,expected_pin):
    """Recheck supplied Runtime observations, never retrieve or change Runtime state."""
    if (type(ctx) is not InvocationRouteContext or type(current_run) is not RunObservation
            or type(current_lease) is not LeaseObservation or type(clock) is not ClockSample):
        return RuntimeModelReview("RUNTIME_MODEL_REFERENCE_HOLD")
    if (ctx.current_run!=current_run or ctx.current_lease!=current_lease):
        return RuntimeModelReview("RUNTIME_MODEL_DRIFT_HOLD")
    # Use latest supplied clock. Existing invocation review checks expiry/epochs.
    review=inspect_provider_preflight(replace(ctx,current_run=current_run,current_lease=current_lease,clock=clock),
                                      snapshot,reference,budget_reference,expected_pin)
    if review.invocation_pin is None:
        return RuntimeModelReview(review.reason)
    return RuntimeModelReview("D0_RUNTIME_MODEL_MATCH_ONLY",review.invocation_pin)


def inspect_runtime_model_with_recovered_memory(
        ctx, current_run, current_lease, clock, context, expected_joint_pin,
        memory_path, reader, expected_witness, public_key, snapshot, reference,
        budget_reference, expected_owner_pin, *, checkpoint_body,
        checkpoint_signature, checkpoint_sha):
    """Runtime entry for the existing MEM-05E review, not an execution gate.

    Bind the externally observed run/lease and latest supplied clock before
    the original recovery, witness, Memory, route and budget review. A stale
    embedded clock cannot replace the current observation. The ordinary
    non-memory diagnostic is not a fallback for this explicit memory path.
    The original MEM-05E result (including all HOLD/deny flags) is preserved.
    Current observations still require independent custody before real use.
    """
    # Keep the existing non-memory module import independent of Ed25519.
    # An unavailable reviewed dependency must stop this path, not downgrade it.
    from app.core.agent_runtime.memory_gateway_review import (
        MemoryGatewayReview, inspect_recovered_memory_gateway,
    )
    if (type(ctx) is not InvocationRouteContext or type(current_run) is not RunObservation
            or type(current_lease) is not LeaseObservation or type(clock) is not ClockSample):
        return MemoryGatewayReview("RUNTIME_MEMORY_MODEL_REFERENCE_HOLD")
    if ctx.current_run != current_run or ctx.current_lease != current_lease:
        return MemoryGatewayReview("RUNTIME_MEMORY_MODEL_DRIFT_HOLD")
    return inspect_recovered_memory_gateway(
        context, expected_joint_pin,
        replace(ctx, current_run=current_run, current_lease=current_lease, clock=clock),
        memory_path, reader, expected_witness, public_key, snapshot, reference,
        budget_reference, expected_owner_pin, checkpoint_body=checkpoint_body,
        checkpoint_signature=checkpoint_signature, checkpoint_sha=checkpoint_sha,
    )
