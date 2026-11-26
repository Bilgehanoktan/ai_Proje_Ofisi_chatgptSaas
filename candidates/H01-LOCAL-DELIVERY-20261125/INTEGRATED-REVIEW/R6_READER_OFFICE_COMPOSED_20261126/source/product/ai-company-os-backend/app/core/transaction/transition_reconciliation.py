"""Read-only UNKNOWN handling, no retry, receipt issuance or independent authority."""
from dataclasses import dataclass, field
from app.core.transaction.postgres_transition_mapping import verify_transition_rows

@dataclass(frozen=True)
class TransitionReconciliation:
    reason: str
    exact_sample_match: bool = False
    retry_allowed: bool = field(default=False, init=False)
    committed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    decision: str = field(default='HOLD', init=False)

def reconcile_transition(cursor, intent, before, target, lease_reference):
    """Caller must use a separate consistent read-only snapshot. Absence is not rollback.
    Exact match is a structural diagnostic, not a signed or independently verified receipt.
    """
    try:
        verify_transition_rows(cursor, intent, before, target, lease_reference)
    except Exception:
        return TransitionReconciliation('D0_READBACK_INCOMPLETE_OR_UNAVAILABLE')
    return TransitionReconciliation('D0_EXACT_SAMPLE_MATCH_INDEPENDENT_REVIEW_REQUIRED', True)
