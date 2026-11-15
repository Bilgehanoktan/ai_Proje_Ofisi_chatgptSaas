"""Real disposable SQLite SQL anchor tests; existing writer integration is separate."""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch
import sqlite3
from app.core.event_store.terminal_anchor import TerminalAnchor, write_anchor, verify_anchor
from app.core.event_store.signed_history import review_signed_snapshot
from app.core.event_store.retained_history import RetainedReview
import test_signed_history_0202 as signed

ROOT=Path(__file__).resolve().parents[3]
SCOPE=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
A=TerminalAnchor('sha256:'+'a'*64,'demo-run',3,'d0-tx-'+'b'*64,'c'*64,'d'*64)
FAILURE='D0_LOCAL_FAILURE_NO_EFFECT'

class Cursor:
    def __init__(self,db): self.c=db.cursor()
    def execute(self,sql,args=()): return self.c.execute(sql.replace('t1_candidate.','').replace('%s','?'),args)
    def fetchone(self): return self.c.fetchone()


class AnchorSQLTests(TestCase):
    def setUp(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);self.path=Path(tmp.name)/'test.sqlite'
        with closing(self.connect()) as db,db:
            db.executescript('''
            CREATE TABLE run_heads(tenant_id text,company_id text,environment_id text,run_id text,plan_revision text,state text,version int,PRIMARY KEY(tenant_id,company_id,environment_id,run_id));
            CREATE TABLE run_mutations(tenant_id text,company_id text,environment_id text,run_id text,version int,transaction_ref text,request_digest text,after_state text,PRIMARY KEY(tenant_id,company_id,environment_id,run_id,version));
            CREATE TABLE sample_settlements(tenant_id text,company_id text,environment_id text,run_id text,version int,transaction_ref text,request_digest text,outcome text,PRIMARY KEY(tenant_id,company_id,environment_id,run_id));
            ''')
            db.executescript((ROOT/'database/0203T/terminal_command_anchors.sql').read_text().replace('t1_candidate.',''))
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?)',(*SCOPE,A.run_id,A.plan_revision,'RUNNING',2))
    def connect(self):
        db=sqlite3.connect(self.path);db.execute('PRAGMA foreign_keys=ON');return db
    def terminal(self,db):
        db.execute('UPDATE run_heads SET state=?,version=? WHERE run_id=?',('FAILED',A.version,A.run_id))
        db.execute('INSERT INTO run_mutations VALUES (?,?,?,?,?,?,?,?)',(*SCOPE,A.run_id,A.version,A.transaction_ref,A.request_digest,'FAILED'))
        db.execute('INSERT INTO sample_settlements VALUES (?,?,?,?,?,?,?,?)',(*SCOPE,A.run_id,A.version,A.transaction_ref,A.request_digest,FAILURE))
    def dump(self):
        with closing(self.connect()) as db: return tuple(tuple(db.execute('SELECT * FROM '+t).fetchall()) for t in ('run_heads','run_mutations','sample_settlements','terminal_command_anchors'))
    def committed(self):
        with closing(self.connect()) as db,db: self.terminal(db);write_anchor(Cursor(db),A)
    def test_commit_and_reopen(self):
        self.committed()
        with closing(self.connect()) as db: verify_anchor(Cursor(db),A)
        self.assertEqual(len(self.dump()[-1]),1)
    def test_rollback_after_anchor(self):
        initial=self.dump()
        with self.assertRaises(RuntimeError),closing(self.connect()) as db,db:
            self.terminal(db);write_anchor(Cursor(db),A);raise RuntimeError('fault before commit')
        self.assertEqual(self.dump(),initial)
    def test_anchor_insert_failure_rolls_back_terminal(self):
        initial=self.dump()
        with self.assertRaises(sqlite3.IntegrityError),closing(self.connect()) as db,db:
            db.execute("CREATE TRIGGER reject_anchor BEFORE INSERT ON terminal_command_anchors BEGIN SELECT RAISE(ABORT,'injected'); END")
            self.terminal(db);write_anchor(Cursor(db),A)
        self.assertEqual(self.dump(),initial)
    def test_missing_terminal_rows(self):
        with self.assertRaisesRegex(ValueError,'ROW_HOLD'),closing(self.connect()) as db,db: write_anchor(Cursor(db),A)
    def test_wrong_tx_rolls_back(self):
        initial=self.dump()
        with self.assertRaises(ValueError),closing(self.connect()) as db,db:
            self.terminal(db);write_anchor(Cursor(db),replace(A,transaction_ref='d0-tx-'+'f'*64))
        self.assertEqual(self.dump(),initial)
    def test_wrong_plan_rolls_back(self):
        initial=self.dump()
        with self.assertRaises(ValueError),closing(self.connect()) as db,db:
            self.terminal(db);write_anchor(Cursor(db),replace(A,plan_revision='sha256:'+'f'*64))
        self.assertEqual(self.dump(),initial)
    def test_duplicate_rejected(self):
        self.committed();initial=self.dump()
        with self.assertRaises(sqlite3.IntegrityError),closing(self.connect()) as db,db:write_anchor(Cursor(db),A)
        self.assertEqual(self.dump(),initial)
    def test_changed_command_hash_rejected(self):
        self.committed()
        with closing(self.connect()) as db,self.assertRaises(ValueError):verify_anchor(Cursor(db),replace(A,command_sha='f'*64))
    def test_changed_settlement_rejected(self):
        self.committed()
        with closing(self.connect()) as db,db:db.execute("UPDATE sample_settlements SET outcome='SUCCEEDED'")
        with closing(self.connect()) as db,self.assertRaises(ValueError):verify_anchor(Cursor(db),A)
    def test_deleted_anchor_rejected(self):
        self.committed()
        with closing(self.connect()) as db,db:db.execute('DELETE FROM terminal_command_anchors')
        with closing(self.connect()) as db,self.assertRaises(ValueError):verify_anchor(Cursor(db),A)
    def test_foreign_key_rolls_back(self):
        initial=self.dump()
        with self.assertRaises(sqlite3.IntegrityError),closing(self.connect()) as db,db:
            db.execute('INSERT INTO terminal_command_anchors VALUES (?,?,?,?,?,?,?,?,?)',(*SCOPE,*A.row()))
        self.assertEqual(self.dump(),initial)
    def test_readback_does_not_mutate(self):
        self.committed();initial=self.dump()
        with closing(self.connect()) as db:
            db.execute('PRAGMA query_only=ON');db.execute('BEGIN');verify_anchor(Cursor(db),A);db.rollback()
        self.assertEqual(self.dump(),initial)


class StrictSignedTests(TestCase):
    def setUp(self):
        self.f=signed.SignatureTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
    def test_strict_requires_anchor(self):
        result=RetainedReview('D0',object(),(('demo-run','a'*64,'d0-tx-'+'2'*64),),True)
        with patch('app.core.event_store.signed_history.review_retained_snapshot',return_value=result) as p:
            r=self.f.snapshot(require_terminal_anchors=True);self.f.hold(r);self.assertIs(p.call_args.kwargs['require_terminal_anchors'],True)
    def test_strict_anchored_match_is_not_authority(self):
        result=RetainedReview('D0',object(),(('demo-run','a'*64,'d0-tx-'+'2'*64),),True,True)
        with patch('app.core.event_store.signed_history.review_retained_snapshot',return_value=result):
            r=self.f.snapshot(require_terminal_anchors=True)
            self.assertTrue(r.atomic_anchor_match and r.signature_match)
            self.assertEqual(r.decision,'HOLD');self.assertFalse(r.independent_verified or r.dispatch_allowed or r.release_ready or r.replay_allowed)
    def test_nonboolean_mode_denied(self):
        with patch('app.core.event_store.signed_history.review_retained_snapshot') as p:
            self.f.hold(self.f.snapshot(require_terminal_anchors=1));p.assert_not_called()

if __name__=='__main__': main()
