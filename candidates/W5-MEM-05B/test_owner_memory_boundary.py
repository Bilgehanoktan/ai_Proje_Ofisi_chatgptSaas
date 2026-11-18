"""MEM-05B diagnostics: separate exact G2 owner input, original MEM05A T1.
Not a production adapter or authorization test. Expected residuals are explicit.
"""
from base64 import urlsafe_b64encode
from contextlib import closing
from dataclasses import fields, replace
from hashlib import sha1, sha256
import importlib.util
import os
from pathlib import Path
import sqlite3
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
OWNER = Path(os.environ['MEM05B_OWNER_ROOT'])
OWNER_PINS = {
    'app.core.transaction.intent_authority': ('product/ai-company-os-backend/app/core/transaction/intent_authority.py', 'b28788f46a39c282d79d29c4abd817ed5fc9de99'),
    'app.core.iam_session': ('product/ai-company-os-backend/app/core/iam_session.py', 'f3c37428acd475e09c228bce47d534d6584cd944'),
}


def load_owner():
    # Only this disposable diagnostic process loads the owner modules. No product overlay.
    # Verify BOTH source bytes before executing either module.
    for rel, pin in OWNER_PINS.values():
        p = OWNER / rel
        raw = p.read_bytes()
        if sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest() != pin:
            raise RuntimeError('MEM05B_OWNER_SOURCE_PIN_HOLD')
    for name, (rel, _) in OWNER_PINS.items():
        if name in sys.modules:
            raise RuntimeError('MEM05B_OWNER_MODULE_ALREADY_LOADED_HOLD')
        spec = importlib.util.spec_from_file_location(name, OWNER / rel)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)


load_owner()
from app.core.iam_session import D0SessionResolver, SessionRecord, credential_digest
from app.core.transaction.intent_authority import RootPin
from app.core.agent_runtime.lifecycle import Scope
from app.core.agent_runtime.memory_witness import MemoryWitness
from app.engines.memory_engine.runtime_binding import MemoryAclView
from app.core.transaction.witnessed_mapping import binding_digest
from app.engines.memory_engine.snapshot_store import publish_snapshot
import test_runtime_memory_t1_w5_mem05a as original


class OwnerMemoryBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.m = original.RuntimeMemoryT1Tests()
        self.m.setUp()
        self.addCleanup(self.m.doCleanups)
        self.w, self.sql, self.h = self.m.w, self.m.sql, self.m.h
        self.scope = self.w.b.f.scope
        self.triple = (self.scope.tenant_id, self.scope.company_id, self.scope.environment_id)
        self.now = 10  # Separate IAM fixture clock, NOT a Runtime clock conversion.
        self.creds = tuple(urlsafe_b64encode(bytes([i])*32).decode().rstrip('=') for i in (1, 2, 3, 4))
        records = tuple(SessionRecord('demo-session-'+str(i), credential_digest(cred),
                         self.scope.principal_id, kind, self.triple, agent, 0, 30)
                        for i,(cred,kind,agent) in enumerate(zip(self.creds,
                            ('AGENT','AGENT','HUMAN','AGENT'),
                            (self.scope.agent_instance_id,self.scope.agent_instance_id,None,'demo-other-agent')),1))
        p = self.w.latest
        self.root = RootPin(p.record_sha,p.key_sha,p.recovery_epoch)
        self.iam = D0SessionResolver.bootstrap_durable(self.w.path.with_name('owner.authority.sqlite'),
            self.root, records, domain='demo-memory-owner', clock=lambda:self.now)

    def resolve(self, i=0):
        return self.iam.resolve(self.creds[i], expected_scope=self.triple)

    def assert_memory_match_only(self):
        r = self.w.review()
        self.assertTrue(r.structural_match)
        self.assertEqual(r.reason, 'D0_WITNESSED_CONTEXT_MATCH_ONLY')
        self.assertEqual(r.decision, 'DENY')
        self.assertFalse(r.retrieval_allowed)
        self.assertFalse(r.dispatch_allowed)
        self.assertFalse(r.provider_call_allowed)
        self.assertFalse(r.release_allowed)

    def test_residual_same_principal_sessions_not_in_memory_binding(self):
        a,b = self.resolve(),self.resolve(1)
        self.assertIsNotNone(a); self.assertIsNotNone(b)
        self.assertNotEqual(a.session_id,b.session_id)
        self.assertEqual((a.principal_id,a.agent_instance_id),(b.principal_id,b.agent_instance_id))
        before = self.sql.f.binding
        self.assert_memory_match_only()
        self.assertEqual(binding_digest(self.sql.i,self.w.j.context,self.w.b.registry,self.w.latest),before)
        # Neither exact IAM session nor owner pin enters this original function's inputs.
        for cls in (Scope, MemoryWitness, MemoryAclView):
            self.assertNotIn('session_id',{f.name for f in fields(cls)})

    def test_residual_human_other_agent_not_authenticated_by_memory(self):
        human,other = self.resolve(2),self.resolve(3)
        self.assertEqual(human.kind,'HUMAN'); self.assertIsNone(human.agent_instance_id)
        self.assertNotEqual(other.agent_instance_id,self.scope.agent_instance_id)
        self.assert_memory_match_only()  # no IAM input; this is not a grant for either

    def test_residual_durable_revocation_not_seen_by_memory(self):
        a = self.resolve()
        before = (self.m.memory.read_bytes(),self.w.path.read_bytes())
        self.assertTrue(self.iam.revoke_local(a.session_id,expected_revision=a.revision))
        self.assertIsNone(self.resolve())
        self.assertNotEqual(self.resolve(1).revision,a.revision)
        self.assert_memory_match_only()
        self.assertEqual(before,(self.m.memory.read_bytes(),self.w.path.read_bytes()))

    def test_residual_iam_expiry_does_not_change_original_memory_review(self):
        a = self.resolve(); self.assertIsNotNone(a)
        self.now = a.expires
        self.assertIsNone(self.resolve())
        self.assert_memory_match_only()

    def test_residual_iam_revoke_during_original_sql_audit_not_seen(self):
        a = self.resolve()
        def fault(role):
            if role == 'AUDIT':
                self.assertTrue(self.iam.revoke_local(a.session_id,expected_revision=a.revision))
                self.assertIsNone(self.resolve())
        self.sql.execute(fault=fault)
        self.sql.exact_readback()
        self.assert_memory_match_only()
        # Only a synthetic local state transition, not G2's fenced path or any effect.

    def denied_snapshot(self):
        s = self.w.b.store.snapshot
        entries = tuple(replace(e,decision='DENY_READ') if e.node_id=='source' else e for e in s.acl.entries)
        return replace(s,acl=replace(s.acl,acl_revision=s.acl.acl_revision+1,entries=entries))

    def publish_denial(self):
        s = self.denied_snapshot()
        pending,pin = self.h.stage(s)
        self.assertEqual(publish_snapshot(self.m.memory,s,self.h.head.snapshot),pending.pending)
        ready = replace(pending,sequence=pending.sequence+1,previous_sha=pin.record_sha,snapshot=pending.pending,pending=None)
        self.h.latest = self.w.append(ready,pin.record_sha)
        self.h.head = ready
        self.h.pins.append(ready.snapshot)

    def test_protection_signed_acl_only_deny_with_active_iam_rolls_back(self):
        a = self.resolve()
        self.publish_denial(); self.m.bind_current()
        self.assertEqual(self.resolve(),a)
        self.assertEqual(self.w.review().reason,'MEMORY_ACL_DENY')
        self.m.rollback('MEMORY_ACL_DENY')

    def test_protection_signed_acl_only_deny_during_sql_audit_rolls_back(self):
        a = self.resolve()
        def fault(role):
            if role == 'AUDIT':
                self.publish_denial()
        self.m.rollback('MEMORY_WITNESS_READ_HOLD',fault=fault)
        self.m.bind_current()
        self.assertEqual(self.w.review().reason,'MEMORY_ACL_DENY')
        self.assertEqual(self.resolve(),a)

    def test_protection_task_run_agent_principal_drift_denied(self):
        for field,value in (('task_id','other-task'),('run_id','demo-other-run'),
                            ('agent_instance_id','demo-other-agent'),('principal_id','demo-other-principal')):
            with self.subTest(field=field):
                run=replace(self.w.b.f.run,scope=replace(self.scope,**{field:value}))
                self.assertEqual(self.w.review(current_run=run).reason,'MEMORY_WITNESS_CONTEXT_HOLD')


if __name__=='__main__':
    unittest.main(verbosity=2)
