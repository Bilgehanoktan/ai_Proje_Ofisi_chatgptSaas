"""Actual 0220 pinned admission + 0196L bound ordinary + exact plan/company readback.
Canonical Research plan, local SQLite only; no result archive or independent success.
"""
from dataclasses import replace
import unittest
import test_research_t1_integration_0225 as base
from app.core.agent_runtime.lifecycle import RunState
from app.core.event_store.history_readback import OrdinaryPin
from app.core.event_store.plan_history_review import RunHistoryPin, inspect_plan_history
from app.core.event_store.company_coordination import inspect_company
from app.core.transaction.postgres_admission_mapping import commit_scheduled_admission
from app.core.transaction.postgres_lifecycle_mapping import AdmissionBinding, D0AdmissionBoundTransitionMapping
from app.core.transaction.postgres_session import CommitOutcomeUnknown
from app.core.development_review.research_slice import RESEARCH_REVISION


class PinnedResearchT1Tests(unittest.TestCase):
    def setUp(self):
        self.x=base.ResearchT1IntegrationTests();self.x.setUp();self.addCleanup(self.x.doCleanups)
        self.f=self.x.f;self.binding=AdmissionBinding(self.x.spec,self.x.intent);self.commands=()
    def pins(self):
        return tuple(RunHistoryPin(r,self.binding if r==self.x.root and self.f.events else None,
            self.commands if r==self.x.root else ()) for r in self.f.initial)
    def admit(self,**kw):
        x=self.x; args=dict(connect=lambda:base.SQLiteConnection(self.f.path),plan=self.f.plan,spec=x.spec,intent=x.intent,
            clock=lambda:x.clock,members=self.f.members,pool=self.f.pool,history=self.f.events,history_pins=self.pins())
        args.update(kw);receipt=commit_scheduled_admission(**args)
        self.f.events+=(x.event(x.intent,'D0_RUN_ADMISSION',0,20),);return receipt
    def step(self,before,target):
        x=self.x; m=D0AdmissionBoundTransitionMapping(self.binding,x.spec.lease,lambda:replace(x.clock,now_tick=11))
        i,receipt,after=x.ordinary(before,target,mapping=m)
        self.commands+=(OrdinaryPin(i,before,target,x.spec.lease),);return after
    def review(self,**kw):
        args=dict(plan=self.f.plan,expected_revision=RESEARCH_REVISION,pins=self.pins(),exclusive_budget_anchors=(self.x.budget,));args.update(kw)
        return self.x.read(lambda c:(inspect_plan_history(c,**args),inspect_company(c,self.f.members,self.f.pool,self.f.events)))
    def chain(self):
        self.admit();admitted=replace(self.x.root,state=RunState.ADMITTED,version=1)
        running=self.step(admitted,RunState.RUNNING);return self.step(running,RunState.VERIFYING)
    def test_canonical_full_pinned_prefix(self):
        p,c=self.review();self.assertTrue(p.structural_match and c.structural_match);self.assertEqual(p.event_count,0)
        self.chain();before=self.x.dump();p,c=self.review()
        self.assertTrue(p.structural_match and p.budget_reconciled and c.structural_match)
        self.assertEqual((p.event_count,c.event_count,c.outstanding_minor),(3,3,20))
        self.assertEqual({t.task_id:t.state for t in p.tasks},dict(draft='QUEUED',merge='QUEUED',plan='VERIFYING',qa='QUEUED',research='QUEUED',iv=None,release=None))
        self.assertFalse(p.dispatch_allowed or p.release_ready or c.independent_verified);self.assertEqual(self.x.dump(),before)
    def test_wrong_roster_no_write(self):
        before=self.x.dump()
        with self.assertRaisesRegex(ValueError,'MEMBER_HOLD'):self.admit(history_pins=self.pins()[:-1])
        self.assertEqual(self.x.dump(),before)
    def test_unverified_child_no_write(self):
        before=self.x.dump();r=next(r for r in self.f.initial if r.scope.task_id=='research');s=self.x.spec_for(r)
        with self.assertRaisesRegex(ValueError,'PREDECESSOR_PROOF'):self.admit(spec=s,intent=self.x.admit_intent(s))
        self.assertEqual(self.x.dump(),before)
    def test_forged_root_success_no_write(self):
        self.f.change("UPDATE run_heads SET state='SUCCEEDED' WHERE task_id='plan'");before=self.x.dump()
        with self.assertRaises(ValueError):self.admit()
        self.assertEqual(self.x.dump(),before)
    def test_wrong_historical_pin_hold(self):
        self.chain();p,_=self.review(pins=self.pins()[:-1]);self.assertFalse(p.structural_match)
    def test_tampered_admission_blocks_ordinary(self):
        self.admit();self.f.change("UPDATE run_audit SET lease_digest='forged' WHERE version=1")
        before=self.x.dump();admitted=replace(self.x.root,state=RunState.ADMITTED,version=1)
        with self.assertRaises(ValueError):self.step(admitted,RunState.RUNNING)
        self.assertEqual(self.x.dump(),before)
    def test_tampered_run_history_holds(self):
        self.chain();self.f.change("UPDATE run_audit SET lease_digest='forged' WHERE version=2")
        p,c=self.review();self.assertFalse(p.structural_match);self.assertTrue(c.structural_match)
    def test_unknown_pinned_admission_no_retry(self):
        e=self.x.event(self.x.intent,'D0_RUN_ADMISSION',0,20)
        with self.assertRaises(CommitOutcomeUnknown):self.admit(connect=lambda:base.SQLiteConnection(self.f.path,True))
        self.f.events+=(e,);before=self.x.dump();p,c=self.review();self.assertTrue(p.structural_match and c.structural_match)
        with self.assertRaises(ValueError):self.admit()
        self.assertEqual(self.x.dump(),before)
