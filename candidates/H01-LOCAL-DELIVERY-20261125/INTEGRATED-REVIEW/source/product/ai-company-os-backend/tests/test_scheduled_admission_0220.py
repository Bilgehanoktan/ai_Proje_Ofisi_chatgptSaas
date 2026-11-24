"""0220 existing SQL mapping + plan history + company admission, SQLite only."""
from contextlib import closing
from dataclasses import replace
import sqlite3
from unittest import TestCase
import test_admission_mapping_0195 as admission
import test_company_terminal_0212 as base
from test_transition_mapping_0194 import PLAN, obs, SQLiteConnectionShim
from app.core.event_store.plan_history_review import RunHistoryPin
from app.core.event_store.company_coordination import inspect_company
from app.core.transaction.postgres_admission_mapping import commit_scheduled_admission
from app.core.transaction.postgres_session import CommitOutcomeUnknown

class ScheduledAdmissionTests(TestCase):
    def setUp(self):
        f=base.CompanyTerminalTests(); f.setUp(); self.addCleanup(f.doCleanups); self.f=f
        self.pins=tuple(RunHistoryPin(obs(t)) for t in 'abcq')
    def invoke(self, **kw):
        f=self.f
        args=dict(connect=lambda:SQLiteConnectionShim(f.path),plan=PLAN,spec=f.initial,intent=f.admit,
                  clock=lambda:admission.CLOCK,members=f.members,pool=f.pool,history=f.history,history_pins=self.pins)
        args.update(kw)
        return commit_scheduled_admission(**args)
    def test_root_commit_same_transaction(self):
        f=self.f; r=self.invoke()
        f.history+=(f.event(f.admit,'D0_RUN_ADMISSION',0,20),)
        self.assertEqual(r.committed_version,1)
        self.assertTrue(f.company().structural_match)
    def test_wrong_membership_no_write(self):
        f=self.f; before=f.dump()
        members=tuple(replace(m,principal_id='demo-other') if m.task_id=='a' else m for m in f.members)
        with self.assertRaisesRegex(ValueError,'MEMBER_HOLD'):
            self.invoke(members=members)
        self.assertEqual(f.dump(),before)
    def test_forged_success_no_write(self):
        f=self.f
        with closing(sqlite3.connect(f.path)) as db,db:
            db.execute("UPDATE run_heads SET state='SUCCEEDED' WHERE task_id='a'")
        before=f.dump(); spec=admission.spec_for('b')
        with self.assertRaisesRegex(ValueError,'PREDECESSOR_PROOF'):
            self.invoke(spec=spec,intent=admission.intent_for(spec))
        self.assertEqual(f.dump(),before)
    def test_root_with_forged_other_head_no_write(self):
        f=self.f
        with closing(sqlite3.connect(f.path)) as db,db:
            db.execute("UPDATE run_heads SET state='SUCCEEDED' WHERE task_id='a'")
        before=f.dump()
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertEqual(f.dump(),before)
    def test_missing_pins_no_write(self):
        f=self.f; before=f.dump()
        with self.assertRaisesRegex(ValueError,'MEMBER_HOLD'):
            self.invoke(history_pins=self.pins[:-1])
        self.assertEqual(f.dump(),before)
    def test_unknown_no_automatic_retry(self):
        f=self.f
        with self.assertRaises(CommitOutcomeUnknown):
            self.invoke(connect=lambda:SQLiteConnectionShim(f.path,True))
        before=f.dump()
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertEqual(f.dump(),before)
