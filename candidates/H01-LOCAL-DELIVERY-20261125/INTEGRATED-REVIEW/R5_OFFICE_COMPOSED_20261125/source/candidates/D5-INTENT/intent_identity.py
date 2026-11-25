"""D5: derive the D4 identity request from the original Core intent and member.

Internal D0 adapter only. Inputs are owner-supplied readbacks, not HTTP claims.
No authentication, role issuance, new authority, SQL, dispatch or commit.
"""
from dataclasses import asdict
from hashlib import sha256
import json

from app.core.agent_runtime.lifecycle import Scope
from app.core.transaction.review import LogicalIntent, valid_intent
from app.core.event_store.company_coordination import Member, SCOPE, _member
from identity_binding import Request, Review, review_binding


def full_intent_digest(intent):
    """Separate pin of all original fields; never replace request_digest."""
    if (type(intent) is not LogicalIntent or type(intent.scope) is not Scope
            or not valid_intent(intent)):
        raise ValueError('D5_INTENT_INVALID')
    body = ['aicos-d5-full-logical-intent-v1', asdict(intent)]
    return sha256(json.dumps(body, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


def derive_request(intent, member, member_scope, authenticated_principal):
    """Use the existing company Member, never a caller-provided project alias.

    No provenance or freshness is inferred from a Member or principal string.
    The owner must obtain those from its protected server-side reader.
    """
    pin = full_intent_digest(intent)
    s = intent.scope
    scope = (s.tenant_id, s.company_id, s.environment_id)
    if (type(member_scope) is not tuple or member_scope != scope or scope != SCOPE
            or type(member) is not Member or not _member(member)
            or member.row()[1:6] != (s.plan_revision, s.task_id, s.run_id,
                                     s.agent_instance_id, s.principal_id)
            or member.initial_version > intent.expected_version):
        raise ValueError('D5_CORE_MEMBER_HOLD')
    if type(authenticated_principal) is not str or authenticated_principal != s.principal_id:
        raise ValueError('D5_PRINCIPAL_HOLD')
    return Request(scope, member.project_id, s.plan_revision, s.task_id, s.run_id,
                   s.agent_instance_id, s.principal_id, pin,
                   intent.policy_epoch, intent.witness_epoch)


def review_bound_intent(intent, member, latest_member, member_scope,
                        latest_member_scope, authenticated_principal,
                        initial_binding, latest_binding, tick):
    """Reuse R4's existing review, including time and revision checks.

    The result is a HOLD diagnostic even on match; no atomic freshness, IAM or
    protected commit is established by this adapter.
    """
    try:
        first = derive_request(intent, member, member_scope, authenticated_principal)
        latest = derive_request(intent, latest_member, latest_member_scope,
                                authenticated_principal)
        if first != latest or member != latest_member:
            return Review('D5_MEMBER_DRIFT_HOLD')
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError) as exc:
        reason = str(exc) if type(exc) is ValueError and str(exc) in (
            'D5_INTENT_INVALID', 'D5_CORE_MEMBER_HOLD', 'D5_PRINCIPAL_HOLD') else 'D5_INPUT_HOLD'
        return Review(reason)
    return review_binding(first, initial_binding, latest_binding, tick)
