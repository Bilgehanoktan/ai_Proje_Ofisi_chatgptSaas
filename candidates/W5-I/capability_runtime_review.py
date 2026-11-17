"""W5-I: read-only composition of existing Memory, Model, Skill and Tool reviews.
No provider or tool invocation, authority, scheduler, ledger or state mutation.
Preflight and consumed-model review are deliberately separate phases.
"""
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
import json
from app.core.agent_runtime.lifecycle import RunObservation, LeaseObservation, ClockSample, uint, token
from app.core.agent_runtime.joint_context import JointContext, joint_context_digest, inspect_joint_context
from app.core.policy.gateway_review import EffectScope, GrantSample, inspect_gateway
from app.core.transaction.review import digest_ok
from app.engines.model_gateway.invocation_route_binding import InvocationRouteContext
from app.engines.model_gateway.runtime_model_review import inspect_runtime_model
from app.engines.model_gateway.durable_receipt_adapter import OwnerReceiptSnapshot, owner_snapshot_digest, inspect_owner_snapshot
from app.engines.skill_engine.manifest_review import SkillManifestSample, valid_manifest
from app.engines.skill_engine.resolver import SourcePin, valid_source, inspect_capabilities


@dataclass(frozen=True)
class ToolReviewRequest:
    tool_id: str
    input_pin: str
    action: str = field(default='TOOL_SAMPLE_REVIEW', init=False)


@dataclass(frozen=True)
class CapabilityRuntimeReview:
    reason: str
    stage: str
    structural_match: bool = False
    signature_match: bool = False
    pep_reference_match: bool = False
    decision: str = field(default='HOLD', init=False)
    pep_decision: str = field(default='DENY', init=False)
    retrieval_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    tool_allowed: bool = field(default=False, init=False)
    skill_enabled: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    transition_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)
    settlement_allowed: bool = field(default=False, init=False)
    independent_verified: bool = field(default=False, init=False)


def capability_runtime_digest(joint, ctx, snapshot, skill, source, tool):
    """Pin typed existing observations, one prospective tool, no payload disclosure.
    This digest is not an IAM grant, trusted owner readback, or execution intent.
    """
    if (type(joint) is not JointContext or type(ctx) is not InvocationRouteContext
            or joint.invocation != ctx.envelope or type(ctx.registry) is not tuple
            or not all(digest_ok(v) for v in (ctx.invocation_pin,ctx.route_pin,ctx.profile_pin))
            or type(snapshot) is not OwnerReceiptSnapshot or type(skill) is not SkillManifestSample
            or not valid_manifest(skill) or type(source) is not SourcePin or not valid_source(source)
            or type(tool) is not ToolReviewRequest or not token(tool.tool_id) or not digest_ok(tool.input_pin)
            or tool.action != 'TOOL_SAMPLE_REVIEW'):
        raise ValueError('CAPABILITY_CONTEXT_SHAPE_HOLD')
    body = dict(joint=joint_context_digest(joint,ctx.registry),invocation=ctx.invocation_pin,
                route=ctx.route_pin,profile=ctx.profile_pin,owner=owner_snapshot_digest(snapshot),
                skill=asdict(skill),source=asdict(source),tool=asdict(tool))
    return sha256(json.dumps(['aicos-d0-w5-capability-runtime-v1',body],sort_keys=True,
        separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')).hexdigest()


def _runtime_ok(ctx, run, lease, clock):
    return (type(ctx) is InvocationRouteContext and type(run) is RunObservation
            and type(lease) is LeaseObservation and type(clock) is ClockSample
            and type(ctx.clock) is ClockSample and all(uint(x) for x in (clock.now_tick,ctx.clock.now_tick))
            and clock.now_tick >= ctx.clock.now_tick and ctx.current_run == run and ctx.current_lease == lease
            and ctx.envelope.run == run and ctx.envelope.lease == lease)


def inspect_capability_runtime(joint, ctx, snapshot, owner_reference, budget_reference, owner_pin,
                               skill, skill_reference, source, source_reference, tool,
                               expected_pin, path, current_run, current_lease, clock,
                               effect, grant, grant_reference, witness, witness_reference, witness_max_age):
    """One diagnostic composition, no grant inheritance across model and tool effects.
    Memory checks bracket the full review; this is NOT atomic with future execution.
    No signed consumed receipt can be used as preflight permission.
    """
    stage='runtime'
    try:
        if not _runtime_ok(ctx,current_run,current_lease,clock):
            return CapabilityRuntimeReview('CAPABILITY_RUNTIME_DRIFT_HOLD',stage)
        stage='pin'
        if not digest_ok(expected_pin) or capability_runtime_digest(joint,ctx,snapshot,skill,source,tool)!=expected_pin:
            return CapabilityRuntimeReview('CAPABILITY_CONTEXT_PIN_HOLD',stage)
        if (not digest_ok(owner_pin) or owner_snapshot_digest(snapshot)!=owner_pin):
            return CapabilityRuntimeReview('CAPABILITY_OWNER_PIN_HOLD',stage)
        joint_pin=joint_context_digest(joint,ctx.registry)
        stage='memory-model'
        first=inspect_joint_context(joint,ctx.registry,joint_pin,path,current_run,current_lease,clock,ctx.raw)
        if not first.structural_match or first.reason!='D0_JOINT_CONTEXT_MATCH_ONLY':
            return CapabilityRuntimeReview(first.reason,stage)
        stage='model-receipt'
        model=inspect_runtime_model(ctx,current_run,current_lease,clock,snapshot,owner_reference,budget_reference,owner_pin)
        if model.reason!='D0_RUNTIME_MODEL_MATCH_ONLY' or model.invocation_pin!=ctx.invocation_pin:
            return CapabilityRuntimeReview(model.reason,stage)
        stage='tool-binding'
        if (type(effect) is not EffectScope or type(grant) is not GrantSample
                or (effect.scope,effect.action,effect.tool_id,effect.effect_digest,effect.budget_id)!=
                   (current_run.scope,tool.action,tool.tool_id,expected_pin,snapshot.budget.budget_id)):
            return CapabilityRuntimeReview('CAPABILITY_TOOL_EFFECT_BINDING_HOLD',stage)
        stage='skill'
        # One requested tool per effect. Both adapters must have the diagnostic overlap;
        # this is not a claim that either can execute the tool or inherit its grant.
        for adapter in (ctx.envelope.primary,ctx.envelope.alternate):
            caps=inspect_capabilities(skill,skill_reference,current_run.scope,source,source_reference,
                                     adapter,ctx.registry,(tool.tool_id,),grant.allowed_tools)
            if (caps.reason!='INDEPENDENT_RECEIPTS_ABSENT' or caps.diagnostic_overlap!=(tool.tool_id,)
                    or caps.effective_tools or caps.enabled):
                return CapabilityRuntimeReview(caps.reason,stage)
        stage='pep'
        pep=inspect_gateway(effect,grant,grant_reference,current_lease,ctx.envelope.lease,
                            clock,witness,witness_reference,witness_max_age)
        if (not pep.structural_match or pep.reason!='PEP_ISOLATION_NOT_PROVEN' or pep.decision!='DENY'
                or pep.dispatch_allowed or pep.provider_called or pep.release_ready):
            return CapabilityRuntimeReview(pep.reason,stage)
        stage='memory-recheck'
        last=inspect_joint_context(joint,ctx.registry,joint_pin,path,current_run,current_lease,clock,ctx.raw)
        if not last.structural_match or last.reason!='D0_JOINT_CONTEXT_MATCH_ONLY':
            return CapabilityRuntimeReview(last.reason,stage)
        return CapabilityRuntimeReview('D0_FOUR_ENGINE_MATCH_ONLY_AUTHORITY_UNPROVEN_HOLD','complete',True)
    except (ValueError,TypeError,AttributeError,OverflowError,RecursionError):
        return CapabilityRuntimeReview('CAPABILITY_REFERENCE_INVALID_HOLD',stage)


def inspect_consumed_model_binding(ctx,snapshot,owner_reference,budget_reference,owner_pin,
                                   receipt_pin,expected_membership_pin,current_run,current_lease,clock):
    """Bridge W5-D typed owner snapshot to W5-H ReceiptEffectPin, not preflight.
    W5-H signature/PEP review stays separate and must use this exact bound pin.
    Membership pin is supplied by owner, never manufactured. Consume transaction
    and reservation issuance transaction are distinct; no equality inferred.
    """
    stage='consumed-binding'
    try:
        # Candidate H is a sibling, not a canonical app package. Import at call time
        # so preflight never depends on consumption helpers or crypto.
        from receipt_pep_review import ReceiptEffectPin, receipt_effect_digest
        if not _runtime_ok(ctx,current_run,current_lease,clock):
            return CapabilityRuntimeReview('CAPABILITY_RUNTIME_DRIFT_HOLD',stage)
        if type(receipt_pin) is not ReceiptEffectPin or not digest_ok(expected_membership_pin):
            return CapabilityRuntimeReview('CONSUMED_MEMBERSHIP_MISSING_HOLD',stage)
        receipt_effect_digest(receipt_pin)
        model_ctx=replace(ctx,clock=clock)
        owner=inspect_owner_snapshot(model_ctx,snapshot,owner_reference,budget_reference,owner_pin)
        if owner.snapshot_pin is None:
            return CapabilityRuntimeReview(owner.reason,stage)
        rb=snapshot.readback
        p=receipt_pin
        if (rb.reservation is None or p.run!=current_run or p.lease!=current_lease
                or (p.invocation_pin,p.route_pin,p.profile_pin,p.reservation_id,p.invocation_idempotency_key,
                    p.owner_snapshot_pin,p.reservation_pin,p.membership_pin,p.currency,p.effect.budget_id,p.effect.tool_id)!=
                   (ctx.invocation_pin,ctx.route_pin,ctx.profile_pin,rb.lookup.reservation_id,
                    rb.lookup.invocation_idempotency_key,owner_pin,snapshot.reservation_pin,
                    expected_membership_pin,snapshot.budget.currency,snapshot.budget.budget_id,
                    ctx.envelope.primary.adapter_id)):
            return CapabilityRuntimeReview('CONSUMED_OWNER_BINDING_HOLD',stage)
        return CapabilityRuntimeReview('D0_CONSUMED_BINDING_ONLY_SIGNATURE_CUSTODY_HOLD',stage,True)
    except (ImportError,ValueError,TypeError,AttributeError,OverflowError,RecursionError):
        return CapabilityRuntimeReview('CONSUMED_REFERENCE_INVALID_HOLD',stage)


def inspect_consumed_model(ctx,snapshot,owner_reference,budget_reference,owner_pin,
                           receipt_pin,receipt_reference,expected_membership_pin,expected_binding_pin,
                           observation,expected_consume,public_key,*,expected_key_sha,current_head,
                           current_run,current_lease,clock,grant,grant_reference,witness,witness_reference,
                           witness_max_age,outcome_unknown):
    """Use the same typed pin in W5-D crosswalk and original W5-H signature review.
    Never return a provider result, authorization, or permission to consume/retry.
    """
    stage='consumed-pep'
    try:
        from receipt_pep_review import inspect_receipt_pep
        if type(outcome_unknown) is not bool or outcome_unknown:
            return CapabilityRuntimeReview('UNKNOWN_RECONCILIATION_REQUIRED_HOLD',stage)
        bound=inspect_consumed_model_binding(ctx,snapshot,owner_reference,budget_reference,owner_pin,
                                             receipt_pin,expected_membership_pin,current_run,current_lease,clock)
        if not bound.structural_match:
            return bound
        result=inspect_receipt_pep(receipt_pin,receipt_reference,expected_binding_pin,observation,expected_consume,
            public_key,expected_key_sha=expected_key_sha,current_head=current_head,current_run=current_run,
            current_lease=current_lease,clock=clock,grant=grant,grant_reference=grant_reference,
            witness=witness,witness_reference=witness_reference,witness_max_age=witness_max_age,
            outcome_unknown=outcome_unknown)
        if (result.reason!='SIGNED_CONSUMED_NO_RETRY_CUSTODY_UNPROVEN_HOLD' or not result.signature_match
                or not result.pep_reference_match or result.decision!='HOLD' or result.pep_decision!='DENY'
                or any((result.provider_call_allowed,result.retry_allowed,result.spend_allowed,
                        result.dispatch_allowed,result.settlement_allowed,result.release_allowed,result.independent_verified))):
            return CapabilityRuntimeReview(result.reason,stage,False,result.signature_match,result.pep_reference_match)
        return CapabilityRuntimeReview('D0_CONSUMED_MODEL_SIGNATURE_MATCH_ONLY_HOLD',stage,True,True,True)
    except (ImportError,ValueError,TypeError,AttributeError,OverflowError,RecursionError):
        return CapabilityRuntimeReview('CONSUMED_PEP_REFERENCE_INVALID_HOLD',stage)
