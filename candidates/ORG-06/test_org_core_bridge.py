"""Local bridge protocol tests with simulated Core/R3 owner ports, not product tests."""
from dataclasses import dataclass, replace, asdict
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
import sqlite3
import tempfile
from pathlib import Path
import org_core_bridge as m

SCOPE = ('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
HEAD = 'a'*64
PLAN = 'sha256:'+'b'*64
PROJECT = 'demo-research-project'
TASK = 'plan'
SEAT = 'lead'
HISTORY = (0,'0'*64)

@dataclass(frozen=True)
class Scope:
    tenant_id: str = SCOPE[0]
    company_id: str = SCOPE[1]
    environment_id: str = SCOPE[2]
    plan_revision: str = PLAN
    task_id: str = TASK
    run_id: str = 'demo-run-plan'
    agent_instance_id: str = 'demo-agent-plan'
    principal_id: str = 'demo-principal-plan'

@dataclass(frozen=True)
class RunPin:
    initial: object

@dataclass(frozen=True)
class Member:
    project_id: str = PROJECT
    plan_revision: str = PLAN
    task_id: str = TASK
    run_id: str = 'demo-run-plan'
    agent_instance_id: str = 'demo-agent-plan'
    principal_id: str = 'demo-principal-plan'
    initial_version: int = 0
    def row(self): return tuple(vars(self).values())

@dataclass(frozen=True)
class TaskHistory:
    task_id: str = TASK
    role: str = 'orchestrator'
    version: int = 0

@dataclass(frozen=True)
class CoreReview:
    structural_match: bool = True
    decision: str = 'HOLD'
    freshness: str = 'HISTORICAL_SAMPLE'
    dispatch_allowed: bool = False
    project_id: str = PROJECT
    plan_revision: str = PLAN
    tasks: tuple = (TaskHistory(),)

class OpsStore:
    def __init__(self, path):
        self.path = path; self._key = SCOPE; self.head = HEAD; self.history = HISTORY
        self.team = (SEAT,); self.queries = []; self.closed = None
    def _connect(self):
        db = sqlite3.connect(self.path); db.execute('PRAGMA query_only=ON'); db.set_trace_callback(self.queries.append); self.closed=db; return db
    def _head(self, db): return self.head
    def _read(self, db, head): return (NS(revision=lambda:'c'*64),)
    def _team(self, db, head, project, staffing): return NS(members=self.team)
    def _history(self, db, head, team, staffing): return self.history, ()

class Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.store=OpsStore(Path(tmp.name)/'mock-owner.sqlite')
        self.core=CoreReview(); self.core_calls=0; self.org_calls=0
        self.result={'structural_match':True,'decision':'HOLD','dispatch_allowed':False,'binding_created':False,'authority':False,'agent_instance_id':None,'principal_id':None,'run_id':None}
        self.args=dict(plan={},expected_revision=PLAN,project_id=PROJECT,pins=(RunPin(NS(scope=Scope(),version=0)),),members=(Member(),),pool=None,events=(),anchor=None,store=self.store,org_head=HEAD,history_pin=HISTORY,task_id=TASK,seat_id=SEAT)
        def core(*a,**kw): self.core_calls+=1; return self.core
        def org(s,seat,observed,expected):
            self.org_calls+=1; self.assertEqual(observed,expected); self.assertEqual(seat,SEAT); return self.result
        def token(x): m.require(type(x) is str and bool(x),'TOKEN')
        def hex_digest(x): m.require(type(x) is str and len(x)==64,'DIGEST')
        def check_pin(x): m.require(x==HISTORY,'HISTORY_PIN')
        deps=(core,CoreReview,lambda s:type(s) is Scope,lambda x:type(x) is int and x>=0,Member,SCOPE,RunPin,TaskHistory,OpsStore,check_pin,lambda *a:a,org,token,hex_digest)
        p=patch.object(m,'_dependencies',return_value=deps); p.start(); self.addCleanup(p.stop)
    def call(self, **kw): return m.review_research_binding(None,**{**self.args,**kw})
    def hold(self, reason, **kw):
        r=self.call(**kw); self.assertFalse(r.structural_match); self.assertEqual(r.reason,reason)
        self.assertIsNone(r.project_id); self.assertFalse(r.dispatch_allowed); self.assertIsNone(r.runtime_binding)
    def test_match_no_authority(self):
        r=self.call(); self.assertTrue(r.structural_match); self.assertEqual(r.task_id,TASK); self.assertEqual(r.decision,'HOLD')
        self.assertFalse(r.authoritative); self.assertFalse(r.release_ready); self.assertEqual(r.geometry_join,'HOLD'); self.assertIsNone(r.runtime_binding)
        self.assertNotIn('principal_id',asdict(r)); self.assertNotIn('run_id',asdict(r)); self.assertEqual(self.store.queries,['BEGIN'])
        with self.assertRaises(sqlite3.ProgrammingError): self.store.closed.execute('SELECT 1')
    def test_other_scope_before_core(self):
        self.store._key=('synthetic-tenant-a','synthetic-company-a','ORG_R4_SAMPLE_ONLY'); self.hold('ORG_SCOPE_HOLD'); self.assertEqual(self.core_calls,0)
    def test_core_reject(self): self.core=replace(self.core,structural_match=False); self.hold('CORE_READBACK_HOLD'); self.assertEqual(self.org_calls,0)
    def test_core_freshness(self): self.core=replace(self.core,freshness='LIVE'); self.hold('CORE_READBACK_HOLD')
    def test_core_dispatch(self): self.core=replace(self.core,dispatch_allowed=True); self.hold('CORE_READBACK_HOLD')
    def test_core_project(self): self.core=replace(self.core,project_id='other'); self.hold('CORE_READBACK_HOLD')
    def test_core_plan(self): self.core=replace(self.core,plan_revision='other'); self.hold('CORE_READBACK_HOLD')
    def test_missing_task(self): self.core=replace(self.core,tasks=()); self.hold('TASK_MEMBERSHIP_HOLD')
    def test_duplicate_task(self): self.core=replace(self.core,tasks=(TaskHistory(),TaskHistory())); self.hold('TASK_MEMBERSHIP_HOLD')
    def test_duplicate_member(self): self.hold('TASK_MEMBERSHIP_HOLD',members=(Member(),Member()))
    def test_wrong_run(self): self.hold('CORE_MEMBER_HOLD',members=(replace(Member(),run_id='demo-wrong'),))
    def test_wrong_principal(self): self.hold('CORE_MEMBER_HOLD',members=(replace(Member(),principal_id='demo-wrong'),))
    def test_wrong_instance(self): self.hold('CORE_MEMBER_HOLD',members=(replace(Member(),agent_instance_id='demo-wrong'),))
    def test_wrong_scope(self): self.hold('CORE_SCOPE_HOLD',pins=(RunPin(NS(scope=replace(Scope(),environment_id='OTHER'),version=0)),))
    def test_gate_not_agent(self): self.core=replace(self.core,tasks=(replace(TaskHistory(),role='independent-verifier'),)); self.hold('TASK_ROLE_HOLD')
    def test_stale_version(self): self.core=replace(self.core,tasks=(replace(TaskHistory(),version=-1),)); self.hold('TASK_ROLE_HOLD')
    def test_boolean_version(self): self.core=replace(self.core,tasks=(replace(TaskHistory(),version=True),)); self.hold('TASK_ROLE_HOLD')
    def test_org_head(self): self.store.head='d'*64; self.hold('ORG_HEAD_HOLD')
    def test_org_history(self): self.store.history=(1,'d'*64); self.hold('ORG_TEAM_HISTORY_HOLD')
    def test_org_team(self): self.store.team=(); self.hold('ORG_TEAM_HISTORY_HOLD')
    def test_org_binding(self): self.result['structural_match']=False; self.hold('ORG_BINDING_HOLD')
    def test_org_grant(self): self.result['binding_created']=True; self.hold('ORG_BINDING_HOLD')
    def test_org_identity_leak(self): self.result['principal_id']='demo-secret'; self.hold('ORG_BINDING_HOLD')
    def test_org_authority(self): self.result['authority']=True; self.hold('ORG_BINDING_HOLD')
    def test_connection_error(self):
        with patch.object(self.store,'_connect',side_effect=OSError('local path secret')): self.hold('REFERENCE_UNAVAILABLE_HOLD')
    def test_no_dependencies(self):
        with patch.object(m,'_dependencies',side_effect=ImportError('private path')): self.hold('REFERENCE_UNAVAILABLE_HOLD')

if __name__=='__main__': unittest.main(verbosity=2)
