"""Fixture-only PG persistence; reuses pinned R3 validation and digest algorithms.
Caller must place exact ORG-05R3 directory on sys.path. No live handoff or dispatch.
"""
from dataclasses import dataclass, asdict
import re
from pg_transaction import SCHEMA, WRITERS, require, run, lock_head, insert, R3Read

ZERO = '0'*64

@dataclass(frozen=True)
class TaskReference:
    scope: tuple
    project: str
    plan: str
    task: str
    role: str
    recipient_instance: str
    principal: str


def reference_check(observed, expected, scope, recipient_instance):
    """Synthetic comparison only: matching caller references are NOT IAM evidence."""
    require(type(observed) is TaskReference and type(expected) is TaskReference and observed==expected,'TASK_REFERENCE')
    require(expected.scope==scope and expected.recipient_instance==recipient_instance,'TASK_SCOPE_INSTANCE')
    require(all(type(x) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}',x) for x in (expected.project,expected.task,expected.role,expected.recipient_instance,expected.principal)),'TASK_FIELDS')
    require(type(expected.plan) is str and re.fullmatch(r'sha256:[0-9a-f]{64}',expected.plan) is not None,'PLAN')
    require(expected.principal.startswith('demo-') and expected.recipient_instance.startswith('demo-'),'D0_REFERENCE')
    return expected


class PgOperations:
    def __init__(self, connect, scope):
        require(type(scope) is tuple and scope in WRITERS.values(),'PG_SCOPE')
        self.connect, self.scope = connect, scope

    def _view(self):
        from durable_ops import OperationsStore
        view = object.__new__(OperationsStore)
        view._key = self.scope
        return view

    def record(self, staffing, expected_head):
        from persistence import revision_id, notice_id
        from integration_guard import validate_staffing
        sd=validate_staffing(staffing)
        require((staffing.org.tenant,staffing.org.company)==self.scope[:2] and all(i.id.startswith('demo-') for i in staffing.instances),'STAFFING_SCOPE')
        def op(db):
            view=self._view(); old=lock_head(db,self.scope)
            require(old==expected_head,'STALE_HEAD')
            if old is None:
                seq=1; require(staffing.previous is None,'GENESIS')
            else:
                prior,n,_,_=view._read(R3Read(db),old); seq=n+1
                require(staffing.previous==prior.revision(),'STAFFING_PARENT')
            rev=revision_id(self.scope,seq,old,sd); k=self.scope+(rev,)
            insert(db,'org_revision',k+(seq,old,sd,staffing.previous))
            roles={d.id:d.role for d in staffing.definitions}; seats={p.id:p.role for p in staffing.org.seats}
            for table, rows in (
                ('org_unit',[(u.id,u.kind,u.parent) for u in staffing.org.units]),
                ('org_position',[(p.id,p.unit,p.role,p.reports_to) for p in staffing.org.seats]),
                ('org_definition_ref',[(d.id,d.role) for d in staffing.definitions]),
                ('org_instance_ref',[(i.id,i.definition,roles[i.definition]) for i in staffing.instances]),
                ('org_binding',[(b.seat,b.instance,seats[b.seat]) for b in staffing.bindings])):
                for row in rows: insert(db,table,k+row)
            insert(db,'org_notice',k+(notice_id(self.scope,rev,seq,old),'ORG_REVISION_RECORDED_D0','HOLD'))
            if old is None: insert(db,'org_head',k)
            else:
                cur=db.execute(f'UPDATE {SCHEMA}.org_head SET rev=%s WHERE t=%s AND c=%s AND e=%s AND rev=%s',(rev,)+self.scope+(old,))
                require(cur.rowcount==1,'HEAD_CAS')
            view._read(R3Read(db),rev)
            return rev
        return run(self.connect,self.scope,True,op)

    def create_team(self, rev, team):
        from operations import ProjectTeam, context, digest
        from integration_guard import token, hex_digest
        hex_digest(rev)
        require(type(team) is ProjectTeam and type(team.members) is tuple and 0<len(team.members)<=4096,'TEAM_SHAPE')
        for value in (team.project,team.coordinator,*team.members): token(value)
        team=ProjectTeam(team.tenant,team.company,team.revision,team.project,team.coordinator,tuple(sorted(team.members)))
        def op(db):
            require(lock_head(db,self.scope)==rev,'STALE_ORG')
            view=self._view(); reader=R3Read(db); s=view._read(reader,rev)[0]; context(s,team)
            k=self.scope+(rev,team.project); h=digest(asdict(team))
            insert(db,'op_team',k+(team.coordinator,h))
            for member in team.members: insert(db,'op_member',k+(member,))
            view._team(reader,rev,team.project,s)
            return h
        return run(self.connect,self.scope,True,op)

    def append_proposal(self, rev, observed, expected, sender, recipient, kind, history_pin):
        from durable_ops import check_pin
        from operations import propose, digest
        from integration_guard import token, hex_digest
        hex_digest(rev); check_pin(history_pin); token(sender); token(recipient)
        require(type(expected) is TaskReference,'TASK_REFERENCE')
        def op(db):
            require(lock_head(db,self.scope)==rev,'STALE_ORG')
            view=self._view(); reader=R3Read(db); s=view._read(reader,rev)[0]
            instances={b.seat:b.instance for b in s.bindings}
            p=reference_check(observed,expected,self.scope,instances.get(recipient))
            team=view._team(reader,rev,p.project,s)
            current,_=view._history(reader,rev,team,s)
            require(current==history_pin and current.count<4096,'HISTORY_CAS')
            proposal=propose(s,team,p.task,sender,recipient,kind)
            require(next(x.role for x in s.org.seats if x.id==recipient)==p.role,'TASK_ROLE')
            k=self.scope+(rev,p.project); n=current.count+1
            h=digest([k,n,p.plan,p.role,asdict(proposal),current.head])
            insert(db,'op_entry',k+(n,p.plan,p.task,sender,recipient,kind,p.role,current.head,h))
            insert(db,'op_notice',k+(n,digest(['ORG_TASK_PROPOSAL_D0',k,n,h]),'HOLD'))
            new,_=view._history(reader,rev,team,s)
            return new
        return run(self.connect,self.scope,True,op)

    def history(self, rev, project, history_pin):
        from durable_ops import check_pin
        from integration_guard import hex_digest, token
        check_pin(history_pin); hex_digest(rev); token(project)
        def op(db):
            view=self._view(); reader=R3Read(db); s=view._read(reader,rev)[0]
            team=view._team(reader,rev,project,s); actual,entries=view._history(reader,rev,team,s)
            require(actual==history_pin,'HISTORY_PIN_MISMATCH')
            return tuple(entries)
        return run(self.connect,self.scope,False,op)

    def read_current(self, expected_head):
        """Internal validated readback only, not a Studio HTTP response or IAM claim."""
        from integration_guard import hex_digest
        hex_digest(expected_head)
        def op(db):
            view=self._view(); reader=R3Read(db)
            actual=view._head(reader)
            require(actual==expected_head,'HEAD_MISMATCH')
            return actual,view._read(reader,actual)
        return run(self.connect,self.scope,False,op)
