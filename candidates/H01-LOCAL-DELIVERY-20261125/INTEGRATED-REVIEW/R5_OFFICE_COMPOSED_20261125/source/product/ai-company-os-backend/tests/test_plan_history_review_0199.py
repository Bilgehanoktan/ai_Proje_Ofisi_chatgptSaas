"""Real disposable SQLite tests; no actual PostgreSQL, live Office or grant evidence."""
import copy
import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace
import test_history_readback_0198 as history
import test_admission_mapping_0195 as admission
from test_transition_mapping_0194 import PLAN, obs, SQLiteCursorShim, SQLiteConnectionShim
from app.core.agent_runtime.lifecycle import RunState
from app.core.orchestrator.engine import canonical_plan
from app.core.transaction.postgres_admission_mapping import D0PostgresAdmissionMapping
from app.core.transaction.postgres_lifecycle_mapping import AdmissionBinding
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction
from app.core.event_store.plan_history_review import RunHistoryPin, inspect_plan_history

class PlanHistoryTests(unittest.TestCase):
    def setUp(self):
        f=history.HistoryTests();f.setUp();self.addCleanup(f.doCleanups)
        self.f=f;self.path=f.f.path;self.plan=copy.deepcopy(PLAN)
        self.revision=canonical_plan(self.plan)['revision']
    def pins(self):
        return tuple(RunHistoryPin(obs(t), self.f.f.binding if t=='a' else None, tuple(self.f.pins) if t=='a' else ()) for t in 'abcq')
    def review(self,pins=None,plan=None,revision=None,anchors=None):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
            with SQLiteCursorShim(db) as c:
                return inspect_plan_history(c,self.plan if plan is None else plan,self.revision if revision is None else revision,self.pins() if pins is None else pins,exclusive_budget_anchors=anchors)
    def change(self,sql):
        with closing(sqlite3.connect(self.path)) as db,db:db.execute(sql)
    def hold(self,r):
        self.assertFalse(r.structural_match);self.assertIsNone(r.event_count);self.assertEqual(r.tasks,());self.assertIsNone(r.plan_revision)
        self.assertFalse(r.dispatch_allowed);self.assertFalse(r.release_ready);self.assertFalse(r.budget_reconciled)
    def test_admitted_roster_and_gates(self):
        r=self.review();self.assertTrue(r.structural_match);self.assertEqual(r.event_count,1);self.assertFalse(r.budget_reconciled)
        by={t.task_id:t for t in r.tasks};self.assertEqual(len(by),6);self.assertEqual(by['a'].state,'ADMITTED');self.assertEqual(by['b'].dependency_status,'DEPENDENCY_HOLD')
        self.assertEqual(by['h'].dependency_status,'INDEPENDENT_GATE_HOLD');self.assertIsNone(by['v'].state);self.assertFalse(r.dispatch_allowed)
    def test_full_failed_history_budget(self):
        self.f.chain();before=self.f.f.dump();r=self.review(anchors=(admission.BUDGET,));self.assertTrue(r.structural_match);self.assertTrue(r.budget_reconciled);self.assertEqual(r.event_count,5)
        by={t.task_id:t for t in r.tasks};self.assertEqual(by['a'].state,'FAILED');self.assertEqual(by['b'].dependency_status,'DEPENDENCY_HOLD');self.assertEqual(self.f.f.dump(),before)
    def test_renewal_budget_revision(self):
        f=self.f;running=f.ordinary(f.f.before,f.f.lease,RunState.RUNNING);f.life(f.f.renewal(running));r=self.review(anchors=(admission.BUDGET,));self.assertTrue(r.budget_reconciled);self.assertEqual(r.event_count,3)
    def test_open_admitted_pool(self):self.assertTrue(self.review(anchors=(admission.BUDGET,)).budget_reconciled)
    def test_missing_pin(self):self.hold(self.review(self.pins()[:-1]))
    def test_duplicate_pin(self):self.hold(self.review((*self.pins(),self.pins()[0])))
    def test_bad_revision(self):self.hold(self.review(revision='sha256:'+'0'*64))
    def test_changed_plan_label(self):
        p=copy.deepcopy(self.plan);p['tasks'][0]['label']='tampered';self.hold(self.review(plan=p))
    def test_pin_wrong_principal(self):
        p=list(self.pins());p[1]=replace(p[1],initial=replace(p[1].initial,scope=replace(p[1].initial.scope,principal_id='demo-other')));self.hold(self.review(tuple(p)))
    def test_forged_success(self):self.change("UPDATE run_heads SET state='SUCCEEDED' WHERE task_id='a'");self.hold(self.review())
    def test_forged_descendant(self):self.change("UPDATE run_heads SET state='RUNNING' WHERE task_id='b'");self.hold(self.review())
    def test_actual_descendant_claim_without_verified_predecessor(self):
        # Forge a bare successful head just long enough for legacy D0 claim.
        # Restore the root to its real pinned state; both histories now match
        # individually, but the plan-level causal order must reject the child.
        self.change("UPDATE run_heads SET state='SUCCEEDED' WHERE task_id='a'")
        spec=admission.spec_for('b',budget=replace(admission.BUDGET,revision=1,outstanding_minor=20))
        i=admission.intent_for(spec)
        self.f.f.f.claim(spec,i)
        self.change("UPDATE run_heads SET state='ADMITTED' WHERE task_id='a'")
        pins=list(self.pins());pins[1]=replace(pins[1],admission=AdmissionBinding(spec,i))
        self.hold(self.review(tuple(pins)))
    def test_missing_head(self):self.change("DELETE FROM run_heads WHERE task_id='q'");self.hold(self.review())
    def test_extra_human_head(self):
        self.change("INSERT INTO run_heads SELECT tenant_id,company_id,environment_id,plan_revision,'h','demo-h',agent_instance_id,principal_id,'QUEUED',0,0 FROM run_heads WHERE task_id='b'");self.hold(self.review())
    def test_unadmitted_event(self):
        self.change("INSERT INTO events SELECT tenant_id,company_id,environment_id,'demo-b',1,'bogus','D0_RUN_ADMISSION',request_digest FROM events WHERE run_id='demo-a'");self.hold(self.review())
    def test_unadmitted_pin_has_command(self):
        f=self.f;f.ordinary(f.f.before,f.f.lease,RunState.RUNNING);p=list(self.pins());p[1]=replace(p[1],commands=tuple(f.pins));self.hold(self.review(tuple(p)))
    def test_tampered_admitted_history_no_partial(self):
        self.f.chain();self.change("DELETE FROM run_audit WHERE version=3");self.hold(self.review())
    def test_tampered_budget_postimage(self):
        self.change('UPDATE sample_budgets SET outstanding_minor=19');self.assertTrue(self.review().structural_match);self.hold(self.review(anchors=(admission.BUDGET,)))
    def test_bad_budget_anchor(self):self.hold(self.review(anchors=(replace(admission.BUDGET,revision=1),)))
    def test_duplicate_budget_anchor(self):self.hold(self.review(anchors=(admission.BUDGET,admission.BUDGET)))
    def test_missing_pool_anchor(self):self.hold(self.review(anchors=()))
    def test_foreign_reservation(self):
        self.change("INSERT INTO sample_reservations SELECT tenant_id,company_id,environment_id,'demo-other',budget_id,budget_revision,amount_minor,currency,request_digest,transaction_ref FROM sample_reservations WHERE run_id='demo-a'")
        self.hold(self.review(anchors=(admission.BUDGET,)))
    def test_separate_read_transaction_consistency(self):
        with closing(sqlite3.connect(self.path)) as db: db.execute('PRAGMA journal_mode=WAL')
        with closing(sqlite3.connect(self.path)) as reader:
            reader.execute('PRAGMA query_only=ON');reader.execute('BEGIN');reader.execute('SELECT count(*) FROM run_heads').fetchone()
            self.change("UPDATE run_heads SET state='RUNNING' WHERE task_id='b'")
            with SQLiteCursorShim(reader) as c:r=inspect_plan_history(c,self.plan,self.revision,self.pins())
            self.assertTrue(r.structural_match);self.hold(self.review())

class ParallelRootTests(unittest.TestCase):
    def setUp(self):
        f=admission.ClaimTests();f.setUp();self.addCleanup(f.doCleanups);self.f=f
        self.plan=copy.deepcopy(PLAN);self.plan['tasks'][1]['depends_on']=[]
        self.revision=canonical_plan(self.plan)['revision'];self.path=f.path
        with closing(sqlite3.connect(self.path)) as db,db:
            db.executescript((admission.ROOT/'database/0196L/candidate_lease_settlement.sql').read_text().replace('t1_candidate.',''))
            db.execute('UPDATE run_heads SET plan_revision=?',(self.revision,))
        self.pins={t:RunHistoryPin(replace(obs(t),scope=replace(obs(t).scope,plan_revision=self.revision))) for t in 'abcq'}
    def claim(self,t,budget):
        s=admission.spec_for(t,budget=budget);r=self.pins[t].initial
        s=replace(s,before=r,lease=replace(s.lease,scope=r.scope),plan_digest=self.revision[7:]);i=admission.intent_for(s)
        LogicalT1Coordinator(lambda:postgres_transaction(lambda:SQLiteConnectionShim(self.path),D0PostgresAdmissionMapping(self.plan,s,lambda:admission.CLOCK))).commit(i)
        self.pins[t]=replace(self.pins[t],admission=AdmissionBinding(s,i))
    def review(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
            with SQLiteCursorShim(db) as c:return inspect_plan_history(c,self.plan,self.revision,tuple(self.pins.values()),exclusive_budget_anchors=(admission.BUDGET,))
    def test_all_queued(self):
        r=self.review();self.assertTrue(r.structural_match);self.assertTrue(r.budget_reconciled);self.assertEqual(r.event_count,0)
        self.assertEqual([t.task_id for t in r.tasks if t.dependency_status=='READY_OBSERVATION_ONLY'],['a','b'])
    def test_two_roots_shared_pool(self):
        self.claim('a',admission.BUDGET);self.claim('b',replace(admission.BUDGET,revision=1,outstanding_minor=20))
        r=self.review();self.assertTrue(r.structural_match);self.assertTrue(r.budget_reconciled);self.assertEqual(r.event_count,2)
        self.assertEqual([t.task_id for t in r.tasks if t.state=='ADMITTED'],['a','b'])
    def test_pin_order_independent(self):
        self.claim('b',admission.BUDGET);self.claim('a',replace(admission.BUDGET,revision=1,outstanding_minor=20));self.assertTrue(self.review().budget_reconciled)

if __name__=='__main__':unittest.main()
