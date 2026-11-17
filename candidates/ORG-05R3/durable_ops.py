"""D0 durable proposals only. No authenticated product API, dispatch or event publication."""
from dataclasses import dataclass, asdict
from pathlib import Path
from contextlib import closing
import sqlite3, re
from persistence import Store, Scope, initialize
from integration_guard import token, require, hex_digest
from operations import ProjectTeam, context, propose, digest
from office_bridge import project, OfficeView, MeetingProposal

DDL = Path(__file__).with_name('operations.sql')
ZERO = '0'*64
TABLES = ('op_team','op_member','op_entry','op_notice')


def initialize_ops(path):
    initialize(path)
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript(DDL.read_text(encoding='utf-8'))
        for table in TABLES:
            for verb in ('UPDATE','DELETE'):
                db.execute(f"CREATE TRIGGER {table}_{verb.lower()} BEFORE {verb} ON {table} BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END")


@dataclass(frozen=True)
class TaskPin:
    scope: Scope
    project: str
    plan: str
    task: str
    role: str


@dataclass(frozen=True)
class HistoryPin:
    count: int
    head: str


@dataclass(frozen=True)
class OfficePin:
    scope: Scope
    world: str
    revision: str


def check_pin(pin):
    require(type(pin) is HistoryPin and type(pin.count) is int and 0<=pin.count<=4096,'HISTORY_PIN')
    hex_digest(pin.head)


class OperationsStore(Store):
    def _current(self,db,rev):
        hex_digest(rev); require(self._head(db)==rev,'STALE_ORG')
        return self._read(db,rev)[0]

    def _team(self,db,rev,project_id,s):
        token(project_id); k=self._key+(rev,project_id)
        row=db.execute('SELECT coordinator,team_digest FROM op_team WHERE t=? AND c=? AND e=? AND rev=? AND project=?',k).fetchone()
        require(row is not None,'TEAM_NOT_FOUND')
        members=tuple(x[0] for x in db.execute('SELECT seat FROM op_member WHERE t=? AND c=? AND e=? AND rev=? AND project=? ORDER BY seat',k))
        team=ProjectTeam(*self._key[:2],s.revision(),project_id,row[0],members)
        context(s,team); require(digest(asdict(team))==row[1],'TEAM_DIGEST')
        return team

    def create_team(self,rev,team):
        require(type(team) is ProjectTeam,'TEAM_SHAPE')
        token(team.project); token(team.coordinator)
        require(type(team.members) is tuple and 0<len(team.members)<=4096,'TEAM_MEMBERS')
        for m in team.members: token(m)
        team=ProjectTeam(team.tenant,team.company,team.revision,team.project,team.coordinator,tuple(sorted(team.members)))
        with closing(self._connect(True)) as db:
            try:
                db.execute('BEGIN IMMEDIATE'); s=self._current(db,rev); context(s,team)
                k=self._key+(rev,team.project)
                db.execute('INSERT INTO op_team VALUES (?,?,?,?,?,?,?)',k+(team.coordinator,digest(asdict(team))))
                db.executemany('INSERT INTO op_member VALUES (?,?,?,?,?,?)',(k+(m,) for m in team.members))
                self._team(db,rev,team.project,s); db.commit()
            except BaseException: db.rollback(); raise
        return digest(asdict(team))

    def _history(self,db,rev,team,s):
        k=self._key+(rev,team.project); prev=ZERO; seen=set(); out=[]
        rows=db.execute('SELECT seq,plan,task,sender,recipient,kind,role,previous,digest FROM op_entry WHERE t=? AND c=? AND e=? AND rev=? AND project=? ORDER BY seq',k)
        seats={p.id:p.role for p in s.org.seats}
        for n,row in enumerate(rows,1):
            seq,plan,task,sender,recipient,kind,role,old,h=row
            require(n<=4096 and seq==n and old==prev,'CHAIN')
            require(re.fullmatch(r'sha256:[0-9a-f]{64}',plan) is not None,'PLAN')
            p=propose(s,team,task,sender,recipient,kind)
            require(seats[recipient]==role,'TASK_ROLE')
            body=[k,n,plan,role,asdict(p),prev]; key=digest([plan,asdict(p)])
            require(key not in seen and digest(body)==h,'ENTRY_DIGEST')
            notice=db.execute('SELECT digest,state FROM op_notice WHERE t=? AND c=? AND e=? AND rev=? AND project=? AND seq=?',k+(n,)).fetchone()
            require(notice==(digest(['ORG_TASK_PROPOSAL_D0',k,n,h]),'HOLD'),'NOTICE')
            seen.add(key); prev=h; out.append({'sequence':n,'plan_revision':plan,'task':task,'sender':sender,'recipient':recipient,'kind':kind,'decision':'HOLD','digest':h})
        count=db.execute('SELECT count(*) FROM op_notice WHERE t=? AND c=? AND e=? AND rev=? AND project=?',k).fetchone()[0]
        require(count==len(out),'NOTICE_COUNT')
        return HistoryPin(len(out),prev),out

    def append_proposal(self,rev,observed,expected,sender,recipient,kind,history_pin):
        check_pin(history_pin)
        require(type(observed) is TaskPin and type(expected) is TaskPin and observed==expected,'TASK_REFERENCE')
        p=expected; require(type(p.scope) is Scope and p.scope.key()==self._key,'TASK_SCOPE')
        for v in (p.project,p.task,p.role,sender,recipient): token(v)
        require(type(p.plan) is str and re.fullmatch(r'sha256:[0-9a-f]{64}',p.plan) is not None,'PLAN')
        with closing(self._connect(True)) as db:
            try:
                db.execute('BEGIN IMMEDIATE'); s=self._current(db,rev); team=self._team(db,rev,p.project,s)
                current,_=self._history(db,rev,team,s); require(current==history_pin and current.count<4096,'HISTORY_CAS')
                proposal=propose(s,team,p.task,sender,recipient,kind)
                require(next(x.role for x in s.org.seats if x.id==recipient)==p.role,'TASK_ROLE')
                k=self._key+(rev,p.project); n=current.count+1
                h=digest([k,n,p.plan,p.role,asdict(proposal),current.head])
                db.execute('INSERT INTO op_entry VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',k+(n,p.plan,p.task,sender,recipient,kind,p.role,current.head,h))
                db.execute('INSERT INTO op_notice VALUES (?,?,?,?,?,?,?,?)',k+(n,digest(['ORG_TASK_PROPOSAL_D0',k,n,h]),'HOLD'))
                new,_=self._history(db,rev,team,s); db.commit(); return new
            except BaseException: db.rollback(); raise

    def history(self,rev,project_id,history_pin):
        """Read an archived or current revision against a separately retained pin."""
        check_pin(history_pin)
        with closing(self._connect()) as db:
            db.execute('BEGIN'); s=self._read(db,rev)[0]; team=self._team(db,rev,project_id,s)
            actual,entries=self._history(db,rev,team,s); require(actual==history_pin,'HISTORY_PIN_MISMATCH')
            return tuple(entries)

    def combined(self,rev,project_id,history_pin,office,office_pin,links=(),pairs=(),meeting_room=None):
        check_pin(history_pin)
        require(type(office_pin) is OfficePin and type(office_pin.scope) is Scope and office_pin.scope.key()==self._key,'OFFICE_SCOPE')
        hex_digest(office_pin.revision)
        require(type(office) is OfficeView and office.world==office_pin.world and office.revision()==office_pin.revision,'OFFICE_PIN')
        with closing(self._connect()) as db:
            db.execute('BEGIN'); s=self._current(db,rev); team=self._team(db,rev,project_id,s)
            actual,entries=self._history(db,rev,team,s); require(actual==history_pin,'HISTORY_PIN_MISMATCH')
            meetings=() if meeting_room is None else (MeetingProposal(team,meeting_room),)
            require(all(p.seat in team.members for p in pairs),'OFFICE_TEAM_SCOPE')
            view=project(s,office,s.revision(),office_pin.revision,links,pairs,meetings)
            return {'schema':'org.combined.preview.v0-D0','scope':dict(zip(('tenant_id','company_id','environment_id'),self._key)),'org_revision':rev,'staffing_revision':s.revision(),'project':project_id,'history':asdict(actual),'proposals':entries,'office_revision':office_pin.revision,'office_pairs':len(view['pairs']),'meeting_proposed':bool(meetings),'geometry_join':'HOLD','runtime_binding':None,'decision':'HOLD','authoritative':False,'dispatch_allowed':False}


@dataclass(frozen=True)
class ReadSession:
    scope: Scope
    principal: str
    expires: int
    permission: str


def studio_read(path,credential,resolve,expected_head,now):
    """Trusted server resolver port ONLY. Never accepts a caller-supplied scope.
    Real authentication, clock and resolver implementation are outside this candidate.
    """
    try:
        require(type(now) is int and now>=0 and type(credential) is str and 0<len(credential)<=4096,'REQUEST')
        session=resolve(credential)
        require(type(session) is ReadSession and type(session.scope) is Scope and type(session.expires) is int and session.expires>now and session.permission=='org.preview.read','SESSION')
        token(session.principal); require(session.principal.startswith('demo-'),'PRINCIPAL')
        return 200, Store(path,session.scope).studio_view(expected_head)
    except Exception:
        return 403, {'decision':'HOLD','reason':'READ_UNAVAILABLE','authoritative':False}
