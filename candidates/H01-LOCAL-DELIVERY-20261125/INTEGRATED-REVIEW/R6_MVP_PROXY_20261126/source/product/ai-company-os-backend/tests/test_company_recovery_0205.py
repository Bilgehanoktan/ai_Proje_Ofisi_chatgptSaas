"""Real SQLite backup/reopen, separate witness and readback. No PG or independent custody."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest import TestCase, main
from unittest.mock import patch
import test_company_coordination_0204 as base
from app.core.event_store.company_recovery import (CompanyCheckpoint,WitnessRecord,WitnessReader,D0WitnessStore,
    checkpoint,genesis,stage_pending,advance_recovery_epoch,witness_sha,review_recovery)

M,P,E=base.MEMBERS,base.POOL,base.EVENTS


class CheckpointTests(TestCase):
    def test_order_canonical_roster_and_caps(self):
        self.assertEqual(checkpoint(M,P,E),checkpoint(tuple(reversed(M)),replace(P,allocations=tuple(reversed(P.allocations))),E))
    def test_bind_project_cap(self):
        p=replace(P,allocations=(replace(P.allocations[0],cap_minor=39),P.allocations[1]))
        self.assertNotEqual(checkpoint(M,P,E),checkpoint(M,p,E))
    def test_bind_principal(self):
        self.assertNotEqual(checkpoint(M,P,E),checkpoint((replace(M[0],principal_id='demo-new'),M[1]),P,E))
    def test_bind_event_predecessor(self):
        self.assertNotEqual(checkpoint(M,P,E),checkpoint(M,P,E[:1]+(replace(E[1],predecessors=()),)+E[2:]))
    def test_bind_epoch_currency_and_source(self):
        for p in (replace(P,witness_epoch=4),replace(P,policy_epoch=4),replace(P,currency='EUR'),replace(P,source_digest='d'*64)):
            self.assertNotEqual(checkpoint(M,P,E),checkpoint(M,p,E))
    def test_invalid_history(self):
        with self.assertRaises(ValueError): checkpoint(M,P,(E[1],))
    def test_checkpoint_postimage(self):
        c=checkpoint(M,P,E);self.assertEqual((c.sequence,c.pool_revision),(5,4));self.assertEqual(len(c.digest),64)
    def test_stage_exact_base(self):
        w=genesis(checkpoint(M,P,()))
        with self.assertRaises(ValueError): stage_pending(w,M,P,E[:1],E[1])
    def test_stage_invalid_target(self):
        w=genesis(checkpoint(M,P,()))
        with self.assertRaises(ValueError): stage_pending(w,M,P,(),replace(E[0],amount_minor=41))
    def test_stage_one_event(self):
        w=genesis(checkpoint(M,P,E[:2]));n=stage_pending(w,M,P,E[:2],E[2])
        self.assertEqual(n.pending_sha,checkpoint(M,P,E[:3]).digest);self.assertEqual(n.pending_pool_revision,w.pool_revision)
    def test_genesis_bad_fields(self):
        for cp in (CompanyCheckpoint('x',0,0),CompanyCheckpoint('a'*64,True,0),CompanyCheckpoint('a'*64,0,-1),CompanyCheckpoint('a'*64,5001,0)):
            with self.assertRaises(ValueError):genesis(cp)
    def test_pending_blocks_epoch_and_second_stage(self):
        w=stage_pending(genesis(checkpoint(M,P,())),M,P,(),E[0])
        with self.assertRaises(ValueError):advance_recovery_epoch(w)
        with self.assertRaises(ValueError):stage_pending(w,M,P,(),E[0])


class WitnessTests(TestCase):
    def setUp(self):
        t=TemporaryDirectory();self.addCleanup(t.cleanup);self.path=Path(t.name)/'witness.sqlite'
        self.store=D0WitnessStore(self.path);self.reader=WitnessReader(self.path)
        self.w=genesis(checkpoint(M,P,()));self.key=self.store.append(self.w,None)
    def test_reopen(self):self.assertEqual(self.reader.read_latest(self.key),self.w)
    def test_old_pin(self):
        n=advance_recovery_epoch(self.w);key=self.store.append(n,self.key)
        self.assertEqual(self.reader.read_latest(key),n)
        with self.assertRaises(ValueError):self.reader.read_latest(self.key)
    def test_cas(self):
        n=advance_recovery_epoch(self.w)
        with self.assertRaises(ValueError):self.store.append(n,'f'*64)
        self.assertEqual(self.reader.read_latest(self.key),self.w)
    def test_epoch_skip(self):
        n=replace(advance_recovery_epoch(self.w),recovery_epoch=3)
        with self.assertRaises(ValueError):self.store.append(n,self.key)
    def test_wrong_previous_sha(self):
        n=replace(advance_recovery_epoch(self.w),previous_sha='f'*64)
        with self.assertRaises(ValueError):self.store.append(n,self.key)
    def test_sequence_rollback_or_skip(self):
        n=advance_recovery_epoch(self.w)
        with self.assertRaises(ValueError):self.store.append(replace(n,sequence=1),self.key)
    def test_pending_cannot_clear(self):
        n=stage_pending(self.w,M,P,(),E[0]);key=self.store.append(n,self.key)
        clear=WitnessRecord(3,1,n.checkpoint_sha,n.sequence,n.pool_revision,key)
        with self.assertRaises(ValueError):self.store.append(clear,key)
        self.assertEqual(self.reader.read_latest(key),n)
    def test_even_exact_target_not_publishable(self):
        n=stage_pending(self.w,M,P,(),E[0]);key=self.store.append(n,self.key)
        target=WitnessRecord(3,1,n.pending_sha,1,n.pending_pool_revision,key)
        with self.assertRaises(ValueError):self.store.append(target,key)
    def test_append_only(self):
        for sql in ('UPDATE recovery_witness SET digest=digest','DELETE FROM recovery_witness','INSERT OR REPLACE INTO recovery_witness SELECT * FROM recovery_witness'):
            with self.assertRaises(sqlite3.IntegrityError),closing(sqlite3.connect(self.path)) as db,db:db.execute(sql)
    def test_privileged_tamper(self):
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('DROP TRIGGER witness_no_update');db.execute('UPDATE recovery_witness SET body=?',(b'[]',))
        with self.assertRaises(ValueError):self.reader.read_latest(self.key)
    def test_concurrent_cas(self):
        n=advance_recovery_epoch(self.w);barrier=Barrier(2,timeout=3)
        def compete(_):
            barrier.wait()
            try:self.store.append(n,self.key);return 'OK'
            except ValueError:return 'HOLD'
        with ThreadPoolExecutor(max_workers=2) as p:self.assertCountEqual(list(p.map(compete,range(2))),['OK','HOLD'])
    def test_oversized_witness_body(self):
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('DROP TRIGGER witness_no_update');db.execute('UPDATE recovery_witness SET body=?',(b'x'*4097,))
        with self.assertRaises(ValueError):self.reader.read_latest(self.key)
    def test_missing_store_does_not_create(self):
        other=self.path.with_name('missing.sqlite')
        with self.assertRaises(sqlite3.Error):WitnessReader(other).read_latest(self.key)
        self.assertFalse(other.exists())


class RecoveryTests(TestCase):
    def setUp(self):
        f=base.CompanySQLTests();f.setUp();self.addCleanup(f.doCleanups);self.f=f
        t=TemporaryDirectory();self.addCleanup(t.cleanup);self.dir=Path(t.name)
        self.store=D0WitnessStore(self.dir/'external.sqlite');self.reader=WitnessReader(self.store.path)
    def initialize(self,events=(),epoch=1):
        self.w=genesis(checkpoint(M,P,events),epoch);self.key=self.store.append(self.w,None)
    def stage(self,history,event):
        self.w=stage_pending(self.w,M,P,history,event);self.key=self.store.append(self.w,self.key)
    def read(self,events=(),path=None,reader=None,key=None,members=M,pool=P):
        with closing(sqlite3.connect(self.f.path if path is None else path)) as db:
            db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
            return review_recovery(base.Cursor(db),members,pool,events,self.reader if reader is None else reader,self.key if key is None else key)
    def flags(self,r):
        self.assertEqual((r.mode,r.decision),('RECOVERY_READ_ONLY','HOLD'))
        self.assertFalse(r.independent_verified or r.dispatch_allowed or r.spend_allowed or r.replay_allowed or r.retry_allowed or r.publish_allowed)
    def hold(self,r):
        self.flags(r);self.assertFalse(r.checkpoint_match or r.pending_target_match);self.assertIsNone(r.recovery_epoch)
    def backup(self,src,dst):
        with closing(sqlite3.connect(src)) as a,closing(sqlite3.connect(dst)) as b:a.backup(b)
    def test_latest_checkpoint_read_only(self):
        self.f.full();self.initialize(E);before=self.f.dump();r=self.read(E)
        self.flags(r);self.assertTrue(r.checkpoint_match);self.assertEqual(self.f.dump(),before)
    def test_old_company_backup_rejected(self):
        old=self.dir/'old.sqlite';self.backup(self.f.path,old)
        self.f.full();self.initialize(E);self.hold(self.read((),path=old))
    def test_both_backups_rolled_back_external_pin_rejects(self):
        self.initialize();oldw=self.dir/'old-witness.sqlite';oldc=self.dir/'old-company.sqlite'
        self.backup(self.store.path,oldw);self.backup(self.f.path,oldc)
        self.stage((),E[0]);self.f.guarded_write((),E[0]);self.hold(self.read((),path=oldc,reader=WitnessReader(oldw)))
    def test_stale_external_pin_rejected(self):
        self.initialize();old=self.key;self.stage((),E[0]);self.hold(self.read(key=old))
    def test_pending_before_commit(self):
        self.initialize();self.stage((),E[0]);r=self.read();self.flags(r)
        self.assertEqual(r.reason,'D0_RECOVERY_UNKNOWN_ABSENCE_NOT_PROOF');self.assertTrue(r.checkpoint_match);self.assertFalse(r.pending_target_match)
    def test_pending_after_commit(self):
        self.initialize();self.stage((),E[0]);self.f.guarded_write((),E[0]);r=self.read((E[0],))
        self.flags(r);self.assertEqual(r.reason,'D0_RECOVERY_UNKNOWN_COMMIT_MATCH_ONLY');self.assertTrue(r.pending_target_match)
    def test_lost_commit_response(self):
        self.initialize();self.stage((),E[0])
        def commit_then_lose_response():
            self.f.guarded_write((),E[0]);raise OSError('response lost after SQLite commit')
        with self.assertRaises(OSError):commit_then_lose_response()
        r=self.read((E[0],));self.flags(r);self.assertTrue(r.pending_target_match)
    def test_rolled_back_write_remains_quarantined(self):
        self.initialize();self.stage((),E[0])
        with self.assertRaises(ValueError):self.f.guarded_write((),E[0],wrong_post=True)
        r=self.read();self.flags(r);self.assertEqual(r.reason,'D0_RECOVERY_UNKNOWN_ABSENCE_NOT_PROOF')
    def test_unstaged_commit_rejected(self):
        self.initialize();self.f.guarded_write((),E[0]);self.hold(self.read((E[0],)))
    def test_different_commit_rejected(self):
        self.initialize();self.stage((),E[0]);other=replace(E[0],amount_minor=19)
        self.f.guarded_write((),other);self.hold(self.read((other,)))
    def test_pending_extra_commit_rejected(self):
        self.initialize();self.stage((),E[0]);self.f.guarded_write((),E[0]);self.f.guarded_write(E[:1],E[1]);self.hold(self.read(E[:2]))
    def test_wrong_pool_readback(self):
        self.f.full();self.initialize(E);self.f.change('UPDATE sample_budgets SET outstanding_minor=31');self.hold(self.read(E))
    def test_unknown_cost(self):
        self.f.full();self.initialize(E);self.f.change('UPDATE sample_budgets SET unknown_cost=1');self.hold(self.read(E))
    def test_tampered_membership(self):
        self.initialize();self.f.change("UPDATE company_run_membership SET principal_id='demo-other' WHERE run_id='demo-a'");self.hold(self.read())
    def test_tampered_caps_even_if_db_unchanged(self):
        self.initialize();p=replace(P,allocations=(replace(P.allocations[0],cap_minor=39),P.allocations[1]));self.hold(self.read(pool=p))
    def test_witness_advance_during_readback(self):
        self.initialize();original=base.inspect_company
        def change(*args):
            self.store.append(advance_recovery_epoch(self.w),self.key);return original(*args)
        with patch('app.core.event_store.company_recovery.inspect_company',side_effect=change):self.hold(self.read())
    def test_restore_epoch_does_not_change_pool_epoch(self):
        self.initialize();n=advance_recovery_epoch(self.w);self.key=self.store.append(n,self.key)
        r=self.read();self.flags(r);self.assertTrue(r.checkpoint_match);self.assertEqual(r.recovery_epoch,2)
        self.assertNotEqual(n.recovery_epoch,P.witness_epoch)
    def test_corrupt_witness_holds(self):
        self.initialize()
        with closing(sqlite3.connect(self.store.path)) as db,db:
            db.execute('DROP TRIGGER witness_no_update');db.execute('UPDATE recovery_witness SET body=?',(b'bad',))
        self.hold(self.read())

if __name__=='__main__':main()
