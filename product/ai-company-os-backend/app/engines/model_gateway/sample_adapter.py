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
