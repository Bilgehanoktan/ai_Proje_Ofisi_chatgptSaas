"""D5-G5: read current R3 organization data, compose existing G4 review.
D0 only. An ORG proposal is not an assignment or authority.
The exact R3 owner modules must be supplied by the isolated checkout runner.
"""
from contextlib import closing
from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from app.core.transaction.identity_binding import Review, digest, revision, token, valid_request
from app.core.transaction.identity_fence_review import (
    IdentityReadback, SessionReference, inspect_session_reference,
)

JOIN_FIELDS = ('tenant', 'company', 'environment', 'org_head', 'org_sequence',
               'staffing_digest', 'team_digest', 'project', 'plan_revision',
               'task', 'run', 'agent', 'principal', 'policy_epoch',
               'witness_epoch', 'role_revision', 'full_intent_digest')


@dataclass(frozen=True)
class OrgReadback:
    join: tuple
    seat: str
    unit: str
    role: str
    history_count: int
    history_head: str
    proposal_digest: str


def org_reference_digest(reference):
    if type(reference) is not OrgReadback:
        raise ValueError('D5G5_ORG_REFERENCE_HOLD')
    return sha256(json.dumps(['aicos-d5g5-org-review-v1', asdict(reference)],
        sort_keys=True, separators=(',', ':'), ensure_ascii=True,
        allow_nan=False).encode('ascii')).hexdigest()


def read_current_org_reference(store, sample, session, *, org_head, seat, role, history_pin):
    """Read current staffing/team/proposal in one existing R3 read transaction.
    No archived head fallback; D4 role revision is not ORG sequence.
    Core/role inputs remain owner observations, not independently verified facts.
    """
    from durable_ops import OperationsStore, check_pin
    from integration_guard import ReviewPin, inspect_runtime
    from operations import digest as org_digest

    if (type(store) is not OperationsStore or type(sample) is not IdentityReadback
            or type(session) is not SessionReference or not valid_request(session.request)
            or not digest(org_head) or not token(seat) or not token(role)):
        raise ValueError('D5G5_ORG_INPUT_HOLD')
    req = session.request
    binding = sample.binding
    if (store._key != req.scope or sample.scope != req.scope
            or sample.principal != req.principal or binding.request != req
            or session.observation.principal_id != req.principal
            or session.observation.agent_instance_id != req.agent
            or not revision(binding.role_revision)):
        raise ValueError('D5G5_ORG_SCOPE_HOLD')
    check_pin(history_pin)
    with closing(store._connect()) as db:
        db.execute('BEGIN')
        try:
            if store._head(db) != org_head:
                raise ValueError('D5G5_ORG_HEAD_HOLD')
            staffing, sequence, _, _ = store._read(db, org_head)
            team = store._team(db, org_head, req.project, staffing)
            actual, entries = store._history(db, org_head, team, staffing)
            if actual != history_pin or seat not in team.members or not revision(sequence):
                raise ValueError('D5G5_ORG_TEAM_HISTORY_HOLD')
            positions = [p for p in staffing.org.seats if p.id == seat]
            if len(positions) != 1 or positions[0].role != role:
                raise ValueError('D5G5_ORG_POSITION_HOLD')
            sd = staffing.revision()
            pin = ReviewPin(*req.scope, sd, req.project, req.plan_revision,
                            req.task, req.run, req.agent, req.principal, role)
            reviewed = inspect_runtime(staffing, seat, pin, pin)
            if (reviewed.get('structural_match') is not True
                    or reviewed.get('decision') != 'HOLD'
                    or reviewed.get('authority') is not False
                    or reviewed.get('dispatch_allowed') is not False
                    or reviewed.get('binding_created') is not False):
                raise ValueError('D5G5_ORG_STAFFING_HOLD')
            proposals = [e for e in entries if
                (e['plan_revision'], e['task'], e['recipient'], e['decision']) ==
                (req.plan_revision, req.task, seat, 'HOLD')]
            if len(proposals) != 1 or not digest(proposals[0]['digest']):
                raise ValueError('D5G5_ORG_PROPOSAL_HOLD')
            join = (*req.scope, org_head, sequence, sd, org_digest(asdict(team)),
                    req.project, req.plan_revision, req.task, req.run, req.agent,
                    req.principal, req.policy_epoch, req.witness_epoch,
                    binding.role_revision, req.intent_sha)
            return OrgReadback(join, seat, positions[0].unit, role,
                               actual.count, actual.head, proposals[0]['digest'])
        finally:
            db.rollback()


def inspect_org_session_reference(resolver, credential, intent, initial, session,
                                  session_sha, read_latest, *, store, org_reference,
                                  org_sha, org_head, seat, role, history_pin,
                                  root, owner_pin, domain):
    """Reuse G4's authority lock and re-read actual ORG during owner callback.
    Separate stores: no atomic freshness, no claim, no write, no commit permission.
    """
    try:
        if (not digest(org_sha) or org_reference_digest(org_reference) != org_sha
                or not callable(read_latest)):
            return Review('D5G5_ORG_REFERENCE_HOLD')
        def current(sample):
            value = read_current_org_reference(store, sample, session, org_head=org_head,
                        seat=seat, role=role, history_pin=history_pin)
            if value != org_reference:
                raise ValueError('D5G5_ORG_DRIFT_HOLD')
            return sample
        current(initial)
        result = inspect_session_reference(resolver, credential, intent, initial,
                    session, session_sha, lambda: current(read_latest()),
                    root=root, owner_pin=owner_pin, domain=domain)
        if not result.structural_match:
            return result
        current(initial)
        return Review('D5G5_ORG_PROPOSAL_SESSION_MATCH_ONLY', True, result.binding_sha)
    except Exception:
        return Review('D5G5_ORG_READBACK_HOLD')
