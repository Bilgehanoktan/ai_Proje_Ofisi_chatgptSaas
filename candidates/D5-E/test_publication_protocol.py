"""D0 fixture only: real temporary SQLite, synthetic owner state, no live grant."""
import contextlib
import hashlib
import importlib.util
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from derive_fixture import derive

HERE=Path(__file__).resolve().parent
raw=derive((HERE/'intent_authority.original.py').read_bytes())
if hashlib.sha256(raw).hexdigest() != '2854609a215d61b6c725037cffec7c2c1c6b40a2bc7898f1da7fb89ff7c380c5':
    raise ValueError('D5E_GENERATED_DRIFT_HOLD')
with tempfile.TemporaryDirectory(prefix='d5e-generated-') as stage:
    generated=Path(stage)/'intent_authority.fixture.py'
    generated.write_bytes(raw)
    spec=importlib.util.spec_from_file_location('d5e_fixture',generated)
    A=importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,{'d5e_fixture':A}):
        spec.loader.exec_module(A)


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


ROOT=A.RootPin(digest('witness'),digest('key'),1)
OLD=A.PublicationPin(1,1,digest('revision-1-active'))
NEW=A.PublicationPin(2,1,digest('revision-2-observation'))


def read_owner(path):
    with contextlib.closing(sqlite3.connect(path/'owner.sqlite')) as db:
        return db.execute('SELECT sha FROM owner_state').fetchone()[0]


def mutate(path,sha=NEW.owner_sha):
    with contextlib.closing(sqlite3.connect(path/'owner.sqlite')) as db:
        db.execute('UPDATE owner_state SET sha=?',(sha,))
        db.commit()


def authority(path):
    return A.D0IntentAuthority(path/'test.authority.sqlite')


def crash_worker(path,point):
    def apply():
        if point=='after':
            mutate(path)
        os._exit(73)
    authority(path).publish_protected(ROOT,OLD,NEW.owner_sha,apply_change=apply,read_owner=lambda:read_owner(path))
    raise AssertionError('worker returned')


class PublicationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='d5e-')
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)
        self.a=A.D0IntentAuthority.create(self.path/'test.authority.sqlite',ROOT,owner_sha=OLD.owner_sha)
        with contextlib.closing(sqlite3.connect(self.path/'owner.sqlite')) as db:
            db.execute('CREATE TABLE owner_state(sha TEXT NOT NULL)')
            db.execute('INSERT INTO owner_state VALUES (?)',(OLD.owner_sha,))
            db.commit()

    def read(self): return read_owner(self.path)
    def state(self):
        with contextlib.closing(self.a._db()) as db:
            return self.a._publication_state(db,1)
    def claim_count(self):
        with contextlib.closing(self.a._db()) as db:
            return db.execute('SELECT count(*) FROM claims').fetchone()[0]
    def claim(self,pin=OLD,suffix='a',reader=None):
        return self.a.claim_and_fence(ROOT,digest('scope-'+suffix),digest('binding-'+suffix),'tx-'+suffix,digest('request-'+suffix),expected_publication=pin,read_owner=reader or self.read)
    def publish(self,apply=None,expected=OLD,sha=NEW.owner_sha):
        return self.a.publish_protected(ROOT,expected,sha,apply_change=apply or (lambda:mutate(self.path,sha)),read_owner=self.read)
    def assert_hold(self,reason,pin=OLD,suffix='a'):
        with self.assertRaisesRegex(ValueError,reason):
            with self.claim(pin,suffix): self.fail('claim unexpectedly entered')
    def assert_pending(self):
        self.assertEqual(self.state(),(NEW,True))
        self.assert_hold('D5E_PUBLICATION_PENDING_HOLD',NEW)
        with self.assertRaisesRegex(ValueError,'D5E_PUBLICATION_PENDING_HOLD'):
            self.publish(apply=lambda:self.fail('pending was resumed'),expected=NEW,sha=digest('new'))
        self.assertEqual(self.claim_count(),0)

    def test_happy_publication_stale_pin_rejected_new_observation_structurally_matches(self):
        self.assertEqual(self.publish(),NEW)
        self.assertEqual(self.state(),(NEW,False))
        self.assert_hold('D5E_PUBLICATION_STALE_HOLD')
        # This checks pin/lock only, not a grant or an IAM status.
        with self.claim(NEW): pass
        self.assertEqual(self.claim_count(),1)
        with contextlib.closing(self.a._db()) as db:
            self.assertEqual(self.a._head(db),(1,ROOT))

    def test_pending_durable_before_external_mutation(self):
        def apply():
            self.assertEqual(self.state(),(NEW,True))
            self.assertEqual(self.read(),OLD.owner_sha)
            mutate(self.path)
        self.assertEqual(self.publish(apply),NEW)

    def test_callback_error_before_change_pending(self):
        def fail(): raise RuntimeError('injected')
        with self.assertRaisesRegex(RuntimeError,'injected'): self.publish(fail)
        self.assertEqual(self.read(),OLD.owner_sha)
        self.assert_pending()

    def test_callback_error_after_change_pending(self):
        def fail():
            mutate(self.path)
            raise RuntimeError('injected')
        with self.assertRaisesRegex(RuntimeError,'injected'): self.publish(fail)
        self.assertEqual(self.read(),NEW.owner_sha)
        self.assert_pending()

    def test_actual_process_death_before_external_change(self):
        p=subprocess.run([sys.executable,'-B',__file__,'--crash',str(self.path),'before'],capture_output=True,timeout=10)
        self.assertEqual(p.returncode,73,p.stderr)
        self.a=authority(self.path)
        self.assertEqual(self.read(),OLD.owner_sha)
        self.assert_pending()

    def test_actual_process_death_after_external_change(self):
        p=subprocess.run([sys.executable,'-B',__file__,'--crash',str(self.path),'after'],capture_output=True,timeout=10)
        self.assertEqual(p.returncode,73,p.stderr)
        self.a=authority(self.path)
        self.assertEqual(self.read(),NEW.owner_sha)
        self.assert_pending()

    def test_readback_mismatch_pending(self):
        with self.assertRaisesRegex(ValueError,'D5E_OWNER_READBACK_HOLD'):
            self.publish(lambda:mutate(self.path,digest('wrong')))
        self.assert_pending()

    def test_out_of_band_owner_drift_preclaim_rejected(self):
        mutate(self.path)
        self.assert_hold('D5E_OWNER_READBACK_HOLD')
        self.assertEqual(self.claim_count(),0)

    def test_owner_read_failure_preclaim_no_consumption(self):
        def unavailable(): raise RuntimeError('owner unreachable')
        with self.assertRaisesRegex(RuntimeError,'owner unreachable'):
            with self.claim(reader=unavailable): self.fail('entered')
        self.assertEqual(self.claim_count(),0)

    def test_legacy_entrypoints_disabled(self):
        with self.assertRaisesRegex(ValueError,'D5E_LEGACY_PUBLISH_HOLD'):
            self.a.publish(ROOT,A.RootPin(digest('other'),ROOT.key_sha,1))
        with self.assertRaisesRegex(ValueError,'D5E_PUBLICATION_INPUT_HOLD'):
            with self.a.claim_and_fence(ROOT,digest('s'),digest('b'),'tx',digest('r')): self.fail('entered')
        with self.assertRaisesRegex(ValueError,'D5E_PRODUCT_WRAPPER_DISABLED_HOLD'):
            A.execute_authority_fenced_transition()
        self.assertEqual(self.claim_count(),0)
        self.assertEqual(self.state(),(OLD,False))

    def test_cooperating_publisher_cannot_enter_held_fence(self):
        with self.claim():
            with self.assertRaisesRegex(sqlite3.OperationalError,'locked'):
                self.publish(apply=lambda:self.fail('mutation before fence release'))
            self.assertEqual(self.state(),(OLD,False))
        self.assertEqual(self.publish(),NEW)
        self.assertEqual(self.claim_count(),1)

    def test_publication_wins_claim_commit_gap_consumed_scope_quarantined(self):
        # Instrument only the first connection's claim COMMIT, then publish via
        # the unchanged generated class on a separate connection before reacquire.
        a=self.a; real=a._db; outer=self
        class Gap:
            def __init__(self,db): self.db=db; self.fired=False
            def __getattr__(self,name): return getattr(self.db,name)
            def execute(self,sql,*args):
                r=self.db.execute(sql,*args)
                if sql=='COMMIT' and not self.fired:
                    self.fired=True
                    authority(outer.path).publish_protected(ROOT,OLD,NEW.owner_sha,apply_change=lambda:mutate(outer.path),read_owner=outer.read)
                return r
        with patch.object(a,'_db',side_effect=lambda:Gap(real())):
            self.assert_hold('D5E_PUBLICATION_STALE_HOLD')
        self.assertEqual(self.state(),(NEW,False))
        self.assertEqual(self.claim_count(),1)
        self.assert_hold('D0_AUTHORITY_ALREADY_CLAIMED_HOLD',NEW)

    def test_append_only_and_alias(self):
        self.publish()
        with self.assertRaisesRegex(ValueError,'D5E_PUBLICATION_ALIAS_HOLD'):
            self.publish(expected=NEW,sha=OLD.owner_sha)
        with contextlib.closing(self.a._db()) as db:
            for stmt in ('DELETE FROM publication_final WHERE seq=2', 'UPDATE publication_versions SET owner_sha=\'x\' WHERE seq=2', 'INSERT OR REPLACE INTO publication_final VALUES (2)', "INSERT OR REPLACE INTO publication_versions VALUES (3,1,'x','"+OLD.owner_sha+"')"):
                with self.assertRaises(sqlite3.IntegrityError): db.execute(stmt)
        self.assertEqual(self.state(),(NEW,False))

    def test_missing_publication_record_fails_closed(self):
        with contextlib.closing(self.a._db()) as db:
            db.execute('DROP TABLE publication_final')
        with self.assertRaises(sqlite3.Error):
            with self.claim(): self.fail('entered')
        self.assertEqual(self.claim_count(),0)

    def test_derived_source_pin_mismatch(self):
        with self.assertRaisesRegex(ValueError,'D5E_ORIGINAL_PIN_HOLD'):
            derive((HERE/'intent_authority.original.py').read_bytes()+b'\n')


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--crash':
        crash_worker(Path(sys.argv[2]),sys.argv[3])
    else: unittest.main(verbosity=2)
