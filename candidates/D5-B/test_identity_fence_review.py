from dataclasses import replace
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from app.core.agent_runtime.lifecycle import Scope
from app.core.event_store.company_coordination import Member, SCOPE
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.intent_authority import D0IntentAuthority, RootPin
from identity_binding import Binding
from intent_identity import derive_request
from identity_fence_review import IdentityReadback, readback_digest, inspect_at_fence


class IdentityFenceTests(unittest.TestCase):
    def setUp(self):
        self.scope = Scope(*SCOPE, 'sha256:'+'a'*64, 'task-a', 'demo-run', 'demo-agent', 'demo-principal')
        self.intent = LogicalIntent(self.scope, Operation.STATE_MUTATION, 3, 'b'*64,
                                    'effect-a','idem-a','grant-a','lease-a',None,2,3)
        self.member = Member('project-a',self.scope.plan_revision,self.scope.task_id,
                             self.scope.run_id,self.scope.agent_instance_id,self.scope.principal_id,0)
        self.binding = Binding(derive_request(self.intent,self.member,SCOPE,self.scope.principal_id),
                               self.scope.principal_id,1,2,3,4,'c'*64,'d'*64,'e'*64,'f'*64,
                               'role_a','database_a','cluster_a',20,True)
        self.root = RootPin('1'*64,'2'*64,1)
        self.initial = IdentityReadback(self.member,SCOPE,self.scope.principal_id,self.binding,self.root,10)
        self.latest = replace(self.initial,tick=11)
        self.pin = readback_digest(self.intent,self.initial)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.authority = D0IntentAuthority.create(Path(self.tmp.name)/'test.authority.sqlite',self.root)

    def check(self, result):
        self.assertEqual(result.decision,'HOLD')
        self.assertFalse(result.commit_allowed or result.dispatch_allowed or result.retry_allowed)
        return result

    def review(self, latest=None, **kw):
        args = dict(intent=self.intent,initial=self.initial,expected_sha=self.pin,
                    expected_root=self.root,read_latest=lambda: self.latest if latest is None else latest)
        args.update(kw)
        return self.check(inspect_at_fence(**args))

    def claim(self):
        # Diagnostic-only IDs in a new disposable authority fixture; never a product claim.
        return self.authority.claim_and_fence(self.root,'3'*64,self.pin,'d5b-test-only',self.intent.request_digest)

    def test_match_under_original_fence(self):
        with self.claim():
            self.assertTrue(self.review().structural_match)
        with closing(self.authority._db()) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone(),(1,))

    def test_sqlite_writer_locked_during_read(self):
        def reader():
            with closing(sqlite3.connect(self.authority.path,timeout=0,isolation_level=None)) as db:
                with self.assertRaisesRegex(sqlite3.OperationalError,'locked'):
                    db.execute('BEGIN IMMEDIATE')
            return self.latest
        with self.claim():
            self.assertTrue(self.review(read_latest=reader).structural_match)
        self.authority.publish(self.root,replace(self.root,record_sha='4'*64))
        with closing(self.authority._db()) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM roots').fetchone(),(2,))

    def test_publisher_before_claim(self):
        self.authority.publish(self.root,replace(self.root,record_sha='4'*64))
        with self.assertRaisesRegex(ValueError,'D0_AUTHORITY_ROOT_HOLD'):
            with self.claim(): self.fail('stale root entered fence')
        with closing(self.authority._db()) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone(),(0,))

    def test_claim_not_reusable_after_failed_review(self):
        with self.claim():
            self.assertFalse(self.review(replace(self.latest,root=replace(self.root,record_sha='4'*64))).structural_match)
        with self.assertRaisesRegex(ValueError,'D0_AUTHORITY_ALREADY_CLAIMED_HOLD'):
            with self.claim(): self.fail('duplicate claim entered fence')

    def test_reference_pin_mismatch_does_not_read(self):
        called=[]
        self.assertFalse(self.review(expected_sha='9'*64,read_latest=lambda: called.append(1)).structural_match)
        self.assertEqual(called,[])

    def test_reference_tick_and_member_are_pinned(self):
        for value in (replace(self.initial,tick=9),replace(self.initial,member=replace(self.member,initial_version=1))):
            self.assertNotEqual(readback_digest(self.intent,value),self.pin)
            self.assertFalse(self.review(initial=value).structural_match)

    def test_root_mismatch(self):
        for root in (replace(self.root,record_sha='4'*64),replace(self.root,key_sha='4'*64),replace(self.root,recovery_epoch=2)):
            self.assertFalse(self.review(replace(self.latest,root=root)).structural_match)

    def test_expected_root_mismatch(self):
        self.assertFalse(self.review(expected_root=replace(self.root,recovery_epoch=2)).structural_match)

    def test_invalid_root(self):
        self.assertFalse(self.review(replace(self.latest,root=replace(self.root,recovery_epoch=True))).structural_match)

    def test_member_project_drift(self):
        m=replace(self.member,project_id='project-b')
        b=replace(self.binding,request=derive_request(self.intent,m,SCOPE,self.scope.principal_id))
        self.assertFalse(self.review(replace(self.latest,member=m,binding=b)).structural_match)

    def test_member_version_drift(self):
        self.assertFalse(self.review(replace(self.latest,member=replace(self.member,initial_version=1))).structural_match)

    def test_principal_drift(self):
        self.assertFalse(self.review(replace(self.latest,principal='demo-other')).structural_match)

    def test_scope_drift(self):
        self.assertFalse(self.review(replace(self.latest,scope=('foreign',*SCOPE[1:]))).structural_match)

    def test_revision_drift(self):
        for k in ('registry_revision','membership_revision','assignment_revision','role_revision'):
            self.assertFalse(self.review(replace(self.latest,binding=replace(self.binding,**{k:10}))).structural_match)

    def test_role_digest_drift(self):
        self.assertFalse(self.review(replace(self.latest,binding=replace(self.binding,role_sha='7'*64))).structural_match)

    def test_revoked_and_expired(self):
        self.assertFalse(self.review(replace(self.latest,binding=replace(self.binding,active=False))).structural_match)
        self.assertFalse(self.review(replace(self.latest,tick=20)).structural_match)
        self.assertTrue(self.review(replace(self.latest,tick=19)).structural_match)

    def test_clock_regression(self):
        self.assertFalse(self.review(replace(self.latest,tick=9)).structural_match)
        self.assertFalse(self.review(replace(self.latest,tick=True)).structural_match)

    def test_intent_change(self):
        self.assertFalse(self.review(intent=replace(self.intent,effect_key='different')).structural_match)

    def test_reader_failure(self):
        def fail(): raise RuntimeError('private detail')
        r=self.review(read_latest=fail)
        self.assertEqual(r.reason,'D5B_READBACK_UNAVAILABLE_HOLD')
        self.assertFalse(r.structural_match)

    def test_invalid_reader_output(self):
        self.assertFalse(self.review(read_latest=lambda: {}).structural_match)

    def test_no_claim_by_review_itself(self):
        self.assertTrue(self.review().structural_match)
        with closing(self.authority._db()) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone(),(0,))


if __name__=='__main__':
    unittest.main()
