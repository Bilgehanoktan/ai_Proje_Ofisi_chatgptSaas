from dataclasses import replace
import unittest
from identity_binding import Request, Binding, SessionFacts, review_boundary, binding_digest, disposition

R=Request(('tenant-a','company-a','env-a'),'project-a','sha256:'+'a'*64,'task-a','run-a','agent-a','principal-a','b'*64,2,3)
B=Binding(R,'principal-a',1,2,3,4,'c'*64,'d'*64,'e'*64,'f'*64,'aicos_test','test_db','test_cluster',10,True)
F=SessionFacts('aicos_test','aicos_test','test_db','test_cluster',123,True,False,0,0,16,False,0)

class BindingTests(unittest.TestCase):
    def review(self,r=R,initial=B,latest=B,tick=9,facts=F,pid=123):
        return review_boundary(r,initial,latest,tick,facts,pid)
    def deny(self,**kwargs):
        v=self.review(**kwargs)
        self.assertFalse(v.structural_match)
        self.assertFalse(v.commit_allowed or v.dispatch_allowed or v.retry_allowed)
    def test_match_never_authority(self):
        v=self.review();self.assertTrue(v.structural_match);self.assertEqual(v.decision,'HOLD')
        self.assertFalse(v.commit_allowed or v.dispatch_allowed or v.retry_allowed)
    def test_scope_dimensions(self):
        for i in range(3):
            s=list(R.scope);s[i]='other';self.deny(r=replace(R,scope=tuple(s)))
    def test_project_plan_task_run_agent_principal_intent_epochs(self):
        for k,v in [('project','other'),('plan_revision','sha256:'+'9'*64),('task','other'),('run','other'),('agent','other'),('principal','other'),('intent_sha','9'*64),('policy_epoch',4),('witness_epoch',5)]:
            with self.subTest(k=k):self.deny(r=replace(R,**{k:v}))
    def test_revision_drift(self):
        for k in ('registry_revision','membership_revision','assignment_revision','role_revision'):
            self.deny(latest=replace(B,**{k:9}))
    def test_digest_drift(self):
        for k in ('registry_sha','membership_sha','assignment_sha','role_sha'):
            self.deny(latest=replace(B,**{k:'9'*64}))
    def test_expiry(self):self.deny(tick=10)
    def test_clock(self):self.deny(tick=True);self.deny(tick=-1)
    def test_revocation(self):
        b=replace(B,active=False);self.deny(initial=b,latest=b)
    def test_delegation(self):
        b=replace(B,authenticated_principal='other');self.deny(initial=b,latest=b)
    def test_malformed_revision(self):
        b=replace(B,role_revision=True);self.deny(initial=b,latest=b)
    def test_session_identity(self):
        for k in ('session_user','current_user','database','cluster'):
            self.deny(facts=replace(F,**{k:'other'}))
    def test_pid(self):self.deny(pid=124);self.deny(pid=True)
    def test_rls(self):self.deny(facts=replace(F,row_security=False));self.deny(facts=replace(F,forced_tables=15))
    def test_unsafe_role(self):self.deny(facts=replace(F,unsafe_role=True))
    def test_memberships(self):self.deny(facts=replace(F,role_memberships=1))
    def test_owner(self):self.deny(facts=replace(F,owned_tables=1))
    def test_schema_create(self):self.deny(facts=replace(F,schema_create=True))
    def test_grants(self):self.deny(facts=replace(F,unsafe_table_grants=1))
    def test_missing(self):self.deny(latest=None);self.deny(facts=None)
    def test_digest_stable_and_bound(self):
        self.assertEqual(binding_digest(B),binding_digest(B));self.assertNotEqual(binding_digest(B),binding_digest(replace(B,role_revision=9)))
    def test_unknown(self):self.assertEqual(disposition('UNKNOWN'),'QUARANTINE_RECONCILE_NO_RETRY')
    def test_close(self):self.assertEqual(disposition('COMMITTED'),'CLOSE_DEDICATED_NO_REUSE')

if __name__=='__main__':unittest.main()
