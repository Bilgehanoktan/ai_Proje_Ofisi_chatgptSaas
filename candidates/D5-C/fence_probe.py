"""D0 diagnostic insertion only. Never authorizes or invokes T1.
A successful structural check is still HOLD. No product route uses this module.
"""
from app.core.transaction.intent_authority import RootPin
from identity_fence_review import IdentityReadback, readback_digest, inspect_at_fence


def check_before_claim(intent, root, initial, expected_sha, read_latest):
    """Reject missing/mismatched references before consuming a fixture claim."""
    try:
        if (type(root) is not RootPin or type(initial) is not IdentityReadback
                or initial.root != root or not callable(read_latest)
                or readback_digest(intent, initial) != expected_sha):
            raise ValueError('D5C_PRECLAIM_HOLD')
    except Exception:
        raise ValueError('D5C_PRECLAIM_HOLD') from None


def stop_inside_fence(intent, root, initial, expected_sha, read_latest):
    """Check the D5-B readback at the original fence point, then ALWAYS stop.

    The reader here is a synthetic test dependency, not an authenticated owner.
    This stop is deliberately before existing journal.stage / T1 execution.
    Never attach to a real claim: even a diagnostic stop consumes the scope.
    """
    result = inspect_at_fence(intent, initial, expected_sha, root, read_latest)
    if not result.structural_match:
        raise ValueError(result.reason)
    raise ValueError('D5C_OWNER_INTEGRATION_HOLD')
