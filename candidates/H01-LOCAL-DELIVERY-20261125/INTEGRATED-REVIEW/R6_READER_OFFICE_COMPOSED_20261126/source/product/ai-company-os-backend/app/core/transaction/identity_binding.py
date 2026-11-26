"""D4-R4 source candidate: identity/session inspection, never execution authority."""
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re


def token(v):
    return type(v) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', v) is not None


def digest(v):
    return type(v) is str and re.fullmatch(r'[0-9a-f]{64}', v) is not None


def revision(v):
    return type(v) is int and 0 < v < 2**63


@dataclass(frozen=True)
class Request:
    scope: tuple[str, str, str]
    project: str
    plan_revision: str
    task: str
    run: str
    agent: str
    principal: str
    intent_sha: str
    policy_epoch: int
    witness_epoch: int


@dataclass(frozen=True)
class Binding:
    request: Request
    authenticated_principal: str
    registry_revision: int
    membership_revision: int
    assignment_revision: int
    role_revision: int
    registry_sha: str
    membership_sha: str
    assignment_sha: str
    role_sha: str
    db_role: str
    database: str
    cluster: str
    expires_tick: int
    active: bool


@dataclass(frozen=True)
class SessionFacts:
    session_user: str
    current_user: str
    database: str
    cluster: str
    backend_pid: int
    row_security: bool
    unsafe_role: bool
    role_memberships: int
    owned_tables: int
    forced_tables: int
    schema_create: bool
    unsafe_table_grants: int


@dataclass(frozen=True)
class Review:
    reason: str
    structural_match: bool = False
    binding_sha: str | None = None
    decision: str = field(default='HOLD', init=False)
    commit_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)


def valid_request(r):
    return (type(r) is Request and type(r.scope) is tuple and len(r.scope) == 3
            and all(token(x) for x in (*r.scope,r.project,r.task,r.run,r.agent,r.principal))
            and type(r.plan_revision) is str and r.plan_revision.startswith('sha256:')
            and digest(r.plan_revision[7:]) and digest(r.intent_sha)
            and all(type(x) is int and 0 <= x < 2**63 for x in (r.policy_epoch,r.witness_epoch)))


def valid_binding(b):
    return (type(b) is Binding and valid_request(b.request)
            and all(token(x) for x in (b.authenticated_principal,b.db_role,b.database,b.cluster))
            and re.fullmatch(r'[a-z_][a-z0-9_]{0,62}',b.db_role) is not None
            and all(revision(x) for x in (b.registry_revision,b.membership_revision,b.assignment_revision,b.role_revision,b.expires_tick))
            and all(digest(x) for x in (b.registry_sha,b.membership_sha,b.assignment_sha,b.role_sha))
            and type(b.active) is bool)


def binding_digest(b):
    from dataclasses import asdict
    if not valid_binding(b):
        raise ValueError('D4_INVALID_BINDING')
    raw=json.dumps(['d4-r4-review-v1',asdict(b)],sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
    return sha256(raw.encode('ascii')).hexdigest()


def review_binding(request, initial, latest, tick):
    """Compare external server observations; does not authenticate or issue grants."""
    if not valid_request(request) or not valid_binding(initial) or not valid_binding(latest):
        return Review('D4_INVALID_INPUT')
    if type(tick) is not int or not 0 <= tick < 2**63:
        return Review('D4_CLOCK_HOLD')
    if initial != latest or initial.request != request:
        return Review('D4_SCOPE_OR_REVISION_HOLD')
    if not latest.active or tick >= latest.expires_tick:
        return Review('D4_REVOKED_OR_EXPIRED')
    if latest.authenticated_principal != request.principal:
        return Review('D4_DELEGATION_NOT_SUPPORTED')
    return Review('D4_BINDING_MATCH_ONLY',True,binding_digest(latest))


def review_session(binding, facts, expected_pid):
    if not valid_binding(binding) or type(facts) is not SessionFacts:
        return Review('D4_SESSION_INPUT_HOLD')
    if (facts.session_user != binding.db_role or facts.current_user != binding.db_role
            or facts.database != binding.database or facts.cluster != binding.cluster
            or not revision(expected_pid) or type(facts.backend_pid) is not int or facts.backend_pid != expected_pid
            or facts.row_security is not True or facts.unsafe_role is not False or facts.schema_create is not False
            or any(type(x) is not int or x != 0 for x in (facts.role_memberships,facts.owned_tables,facts.unsafe_table_grants))
            or type(facts.forced_tables) is not int or facts.forced_tables != 16):
        return Review('D4_SESSION_HOLD')
    return Review('D4_SESSION_MATCH_ONLY',True,binding_digest(binding))


def review_boundary(request, initial, latest, tick, facts, expected_pid):
    b=review_binding(request,initial,latest,tick)
    if not b.structural_match:
        return b
    s=review_session(latest,facts,expected_pid)
    if not s.structural_match:
        return s
    return Review('D4_BOUNDARY_MATCH_ONLY',True,b.binding_sha)


def disposition(outcome):
    if outcome == 'UNKNOWN':
        return 'QUARANTINE_RECONCILE_NO_RETRY'
    return 'CLOSE_DEDICATED_NO_REUSE'
