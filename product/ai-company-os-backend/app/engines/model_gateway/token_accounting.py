"""D0 token accounting observations; never creates, settles or spends a reservation."""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from app.core.agent_runtime.lifecycle import Scope, token, uint, valid_scope
from app.core.transaction.review import digest_ok
from .cost_estimator import valid_currency
from .routing_decision import routing_decision_digest, verify_routing_decision


@dataclass(frozen=True)
class UsageBinding:
    scope: Scope
    attempt: int
    route_pin: str
    profile_pin: str
    invocation_pin: str
    currency: str
    policy_epoch: int
    witness_epoch: int


@dataclass(frozen=True)
class ReservationEvidence:
    binding: UsageBinding
    budget_id: str
    reservation_id: str
    reserved_minor: int
    receipt_pin: str


@dataclass(frozen=True)
class UsageEvidence:
    binding: UsageBinding
    input_tokens: int
    output_tokens: int
    actual_minor: int
    receipt_pin: str


@dataclass(frozen=True)
class ReconciliationEvidence:
    binding: UsageBinding
    reservation_pin: str
    usage_pin: str
    recognized_minor: int
    released_minor: int
    receipt_pin: str


@dataclass(frozen=True)
class AccountingReview:
    reason: str
    currency: str | None = None
    estimated_minor: int | None = None
    reserved_minor: int | None = None
    actual_minor: int | None = None
    actual_input_tokens: int | None = None
    actual_output_tokens: int | None = None
    reconciled_minor: int | None = None
    released_minor: int | None = None
    decision: str = field(default="HOLD", init=False)
    spend_allowed: bool = field(default=False, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    settlement_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)


def valid_usage_binding(b):
    return (type(b) is UsageBinding and type(b.scope) is Scope and valid_scope(b.scope)
            and all(uint(x) for x in (b.attempt,b.policy_epoch,b.witness_epoch))
            and all(digest_ok(x) for x in (b.route_pin,b.profile_pin,b.invocation_pin))
            and valid_currency(b.currency))


def accounting_evidence_digest(e):
    """Pin a typed synthetic observation, not a signature or independently obtained receipt."""
    if type(e) not in (ReservationEvidence, UsageEvidence, ReconciliationEvidence):
        raise ValueError("ACCOUNTING_EVIDENCE_INVALID")
    if not valid_usage_binding(e.binding) or not digest_ok(e.receipt_pin):
        raise ValueError("ACCOUNTING_EVIDENCE_INVALID")
    if type(e) is ReservationEvidence:
        valid = all(type(x) is str and token(x) for x in (e.budget_id,e.reservation_id)) and uint(e.reserved_minor)
    elif type(e) is UsageEvidence:
        valid = all(uint(x) for x in (e.input_tokens,e.output_tokens,e.actual_minor))
    else:
        valid = (digest_ok(e.reservation_pin) and digest_ok(e.usage_pin)
                 and uint(e.recognized_minor) and uint(e.released_minor))
    if not valid:
        raise ValueError("ACCOUNTING_EVIDENCE_INVALID")
    return sha256(json.dumps({"version":"D0_TOKEN_ACCOUNTING_V1","type":type(e).__name__,"body":asdict(e)},
        sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()


def inspect_token_accounting(binding, record, expected_route_pin, profiles, registry, metrics,
                             current_policy_epoch, current_witness_epoch, *,
                             reservation=None, reservation_pin=None, usage=None, usage_pin=None,
                             reconciliation=None, reconciliation_pin=None, outcome_unknown=False):
    """A pure D0 comparison of observations. Unknown usage is never estimated or zero-filled.

    The invocation pin/attempt and evidence receipts are supplied references; no independent
    readback, invocation-to-profile proof, actual charge or ledger mutation is performed.
    """
    try:
        if (not valid_usage_binding(binding) or type(outcome_unknown) is not bool
                or binding.route_pin != expected_route_pin
                or not verify_routing_decision(record,expected_route_pin,profiles,registry,metrics,
                                               current_policy_epoch,current_witness_epoch)
                or routing_decision_digest(record) != binding.route_pin
                or (binding.scope,binding.currency,binding.policy_epoch,binding.witness_epoch) !=
                   (record.query.scope,record.policy.currency,record.policy.policy_epoch,record.policy.witness_epoch)):
            return AccountingReview("ACCOUNTING_ROUTE_BINDING_HOLD")
        candidate = next((c for c in record.candidates if c.profile_digest == binding.profile_pin),None)
        if candidate is None:
            return AccountingReview("ACCOUNTING_PROFILE_HOLD")
        values = dict(currency=binding.currency,estimated_minor=candidate.estimated_minor)
        for e, pin, cls in ((reservation,reservation_pin,ReservationEvidence),
                            (usage,usage_pin,UsageEvidence),(reconciliation,reconciliation_pin,ReconciliationEvidence)):
            if e is None:
                if pin is not None:
                    return AccountingReview("ACCOUNTING_EVIDENCE_MISSING_HOLD",**values)
            elif (type(e) is not cls or e.binding != binding or not digest_ok(pin)
                    or accounting_evidence_digest(e) != pin):
                return AccountingReview("ACCOUNTING_EVIDENCE_BINDING_HOLD",**values)
        receipts = [e.receipt_pin for e in (reservation,usage,reconciliation) if e is not None]
        if len(set(receipts)) != len(receipts):
            return AccountingReview("ACCOUNTING_RECEIPT_ALIAS_HOLD",**values)
        if reservation is not None:
            values["reserved_minor"] = reservation.reserved_minor
        if outcome_unknown:
            return AccountingReview("UNKNOWN_USAGE_HOLD",**values)
        if usage is not None:
            values.update(actual_minor=usage.actual_minor,actual_input_tokens=usage.input_tokens,
                          actual_output_tokens=usage.output_tokens)
        if reservation is None:
            return AccountingReview("RESERVATION_MISSING_HOLD",**values)
        if reservation.reserved_minor < candidate.estimated_minor:
            return AccountingReview("RESERVATION_INSUFFICIENT_HOLD",**values)
        if usage is None:
            return AccountingReview("USAGE_MISSING_HOLD",**values)
        if (usage.actual_minor > reservation.reserved_minor or usage.input_tokens > record.query.input_tokens
                or usage.output_tokens > record.query.output_tokens):
            return AccountingReview("USAGE_LIMIT_EXCEEDED_HOLD",**values)
        if reconciliation is None:
            return AccountingReview("RECONCILIATION_MISSING_HOLD",**values)
        if (reconciliation.reservation_pin != accounting_evidence_digest(reservation)
                or reconciliation.usage_pin != accounting_evidence_digest(usage)
                or reconciliation.recognized_minor != usage.actual_minor
                or reconciliation.recognized_minor + reconciliation.released_minor != reservation.reserved_minor):
            return AccountingReview("RECONCILIATION_MISMATCH_HOLD",**values)
        return AccountingReview("D0_RECONCILIATION_MATCH_ONLY",**values,
                                reconciled_minor=reconciliation.recognized_minor,
                                released_minor=reconciliation.released_minor)
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        return AccountingReview("ACCOUNTING_REFERENCE_INVALID_HOLD")
