"""W5 read-only receipt contract; owner adapter absent, no ledger or settlement writer."""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Protocol
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok
from app.engines.budget_engine.reservation_review import BudgetSnapshot, valid_budget
from .invocation_route_binding import inspect_invocation_route
from .token_accounting import (UsageBinding, ReservationEvidence, UsageEvidence, ReconciliationEvidence,
                               AccountingReview, valid_usage_binding, accounting_evidence_digest,
                               inspect_token_accounting)


@dataclass(frozen=True)
class ReceiptLookup:
    binding: UsageBinding
    budget_id: str
    reservation_id: str
    invocation_idempotency_key: str


@dataclass(frozen=True)
class ReceiptReadback:
    lookup: ReceiptLookup
    budget_revision: int
    budget_source_pin: str
    reservation: ReservationEvidence | None = None
    usage: UsageEvidence | None = None
    reconciliation: ReconciliationEvidence | None = None
    outcome_unknown: bool = False


class ReservationUsageReceiptPort(Protocol):
    """Future owner-provided, scoped, consistent readback; no default implementation.

    Must not synthesize receipts from admission rows, estimates or aggregate balances.
    Missing, revoked, stale or ambiguous custody returns no usable readback.
    """
    def read_receipts(self, lookup: ReceiptLookup) -> ReceiptReadback | None: ...


@dataclass(frozen=True)
class ReceiptPortReview:
    reason: str
    accounting: AccountingReview | None = None
    decision: str = field(default="HOLD",init=False)
    provider_call_allowed: bool = field(default=False,init=False)
    spend_allowed: bool = field(default=False,init=False)
    settlement_allowed: bool = field(default=False,init=False)
    dispatch_allowed: bool = field(default=False,init=False)


def make_receipt_lookup(ctx,budget_id):
    result=inspect_invocation_route(ctx)
    if result.binding is None or not token(budget_id):
        raise ValueError("RECEIPT_LOOKUP_HOLD")
    return ReceiptLookup(result.binding,budget_id,ctx.envelope.reservation_ref,ctx.envelope.idempotency_key)


def receipt_readback_digest(readback):
    if (type(readback) is not ReceiptReadback or type(readback.lookup) is not ReceiptLookup
            or not valid_usage_binding(readback.lookup.binding)
            or not all(type(v) is str and token(v) for v in (readback.lookup.budget_id,
                        readback.lookup.reservation_id,readback.lookup.invocation_idempotency_key))
            or not uint(readback.budget_revision) or not digest_ok(readback.budget_source_pin)
            or type(readback.outcome_unknown) is not bool):
        raise ValueError("RECEIPT_READBACK_INVALID")
    for e,cls in ((readback.reservation,ReservationEvidence),(readback.usage,UsageEvidence),
                  (readback.reconciliation,ReconciliationEvidence)):
        if e is not None:
            if type(e) is not cls or e.binding != readback.lookup.binding:
                raise ValueError("RECEIPT_READBACK_BINDING_INVALID")
            accounting_evidence_digest(e)
    return sha256(json.dumps({"version":"D0_MODEL_RECEIPT_READBACK_V1","body":asdict(readback)},
                  sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()


def inspect_receipt_readback(ctx,budget,budget_reference,readback,expected_readback_pin,*,
                             reservation_pin=None,usage_pin=None,reconciliation_pin=None):
    """Pure comparison only. No port call; externally supplied pins are not trusted custody.

    Existing run-level admission CommitReceipt/sample_reservations cannot satisfy this port.
    Aggregate BudgetSnapshot is a sanity check, never proof of reservation membership.
    """
    try:
        route=inspect_invocation_route(ctx)
        if route.binding is None:
            return ReceiptPortReview(route.reason)
        b=route.binding
        if (type(budget) is not BudgetSnapshot or type(budget_reference) is not BudgetSnapshot
                or not valid_budget(budget) or not valid_budget(budget_reference) or budget!=budget_reference
                or (budget.scope,budget.currency,budget.policy_epoch,budget.witness_epoch)!=
                   (b.scope,b.currency,b.policy_epoch,b.witness_epoch)):
            return ReceiptPortReview("RECEIPT_BUDGET_REFERENCE_HOLD")
        if budget.unknown_cost:
            return ReceiptPortReview("UNKNOWN_COST_HOLD")
        if budget.outstanding_minor+budget.recognized_cost_minor > budget.limit_minor:
            return ReceiptPortReview("RECEIPT_BUDGET_LIMIT_HOLD")
        if readback is None:
            return ReceiptPortReview("INVOCATION_RECEIPT_MISSING_HOLD")
        if (not digest_ok(expected_readback_pin) or receipt_readback_digest(readback)!=expected_readback_pin
                or readback.lookup!=make_receipt_lookup(ctx,budget.budget_id)
                or (readback.budget_revision,readback.budget_source_pin)!=(budget.revision,budget.source_digest)):
            return ReceiptPortReview("RECEIPT_READBACK_PIN_OR_SCOPE_HOLD")
        r=readback.reservation
        if r is not None and ((r.budget_id,r.reservation_id)!=(budget.budget_id,ctx.envelope.reservation_ref)
                              or r.reserved_minor < ctx.envelope.sample_cost_ceiling_minor):
            return ReceiptPortReview("RECEIPT_RESERVATION_ID_OR_CEILING_HOLD")
        a=inspect_token_accounting(b,ctx.record,ctx.route_pin,ctx.profiles,ctx.registry,ctx.metrics,
            ctx.clock.policy_epoch,ctx.clock.witness_epoch,reservation=r,reservation_pin=reservation_pin,
            usage=readback.usage,usage_pin=usage_pin,reconciliation=readback.reconciliation,
            reconciliation_pin=reconciliation_pin,outcome_unknown=readback.outcome_unknown)
        if a.actual_minor is not None and a.actual_minor > ctx.envelope.sample_cost_ceiling_minor:
            return ReceiptPortReview("RECEIPT_INVOCATION_COST_OVERRUN_HOLD",a)
        if a.reason=="D0_RECONCILIATION_MATCH_ONLY":
            if a.reconciled_minor > budget.recognized_cost_minor:
                return ReceiptPortReview("RECEIPT_RECOGNIZED_BALANCE_HOLD")
            return ReceiptPortReview("D0_RECEIPT_MATCH_ONLY_OWNER_CUSTODY_HOLD",a)
        # Unreconciled reservation is only an observation; do not infer releases or actual spend.
        if a.reserved_minor is not None and a.reserved_minor > budget.outstanding_minor:
            return ReceiptPortReview("RECEIPT_OUTSTANDING_BALANCE_HOLD")
        return ReceiptPortReview(a.reason,a)
    except (ValueError,TypeError,AttributeError,OverflowError,RecursionError):
        return ReceiptPortReview("RECEIPT_REFERENCE_INVALID_HOLD")
