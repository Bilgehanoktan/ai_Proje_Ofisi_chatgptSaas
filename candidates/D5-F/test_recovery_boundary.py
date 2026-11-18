"""Test existing D5-E unchanged. Two residuals are reproduced, not repaired."""
import contextlib
import hashlib
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

# Parent is supplied by the exact sibling candidate checkout, not repinned.
parent = Path(__file__).resolve().parent.parent / 'D5-E'
pins = {'derive_fixture.py':'118db973fe9378994496f8ba7fdf081b8f49f31a',
        'intent_authority.original.py':'fa47acd32adb309896f762ec50e47bf26641adbb',
        'test_publication_protocol.py':'670c50f5007884620920d701d43337581642af32'}
for name,pin in pins.items():
    raw=(parent/name).read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=pin:
        raise ValueError('D5F_PARENT_PIN_HOLD: '+name)
sys.path.insert(0,str(parent))
import test_publication_protocol as p


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        p.PublicationTests.setUp(self)
        self.root_file=self.path/'test.authority.sqlite'
        self.owner_file=self.path/'owner.sqlite'
        self.backup=self.path/'backup'
        self.backup.mkdir()
        for file in (self.root_file,self.owner_file):
            with contextlib.closing(sqlite3.connect(file)) as src, contextlib.closing(sqlite3.connect(self.backup/file.name)) as dst:
                src.backup(dst)

    def read(self): return p.read_owner(self.path)
    def state(self): return p.PublicationTests.state(self)
    def claim_count(self): return p.PublicationTests.claim_count(self)
    def claim(self,pin=p.OLD,suffix='a'): return p.PublicationTests.claim(self,pin,suffix)
    def publish(self,apply=None,expected=p.OLD,sha=p.NEW.owner_sha): return p.PublicationTests.publish(self,apply,expected,sha)
    def assert_hold(self,reason,pin=p.OLD,suffix='a'): return p.PublicationTests.assert_hold(self,reason,pin,suffix)
    def assert_pending(self): return p.PublicationTests.assert_pending(self)

    def restore(self,*files):
        # No live connections; restore only disposable fixture files.
        for file in files: shutil.copyfile(self.backup/file.name,file)
        self.a=p.authority(self.path)

    def inject_final_commit(self,after):
        real=self.a._db
        class Connection:
            def __init__(self,db): self.db=db; self.commits=0
            def __getattr__(self,name): return getattr(self.db,name)
            def execute(self,sql,*args):
                if sql=='COMMIT':
                    self.commits+=1
                    if self.commits==2:
                        if after: self.db.execute(sql,*args)
                        raise OSError('D5F_INJECTED_FINAL_ACK')
                return self.db.execute(sql,*args)
        with patch.object(self.a,'_db',side_effect=lambda:Connection(real())):
            with self.assertRaisesRegex(OSError,'D5F_INJECTED_FINAL_ACK'):
                self.publish()
        self.a=p.authority(self.path)

    def test_F01_finalization_ack_lost_after_actual_commit(self):
        self.inject_final_commit(after=True)
        self.assertEqual(self.state(),(p.NEW,False))
        self.assertEqual(self.read(),p.NEW.owner_sha)
        self.assert_hold('D5E_PUBLICATION_STALE_HOLD')
        with self.assertRaisesRegex(ValueError,'D5E_PUBLICATION_STALE_HOLD'):
            self.publish(apply=lambda:self.fail('reapplied old publication'))
        self.assertEqual(self.claim_count(),0)

    def test_F02_finalization_failed_before_commit_pending(self):
        self.inject_final_commit(after=False)
        self.assertEqual(self.read(),p.NEW.owner_sha)
        self.assert_pending()

    def test_F03_authority_only_restore(self):
        self.publish()
        self.restore(self.root_file)
        self.assert_hold('D5E_PUBLICATION_STALE_HOLD',p.NEW)
        self.assert_hold('D5E_OWNER_READBACK_HOLD',p.OLD)
        self.assertEqual(self.claim_count(),0)

    def test_F04_owner_only_restore(self):
        self.publish()
        self.restore(self.owner_file)
        self.assert_hold('D5E_OWNER_READBACK_HOLD',p.NEW)
        self.assert_hold('D5E_PUBLICATION_STALE_HOLD',p.OLD)
        self.assertEqual(self.claim_count(),0)

    def test_F05_both_restored_retained_latest_pin_rejects(self):
        retained=self.publish()
        with self.claim(retained): pass
        self.restore(self.root_file,self.owner_file)
        self.assert_hold('D5E_PUBLICATION_STALE_HOLD',retained)
        self.assertEqual(self.claim_count(),0)

    def test_F06_RESIDUAL_full_restore_and_stale_pin_reopens_scope(self):
        with self.claim(): pass
        self.assertEqual(self.claim_count(),1)
        self.publish()
        self.restore(self.root_file,self.owner_file)
        # Counterexample: no independent custody is available; old pin also restored.
        with self.claim(): pass
        self.assertEqual(self.claim_count(),1)

    def test_F07_RESIDUAL_external_bypass_while_fence_held(self):
        with self.claim():
            p.mutate(self.path)
            self.assertEqual(self.read(),p.NEW.owner_sha)
            self.assertEqual(self.state(),(p.OLD,False))
        self.assert_hold('D5E_OWNER_READBACK_HOLD',p.OLD,'fresh')


if __name__=='__main__': unittest.main(verbosity=2)
