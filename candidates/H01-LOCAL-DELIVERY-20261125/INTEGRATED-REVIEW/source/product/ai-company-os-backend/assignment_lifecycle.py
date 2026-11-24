"""ORG-05R3 additive D0 assignment review. Never an issuer or execution gate.
Calls run inside the existing OperationsStore transaction; no commit/dispatch here.
All inputs are explicit synthetic observations, NOT authenticated owner evidence.
"""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from app.core.transaction.identity_binding import Request, valid_request, token, digest, revision

SCOPE = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY')
ZERO = '0'*64
DDL = Path(__file__).with_name('assignment_review.sql')

@dataclass(frozen=True)
class AssignmentPin:
    request: Request
    org_head: str
    org_sequence: int
    staffing_digest: str
    team_digest: str
    history_count: int
    history_head: str
    proposal_digest: str
    seat: str
    task_role: str
    core_version: int
    registry_revision: int
    registry_sha: str
    membership_revision: int
    membership_sha: str
    role_revision: int
    role_sha: str

@dataclass(frozen=True)
class ApprovalObservation:
    action: str
    decision_ref: str
    issuer: str
    custody: str
    issued_tick: int
    expires_tick: int

@dataclass(frozen=True)
class AssignmentReview:
    state: str
    revision: int = 0
    assignment_sha: str = ZERO
    structural_match: bool = False
    decision: str = field(default='HOLD', init=False)
    authoritative: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    commit_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)


def need(ok, why):
    if not ok:
        raise ValueError(why)


def tick_ok(v):
    return type(v) is int and 0 <= v < 2**63


def demo(v):
    return token(v) and v.startswith('demo-')


def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def record_digest(scope, run, revision_no, state, previous, body):
    return sha256(canonical(['org.assignment.review.v0-D0',scope,run,revision_no,state,previous,body]).encode('ascii')).hexdigest()


def validate(p, a, now, action):
    need(type(p) is AssignmentPin and valid_request(p.request) and p.request.scope==SCOPE,'ASSIGNMENT_SCOPE')
    r=p.request
    need(all(demo(x) for x in (r.project,r.run,r.agent,r.principal)) and token(p.seat)
         and p.task_role in ('orchestrator','research','engineer','qa'),'ASSIGNMENT_REFERENCE')
    need(all(revision(x) for x in (p.org_sequence,p.history_count,p.registry_revision,p.membership_revision,p.role_revision))
         and p.history_count<=4096 and tick_ok(p.core_version),'ASSIGNMENT_REVISION')
    pins=(p.org_head,p.staffing_digest,p.team_digest,p.history_head,p.proposal_digest,p.registry_sha,p.membership_sha,p.role_sha)
    need(all(digest(x) for x in pins),'ASSIGNMENT_DIGEST')
    # Independent domain pins, never alias a proposal digest to owner evidence.
    need(len({p.registry_sha,p.membership_sha,p.role_sha,p.proposal_digest})==4,'ASSIGNMENT_ALIAS')
    need(type(a) is ApprovalObservation and a.action==action and all(demo(x) for x in (a.decision_ref,a.issuer,a.custody))
         and len({a.issuer,a.custody,r.principal,r.agent})==4,'APPROVAL_OBSERVATION')
    need(tick_ok(now) and tick_ok(a.issued_tick) and revision(a.expires_tick)
         and a.issued_tick<=now<a.expires_tick,'APPROVAL_CLOCK')


def source_match(db, p):
    """Exact persisted proposal/seat/team/head references; existing _history also runs in Store wrapper."""
    r=p.request; k=(*SCOPE,p.org_head,r.project)
    head=db.execute('SELECT rev FROM org_head WHERE t=? AND c=? AND e=?',SCOPE).fetchone()
    need(head==(p.org_head,),'ASSIGNMENT_ORG_HEAD')
    org=db.execute('SELECT seq,staffing_digest FROM org_revision WHERE t=? AND c=? AND e=? AND rev=?',k[:4]).fetchone()
    need(org==(p.org_sequence,p.staffing_digest),'ASSIGNMENT_STAFFING')
    team=db.execute('SELECT team_digest FROM op_team WHERE t=? AND c=? AND e=? AND rev=? AND project=?',k).fetchone()
    need(team==(p.team_digest,),'ASSIGNMENT_TEAM')
    rows=db.execute('SELECT seq,plan,task,recipient,role,digest FROM op_entry WHERE t=? AND c=? AND e=? AND rev=? AND project=? ORDER BY seq',k).fetchmany(4097)
    need(len(rows)==p.history_count and rows[-1][-1]==p.history_head and all(x[0]==i for i,x in enumerate(rows,1)),'ASSIGNMENT_HISTORY')
    matches=[x for x in rows if x[-1]==p.proposal_digest]
    need(len(matches)==1 and matches[0][1:5]==(r.plan_revision,r.task,p.seat,p.task_role),'ASSIGNMENT_PROPOSAL')
    seq=matches[0][0]
    notice=db.execute('SELECT state FROM op_notice WHERE t=? AND c=? AND e=? AND rev=? AND project=? AND seq=?',(*k,seq)).fetchone()
    member=db.execute('SELECT seat FROM op_member WHERE t=? AND c=? AND e=? AND rev=? AND project=? AND seat=?',(*k,p.seat)).fetchone()
    binding=db.execute('SELECT instance,role FROM org_binding WHERE t=? AND c=? AND e=? AND rev=? AND seat=?',(*k[:4],p.seat)).fetchone()
    need(notice==('HOLD',) and member==(p.seat,) and binding==(r.agent,p.task_role),'ASSIGNMENT_SEAT')


def read_chain(db, run):
    need(demo(run),'ASSIGNMENT_RUN')
    rows=db.execute('SELECT revision,state,previous,digest,body FROM op_assignment_review WHERE t=? AND c=? AND e=? AND run=? ORDER BY revision',(*SCOPE,run)).fetchmany(3)
    need(len(rows)<=2,'ASSIGNMENT_CHAIN')
    prev=ZERO; first=None
    for i,(n,state,old,h,raw) in enumerate(rows,1):
        body=json.loads(raw)
        need(n==i and state==('ACCEPTED_D0' if i==1 else 'REVOKED_D0') and old==prev
             and canonical(body)==raw and h==record_digest(SCOPE,run,n,state,old,body),'ASSIGNMENT_CHAIN')
        need(set(body)=={'pin','approval'} and body['pin']['request']['run']==run
             and tuple(body['pin']['request']['scope'])==SCOPE,'ASSIGNMENT_CHAIN')
        # Reconstruct and validate persisted typed inputs; issuer data remains synthetic.
        pp=dict(body['pin']); rq=dict(pp.pop('request')); rq['scope']=tuple(rq['scope'])
        pp=AssignmentPin(Request(**rq),**pp); aa=ApprovalObservation(**body['approval'])
        validate(pp,aa,aa.issued_tick,'ACCEPT' if i==1 else 'REVOKE')
        if i==1: first=body
        else:
            need(body['pin']==first['pin'] and aa.issued_tick>=first['approval']['issued_tick']
                 and aa.decision_ref!=first['approval']['decision_ref'],'ASSIGNMENT_CHAIN')
        prev=h
    return rows,first


def append_decision(db, pin, approval, now, expected_sha, *, revoke=False):
    """Caller owns BEGIN IMMEDIATE and rollback. No in-place update or run retargeting."""
    need(db.in_transaction and type(revoke) is bool and digest(expected_sha),'ASSIGNMENT_TX')
    validate(pin,approval,now,'REVOKE' if revoke else 'ACCEPT')
    r=pin.request; rows,first=read_chain(db,r.run)
    need((rows[-1][3] if rows else ZERO)==expected_sha,'ASSIGNMENT_CAS')
    body=json.loads(canonical({'pin':asdict(pin),'approval':asdict(approval)}))
    if revoke:
        need(len(rows)==1 and body['pin']==first['pin'] and approval.issued_tick>=first['approval']['issued_tick']
             and approval.decision_ref!=first['approval']['decision_ref'],'ASSIGNMENT_REVOKE')
        n,state=2,'REVOKED_D0'
    else:
        need(not rows,'ASSIGNMENT_ALREADY_RECORDED')
        source_match(db,pin)
        n,state=1,'ACCEPTED_D0'
    h=record_digest(SCOPE,r.run,n,state,expected_sha,body)
    db.execute('INSERT INTO op_assignment_review VALUES (?,?,?,?,?,?,?,?,?)',(*SCOPE,r.run,n,state,expected_sha,h,canonical(body)))
    read_chain(db,r.run)
    return AssignmentReview(state,n,h,True)


def inspect_assignment(db, pin, expected_sha, now):
    """Read against independently retained pin; no current grant even when matched."""
    try:
        need(db.in_transaction and type(pin) is AssignmentPin and valid_request(pin.request)
             and pin.request.scope==SCOPE and digest(expected_sha) and tick_ok(now),'ASSIGNMENT_READ')
        rows,first=read_chain(db,pin.request.run)
        if not rows: return AssignmentReview('MISSING_HOLD')
        n,state,_,h,_=rows[-1]
        need(h==expected_sha and json.loads(canonical(asdict(pin)))==first['pin'],'ASSIGNMENT_READBACK')
        if state=='REVOKED_D0': return AssignmentReview(state,n,h,True)
        if now<first['approval']['issued_tick'] or now>=first['approval']['expires_tick']:
            return AssignmentReview('EXPIRED_OR_CLOCK_HOLD',n,h)
        source_match(db,pin)
        return AssignmentReview(state,n,h,True)
    except Exception:
        return AssignmentReview('READ_UNAVAILABLE_HOLD')


def verify_core_reference(pin, cursor, args, intent, member, member_scope, principal):
    """Reuse actual historical Core reader, not a supplied boolean or role label.
    Caller owns the separate consistent Core cursor. No cross-store freshness/authority.
    """
    from app.core.development_review.research_slice import inspect_research_slice, ResearchSliceReview
    from app.core.event_store.plan_history_review import TaskHistory
    from app.core.event_store.company_coordination import Member
    from app.core.transaction.intent_identity import derive_request
    need(type(pin) is AssignmentPin and type(args) is dict and type(member) is Member,'ASSIGNMENT_CORE_INPUT')
    r=pin.request
    need(derive_request(intent,member,member_scope,principal)==r and intent.expected_version==pin.core_version,'ASSIGNMENT_CORE_REQUEST')
    members=args.get('members')
    need(type(members) is tuple and all(type(m) is Member for m in members),'ASSIGNMENT_CORE_MEMBERS')
    selected=[m for m in members if (m.project_id,m.plan_revision,m.task_id)==(r.project,r.plan_revision,r.task)]
    need(selected==[member] and args.get('project_id')==r.project and args.get('expected_revision')==r.plan_revision,'ASSIGNMENT_CORE_MEMBER')
    result=inspect_research_slice(cursor,**args)
    need(type(result) is ResearchSliceReview and result.structural_match is True and result.decision=='HOLD'
         and result.freshness=='HISTORICAL_SAMPLE' and result.dispatch_allowed is False and result.release_ready is False
         and result.project_id==r.project and result.plan_revision==r.plan_revision
         and type(result.tasks) is tuple and all(type(t) is TaskHistory for t in result.tasks),'ASSIGNMENT_CORE_READBACK')
    tasks=[t for t in result.tasks if t.task_id==r.task]
    need(len(tasks)==1 and type(tasks[0].version) is int and (tasks[0].role,tasks[0].version)==(pin.task_role,pin.core_version),'ASSIGNMENT_CORE_TASK')
