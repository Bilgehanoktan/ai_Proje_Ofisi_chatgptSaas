"""ORG-05 isolated D0 preflight, NOT a runtime binding or an authorization port."""
from dataclasses import dataclass, asdict
import re
from org_model import Org, Unit, Seat
from staffing import Staffing, Definition, Instance, Binding, verify_successor
from operations import ProjectTeam, context, digest, verify_history
from office_bridge import OfficeView, RoomLink, PairProposal, MeetingProposal, project

D0 = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY')
ROLES = frozenset(('orchestrator', 'research', 'engineer', 'qa'))
RESERVED = frozenset(('independent-verifier', 'policy-review', 'w-a-witness', 'iv', 'wa', 'w-a', 'pep', 'policy-engine', 'tool-gateway-pep', 'h01', 'human-ceo'))


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def token(v):
    require(type(v) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', v) is not None, 'TOKEN')


def role(v):
    require(type(v) is str and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', v) is not None and len(v) <= 128 and v not in RESERVED, 'ROLE')


def hex_digest(v):
    require(type(v) is str and re.fullmatch(r'[0-9a-f]{64}', v) is not None, 'DIGEST')


def validate_staffing(s):
    require(type(s) is Staffing and type(s.org) is Org, 'SHAPE')
    o = s.org
    token(o.tenant); token(o.company)
    for rows, cls in ((o.units, Unit), (o.seats, Seat), (s.definitions, Definition), (s.instances, Instance), (s.bindings, Binding)):
        require(type(rows) is tuple and all(type(x) is cls for x in rows), 'SHAPE')
        require(len(rows) <= 4096, 'REVIEW_LIMIT')
        for x in rows:
            for k, v in asdict(x).items():
                if k == 'role': role(v)
                elif k in ('parent', 'reports_to') and v is None: continue
                else: token(v)
    return s.revision()


@dataclass(frozen=True)
class ReviewPin:
    tenant_id: str
    company_id: str
    environment_id: str
    staffing_revision: str
    project_id: str
    plan_revision: str
    task_id: str
    run_id: str
    agent_instance_id: str
    principal_id: str
    role: str


def inspect_runtime(s, seat, observed, expected):
    """Compare separate caller-supplied D0 pins. Never establish their provenance."""
    result = {'decision': 'HOLD', 'structural_match': False, 'binding_created': False, 'dispatch_allowed': False, 'agent_instance_id': None, 'principal_id': None, 'run_id': None, 'authority': False, 'reason': 'REFERENCE_MISMATCH'}
    try:
        rev = validate_staffing(s)
        require(type(observed) is ReviewPin and type(expected) is ReviewPin and observed == expected, 'REFERENCE_MISMATCH')
        p = expected
        require((p.tenant_id, p.company_id, p.environment_id) == D0 and (s.org.tenant, s.org.company) == D0[:2], 'D0_SCOPE')
        hex_digest(p.staffing_revision); require(p.staffing_revision == rev, 'STALE_STAFFING')
        require(type(p.plan_revision) is str and re.fullmatch(r'sha256:[0-9a-f]{64}', p.plan_revision) is not None, 'PLAN_REVISION')
        for v in (p.project_id, p.run_id, p.agent_instance_id, p.principal_id):
            token(v); require(v.startswith('demo-'), 'D0_ID')
        token(p.task_id); token(seat)
        require(type(p.role) is str and p.role in ROLES, 'RUNTIME_ROLE')
        positions = {x.id: x for x in s.org.seats}
        occupied = {x.seat: x.instance for x in s.bindings}
        require(seat in positions and positions[seat].role == p.role and occupied.get(seat) == p.agent_instance_id, 'STAFFING_BINDING')
        return {**result, 'structural_match': True, 'reason': 'D0_PIN_MATCH_ONLY'}
    except (ValueError, TypeError, AttributeError, KeyError, RecursionError):
        return result


def verify_retained_history(s, team, entries, expected_count, expected_head):
    """Detect truncation/rewrite against a separately retained pin, not a signature."""
    validate_staffing(s)
    require(type(expected_count) is int and 0 <= expected_count <= 4096 and type(entries) is tuple and len(entries) == expected_count, 'HISTORY_COUNT')
    hex_digest(expected_head)
    require(all(type(e.sequence) is int for e in entries), 'HISTORY_SEQUENCE')
    head = verify_history(s, team, entries)
    require(head == expected_head, 'HISTORY_HEAD')
    return head


def review_office_successor(old, new, view, prior, links, pairs, meetings=()):
    """Reconstruct prior projection from original typed proposals; invalidate all."""
    validate_staffing(old); validate_staffing(new)
    nxt = verify_successor(old, new)
    require(type(view) is OfficeView and type(prior) is dict, 'SHAPE')
    require(prior == project(old, view, old.revision(), view.revision(), links, pairs, meetings), 'PRIOR_PROJECTION')
    return {'oldRevision': old.revision(), 'newRevision': nxt, 'invalidatedActors': sorted(p.avatar for p in pairs), 'invalidatedMeetings': sorted((m.team.project, m.room, digest(asdict(m.team))) for m in meetings), 'requiresReproposal': True, 'geometryJoin': 'HOLD', 'placement': None, 'authoritative': False}
