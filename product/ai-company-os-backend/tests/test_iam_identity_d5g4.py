"""D5-G4: actual G2 resolver + original D4/D5 review on synthetic owner inputs."""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import secrets
import unittest
from app.core.agent_runtime.lifecycle import Scope
from app.core.event_store.company_coordination import Member
from app.core.iam_session import D0_SCOPE, D0SessionResolver, SessionRecord, credential_digest
from app.core.transaction.intent_authority import RootPin
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.identity_binding import Binding, Review
from app.core.transaction.intent_identity import derive_request
from app.core.transaction.identity_fence_review import (IdentityReadback, capture_session_reference,
    inspect_session_reference, session_reference_digest)


class SessionIdentityTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.now = 100
        self.root = RootPin('a'*64,'b'*64,1)
        self.secrets = [secrets.token_urlsafe(32) for _ in range(4)]
        records = tuple(SessionRecord('demo-session-'+str(i),credential_digest(secret),'demo-principal',kind,
                                      D0_SCOPE,agent,100,200)
                        for i,(secret,kind,agent) in enumerate(zip(self.secrets,
                            ('AGENT','AGENT','AGENT','HUMAN'),('demo-agent','demo-agent','demo-other',None))))
        self.resolver = D0SessionResolver.bootstrap_durable(Path(tmp.name)/'test.authority.sqlite',self.root,
            records,domain='demo-clock',clock=lambda:self.now)
        self.pin = self.resolver.durable_pin
        s = Scope(*D0_SCOPE,'sha256:'+'c'*64,'task','demo-run','demo-agent','demo-principal')
        self.intent = LogicalIntent(s,Operation.STATE_MUTATION,5,'d'*64,'effect','idem','grant','lease',None,1,2)
        self.member = Member('project',s.plan_revision,s.task_id,s.run_id,s.agent_instance_id,s.principal_id,0)
        request = derive_request(self.intent,self.member,D0_SCOPE,s.principal_id)
        binding = Binding(request,s.principal_id,1,1,1,1,'1'*64,'2'*64,'3'*64,'4'*64,'demo_role','db','cluster',500,True)
        self.initial = IdentityReadback(self.member,D0_SCOPE,s.principal_id,binding,self.root,300)
        self.ref = self.capture()
        self.sha = session_reference_digest(self.ref)

    def capture(self, secret=None, sample=None, intent=None, **kw):
        args = dict(root=self.root,owner_pin=self.pin,domain='demo-clock') | kw
        return capture_session_reference(self.resolver,secret or self.secrets[0],intent or self.intent,
                                         sample or self.initial,**args)

    def review(self, secret=None, initial=None, latest=None, intent=None, ref=None, sha=None, reader=None, **kw):
        args = dict(root=self.root,owner_pin=self.pin,domain='demo-clock') | kw
        return inspect_session_reference(self.resolver,secret or self.secrets[0],intent or self.intent,
            initial or self.initial,ref or self.ref,sha or self.sha,reader or (lambda:latest or self.initial),**args)

    def denied(self,result):
        self.assertIs(type(result),Review)
        self.assertFalse(result.structural_match)
        self.assertEqual(result.decision,'HOLD')
        self.assertFalse(result.commit_allowed or result.dispatch_allowed or result.retry_allowed)

    def test_exact_request_same_session_hold_only(self):
        result = self.review(latest=replace(self.initial,tick=301))
        self.assertTrue(result.structural_match)
        self.assertEqual(result.decision,'HOLD')
        self.assertFalse(result.commit_allowed or result.dispatch_allowed or result.retry_allowed)
        self.assertEqual(self.ref.request,self.initial.binding.request)
        self.assertEqual(self.ref.observation.session_id,'demo-session-0')
        self.assertNotIn(self.secrets[0],repr(self.ref))

    def test_same_principal_different_session_rejected(self):
        self.denied(self.review(secret=self.secrets[1]))
        self.assertNotEqual(self.sha,session_reference_digest(self.capture(secret=self.secrets[1])))

    def test_wrong_agent_and_human_rejected(self):
        for token in self.secrets[2:]:
            self.denied(self.review(secret=token))
            with self.assertRaises(ValueError): self.capture(secret=token)

    def test_forged_credential(self):
        self.denied(self.review(secret=secrets.token_urlsafe(32)))

    def test_changed_intent_digest_and_fields(self):
        for i in (replace(self.intent,request_digest='e'*64),replace(self.intent,expected_version=6),
                  replace(self.intent,grant_ref='new-grant'),replace(self.intent,policy_epoch=2),
                  replace(self.intent,scope=replace(self.intent.scope,task_id='other'))):
            self.denied(self.review(intent=i))

    def test_project_alias_and_membership_drift(self):
        m = replace(self.member,project_id='other')
        self.denied(self.review(latest=replace(self.initial,member=m)))
        self.denied(self.review(latest=replace(self.initial,binding=replace(self.initial.binding,membership_revision=2))))

    def test_role_revision_and_physical_role_drift(self):
        for b in (replace(self.initial.binding,role_revision=2),replace(self.initial.binding,db_role='other_role')):
            self.denied(self.review(latest=replace(self.initial,binding=b)))

    def test_d4_expiry_and_clock_regression(self):
        self.denied(self.review(latest=replace(self.initial,tick=500)))
        self.denied(self.review(latest=replace(self.initial,tick=299)))

    def test_iam_expiry_independent_of_d4_tick(self):
        self.now=200
        self.denied(self.review())

    def test_revoke_exact_session(self):
        self.assertTrue(self.resolver.revoke_local('demo-session-0',expected_revision=1))
        self.denied(self.review())

    def test_unrelated_revocation_changes_owner_pin(self):
        self.assertTrue(self.resolver.revoke_local('demo-session-1',expected_revision=1))
        self.denied(self.review())
        self.denied(self.review(owner_pin=self.resolver.durable_pin))

    def test_wrong_reference_hash_root_and_domain(self):
        self.denied(self.review(sha='e'*64))
        self.denied(self.review(root=RootPin('f'*64,'b'*64,1)))
        self.denied(self.review(domain='demo-other-clock'))

    def test_readback_failure_stays_hold(self):
        def unavailable(): raise OSError('owner unavailable')
        self.denied(self.review(reader=unavailable))

    def test_review_has_no_claim_or_publication_write(self):
        self.assertTrue(self.review().structural_match)
        with closing(self.resolver._authority._db()) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM iam_claim_pins').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM roots').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM iam_revocations').fetchone()[0],0)


if __name__=='__main__': unittest.main()
