"""Local fixed-output adapter; no prompt, SDK, credentials, provider or tool call."""
from dataclasses import dataclass
from .registry import AdapterPin, exact_pin
from .fallback import inspect_fallback
from .provider_contract import ProviderKind, ProviderRequest, inspect_provider_request
from hashlib import sha256
from .runtime_binding import InvocationEnvelope, invocation_digest, inspect_invocation
from ..skill_engine.manifest_review import SkillManifestSample
from ..skill_engine.resolver import SourcePin, inspect_capabilities
from app.core.policy.gateway_review import EffectScope, GrantSample, inspect_gateway
from app.core.policy.witness_review import WitnessSample
from app.core.agent_runtime.lifecycle import ClockSample


@dataclass(frozen=True)
class SampleOutput:
    reason: str
    output: str | None = None
    provider_called: bool = False
    spend_allowed: bool = False
    dispatch_allowed: bool = False


def sample_model(primary: AdapterPin, alternate: AdapterPin, registry: tuple[AdapterPin, ...]) -> SampleOutput:
    if not exact_pin(primary, registry) or not exact_pin(alternate, registry):
        return SampleOutput('ADAPTER_PIN_INVALID')
    if (primary.adapter_id, alternate.adapter_id) != ('demo-model', 'demo-fallback'):
        return SampleOutput('SAMPLE_ADAPTER_ONLY')
    review = inspect_fallback(primary, alternate, registry, ('demo-tool',), ())
    if not review.structural_match or review.provider_call_allowed or review.decision != 'DENY':
        return SampleOutput('SAMPLE_ADAPTER_HOLD')
    request = ProviderRequest(primary.scope, ProviderKind.SAMPLE,
                              sha256(b'D0 fixed sample input').hexdigest(), ('demo-tool',), (), 64)
    if not inspect_provider_request(request, primary, alternate, registry).structural_match:
        return SampleOutput('SAMPLE_ADAPTER_HOLD')
    return SampleOutput('FIXED_SAMPLE_ONLY', 'Synthetic adapter review output; not a model response.')


@dataclass(frozen=True)
class SampleCapabilityContext:
    """Pinned diagnostic skill/tool inputs; never effective permissions."""
    skill: SkillManifestSample
    skill_reference: SkillManifestSample
    source: SourcePin
    source_reference: SourcePin
    policy_tools: tuple[str, ...]
    effect: EffectScope
    grant: GrantSample
    grant_reference: GrantSample
    witness: WitnessSample
    witness_reference: WitnessSample
    witness_max_age: int


def sample_task_output(envelope, registry, capabilities, clock, raw):
    """Use existing model, skill and ToolGateway inspectors, then fixed output.

    No model/skill/tool execution. The output is independent of the input bytes.
    A diagnostic match is deliberately not an allow decision.
    """
    if (type(capabilities) is not SampleCapabilityContext
            or type(envelope) is not InvocationEnvelope or type(clock) is not ClockSample
            or type(capabilities.effect) is not EffectScope
            or envelope.request.requested != ('demo-tool',)):
        return SampleOutput('D0_SAMPLE_TASK_SHAPE_HOLD')
    try:
        pin = invocation_digest(envelope, registry)
        check = inspect_invocation(envelope, registry, pin, envelope.run, envelope.lease, clock, raw)
        if (not check.structural_match or check.decision != 'DENY'
                or check.provider_call_allowed or check.spend_allowed or check.dispatch_allowed):
            return SampleOutput(check.reason)
        c = capabilities
        for adapter in (envelope.primary, envelope.alternate):
            skill = inspect_capabilities(c.skill,c.skill_reference,envelope.run.scope,
                c.source,c.source_reference,adapter,registry,envelope.request.requested,c.policy_tools)
            if (skill.reason != 'INDEPENDENT_RECEIPTS_ABSENT' or skill.diagnostic_overlap != ('demo-tool',)
                    or skill.enabled or skill.effective_tools or skill.status != 'QUARANTINED'):
                return SampleOutput('D0_SAMPLE_SKILL_HOLD')
        e=c.effect
        if (e.scope,e.action,e.tool_id,e.effect_digest)!=(envelope.run.scope,'MODEL_SAMPLE_REVIEW','demo-tool',pin):
            return SampleOutput('D0_SAMPLE_EFFECT_BINDING_HOLD')
        gate=inspect_gateway(e,c.grant,c.grant_reference,envelope.lease,envelope.lease,clock,
                             c.witness,c.witness_reference,c.witness_max_age)
        if (not gate.structural_match or gate.reason!='PEP_ISOLATION_NOT_PROVEN' or gate.decision!='DENY'
                or gate.dispatch_allowed or gate.provider_called or gate.release_ready):
            return SampleOutput(gate.reason)
        return sample_model(envelope.primary,envelope.alternate,registry)
    except (ValueError,TypeError,AttributeError,OverflowError,RecursionError):
        return SampleOutput('D0_SAMPLE_TASK_SHAPE_HOLD')


def sample_task_output_with_recovered_memory(
        ctx, current_run, current_lease, clock, context, expected_joint_pin,
        memory_path, reader, expected_witness, public_key, snapshot, reference,
        budget_reference, expected_owner_pin, capabilities, *, checkpoint_body,
        checkpoint_signature, checkpoint_sha):
    """Explicit D0 consumer of the recovered-memory Runtime path.

    Retains the historical fixed-output function and its wire shape. No real
    model/tool invocation, receipt, persisted result or execution authority.
    The economic and capability references must refer to the same reviewed
    invocation and signed witness. A failure never falls back to the old path.
    Readback is diagnostic, not an atomic effect fence or independent custody.
    """
    try:
        from .runtime_model_review import inspect_runtime_model_with_recovered_memory
        from app.core.agent_runtime.memory_gateway_review import MemoryGatewayReview
        from app.core.agent_runtime.memory_witness import (
            LatestWitnessPin, MemoryWitness, MemoryWitnessReader, witness_sha,
        )
        if (type(capabilities) is not SampleCapabilityContext
                or type(capabilities.effect) is not EffectScope
                or type(capabilities.witness) is not WitnessSample
                or type(capabilities.witness_reference) is not WitnessSample
                or type(expected_witness) is not LatestWitnessPin
                or type(reader) is not MemoryWitnessReader):
            return SampleOutput('D0_RECOVERED_SAMPLE_CONTEXT_HOLD')
        review = inspect_runtime_model_with_recovered_memory(
            ctx, current_run, current_lease, clock, context, expected_joint_pin,
            memory_path, reader, expected_witness, public_key, snapshot, reference,
            budget_reference, expected_owner_pin, checkpoint_body=checkpoint_body,
            checkpoint_signature=checkpoint_signature, checkpoint_sha=checkpoint_sha,
        )
        if (type(review) is not MemoryGatewayReview or review.structural_match is not True
                or review.reason != 'D0_RECOVERED_MEMORY_GATEWAY_MATCH_ONLY'
                or review.decision != 'HOLD'
                or any(getattr(review, name) is not False for name in (
                    'retrieval_allowed', 'release_allowed', 'provider_call_allowed',
                    'dispatch_allowed', 'spend_allowed', 'settlement_allowed',
                    'transition_allowed', 'retry_allowed', 'independent_verified',
                    'atomicity_verified'))):
            return SampleOutput('D0_RECOVERED_SAMPLE_RUNTIME_HOLD')
        signed = reader.read_latest(expected_witness, public_key)
        if type(signed) is not MemoryWitness or witness_sha(signed) != expected_witness.record_sha:
            return SampleOutput('D0_RECOVERED_SAMPLE_WITNESS_HOLD')
        expected = WitnessSample(signed.scope, expected_witness.key_sha,
                                 signed.witness_epoch, signed.sequence,
                                 expected_witness.record_sha, signed.issued_tick)
        if (capabilities.witness != expected or capabilities.witness_reference != expected
                or signed.scope != current_run.scope or signed.pending is not None
                or signed.recovery_epoch != expected_witness.recovery_epoch
                or (signed.policy_epoch, signed.witness_epoch) != (clock.policy_epoch, clock.witness_epoch)
                or not signed.issued_tick <= clock.now_tick < signed.expires_tick):
            return SampleOutput('D0_RECOVERED_SAMPLE_WITNESS_HOLD')
        if capabilities.effect.budget_id != snapshot.budget.budget_id:
            return SampleOutput('D0_RECOVERED_SAMPLE_BUDGET_HOLD')
        return sample_task_output(ctx.envelope, ctx.registry, capabilities, clock, ctx.raw)
    except Exception:
        # Including unavailable cryptography or unexpected owner readback errors.
        return SampleOutput('D0_RECOVERED_SAMPLE_REVIEW_ERROR_HOLD')
