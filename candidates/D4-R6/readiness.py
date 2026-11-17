"""Review-only gate inventory; caller observations never confer authority."""
from dataclasses import dataclass, field

GATES = ('r2_exact_pg','r3_race_pg','r3_lost_ack_pg','org_pg_26',
         'common_scope_owner_review','canonical_identity_resolver',
         'canonical_org_task_run_binding','role_scope_acl_provenance',
         'atomic_revocation_fence','unknown_durable_reconciliation',
         'r03_owner_mapping','independent_security_review')
CORE_SCOPE = ('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
ORG_SCOPES = (('synthetic-tenant-a','synthetic-company-a','ORG_R4_SAMPLE_ONLY'),
              ('synthetic-tenant-b','synthetic-company-b','ORG_R4_SAMPLE_ONLY'))


@dataclass(frozen=True)
class Review:
    missing: tuple[str,...]
    structural_complete: bool = False
    decision: str = field(default='HOLD',init=False)
    activation_allowed: bool = field(default=False,init=False)
    retry_allowed: bool = field(default=False,init=False)


def review_gates(observations):
    """Boolean review inventory only, not evidence verification or gate promotion."""
    if type(observations) is not dict or set(observations)!=set(GATES):
        return Review(GATES)
    missing=tuple(k for k in GATES if observations[k] is not True)
    return Review(missing,not missing)


def scope_review(core, org):
    """Exact proposed D0 profile comparison; no alias or permission."""
    return ('D4_COMMON_SCOPE_MATCH_REVIEW_ONLY' if type(core) is tuple and type(org) is tuple
            and core==org==CORE_SCOPE else 'D4_COMMON_SCOPE_HOLD')


def outcome_review(outcome, exact_readback):
    """No result grants retry, dispatch, compensation or independent acceptance."""
    if outcome=='UNKNOWN' or outcome=='PENDING':
        return 'QUARANTINE_EXACT_READBACK_HOLD' if exact_readback is True else 'QUARANTINE_UNRESOLVED_HOLD'
    return 'CLOSE_DEDICATED_HOLD'
