"""D0 exact route/invocation comparison; no selection, tokenizer, grant or I/O."""
from dataclasses import dataclass, field
from app.core.agent_runtime.lifecycle import ClockSample, RunObservation, LeaseObservation, uint
from app.core.transaction.review import digest_ok
from .runtime_binding import InvocationEnvelope, inspect_invocation
from .provider_contract import ProviderRequest
from .profile_registry import profile_digest
from .routing_decision import RoutingDecisionRecord, verify_routing_decision
from .token_accounting import UsageBinding


@dataclass(frozen=True)
class InvocationRouteContext:
    envelope: InvocationEnvelope
    registry: tuple
    invocation_pin: str
    current_run: RunObservation
    current_lease: LeaseObservation
    clock: ClockSample
    raw: bytes = field(repr=False)
    record: RoutingDecisionRecord
    route_pin: str
    profiles: tuple
    metrics: tuple
    profile_pin: str
    input_tokens: int  # Explicit synthetic count, not an independently measured token count.


@dataclass(frozen=True)
class InvocationRouteReview:
    reason: str
    binding: UsageBinding | None = None
    decision: str = field(default="HOLD", init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)


def inspect_invocation_route(ctx):
    """Replay the existing route and invocation against supplied current references.

    The primary is a caller-nominated diagnostic candidate, not a router winner.
    The alternate is checked too; neither can be executed or used as fallback.
    """
    try:
        if (type(ctx) is not InvocationRouteContext or type(ctx.envelope) is not InvocationEnvelope
                or type(ctx.registry) is not tuple or type(ctx.current_run) is not RunObservation
                or type(ctx.current_lease) is not LeaseObservation or type(ctx.clock) is not ClockSample
                or type(ctx.envelope.run) is not RunObservation or type(ctx.envelope.lease) is not LeaseObservation
                or type(ctx.envelope.request) is not ProviderRequest or not uint(ctx.input_tokens)
                or not uint(ctx.current_run.version) or not uint(ctx.current_run.attempt)
                or not all(digest_ok(p) for p in (ctx.invocation_pin,ctx.route_pin,ctx.profile_pin))):
            return InvocationRouteReview("INVOCATION_ROUTE_SHAPE_HOLD")
        e=ctx.envelope
        base=inspect_invocation(e,ctx.registry,ctx.invocation_pin,ctx.current_run,ctx.current_lease,ctx.clock,ctx.raw)
        if not base.structural_match:
            return InvocationRouteReview(base.reason)
        if not verify_routing_decision(ctx.record,ctx.route_pin,ctx.profiles,ctx.registry,ctx.metrics,
                                       ctx.clock.policy_epoch,ctx.clock.witness_epoch):
            return InvocationRouteReview("INVOCATION_ROUTE_REPLAY_HOLD")
        q,p=ctx.record.query,ctx.record.policy
        if (q.scope != e.run.scope or e.request.requested != q.requested
                or e.request.max_output_tokens != q.output_tokens or ctx.input_tokens != q.input_tokens):
            return InvocationRouteReview("INVOCATION_QUERY_BINDING_HOLD")
        indexed={profile_digest(m,ctx.registry):m for m in ctx.profiles}
        eligible={c.profile_digest:c for c in ctx.record.candidates}
        primary=indexed.get(ctx.profile_pin)
        if (primary is None or primary.adapter != e.primary or primary.provider is not e.request.provider
                or ctx.profile_pin not in eligible):
            return InvocationRouteReview("INVOCATION_PRIMARY_PROFILE_HOLD")
        alternate=next((k for k,v in indexed.items() if v.adapter==e.alternate and v.provider is e.request.provider),None)
        if alternate not in eligible or alternate==ctx.profile_pin:
            return InvocationRouteReview("INVOCATION_ALTERNATE_PROFILE_HOLD")
        if (e.sample_cost_ceiling_minor > p.max_cost_minor
                or any(eligible[k].estimated_minor > e.sample_cost_ceiling_minor for k in (ctx.profile_pin,alternate))):
            return InvocationRouteReview("INVOCATION_COST_CEILING_HOLD")
        binding=UsageBinding(e.run.scope,e.run.attempt,ctx.route_pin,ctx.profile_pin,ctx.invocation_pin,
                             p.currency,p.policy_epoch,p.witness_epoch)
        return InvocationRouteReview("D0_INVOCATION_ROUTE_MATCH_ONLY",binding)
    except (ValueError,TypeError,AttributeError,OverflowError,RecursionError):
        return InvocationRouteReview("INVOCATION_ROUTE_REFERENCE_INVALID_HOLD")
