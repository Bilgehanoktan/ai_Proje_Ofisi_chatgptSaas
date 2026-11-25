"""D0 same-invocation Memory/Gateway review; no grant or executable effect boundary."""
from dataclasses import dataclass, field

from app.core.agent_runtime.joint_context import JointContext, joint_context_digest
from app.core.agent_runtime.memory_witness import WitnessedReview, inspect_witnessed_context
from app.core.transaction.review import digest_ok
from app.engines.model_gateway.invocation_route_binding import InvocationRouteContext
from app.engines.model_gateway.provider_preflight import ProviderPreflightReview, inspect_provider_preflight
from app.engines.model_gateway.runtime_binding import invocation_digest


@dataclass(frozen=True)
class MemoryGatewayReview:
    reason: str
    structural_match: bool = False
    decision: str = field(default='HOLD', init=False)
    retrieval_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    settlement_allowed: bool = field(default=False, init=False)
    transition_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)
    independent_verified: bool = field(default=False, init=False)
    atomicity_verified: bool = field(default=False, init=False)


def _memory_match(r):
    return (type(r) is WitnessedReview and r.structural_match is True
            and r.reason == 'D0_WITNESSED_CONTEXT_MATCH_ONLY' and r.decision == 'DENY'
            and all(v is False for v in (r.retrieval_allowed, r.release_allowed,
                r.provider_call_allowed, r.dispatch_allowed, r.spend_allowed,
                r.independent_verified, r.retry_allowed)))


def _gateway_match(r, invocation_pin, owner_pin):
    return (type(r) is ProviderPreflightReview and r.decision == 'HOLD'
            and r.reason == 'D0_PROVIDER_PREFLIGHT_MATCH_ONLY'
            and r.invocation_pin == invocation_pin and r.owner_snapshot_pin == owner_pin
            and r.selected_model is None and r.actual_tokens is None and r.actual_cost_minor is None
            and all(v is False for v in (r.provider_call_allowed, r.dispatch_allowed, r.spend_allowed)))


def inspect_memory_gateway(context, expected_joint_pin, ctx, memory_path, reader,
                           expected_witness, public_key, snapshot, reference,
                           budget_reference, expected_owner_pin):
    """Reuse both existing readers on one exact invocation and approved byte span.

    Pins and current observations are supplied by the caller, not acquired from
    protected owner custody here. No new digest protocol, writer, grant or SDK.
    The second full witness/history review detects intervening memory changes;
    even a match is not atomic with a later effect or proof of current IAM/ORG.
    """
    try:
        if (type(context) is not JointContext or type(ctx) is not InvocationRouteContext
                or not all(digest_ok(p) for p in (expected_joint_pin, ctx.invocation_pin, expected_owner_pin))
                or context.invocation != ctx.envelope
                or invocation_digest(context.invocation, ctx.registry) != ctx.invocation_pin
                or invocation_digest(ctx.envelope, ctx.registry) != ctx.invocation_pin
                or joint_context_digest(context, ctx.registry) != expected_joint_pin):
            return MemoryGatewayReview('MEMORY_GATEWAY_INVOCATION_BINDING_HOLD')
        args = (context, ctx.registry, expected_joint_pin, memory_path, ctx.current_run,
                ctx.current_lease, ctx.clock, ctx.raw, reader, expected_witness, public_key)
        first = inspect_witnessed_context(*args)
        if not _memory_match(first):
            return MemoryGatewayReview('MEMORY_GATEWAY_MEMORY_HOLD')
        gateway = inspect_provider_preflight(ctx, snapshot, reference, budget_reference, expected_owner_pin)
        if not _gateway_match(gateway, ctx.invocation_pin, expected_owner_pin):
            return MemoryGatewayReview('MEMORY_GATEWAY_PREFLIGHT_HOLD')
        second = inspect_witnessed_context(*args)
        if not _memory_match(second) or first != second:
            return MemoryGatewayReview('MEMORY_GATEWAY_MEMORY_RECHECK_HOLD')
        return MemoryGatewayReview('D0_MEMORY_GATEWAY_MATCH_ONLY', True)
    except Exception:
        # No exception text or caller bytes are exposed. Fail closed even on an
        # unexpected reader failure; no permission or retry can be returned.
        return MemoryGatewayReview('MEMORY_GATEWAY_REVIEW_ERROR_HOLD')


# MEM-05E: reuse the full recovery review at the existing Gateway boundary.
from app.core.agent_runtime.memory_recovery_review import (
    MemoryRecoveryReview, inspect_memory_recovery,
)


def _clean_recovery(r):
    return (type(r) is MemoryRecoveryReview
            and r.reason == 'D0_MEMORY_RECOVERY_HEAD_MATCH_ONLY'
            and r.history_match is True and r.checkpoint_match is True
            and r.pending_observation == 'NONE_OBSERVED'
            and r.decision == 'HOLD' and r.quarantine_required is True
            and all(getattr(r, name) is False for name in (
                'retrieval_allowed', 'release_allowed', 'provider_call_allowed',
                'dispatch_allowed', 'spend_allowed', 'settlement_allowed',
                'transition_allowed', 'retry_allowed', 'replay_allowed',
                'publish_allowed', 'clear_pending_allowed', 'prune_allowed',
                'independent_verified', 'atomicity_verified')))


def inspect_recovered_memory_gateway(context, expected_joint_pin, ctx, memory_path, reader,
                                     expected_witness, public_key, snapshot, reference,
                                     budget_reference, expected_owner_pin, *, checkpoint_body,
                                     checkpoint_signature, checkpoint_sha):
    """Compose the existing full recovery and same-invocation reviews, read-only.

    The recovery lease reference is the exact invocation envelope lease, never
    a separate caller-chosen lease. Both observations reuse the same external
    witness/checkpoint pins and Runtime context. PENDING (even a matching target)
    cannot pass. The existing Gateway rejects economic UNKNOWN and used receipts.
    Re-observation is not a protected fence; D5/T1 and current IAM/ORG ownership
    are NOT established. Do not attach either review to execution or retry.
    """
    try:
        if (type(context) is not JointContext or type(ctx) is not InvocationRouteContext
                or context.invocation != ctx.envelope
                or not digest_ok(checkpoint_sha)):
            return MemoryGatewayReview('MEMORY_GATEWAY_RECOVERY_INPUT_HOLD')
        args = (memory_path, reader, expected_witness, public_key, checkpoint_body,
                checkpoint_signature, checkpoint_sha, ctx.current_run,
                ctx.current_lease, ctx.envelope.lease, ctx.clock)
        first = inspect_memory_recovery(*args)
        if not _clean_recovery(first):
            return MemoryGatewayReview('MEMORY_GATEWAY_RECOVERY_HOLD')
        gateway = inspect_memory_gateway(context, expected_joint_pin, ctx, memory_path,
                    reader, expected_witness, public_key, snapshot, reference,
                    budget_reference, expected_owner_pin)
        if (type(gateway) is not MemoryGatewayReview or gateway.structural_match is not True
                or gateway.reason != 'D0_MEMORY_GATEWAY_MATCH_ONLY' or gateway.decision != 'HOLD'
                or any(getattr(gateway, name) is not False for name in (
                    'retrieval_allowed', 'release_allowed', 'provider_call_allowed',
                    'dispatch_allowed', 'spend_allowed', 'settlement_allowed',
                    'transition_allowed', 'retry_allowed', 'independent_verified',
                    'atomicity_verified'))):
            return MemoryGatewayReview('MEMORY_GATEWAY_RECOVERY_PREFLIGHT_HOLD')
        second = inspect_memory_recovery(*args)
        if not _clean_recovery(second) or first != second:
            return MemoryGatewayReview('MEMORY_GATEWAY_RECOVERY_RECHECK_HOLD')
        return MemoryGatewayReview('D0_RECOVERED_MEMORY_GATEWAY_MATCH_ONLY', True)
    except Exception:
        return MemoryGatewayReview('MEMORY_GATEWAY_RECOVERY_ERROR_HOLD')
