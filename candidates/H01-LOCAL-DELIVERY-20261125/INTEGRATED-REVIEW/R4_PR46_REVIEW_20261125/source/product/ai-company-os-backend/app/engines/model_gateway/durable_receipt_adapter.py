"""W5-D: owner snapshot comparison only; no database, ledger or authority."""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Protocol
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok
from app.engines.budget_engine.reservation_review import BudgetSnapshot, valid_budget
from .reservation_usage_receipt import (ReceiptLookup, ReceiptReadback, ReceiptPortReview,
    make_receipt_lookup, receipt_readback_digest, inspect_receipt_readback)
from .token_accounting import accounting_evidence_digest


@dataclass(frozen=True)
class OwnerReceiptSnapshot:
    """Proposed per-invocation owner readback, not the run-level T1 CommitReceipt."""
    snapshot_id: str
    transaction_ref: str
    owner_revision: int
    budget: BudgetSnapshot
    readback: ReceiptReadback
    reservation_pin: str | None
    usage_pin: str | None
    reconciliation_pin: str | None


class DurableReceiptOwnerPort(Protocol):
    """Future T1/Budget-owned coherent read, scoped to one invocation.

    Missing or ambiguous membership, unknown outcome or unavailable custody must
    not be reconstructed from admission totals. No default physical mapping.
    """
    def read_snapshot(self, lookup: ReceiptLookup) -> OwnerReceiptSnapshot | None: ...


@dataclass(frozen=True)
class OwnerReceiptReview:
    reason: str
    receipt: ReceiptPortReview | None = None
    snapshot_pin: str | None = None
    decision: str = field(default="HOLD", init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    settlement_allowed: bool = field(default=False, init=False)
    custody_verified: bool = field(default=False, init=False)


def owner_snapshot_digest(s):
    if (type(s) is not OwnerReceiptSnapshot or not token(s.snapshot_id)
            or not token(s.transaction_ref) or not uint(s.owner_revision)
            or type(s.budget) is not BudgetSnapshot or not valid_budget(s.budget)
            or type(s.readback) is not ReceiptReadback):
        raise ValueError("OWNER_SNAPSHOT_INVALID")
    rb=s.readback
    receipt_readback_digest(rb)
    if (rb.lookup.budget_id,rb.budget_revision,rb.budget_source_pin)!=(
            s.budget.budget_id,s.budget.revision,s.budget.source_digest):
        raise ValueError("OWNER_BUDGET_BINDING_INVALID")
    if rb.reconciliation is not None and (rb.reservation is None or rb.usage is None):
        raise ValueError("OWNER_RECONCILIATION_ORPHAN")
    for e,p in ((rb.reservation,s.reservation_pin),(rb.usage,s.usage_pin),
                (rb.reconciliation,s.reconciliation_pin)):
        if (e is None and p is not None) or (e is not None and
                (not digest_ok(p) or accounting_evidence_digest(e)!=p)):
            raise ValueError("OWNER_EVIDENCE_PIN_INVALID")
    return sha256(json.dumps({"version":"D0_OWNER_RECEIPT_V1","body":asdict(s)},
        sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()


def inspect_owner_snapshot(ctx,snapshot,reference,budget_reference,expected_pin):
    """Compare separately supplied observations; do not call an owner port here."""
    try:
        if snapshot is None or reference is None:
            return OwnerReceiptReview("OWNER_READBACK_MISSING_HOLD")
        if (type(snapshot) is not OwnerReceiptSnapshot or type(reference) is not OwnerReceiptSnapshot
                or not digest_ok(expected_pin) or owner_snapshot_digest(snapshot)!=expected_pin
                or owner_snapshot_digest(reference)!=expected_pin or snapshot!=reference):
            return OwnerReceiptReview("OWNER_SNAPSHOT_REFERENCE_HOLD")
        if snapshot.readback.lookup!=make_receipt_lookup(ctx,snapshot.budget.budget_id):
            return OwnerReceiptReview("OWNER_INVOCATION_BINDING_HOLD")
        result=inspect_receipt_readback(ctx,snapshot.budget,budget_reference,snapshot.readback,
            receipt_readback_digest(snapshot.readback),reservation_pin=snapshot.reservation_pin,
            usage_pin=snapshot.usage_pin,reconciliation_pin=snapshot.reconciliation_pin)
        if result.reason not in ("USAGE_MISSING_HOLD","D0_RECEIPT_MATCH_ONLY_OWNER_CUSTODY_HOLD"):
            return OwnerReceiptReview(result.reason,result)
        # A diagnostic match of the complete readback is not independently verified custody.
        return OwnerReceiptReview("D0_OWNER_SNAPSHOT_MATCH_ONLY",result,expected_pin)
    except (ValueError,TypeError,AttributeError,OverflowError,RecursionError):
        return OwnerReceiptReview("OWNER_SNAPSHOT_INVALID_HOLD")
