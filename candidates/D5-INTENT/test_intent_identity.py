from dataclasses import replace
import unittest

from app.core.agent_runtime.lifecycle import Scope
from app.core.transaction.review import LogicalIntent, Operation
from app.core.event_store.company_coordination import Member, SCOPE
from identity_binding import Binding
from intent_identity import derive_request, full_intent_digest, review_bound_intent


class IntentIdentityTests(unittest.TestCase):
    def setUp(self):
        self.scope = Scope(*SCOPE, 'sha256:'+'a'*64, 'task-a', 'demo-run', 'demo-agent', 'demo-principal')
        self.intent = LogicalIntent(self.scope, Operation.STATE_MUTATION, 3, 'b'*64,
                                    'effect-a','idem-a','grant-a','lease-a',None,2,3)
        self.member = Member('project-a',self.scope.plan_revision,self.scope.task_id,
                             self.scope.run_id,self.scope.agent_instance_id,self.scope.principal_id,0)
        self.binding = Binding(derive_request(self.intent,self.member,SCOPE,self.scope.principal_id),
                               self.scope.principal_id,1,2,3,4,'c'*64,'d'*64,'e'*64,'f'*64,
                               'role_a','database_a','cluster_a',20,True)

    def review(self, **changes):
        args = dict(intent=self.intent, member=self.member, latest_member=self.member,
                    member_scope=SCOPE,latest_member_scope=SCOPE,
                    authenticated_principal=self.scope.principal_id,
                    initial_binding=self.binding,latest_binding=self.binding,tick=10)
        args.update(changes)
        result = review_bound_intent(**args)
        self.assertEqual(result.decision,'HOLD')
        self.assertFalse(result.commit_allowed or result.dispatch_allowed or result.retry_allowed)
        return result

    def test_match(self):
        self.assertTrue(self.review().structural_match)

    def test_request_reuses_scope(self):
        r = derive_request(self.intent,self.member,SCOPE,self.scope.principal_id)
        self.assertEqual((r.scope,r.project,r.plan_revision,r.task,r.run,r.agent,r.principal),
                         (SCOPE,*self.member.row()[:6]))
        self.assertEqual(r.intent_sha,full_intent_digest(self.intent))
        self.assertNotEqual(r.intent_sha,self.intent.request_digest)

    def test_digest_stable(self):
        self.assertEqual(full_intent_digest(self.intent),full_intent_digest(replace(self.intent)))

    def test_all_intent_fields_pin(self):
        mutations=dict(operation=Operation.TERMINAL,expected_version=4,request_digest='1'*64,
                       effect_key='effect-b',idempotency_key='idem-b',grant_ref='grant-b',
                       lease_ref='lease-b',budget_ref='budget-b',policy_epoch=4,witness_epoch=5,
                       lease_or_budget_changes=True)
        for k,v in mutations.items():
            with self.subTest(k=k):
                changed=replace(self.intent,**{k:v})
                self.assertNotEqual(full_intent_digest(changed),full_intent_digest(self.intent))
                self.assertFalse(self.review(intent=changed).structural_match)

    def test_scope_fields(self):
        for k,v in dict(plan_revision='sha256:'+'9'*64, task_id='task-b',run_id='demo-other-run',
                        agent_instance_id='demo-other-agent',principal_id='demo-other-principal').items():
            with self.subTest(k=k):
                self.assertFalse(self.review(intent=replace(self.intent,scope=replace(self.scope,**{k:v}))).structural_match)

    def test_foreign_scope(self):
        for k in ('tenant_id','company_id','environment_id'):
            with self.subTest(k=k):
                self.assertFalse(self.review(intent=replace(self.intent,scope=replace(self.scope,**{k:'foreign'}))).structural_match)

    def test_member_scope(self):
        self.assertFalse(self.review(member_scope=('a','b','c')).structural_match)
        self.assertFalse(self.review(latest_member_scope=list(SCOPE)).structural_match)

    def test_member_identity(self):
        for k in ('plan_revision','task_id','run_id','agent_instance_id','principal_id'):
            with self.subTest(k=k):
                self.assertFalse(self.review(latest_member=replace(self.member,**{k:'invalid'})).structural_match)

    def test_project_drift(self):
        self.assertFalse(self.review(latest_member=replace(self.member,project_id='project-b')).structural_match)

    def test_member_initial_version_future(self):
        self.assertFalse(self.review(member=replace(self.member,initial_version=4)).structural_match)

    def test_member_initial_version_drift(self):
        self.assertFalse(self.review(latest_member=replace(self.member,initial_version=1)).structural_match)

    def test_principal(self):
        self.assertFalse(self.review(authenticated_principal='demo-other').structural_match)
        self.assertFalse(self.review(authenticated_principal=None).structural_match)

    def test_binding_principal(self):
        b=replace(self.binding,authenticated_principal='demo-other')
        self.assertFalse(self.review(initial_binding=b,latest_binding=b).structural_match)

    def test_binding_revision_drift(self):
        for k in ('registry_revision','membership_revision','assignment_revision','role_revision'):
            with self.subTest(k=k):
                self.assertFalse(self.review(latest_binding=replace(self.binding,**{k:10})).structural_match)

    def test_revoked(self):
        b=replace(self.binding,active=False)
        self.assertFalse(self.review(initial_binding=b,latest_binding=b).structural_match)

    def test_expired(self):
        self.assertTrue(self.review(tick=19).structural_match)
        self.assertFalse(self.review(tick=20).structural_match)
        self.assertFalse(self.review(tick=True).structural_match)

    def test_invalid_intent(self):
        for v in (None,{},replace(self.intent,request_digest='bad'),replace(self.intent,expected_version=True)):
            with self.subTest(v=v):
                self.assertFalse(self.review(intent=v).structural_match)

    def test_invalid_member(self):
        self.assertFalse(self.review(member=None).structural_match)
        self.assertFalse(self.review(member=self.member.row()).structural_match)

    def test_project_cannot_come_from_binding(self):
        b=replace(self.binding,request=replace(self.binding.request,project='project-b'))
        self.assertFalse(self.review(initial_binding=b,latest_binding=b).structural_match)


if __name__=='__main__':
    unittest.main()
