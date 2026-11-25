"""R4 current-source D0 writer -> real Core/ORG/IAM readback, no crypto or PG.
Uses original 0225 persisted writer fixture and actual product OperationsStore.
Not the original seven-case historical G7 runner; never a grant or acceptance.
"""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import secrets
import sqlite3
import unittest
import test_pinned_research_t1_0225 as pinned
from app.core.agent_runtime.lifecycle import RunState
from app.core.event_store.company_coordination import SCOPE
from app.core.development_review.research_slice import RESEARCH_REVISION
from app.core.iam_session import D0SessionResolver, SessionRecord, credential_digest
from app.core.transaction.intent_authority import RootPin
from app.core.transaction.identity_binding import Binding
from app.core.transaction.intent_identity import derive_request
from app.core.transaction.identity_fence_review import IdentityReadback, capture_session_reference, session_reference_digest
from app.core.transaction.org_membership_review import read_current_org_reference, org_reference_digest
from app.core.transaction.core_org_session_review import inspect_core_org_session_reference
from durable_ops import initialize_ops, OperationsStore, TaskPin, HistoryPin, ZERO
from persistence import Scope
from org_model import Org, Unit, Seat
from staffing import Staffing, Definition, Instance, Binding as StaffBinding
from operations import ProjectTeam

class CurrentR4ThreeStoreTests(unittest.TestCase):
    def setUp(self):
        self.p=pinned.PinnedResearchT1Tests();self.p.setUp();self.addCleanup(self.p.doCleanups)
        self.f=self.p.f
        self.member=next(m for m in self.f.members if m.task_id=='research')
        run=next(r for r in self.f.initial if r.scope.task_id=='research')
        self.intent=self.p.x.admit_intent(self.p.x.spec_for(run))
        self.root=RootPin('a'*64,'b'*64,1);self.now=100;self.secret=secrets.token_urlsafe(32)
        self.iam_path=self.f.path.with_name('r4.authority.sqlite')
        self.iam=D0SessionResolver.bootstrap_durable(self.iam_path,self.root,(
            SessionRecord('demo-session-research',credential_digest(self.secret),self.member.principal_id,
                          'AGENT',SCOPE,self.member.agent_instance_id,100,200),),domain='demo-clock',clock=lambda:self.now)
        self.owner_pin=self.iam.durable_pin
        req=derive_request(self.intent,self.member,SCOPE,self.member.principal_id)
        self.initial=IdentityReadback(self.member,SCOPE,self.member.principal_id,
             Binding(req,self.member.principal_id,1,1,1,1,'1'*64,'2'*64,'3'*64,'4'*64,'demo_role','db','cluster',500,True),self.root,300)
        self.session=capture_session_reference(self.iam,self.secret,self.intent,self.initial,root=self.root,owner_pin=self.owner_pin,domain='demo-clock')
        self.org_path=self.f.path.with_name('r4.org.sqlite');initialize_ops(self.org_path)
        self.scope=Scope(*SCOPE);self.store=OperationsStore(self.org_path,self.scope)
        t,c,_=SCOPE
        self.staff=Staffing(Org(t,c,(Unit(c,'company',None),Unit('ops','department',c)),
             (Seat('lead','ops','orchestrator'),Seat('worker','ops','research','lead'))),
             (Definition('d-lead','orchestrator'),Definition('d-worker','research')),
             (Instance('demo-agent-plan','d-lead',t,c),Instance(self.member.agent_instance_id,'d-worker',t,c)),
             (StaffBinding('lead','demo-agent-plan'),StaffBinding('worker',self.member.agent_instance_id)))
        self.head=self.store.record(self.staff,None)
        self.store.create_team(self.head,ProjectTeam(t,c,self.staff.revision(),self.f.project,'lead',('lead','worker')))
        task=TaskPin(self.scope,req.project,req.plan_revision,req.task,'research')
        self.history=self.store.append_proposal(self.head,task,task,'lead','worker','delegation',HistoryPin(0,ZERO))
        self.org=read_current_org_reference(self.store,self.initial,self.session,org_head=self.head,seat='worker',role='research',history_pin=self.history)
    def snapshots(self):
        out=[]
        for path in (self.f.path,self.org_path,self.iam_path):
            with closing(sqlite3.connect(path)) as db:out.append(tuple(db.iterdump()))
        return tuple(out)
    def review(self,**changes):
        args=dict(resolver=self.iam,credential=self.secret,intent=self.intent,initial=self.initial,
            session=self.session,session_sha=session_reference_digest(self.session),read_latest=lambda:self.initial,
            plan=self.f.plan,pins=self.p.pins(),members=self.f.members,pool=self.f.pool,events=self.f.events,
            anchor=self.p.x.budget,store=self.store,org_reference=self.org,org_sha=org_reference_digest(self.org),
            org_head=self.head,seat='worker',history_pin=self.history,root=self.root,owner_pin=self.owner_pin,domain='demo-clock')
        args.update(changes);before=self.snapshots()
        r=self.p.x.read(lambda cursor:inspect_core_org_session_reference(cursor,**args))
        self.assertEqual(self.snapshots(),before)
        self.assertEqual(r.decision,'HOLD');self.assertFalse(r.commit_allowed or r.dispatch_allowed or r.retry_allowed)
        return r
    def matched(self):
        r=self.review();self.assertTrue(r.structural_match,r.reason)
        self.assertEqual(r.reason,'D5G6_CORE_ORG_HISTORY_SESSION_MATCH_ONLY')
    def test_real_three_store_prefix(self):
        self.matched()
        self.p.admit();self.matched()
        running=self.p.step(replace(self.p.x.root,state=RunState.ADMITTED,version=1),RunState.RUNNING);self.matched()
        self.p.step(running,RunState.VERIFYING);self.matched()
        self.assertEqual(len(self.f.events),3)
        # Research is still queued; a structural match never grants dispatch.
        with closing(sqlite3.connect(self.iam_path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM claims').fetchone(),(0,))
    def test_persisted_core_member_tamper(self):
        self.p.chain();self.matched()
        self.f.change("UPDATE company_run_membership SET principal_id='demo-forged' WHERE task_id='research'")
        self.assertFalse(self.review().structural_match)
    def test_revoked_session(self):
        self.p.chain();self.matched()
        self.assertTrue(self.iam.revoke_local('demo-session-research',expected_revision=1))
        self.assertFalse(self.review().structural_match)
    def test_org_head_drift(self):
        self.p.chain();self.matched()
        self.store.record(replace(self.staff,previous=self.staff.revision()),self.head)
        self.assertFalse(self.review().structural_match)
    def test_tampered_writer_history(self):
        self.p.chain();self.matched()
        self.f.change("UPDATE run_audit SET lease_digest='forged' WHERE version=2")
        self.assertFalse(self.review().structural_match)
    def test_latest_member_drift(self):
        self.p.chain();self.matched()
        self.assertFalse(self.review(read_latest=lambda:replace(self.initial,member=replace(self.member,principal_id='demo-forged'))).structural_match)

if __name__=='__main__':unittest.main(verbosity=2)
