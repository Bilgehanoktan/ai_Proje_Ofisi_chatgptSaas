"""D4-R1 review model only. Not authentication, authorization or a DB adapter."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Scope:
    tenant: str
    company: str
    environment: str


@dataclass(frozen=True)
class Binding:
    scope: Scope
    principal: str
    db_role: str
    revision: int


@dataclass(frozen=True)
class SessionFacts:
    session_user: str
    current_user: str
    database: str
    idle: bool
    row_security: bool
    superuser: bool
    bypassrls: bool
    owner_membership: bool
    other_scope_membership: bool


def review_checkout(binding, reference, request_scope, request_principal, facts, database):
    """Compare already supplied observations; never establish their provenance."""
    if type(binding) is not Binding or type(reference) is not Binding or type(facts) is not SessionFacts:
        return 'HOLD_MISSING_REFERENCE'
    if (type(binding.scope) is not Scope or type(request_scope) is not Scope
            or any(type(v) is not str or not v.strip() for v in
                   (binding.scope.tenant, binding.scope.company, binding.scope.environment,
                    binding.principal, binding.db_role, database))
            or type(binding.revision) is not int or binding.revision <= 0):
        return 'HOLD_INVALID_BINDING'
    if binding != reference or request_scope != reference.scope or request_principal != reference.principal:
        return 'HOLD_SCOPE_OR_REVISION'
    if (facts.session_user != reference.db_role or facts.current_user != reference.db_role
            or facts.database != database or facts.idle is not True or facts.row_security is not True
            or any(v is not False for v in (facts.superuser, facts.bypassrls,
                                           facts.owner_membership, facts.other_scope_membership))):
        return 'HOLD_SESSION'
    return 'MATCH_REVIEW_ONLY'


def review_release(*, outcome, rollback_ok, reset_ok, idle, identity_match, clean_state):
    """Conservative pool disposition model; no actual reset or checkout."""
    if outcome == 'UNKNOWN':
        return 'QUARANTINE_RECONCILE'
    if outcome not in ('COMMITTED', 'ROLLED_BACK'):
        return 'DISCARD'
    if any(v is not True for v in (rollback_ok, reset_ok, idle, identity_match, clean_state)):
        return 'DISCARD'
    return 'CLOSE_DEDICATED_REVIEW_ONLY'
