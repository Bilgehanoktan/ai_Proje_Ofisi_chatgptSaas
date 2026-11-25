"""Full prior D0 writer/reader SQLite fixture; emulates PG session setup, not PG evidence."""
from contextlib import closing
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase, main
import sqlite3
import test_plan_history_review_0199 as base
from test_transition_mapping_0194 import SQLiteCursorShim
from app.core.agent_runtime.lifecycle import RunState
from app.core.event_store.history_readback import LifecyclePin
from app.core.event_store.retained_history import ReferenceReader, ReferenceStore, history_reference, reference_bytes
from app.core.event_store.terminal_anchor import TerminalAnchorMapping, anchor_from_pin
from app.core.event_store.postgres_snapshot import _CONFIG, _CHECK, read_plan_snapshot
from app.core.event_store.signed_history import (Checkpoint, ExternalPin, TerminalClaim, checkpoint_bytes,
    terminal_bytes, review_signed_snapshot)
from app.core.transaction.postgres_session import CommitOutcomeUnknown
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT=Path(__file__).resolve().parents[3]

class SnapshotCursor(SQLiteCursorShim):
    """Emulate PostgreSQL context query/settings, execute all actual reader SQL on SQLite."""
    def execute(self,sql,params=()):
        self.context=None
        if sql==_CHECK:
            self.context=[('aicos_d0_0203_test','repeatable read','on',False,False)];return
        if sql==_CONFIG or sql in ("SET LOCAL statement_timeout='5s'","SET LOCAL lock_timeout='2s'"):
            return
        return super().execute(sql,params)
    def fetchone(self):
        if self.context is not None: return self.context.pop(0) if self.context else None
        return super().fetchone()

class SnapshotConnection:
    autocommit=False
    def __init__(self,path):
        self.info=SimpleNamespace(transaction_status=0)
        self.db=sqlite3.connect(path);self.db.execute('PRAGMA query_only=ON');self.db.execute('BEGIN')
    def cursor(self): return SnapshotCursor(self.db)
    def rollback(self): self.db.rollback()
    def close(self): self.db.close()

class AnchorLifecycleTests(TestCase):
    def setUp(self):
        f=base.PlanHistoryTests();f.setUp();self.addCleanup(f.doCleanups);self.f=f
        self.h=f.f;self.l=self.h.f;self.path=self.l.path
        with closing(sqlite3.connect(self.path)) as db,db:
            db.executescript((ROOT/'database/0203T/terminal_command_anchors.sql').read_text().replace('t1_candidate.',''))
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.store=ReferenceStore(Path(tmp.name)/'refs.db');self.reader=ReferenceReader(self.store.path)
        running=self.h.ordinary(self.l.before,self.l.lease,RunState.RUNNING)
        self.spec=self.l.failure(running);self.intent=self.l.intent(self.spec);self.cmd=LifecyclePin(self.intent,self.spec)
        self.anchor=anchor_from_pin(self.cmd);self.key=self.store.put(reference_bytes('terminal-command-v1',self.cmd))
        self.assertEqual(self.key,self.anchor.command_sha)
    def mapping(self,key=None):
        return TerminalAnchorMapping(self.spec,lambda:self.l.clock,self.reader,self.key if key is None else key)
    def execute(self,unknown=False):
        r=self.l.execute(self.spec,self.intent,mapping=self.mapping(),unknown=unknown)
        self.h.pins.append(self.cmd);return r
    def rows(self):
        with closing(sqlite3.connect(self.path)) as db: return tuple(db.execute('SELECT * FROM terminal_command_anchors').fetchall())
    def snapshot(self):
        return read_plan_snapshot(lambda:SnapshotConnection(self.path),self.f.plan,self.f.revision,self.f.pins(),require_terminal_anchors=True)
    def signed(self):
        pins=self.f.pins();rev=self.f.revision;plan=self.f.plan
        h=self.store.put(history_reference(plan,rev,pins));a=self.anchor
        c=Checkpoint('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',rev,h,'demo-iv','iv-key',1,2,3,4,10,20,
                     (TerminalClaim(a.run_id,a.command_sha,a.transaction_ref,'D0_LOCAL_FAILURE_NO_EFFECT'),))
        signer=Ed25519PrivateKey.generate();pub=signer.public_key().public_bytes_raw()
        pin=ExternalPin(sha256(checkpoint_bytes(c)).hexdigest(),sha256(pub).hexdigest(),c.issuer,c.key_id,1,2,3,4,rev,False,
                        tuple(sorted({p.initial.scope.principal_id for p in pins})))
        return review_signed_snapshot(self.reader,lambda:SnapshotConnection(self.path),plan,rev,pins,c,pin,pub,
                    signer.sign(checkpoint_bytes(c)),((a.run_id,signer.sign(terminal_bytes(c,c.terminal_claims[0]))),),15,
                    require_terminal_anchors=True)
    def test_actual_writer_and_signed_readback(self):
        receipt=self.execute();self.assertEqual(receipt.transaction_ref,self.anchor.transaction_ref)
        self.assertEqual(len(self.rows()),1);self.assertTrue(self.snapshot().structural_match)
        r=self.signed();self.assertTrue(r.atomic_anchor_match and r.signature_match);self.assertEqual(r.history.event_count,3)
        self.assertFalse(r.independent_verified or r.dispatch_allowed or r.release_ready or r.replay_allowed)
    def test_missing_archive_no_terminal(self):
        before=self.l.dump()
        with self.assertRaises(ValueError):self.l.execute(self.spec,self.intent,mapping=self.mapping('0'*64))
        self.assertEqual(self.l.dump(),before);self.assertEqual(self.rows(),())
    def test_anchor_failure_rolls_back_all_roles(self):
        before=self.l.dump()
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("CREATE TRIGGER reject_anchor BEFORE INSERT ON terminal_command_anchors BEGIN SELECT RAISE(ABORT,'injected'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.execute()
        self.assertEqual(self.l.dump(),before);self.assertEqual(self.rows(),())
    def test_unknown_commit_read_only(self):
        with self.assertRaises(CommitOutcomeUnknown):self.execute(unknown=True)
        self.h.pins.append(self.cmd)
        self.assertTrue(self.snapshot().structural_match);self.assertTrue(self.signed().atomic_anchor_match)
    def test_legacy_terminal_not_strict(self):
        self.h.life(self.spec);self.assertFalse(self.snapshot().structural_match);self.assertFalse(self.signed().signature_match)
    def test_anchor_tamper(self):
        self.execute()
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('UPDATE terminal_command_anchors SET command_sha=?',('f'*64,))
        self.assertFalse(self.snapshot().structural_match);self.assertFalse(self.signed().signature_match)
    def test_anchor_deleted(self):
        self.execute()
        with closing(sqlite3.connect(self.path)) as db,db:db.execute('DELETE FROM terminal_command_anchors')
        self.assertFalse(self.snapshot().structural_match);self.assertFalse(self.signed().signature_match)

if __name__=='__main__': main()
