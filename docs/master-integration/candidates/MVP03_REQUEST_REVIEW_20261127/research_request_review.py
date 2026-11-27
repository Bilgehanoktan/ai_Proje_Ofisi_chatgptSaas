"""MVP-03 candidate: fixed-plan request validation, never admission or persistence."""
from dataclasses import dataclass, field
import json

from app.core.orchestrator.engine import canonical_plan
from app.core.transaction.identity_binding import token, digest

# Proposal only: transport limits must be ratified before mounting any route.
MAX_BODY_BYTES = 4096
_FIELDS = frozenset({'worktype', 'project_ref', 'plan_ref', 'expected_plan_revision'})
_FIXED_PLAN = 'demo-plan-research'
_FIXED_REVISION = 'sha256:6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9'


@dataclass(frozen=True)
class ResearchRequestReview:
    reason: str
    structural_match: bool = False
    decision: str = field(default='HOLD', init=False)
    persistence_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    committed: bool = field(default=False, init=False)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError('NON_JSON_CONSTANT')


def inspect_research_request(raw, idempotency_key, *, server_project_ref, server_plan):
    """Inspect bytes and the server-selected D0 plan; no identity/permission proof.

    The server inputs are observations, not authenticated objects. A structural
    match does not prove membership, deduplication, persistence or permission.
    No side effects, credential input, receipt, grant, new ledger or T1 digest.
    """
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BODY_BYTES:
        return ResearchRequestReview('REQUEST_SIZE_OR_TYPE_HOLD')
    if not token(idempotency_key):
        return ResearchRequestReview('IDEMPOTENCY_KEY_SHAPE_HOLD')
    try:
        body = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                          parse_constant=_reject_constant)
    except (ValueError, UnicodeError, RecursionError):
        return ResearchRequestReview('REQUEST_JSON_HOLD')
    if type(body) is not dict or set(body) != _FIELDS:
        return ResearchRequestReview('REQUEST_FIELDS_HOLD')
    revision = body['expected_plan_revision']
    if (body['worktype'] != 'RESEARCH' or not token(body['project_ref'])
            or not token(body['plan_ref']) or type(revision) is not str
            or not revision.startswith('sha256:') or not digest(revision[7:])):
        return ResearchRequestReview('REQUEST_VALUE_HOLD')
    if not token(server_project_ref) or body['project_ref'] != server_project_ref:
        return ResearchRequestReview('REQUEST_PROJECT_HOLD')
    try:
        projection = canonical_plan(server_plan)
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        return ResearchRequestReview('PLAN_COMPILER_HOLD')
    if (body['plan_ref'] != _FIXED_PLAN or projection['plan_id'] != _FIXED_PLAN
            or revision != _FIXED_REVISION or projection['revision'] != _FIXED_REVISION
            or projection['admission'] != 'DENY'
            or projection['dispatch_allowed'] is not False
            or projection['release_ready'] is not False):
        return ResearchRequestReview('REQUEST_PLAN_PIN_HOLD')
    return ResearchRequestReview('D0_REQUEST_REFERENCE_MATCH_ONLY', True)
