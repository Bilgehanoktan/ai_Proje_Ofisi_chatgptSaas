"""Original wrapper prefix + real existing authority, mocked lazy T1 dependencies.
No original T1 execution is claimed. All writes are disposable authority fixture claims.
"""
from dataclasses import replace
from pathlib import Path
from contextlib import closing
import sqlite3
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
from unittest import TestCase
from unittest.mock import patch, Mock

from app.core.transaction import intent_authority as original
from app.core.agent_runtime.lifecycle import Scope
from app.core.transaction.review import LogicalIntent, Operation
from app.core.event_store.company_coordination import Member, SCOPE
from identity_binding import Binding
from intent_identity import derive_request
from identity_fence_review import IdentityReadback, readback_digest
from build_probe import probe_source


class FenceInsertionTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.root = original.RootPin('1'*64,'2'*64,1)
        self.authority = original.D0IntentAuthority.create(self.path/'root.authority.sqlite',self.root)
        for name in ('memory','reader','journal'):
            (self.path/name).touch()
        s = Scope(*SCOPE,'sha256:'+'a'*64,'task','demo-run','demo-agent','demo-principal')
        self.intent = LogicalIntent(s,Operation.STATE_MUTATION,3,'b'*64,'effect','idem','grant','lease',None,2,3)
        m=Member('project',s.plan_revision,s.task_id,s.run_id,s.agent_instance_id,s.principal_id,0)
        b=Binding(derive_request(self.intent,m,SCOPE,s.principal_id),s.principal_id,1,2,3,4,
                  'c'*64,'d'*64,'e'*64,'f'*64,'role_a','database_a','cluster_a',20,True)
        self.initial=IdentityReadback(m,SCOPE,s.principal_id,b,self.root,10)
        self.latest=replace(self.initial,tick=11)
        self.sha=readback_digest(self.intent,self.initial)
        self.witness_type=type('LatestWitnessPin',(),{})
        self.witness=self.witness_type(); self.witness.record_sha=self.root.record_sha
        self.witness.key_sha=self.root.key_sha; self.witness.recovery_epoch=self.root.recovery_epoch
        self.downstream=Mock(side_effect=AssertionError('T1 must never be called'))
        self.binding_check=Mock(return_value='4'*64)
        self.pin=SimpleNamespace(scope_sha='5'*64,binding='6'*64,transaction_ref='d5c-diagnostic',request_digest=self.intent.request_digest)
        self.reader=Mock(return_value=self.latest)
        modules={}
        for name,fields in {
            'app.core.transaction.fenced_transition':dict(execute_fenced_transition=self.downstream,
                intent_pin=lambda *_:self.pin,resolve_fence_binding=lambda *_:'6'*64,
                resolve_result_binding=lambda *_:'6'*64,check_result_store_separation=lambda *_:None),
            'app.core.transaction.witnessed_mapping':dict(binding_digest=self.binding_check),
            'app.core.agent_runtime.memory_witness':dict(LatestWitnessPin=self.witness_type),
        }.items():
            mod=ModuleType(name); vars(mod).update(fields); modules[name]=mod
        p=patch.dict(sys.modules,modules); p.start(); self.addCleanup(p.stop)
        raw=Path(original.__file__).read_bytes()
        namespace=dict(vars(original)); exec(compile(probe_source(raw),'<D5-C probe>','exec'),namespace)
        self.probe=namespace['probe_authority_fenced_transition']
        self.args=dict(authority=self.authority,intent=self.intent,context=None,registry=None,
            witness=self.witness,expected_binding='4'*64,memory_path=self.path/'memory',
            reader=SimpleNamespace(path=self.path/'reader'),public_key=None,raw=b'',
            journal=SimpleNamespace(path=self.path/'journal'),connect=Mock(),clock=Mock(),
            initial_identity=self.initial,identity_sha=self.sha,read_latest=self.reader)

    def claims(self):
        with closing(sqlite3.connect(self.authority.path)) as db:
            return db.execute('SELECT count(*) FROM claims').fetchone()[0]

    def hold(self, reason, **changes):
        with self.assertRaisesRegex(ValueError,reason): self.probe(**(self.args|changes))
        self.downstream.assert_not_called(); self.args['connect'].assert_not_called()

    def test_original_wrapper_pin(self):
        raw=Path(original.__file__).read_bytes()
        with self.assertRaisesRegex(ValueError,'SOURCE_PIN'): probe_source(raw+b'\n')
        self.assertNotIn('probe_authority_fenced_transition',vars(original))

    def test_missing_initial_preclaim(self):
        self.hold('PRECLAIM',initial_identity=None); self.assertEqual(self.claims(),0)
        self.reader.assert_not_called()

    def test_bad_digest_preclaim(self):
        self.hold('PRECLAIM',identity_sha='0'*64); self.assertEqual(self.claims(),0)
        self.reader.assert_not_called()

    def test_wrong_root_preclaim(self):
        self.hold('PRECLAIM',initial_identity=replace(self.initial,root=replace(self.root,recovery_epoch=2)))
        self.assertEqual(self.claims(),0)

    def test_missing_reader_preclaim(self):
        self.hold('PRECLAIM',read_latest=None); self.assertEqual(self.claims(),0)

    def test_original_binding_failure_preclaim(self):
        self.binding_check.return_value='0'*64
        self.hold('AUTHORITY_BINDING'); self.assertEqual(self.claims(),0); self.reader.assert_not_called()

    def test_match_still_stops(self):
        self.hold('OWNER_INTEGRATION_HOLD'); self.assertEqual(self.claims(),1)
        self.reader.assert_called_once_with()
        self.hold('ALREADY_CLAIMED'); self.reader.assert_called_once_with()

    def test_revoked_inside_fence(self):
        self.reader.return_value=replace(self.latest,binding=replace(self.latest.binding,active=False))
        self.hold('REVOKED_OR_EXPIRED'); self.assertEqual(self.claims(),1)

    def test_role_drift_inside_fence(self):
        self.reader.return_value=replace(self.latest,binding=replace(self.latest.binding,role_revision=9))
        self.hold('SCOPE_OR_REVISION'); self.assertEqual(self.claims(),1)

    def test_reader_error_consumes(self):
        self.reader.side_effect=OSError('private')
        self.hold('READBACK_UNAVAILABLE'); self.assertEqual(self.claims(),1)
        self.hold('ALREADY_CLAIMED')

    def test_publisher_before_claim(self):
        self.authority.publish(self.root,replace(self.root,record_sha='7'*64))
        self.hold('ROOT_HOLD'); self.assertEqual(self.claims(),0); self.reader.assert_not_called()

    def test_reader_under_original_lock(self):
        def read():
            with closing(sqlite3.connect(self.authority.path,timeout=0,isolation_level=None)) as db:
                with self.assertRaisesRegex(sqlite3.OperationalError,'locked'): db.execute('BEGIN IMMEDIATE')
            return self.latest
        self.hold('OWNER_INTEGRATION_HOLD',read_latest=read)
        self.authority.publish(self.root,replace(self.root,record_sha='7'*64))
        self.assertEqual(self.claims(),1)

    def test_original_path_separation(self):
        self.hold('AUTHORITY_SEPARATION',memory_path=self.authority.path)
        self.assertEqual(self.claims(),0); self.reader.assert_not_called()
