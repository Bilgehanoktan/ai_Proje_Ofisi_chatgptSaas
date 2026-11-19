"""W5-H D0 crosswalk: signed consumed observation + existing deny-only PEP.
No receipt issuer, signer, store, provider, authorization, settlement or retry.
The pins are prospective owner observations, NOT derived from W5-G run rows.
"""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from app.core.agent_runtime.lifecycle import (
    Scope, RunObservation, RunState, LeaseObservation, ClockSample,
    valid_scope, valid_lease, token, uint,
)
from app.core.policy.gateway_review import EffectScope, valid_effect, inspect_gateway
from app.core.transaction.effect_fence_reference import Head, digest
from app.core.transaction.signed_consume_reference import (
    Scope as ConsumeScope, ConsumeRequest, canonical, review_observation,
)


@dataclass(frozen=True)
class ReceiptEffectPin:
    """Provisional crosswalk, not a canonical W5 receipt or proof of membership."""
    run: RunObservation
    lease: LeaseObservation
    effect: EffectScope
    project_id: str
    effect_id: str
    invocation_pin: str
    route_pin: str
    profile_pin: str
    reservation_id: str
    invocation_idempotency_key: str
    owner_snapshot_pin: str
    reservation_pin: str
    membership_pin: str
    transaction_ref: str
    currency: str


@dataclass(frozen=True)
class ReceiptPEPReview:
    reason: str
    signature_match: bool = False
    pep_reference_match: bool = False
    decision: str = field(default='HOLD', init=False)
    pep_decision: str = field(default='DENY', init=False)
    independent_verified: bool = field(default=False, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    settlement_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)


def receipt_effect_digest(p):
    if (type(p) is not ReceiptEffectPin or type(p.run) is not RunObservation
            or type(p.run.scope) is not Scope or not valid_scope(p.run.scope)
            or p.run.state is not RunState.RUNNING or not uint(p.run.version) or not uint(p.run.attempt)
            or type(p.lease) is not LeaseObservation or not valid_lease(p.lease)
            or type(p.effect) is not EffectScope or not valid_effect(p.effect)
            or not all(type(v) is str and token(v) for v in (p.project_id,p.effect_id,p.reservation_id,
                        p.invocation_idempotency_key,p.transaction_ref))
            or not all(digest(v) for v in (p.invocation_pin,p.route_pin,p.profile_pin,
                        p.owner_snapshot_pin,p.reservation_pin,p.membership_pin))
            or type(p.currency) is not str or len(p.currency)!=3 or not p.currency.isascii()
            or not p.currency.isalpha() or not p.currency.isupper()):
        raise ValueError('RECEIPT_EFFECT_SHAPE_HOLD')
    e,l=p.effect,p.lease
    if (e.scope!=p.run.scope or l.scope!=p.run.scope or e.action!='MODEL_SAMPLE_REVIEW'
            or e.effect_digest!=p.invocation_pin
            or (e.lease_id,e.grant_id,e.policy_epoch,e.witness_epoch,e.fence)!=
               (l.lease_id,l.grant_id,l.policy_epoch,l.witness_epoch,l.fence)):
        raise ValueError('RECEIPT_EFFECT_SCOPE_HOLD')
    # Explicit version/domain separator; no authority from hash alone.
    return sha256(canonical(['aicos-d0-w5-receipt-effect-v1',asdict(p)])).hexdigest()


def consume_scope(p):
    """Project/effect are explicit owner pins; do not invent from Runtime scope."""
    receipt_effect_digest(p)
    s=p.run.scope
    return ConsumeScope(s.tenant_id,s.company_id,s.environment_id,p.project_id,s.task_id,s.run_id,p.effect_id)


def replay_keys(p):
    """Prospective uniqueness crosswalk. Stable across attempt, route, effect and tx.
    No persistence, negative proof, or enforcement of uniqueness by this helper.
    """
    receipt_effect_digest(p)
    s=p.run.scope
    scope=(s.tenant_id,s.company_id,s.environment_id)
    return (
        sha256(canonical(['w5-reservation-identity-v1',scope,p.effect.budget_id,p.reservation_id])).hexdigest(),
        sha256(canonical(['w5-invocation-idempotency-v1',scope,p.invocation_idempotency_key])).hexdigest(),
        sha256(canonical(['w5-invocation-pin-v1',scope,p.invocation_pin])).hexdigest(),
    )


def inspect_replay(p, retained):
    """Only diagnostic on supplied history. Empty history is never proof of freshness."""
    try:
        keys=replay_keys(p)
        if type(retained) is not tuple or len(retained)>4096:
            return ReceiptPEPReview('REPLAY_HISTORY_SHAPE_HOLD')
        for prior in retained:
            if set(keys).intersection(replay_keys(prior)):
                return ReceiptPEPReview('REPLAY_IDENTITY_MATCH_HOLD')
        return ReceiptPEPReview('REPLAY_ABSENCE_UNPROVEN_HOLD')
    except (ValueError,TypeError,AttributeError,OverflowError,RecursionError):
        return ReceiptPEPReview('REPLAY_HISTORY_SHAPE_HOLD')


def inspect_receipt_pep(p, reference, expected_binding_pin, observation, expected_consume,
                        public_key, *, expected_key_sha, current_head, current_run,
                        current_lease, clock, grant, grant_reference, witness,
                        witness_reference, witness_max_age, outcome_unknown):
    """Use exact existing crypto and PEP reviewers; never consume or invoke.
    Even a matching synthetic signed consume is already consumed, not preflight.
    Independent key/head/challenge, owner membership and IV custody are unproven.
    """
    try:
        if type(outcome_unknown) is not bool:
            return ReceiptPEPReview('OUTCOME_SHAPE_HOLD')
        if outcome_unknown:
            return ReceiptPEPReview('UNKNOWN_RECONCILIATION_REQUIRED_HOLD')
        if (not digest(expected_binding_pin) or receipt_effect_digest(p)!=expected_binding_pin
                or receipt_effect_digest(reference)!=expected_binding_pin or p!=reference):
            return ReceiptPEPReview('RECEIPT_EFFECT_REFERENCE_HOLD')
        if (type(current_run) is not RunObservation or type(current_lease) is not LeaseObservation
                or type(clock) is not ClockSample or not uint(current_run.version)
                or not uint(current_run.attempt) or type(current_run.scope) is not Scope
                or current_run!=p.run or current_lease!=p.lease):
            return ReceiptPEPReview('RUNTIME_REFERENCE_DRIFT_HOLD')
        if (type(expected_consume) is not ConsumeRequest or type(current_head) is not Head
                or expected_consume.scope!=consume_scope(p)
                or expected_consume.binding_sha!=expected_binding_pin
                or expected_consume.request_sha!=p.invocation_pin
                or expected_consume.transaction_ref!=p.transaction_ref):
            return ReceiptPEPReview('CONSUME_EFFECT_BINDING_HOLD')
        # Separate roots: only the proposed epoch relation, not equality of hashes/sequences.
        if current_head.epoch!=p.effect.witness_epoch or expected_consume.head.epoch!=p.effect.witness_epoch:
            return ReceiptPEPReview('CONSUME_WITNESS_EPOCH_HOLD')
        pep=inspect_gateway(p.effect,grant,grant_reference,p.lease,current_lease,clock,
                            witness,witness_reference,witness_max_age)
        if not pep.structural_match or pep.decision!='DENY' or pep.dispatch_allowed or pep.provider_called:
            return ReceiptPEPReview(pep.reason if not pep.structural_match else 'PEP_BOUNDARY_HOLD')
        signed=review_observation(observation,expected_consume,public_key,
                                  expected_key_sha=expected_key_sha,current_head=current_head,now_tick=clock.now_tick)
        if not signed.signature_match:
            return ReceiptPEPReview(signed.reason,pep_reference_match=True)
        return ReceiptPEPReview('SIGNED_CONSUMED_NO_RETRY_CUSTODY_UNPROVEN_HOLD',True,True)
    except (ValueError,TypeError,AttributeError,OverflowError,RecursionError):
        return ReceiptPEPReview('RECEIPT_PEP_REFERENCE_INVALID_HOLD')
