"""0219 D0 company/admission/witness profile checks. No real grants or PG evidence."""
from dataclasses import replace
from unittest import TestCase
from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime.transition_command import transition_digest
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.fenced_transition import (
    CompanyTransitionContext, company_transition_binding, resolve_fence_binding,
)
from app.core.transaction.postgres_transition_mapping import transaction_ref
from app.core.transaction.postgres_lifecycle_mapping import D0AdmissionBoundTransitionMapping
import test_company_terminal_0212 as base


class CompanyFenceBindingTests(TestCase):
    def setUp(self):
        f=base.CompanyTerminalTests()
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.f=f
        f.admission()
        f.ordinary(RunState.RUNNING)
        b,l=f.before,f.lease
        self.intent=LogicalIntent(b.scope,Operation.STATE_MUTATION,b.version,
            transition_digest(b,RunState.VERIFYING),'verify-0219','verify-idem-0219',
            l.grant_id,l.lease_id,None,l.policy_epoch,l.witness_epoch)
        self.witness_pin='a'*64
        self.ctx=CompanyTransitionContext(f.binding,f.members,f.pool,f.history,
            f.event(self.intent,'D0_RUN_TRANSITION'))

    def pin(self,ctx=None):
        return company_transition_binding(self.intent,self.witness_pin,ctx or self.ctx)

    def test_exact_profile_and_legacy_separation(self):
        p=self.pin()
        self.assertNotEqual(p,self.witness_pin)
        self.assertEqual(resolve_fence_binding(self.intent,self.witness_pin,self.ctx,p),p)
        self.assertEqual(resolve_fence_binding(self.intent,self.witness_pin,None,None),self.witness_pin)

    def test_partial_or_wrong_pin_holds(self):
        for ctx,p in ((None,self.pin()),(self.ctx,None),(self.ctx,'b'*64)):
            with self.subTest(ctx=ctx is not None,p=p):
                with self.assertRaises(ValueError):
                    resolve_fence_binding(self.intent,self.witness_pin,ctx,p)

    def test_project_or_principal_substitution_holds(self):
        for ctx in (replace(self.ctx,event=replace(self.ctx.event,project_id='project-b')),
                    replace(self.ctx,members=tuple(replace(m,principal_id='demo-other')
                        if m.run_id==self.intent.scope.run_id else m for m in self.ctx.members))):
            with self.assertRaises(ValueError):
                self.pin(ctx)

    def test_wrong_admission_holds(self):
        a=self.ctx.admission
        bad=replace(a,intent=replace(a.intent,scope=replace(a.intent.scope,principal_id='demo-other')))
        with self.assertRaises(ValueError):
            self.pin(replace(self.ctx,admission=bad))

    def test_history_and_pool_pin_drift_holds(self):
        p=self.pin()
        changed=replace(self.ctx,pool=replace(self.ctx.pool,source_digest='b'*64))
        self.assertNotEqual(self.pin(changed),p)
        with self.assertRaises(ValueError):
            resolve_fence_binding(self.intent,self.witness_pin,changed,p)

    def test_original_company_admission_transaction_and_readback(self):
        # Existing actual SQLite mapping; not the complete witness/authority wrapper.
        f=self.f
        r=f.execute(D0AdmissionBoundTransitionMapping(f.binding,f.lease,lambda:f.clock),
            self.intent,self.ctx.event,(f.before,RunState.VERIFYING))
        self.assertEqual(r.transaction_ref,transaction_ref(self.intent))
        self.assertTrue(f.company().structural_match)
