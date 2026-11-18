"""Composition tests only; use original D5-E/F and 0204-C SQLite fixtures."""
from contextlib import closing
from dataclasses import FrozenInstanceError, replace
import hashlib
from pathlib import Path
import shutil
import sqlite3
import sys
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BACKEND=ROOT/'product/ai-company-os-backend'
PINS={
    'product/ai-company-os-backend/app/core/event_store/company_recovery.py':'aaefcebc02c02546a66cd2a32e52f00981b7bcd0',
    'product/ai-company-os-backend/app/core/event_store/company_coordination.py':'fb068ef9bececca21e6b0562b12ac41aa3d4fcc5',
    'product/ai-company-os-backend/app/core/event_store/ledger.py':'e3f94cab61a27c7d4c89d02516887146b2026eb3',
    'product/ai-company-os-backend/app/__init__.py':'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
    'product/ai-company-os-backend/app/core/__init__.py':'9d457472970b7f581687ba142d1bf99ba91c7388',
    'product/ai-company-os-backend/app/core/event_store/__init__.py':'c4c3c4dd20cc9a7e1e76fc80c231f223467fdd78',
    'product/ai-company-os-backend/tests/test_company_coordination_0204.py':'ce4f8fb249787c9e18a03a63225dbcddf7445650',
    'database/0204C/company_event_order.sql':'edb2ef263204b89f88f172000ecb031428a027e4',
    'candidates/D5-F/test_recovery_boundary.py':'5a830423a3c009752fd8644e2aafa330a7bc2f58',
    'candidates/D5-E/derive_fixture.py':'118db973fe9378994496f8ba7fdf081b8f49f31a',
    'candidates/D5-E/intent_authority.original.py':'fa47acd32adb309896f762ec50e47bf26641adbb',
    'candidates/D5-E/test_publication_protocol.py':'670c50f5007884620920d701d43337581642af32',
}
for path,pin in PINS.items():
    raw=(ROOT/path).read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=pin:
        raise ValueError('D5FR1_SOURCE_PIN_HOLD: '+path)
sys.path[:0]=[str(BACKEND),str(BACKEND/'tests'),str(HERE.parent/'D5-F')]
import test_recovery_boundary as boundary
import test_company_coordination_0204 as base
from app.core.event_store.company_recovery import (D0WitnessStore,WitnessReader,checkpoint,
    genesis,advance_recovery_epoch,witness_sha,stage_pending)
from recovery_adapter import review_publication_recovery, PublicationRecoveryReview

p=boundary.p


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.pub=boundary.RecoveryTests();self.pub.setUp();self.addCleanup(self.pub.doCleanups)
        self.company=base.CompanySQLTests();self.company.setUp();self.addCleanup(self.company.doCleanups)
        self.company.full()
        self.store=D0WitnessStore(self.pub.path/'witness.sqlite')
        self.reader=WitnessReader(self.store.path)
        self.w=genesis(checkpoint(base.MEMBERS,base.POOL,base.EVENTS),epoch=7)
        self.wsha=self.store.append(self.w,None)
        self.old_witness=self.pub.path/'witness-old.sqlite'
        with closing(sqlite3.connect(self.store.path)) as src,closing(sqlite3.connect(self.old_witness)) as dst:src.backup(dst)
        self.old_company=self.pub.path/'company-old.sqlite'
        with closing(self.company.connect()) as src,closing(sqlite3.connect(self.old_company)) as dst:src.backup(dst)

    def review(self,pin=p.OLD,**changes):
        before=self.company.dump()
        with closing(sqlite3.connect(self.company.path.as_uri()+'?mode=ro',uri=True)) as db:
            db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
            args=dict(authority=self.pub.a,owner_path=self.pub.owner_file,company_cursor=base.Cursor(db),
                members=base.MEMBERS,pool=base.POOL,events=base.EVENTS,witness_reader=self.reader,
                expected_witness_sha=self.wsha,expected_company_epoch=self.w.recovery_epoch,
                expected_root=p.ROOT,expected_publication=pin,expected_scope=base.SCOPE)
            args.update(changes)
            result=review_publication_recovery(**args)
        self.assertEqual(self.company.dump(),before)
        self.assertIs(type(result),PublicationRecoveryReview)
        self.assertEqual((result.mode,result.decision),('RECOVERY_READ_ONLY','HOLD'))
        for name in ('independent_verified','dispatch_allowed','spend_allowed','replay_allowed','retry_allowed','publish_allowed','finalize_allowed'):
            self.assertIs(getattr(result,name),False)
        return result

    def reason(self,reason,pin=p.OLD,**kw):
        result=self.review(pin,**kw);self.assertEqual(result.reason,reason);return result

    def bump(self):
        self.w=advance_recovery_epoch(self.w);self.wsha=self.store.append(self.w,self.wsha)

    def interrupted(self,after):
        def apply():
            if after:p.mutate(self.pub.path)
            raise OSError('injected connection loss')
        with self.assertRaises(OSError):self.pub.publish(apply)

    def test_A01_before_external_mutation(self):
        self.interrupted(False)
        self.reason('D5FR1_PENDING_BASE_ABSENCE_NOT_PROOF',p.NEW)
        self.pub.assert_pending()

    def test_A02_after_external_mutation(self):
        self.interrupted(True)
        self.reason('D5FR1_PENDING_TARGET_MATCH_ONLY',p.NEW)
        self.pub.assert_pending()

    def test_A03_before_finalization_commit(self):
        self.pub.inject_final_commit(after=False)
        self.reason('D5FR1_PENDING_TARGET_MATCH_ONLY',p.NEW)
        self.pub.assert_pending()

    def test_A04_after_finalization_ack_loss(self):
        self.pub.inject_final_commit(after=True)
        self.reason('D5FR1_PUBLICATION_PIN_HOLD')
        self.assertTrue(self.reason('D5FR1_LOCAL_MATCH_ONLY',p.NEW).local_match)
        self.assertEqual(self.pub.claim_count(),0)

    def test_A05_replayed_publication_reference(self):
        self.pub.publish()
        self.reason('D5FR1_PUBLICATION_PIN_HOLD')
        with self.assertRaisesRegex(ValueError,'D5E_PUBLICATION_STALE_HOLD'):self.pub.publish()

    def test_A06_authority_restore(self):
        self.pub.publish();self.pub.restore(self.pub.root_file)
        self.reason('D5FR1_PUBLICATION_PIN_HOLD',p.NEW)
        self.reason('D5FR1_OWNER_READBACK_HOLD')

    def test_A07_owner_restore(self):
        self.pub.publish();self.pub.restore(self.pub.owner_file)
        self.reason('D5FR1_OWNER_READBACK_HOLD',p.NEW)

    def test_A08_witness_restore(self):
        self.bump();shutil.copyfile(self.old_witness,self.store.path)
        self.reason('D5FR1_COMPANY_PIN_HOLD')

    def test_A09_full_restore_residual_no_authorization(self):
        old=self.wsha;epoch=self.w.recovery_epoch
        with self.pub.claim():pass
        self.pub.publish();self.bump()
        self.company.guarded_write(base.EVENTS,base.E6)
        self.pub.restore(self.pub.root_file,self.pub.owner_file)
        shutil.copyfile(self.old_witness,self.store.path);shutil.copyfile(self.old_company,self.company.path)
        self.reason('D5FR1_COMPANY_PIN_HOLD',p.NEW)
        # Deliberate residual: all old pins + local files match. Match never grants.
        self.assertTrue(self.reason('D5FR1_LOCAL_MATCH_ONLY',expected_witness_sha=old,expected_company_epoch=epoch).local_match)
        self.assertEqual(self.pub.claim_count(),0)

    def test_A10_missing_independent_reference(self):
        self.reason('D5FR1_COMPANY_PIN_HOLD',expected_witness_sha=None)
        self.reason('D5FR1_EXTERNAL_OR_READBACK_HOLD',witness_reader=WitnessReader(self.pub.path/'missing.sqlite'))

    def test_A11_wrong_scope_epoch_and_root(self):
        self.reason('D5FR1_INPUT_HOLD',expected_scope=('other',*base.SCOPE[1:]))
        self.reason('D5FR1_COMPANY_PIN_HOLD',expected_company_epoch=8)
        self.reason('D5FR1_ROOT_PIN_HOLD',expected_root=replace(p.ROOT,recovery_epoch=2))
        # Epoch 7 and root epoch 1 are distinct and not equated.
        self.assertTrue(self.reason('D5FR1_LOCAL_MATCH_ONLY').local_match)

    def test_A12_concurrent_claim_is_not_recovered(self):
        with self.pub.claim():
            self.assertTrue(self.reason('D5FR1_LOCAL_MATCH_ONLY').local_match)
            self.assertEqual(self.pub.claim_count(),1)
        self.pub.assert_hold('D0_AUTHORITY_ALREADY_CLAIMED_HOLD')

    def test_A13_no_unauthorized_finalization_or_pending_clear(self):
        self.interrupted(True)
        paths=(self.pub.root_file,self.pub.owner_file,self.store.path,self.company.path)
        before=[hashlib.sha256(x.read_bytes()).hexdigest() for x in paths]
        self.reason('D5FR1_PENDING_TARGET_MATCH_ONLY',p.NEW)
        self.assertEqual([hashlib.sha256(x.read_bytes()).hexdigest() for x in paths],before)
        self.pub.assert_pending()
        # Company pending is also not publication permission.
        w=stage_pending(self.w,base.MEMBERS,base.POOL,base.EVENTS,base.E6)
        self.wsha=self.store.append(w,self.wsha);self.w=w
        self.assertEqual(self.review(p.NEW).company_reason,'D0_RECOVERY_UNKNOWN_ABSENCE_NOT_PROOF')

    def test_A14_read_only_even_on_match_and_drift(self):
        result=self.reason('D5FR1_LOCAL_MATCH_ONLY')
        with self.assertRaises(FrozenInstanceError):result.dispatch_allowed=True
        original=self.reader.read_latest;calls=0
        def change(sha):
            nonlocal calls
            calls+=1
            r=original(sha)
            if calls==1:p.mutate(self.pub.path)
            return r
        with patch.object(self.reader,'read_latest',side_effect=change):
            self.reason('D5FR1_OBSERVATION_DRIFT_HOLD')
        self.assertEqual(self.pub.claim_count(),0)


if __name__=='__main__':unittest.main(verbosity=2)
