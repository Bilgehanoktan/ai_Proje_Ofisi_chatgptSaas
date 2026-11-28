"""Selected G7 protocol tests with actual Core SQL reader and ORG-06 bridge.

Core company rows are direct synthetic fixture seeds using original DDL. The
full Research history, R3 staffing and G5 session ports are simulated here;
these tests are NOT the actual three-store integration or authorization.
"""
from contextlib import closing
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import patch

from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, valid_scope, uint
from app.core.event_store.company_coordination import Member, SCOPE, Pool, Allocation, CompanyEvent, inspect_company
from app.core.transaction.identity_binding import Binding, Review, review_binding, token, digest
from app.core.transaction.intent_identity import derive_request
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.core_org_session_review import inspect_core_org_session_reference
import org_core_bridge as bridge

ROOT = Path(__file__).resolve().parents[3]
SQL = ('0192/candidate_event_outbox_fence.sql','0193/candidate_run_head.sql',
       '0194/candidate_transition_roles.sql','0195/candidate_admission_budget.sql',
       '0196L/candidate_lease_settlement.sql','0203T/terminal_command_anchors.sql',
       '0204C/company_event_order.sql')
PLAN = 'sha256:'+'b'*64
PROJECT = 'demo-research-project'
HEAD = 'c'*64
HISTORY = (0, '0'*64)


@dataclass(frozen=True)
class IdentityReadback:
    member: Member
    scope: tuple
    principal: str
    binding: Binding
    tick: int


@dataclass(frozen=True)
class SessionReference:
    request: object


@dataclass(frozen=True)
class OrgReadback:
    role: str
    seat: str = 'worker'


@dataclass(frozen=True)
class RunPin:
    initial: RunObservation


@dataclass(frozen=True)
class TaskHistory:
    task_id: str
    role: str
    version: int


@dataclass(frozen=True)
class CoreReview:
    structural_match: bool
    project_id: str
    plan_revision: str
    tasks: tuple
    decision: str = 'HOLD'
    freshness: str = 'HISTORICAL_SAMPLE'
    dispatch_allowed: bool = False
    release_ready: bool = False


class SelectCursor:
    def __init__(self, db): self.c = db.cursor()
    def execute(self, sql, params=()):
        if not sql.startswith('SELECT ') or ';' in sql or 'FOR UPDATE' in sql:
            raise ValueError('SELECT_ONLY')
        return self.c.execute(sql.replace('t1_candidate.','').replace('%s','?'),params)
    def fetchone(self): return self.c.fetchone()


class OpsStore:
    # Explicitly simulated ORG owner port; no actual R3 persistence here.
    _key = SCOPE
    def __init__(self, path): self.path = path
    def _connect(self):
        db = sqlite3.connect(self.path)
        db.execute('PRAGMA query_only=ON')
        return db
    def _head(self, db): return HEAD
    def _read(self, db, head): return (NS(revision=lambda:'a'*64),)
    def _team(self, db, head, project, staffing): return NS(members=('worker',))
    def _history(self, db, head, team, staffing): return HISTORY, ()


def require_token(x): bridge.require(token(x),'TEST_TOKEN_HOLD')
def require_digest(x): bridge.require(digest(x),'TEST_DIGEST_HOLD')
def check_history(x): bridge.require(x==HISTORY,'TEST_HISTORY_HOLD')


class ResearchMembershipTests(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)/'core.sqlite'
        self.store = OpsStore(Path(temp.name)/'simulated-org.sqlite')
        self.scope = Scope(*SCOPE,PLAN,'research','demo-run-research','demo-agent-research','demo-principal-research')
        self.member = Member(PROJECT,PLAN,'research',self.scope.run_id,self.scope.agent_instance_id,self.scope.principal_id,0)
        self.members = (self.member,)
        self.pins = (RunPin(RunObservation(self.scope,RunState.QUEUED,0,0)),)
        self.pool = Pool('budget','USD',100,0,2,3,'d'*64,(Allocation(PROJECT,100),))
        self.events = ()
        self.role = 'research'
        self.core_reads = 0
        self.g5_calls = 0
        self.g5_mode = 'normal'
        self.set_intent(0)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('PRAGMA foreign_keys=ON')
            for p in SQL:
                db.executescript((ROOT/'database'/p).read_text().replace('CREATE SCHEMA t1_candidate;','').replace('t1_candidate.',''))
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',(*SCOPE,PLAN,'research',self.scope.run_id,self.scope.agent_instance_id,self.scope.principal_id,'QUEUED',0,0))
            db.execute('INSERT INTO company_run_membership VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,*self.member.row()))
            db.execute('INSERT INTO company_stream_heads VALUES (?,?,?,0)',SCOPE)
            db.execute('INSERT INTO sample_budgets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(*SCOPE,'budget',0,'USD',100,0,0,False,2,3,'d'*64))
        # Use exact ORG-06 bridge with a real original company readback and
        # explicit stand-ins for the larger Research history and R3 ports.
        deps=(self.core, CoreReview, valid_scope, uint, Member, SCOPE, RunPin,
              TaskHistory, OpsStore, check_history, lambda *a:a, self.org,
              require_token, require_digest)
        p=patch.object(bridge,'_dependencies',return_value=deps); p.start(); self.addCleanup(p.stop)
        g4=ModuleType('app.core.transaction.identity_fence_review')
        g4.IdentityReadback=IdentityReadback; g4.SessionReference=SessionReference
        g5=ModuleType('app.core.transaction.org_membership_review')
        g5.OrgReadback=OrgReadback; g5.inspect_org_session_reference=self.g5
        core=ModuleType('app.core.development_review.research_slice')
        core.inspect_research_slice=self.core; core.ResearchSliceReview=CoreReview
        history=ModuleType('app.core.event_store.plan_history_review'); history.TaskHistory=TaskHistory
        p=patch.dict(sys.modules,{g4.__name__:g4,g5.__name__:g5,core.__name__:core,history.__name__:history}); p.start(); self.addCleanup(p.stop)

    def set_intent(self, version):
        self.intent=LogicalIntent(self.scope,Operation.STATE_MUTATION,version,'e'*64,'effect','idem','grant','lease',None,2,3)
        req=derive_request(self.intent,self.member,SCOPE,self.scope.principal_id)
        binding=Binding(req,self.scope.principal_id,1,1,1,1,'1'*64,'2'*64,'3'*64,'4'*64,'demo_db_role','db','cluster',500,True)
        self.initial=IdentityReadback(self.member,SCOPE,self.scope.principal_id,binding,10)
        self.session=SessionReference(req)

    def core(self,cursor,plan,expected_revision,project_id,pins,members,pool,events,anchor,*,evidence=None):
        self.core_reads+=1
        actual=inspect_company(cursor,members,pool,events)
        # Plan/history is simulated, not passed as actual ResearchSliceReview.
        version=self.member.initial_version+sum(e.run_id==self.member.run_id for e in events)
        return CoreReview(actual.structural_match,project_id,expected_revision,(TaskHistory('research',self.role,version),))

    def org(self,staffing,seat,observed,expected):
        self.assertEqual(observed,expected)
        return dict(structural_match=True,decision='HOLD',dispatch_allowed=False,
                    binding_created=False,authority=False,agent_instance_id=None,principal_id=None,run_id=None)

    def g5(self,resolver,credential,intent,initial,session,session_sha,read_latest,**kw):
        self.g5_calls+=1
        self.assertEqual(kw['role'],self.role)
        self.assertNotEqual(kw['role'],initial.binding.db_role)
        if self.g5_mode=='skip': return Review('D5G5_ORG_PROPOSAL_SESSION_MATCH_ONLY',True,'f'*64)
        if self.g5_mode=='deny': return Review('SIMULATED_SESSION_HOLD')
        if self.g5_mode=='catch':
            try: read_latest()
            except Exception: pass
            return Review('D5G5_ORG_PROPOSAL_SESSION_MATCH_ONLY',True,'f'*64)
        latest=read_latest()
        if self.g5_mode=='double':
            try: read_latest()
            except Exception: pass
        r=review_binding(session.request,initial.binding,latest.binding,latest.tick)
        if self.g5_mode=='post_drift': self.role='qa'
        if self.g5_mode=='bad_digest': return Review('D5G5_ORG_PROPOSAL_SESSION_MATCH_ONLY',True,'not-a-hash')
        return Review('D5G5_ORG_PROPOSAL_SESSION_MATCH_ONLY',True,r.binding_sha) if r.structural_match else r

    def call(self,**kw):
        args=dict(plan={},pins=self.pins,members=self.members,pool=self.pool,events=self.events,anchor=None,
                  store=self.store,org_reference=OrgReadback('research'),org_sha='f'*64,org_head=HEAD,
                  seat='worker',history_pin=HISTORY,root=None,owner_pin=None,domain='demo-clock')
        args.update(kw)
        latest=args.pop('latest',lambda:self.initial)
        before=sha256(self.path.read_bytes()).hexdigest()
        with closing(sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            r=inspect_core_org_session_reference(SelectCursor(db),None,'test-only',self.intent,
                self.initial,self.session,'f'*64,latest,**args)
        self.assertEqual(before,sha256(self.path.read_bytes()).hexdigest())
        self.assertIs(type(r),Review)
        self.assertEqual(r.decision,'HOLD')
        self.assertFalse(r.commit_allowed or r.dispatch_allowed or r.retry_allowed)
        return r

    def deny(self,**kw): self.assertFalse(self.call(**kw).structural_match)
    def mutate(self,sql):
        with closing(sqlite3.connect(self.path)) as db,db: db.execute(sql)

    def test_real_core_membership_match_hold_only(self):
        self.assertTrue(self.call().structural_match)
        self.assertEqual((self.core_reads,self.g5_calls),(4,1))

    def test_persisted_member_principal_drift(self):
        self.mutate("UPDATE company_run_membership SET principal_id='demo-other'")
        self.deny(); self.assertEqual(self.g5_calls,0)

    def test_persisted_head_version_drift(self):
        self.mutate('UPDATE run_heads SET version=1')
        self.deny(); self.assertEqual(self.g5_calls,0)

    def test_duplicate_member(self):
        self.deny(members=(self.member,self.member)); self.assertEqual(self.core_reads,0)

    def test_project_alias(self):
        self.deny(members=(replace(self.member,project_id='demo-other'),)); self.assertEqual(self.core_reads,0)

    def test_role_mismatch(self):
        self.deny(org_reference=OrgReadback('qa')); self.assertEqual(self.g5_calls,0)

    def test_intent_version_not_persisted_version(self):
        self.set_intent(1); self.deny(); self.assertEqual(self.g5_calls,0)

    def test_latest_member_changed(self):
        self.deny(latest=lambda:replace(self.initial,member=replace(self.member,initial_version=1)))

    def test_session_port_does_not_read_latest(self):
        self.g5_mode='skip'; self.deny()

    def test_session_port_reads_latest_twice(self):
        self.g5_mode='double'; self.deny()

    def test_session_port_masks_failed_read(self):
        self.g5_mode='catch'
        self.deny(latest=lambda:replace(self.initial,member=replace(self.member,initial_version=1)))

    def test_latest_scope_changed(self):
        self.deny(latest=lambda:replace(self.initial,scope=('other',*SCOPE[1:])))

    def test_latest_principal_changed(self):
        self.deny(latest=lambda:replace(self.initial,principal='demo-other'))

    def test_latest_boolean_member_version(self):
        self.deny(latest=lambda:replace(self.initial,member=replace(self.member,initial_version=False)))

    def test_session_port_denies(self):
        self.g5_mode='deny'; self.deny()

    def test_role_changed_after_session(self):
        self.g5_mode='post_drift'; self.deny()

    def test_invalid_result_digest(self):
        self.g5_mode='bad_digest'; self.deny()

    def test_d4_role_revision_drift(self):
        self.deny(latest=lambda:replace(self.initial,binding=replace(self.initial.binding,role_revision=2)))

    def test_real_seeded_admission_version(self):
        # Real SQL rows, not a T1 writer test. Existing company replay validates the event.
        e=CompanyEvent(1,PROJECT,self.scope.run_id,1,'d0-tx-'+'b'*64,'a'*64,'D0_RUN_ADMISSION',(),0,20)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute("UPDATE run_heads SET state='ADMITTED',version=1")
            db.execute('INSERT INTO run_admissions VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,e.run_id,'admission',e.transaction_ref,e.request_digest,'lease','grant','budget'))
            db.execute('UPDATE sample_budgets SET revision=1,outstanding_minor=20')
            db.execute('INSERT INTO sample_reservations VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,e.run_id,'budget',1,20,'USD',e.request_digest,e.transaction_ref))
            db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?)',(*SCOPE,e.run_id,e.version,e.transaction_ref,e.kind,e.request_digest))
            db.execute('INSERT INTO company_event_order VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,*e.order_row()))
            db.execute('UPDATE company_stream_heads SET sequence=1')
        self.events=(e,); self.set_intent(1)
        self.assertTrue(self.call().structural_match)
        self.set_intent(0); self.deny()
