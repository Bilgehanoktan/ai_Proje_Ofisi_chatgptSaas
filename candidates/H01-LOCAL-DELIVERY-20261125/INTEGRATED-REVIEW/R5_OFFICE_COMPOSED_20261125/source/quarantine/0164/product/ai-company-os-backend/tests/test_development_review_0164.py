"""Unexecuted candidate oracles; no real agents, filesystem or network."""
import unittest
from dataclasses import replace
from hashlib import sha256
from app.core.development_review.model import (
    FilePin, ReviewScope, PrincipalPin, ROLES, scope_digest, valid_scope)
from app.core.development_review.planner import compile_review, valid_plan
from app.core.development_review.policy import (
    ReviewRequest, FileReadback, inspect_request, inspect_patch_bytes, ACTIONS)
from app.core.development_review.evidence import (
    Observation, observation_digest, subject_digest, inspect_evidence)


def h(b):
    return sha256(b).hexdigest()


class DevelopmentReviewCandidateTests(unittest.TestCase):
    def setUp(self):
        self.path = 'app/core/development_review/model.py'
        self.scope = ReviewScope('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY',
                                 'review-1', 'a'*40, h(b'manifest'), 4, 7,
                                 (FilePin(self.path, None, h(b'new')),))
        self.roster = tuple(PrincipalPin(r, 'demo-p-'+r, 'demo-c-'+r, 'demo-e-'+r) for r in ROLES)
        self.plan = compile_review(self.scope, self.roster)
        self.request = ReviewRequest(scope_digest(self.scope), self.plan.plan_sha256, 'candidate',
                                     self.roster[2], ACTIONS['engineer'], self.scope.files, 4, 7)
        self.outputs = tuple(t.id.encode() for t in self.plan.tasks)
        seen = {}; rows = []
        for t, raw in zip(self.plan.tasks, self.outputs):
            actor = next(p for p in self.roster if p.role == t.role)
            o = Observation('e-'+t.id, scope_digest(self.scope), self.plan.plan_sha256, t.id, actor,
                            subject_digest(self.scope), tuple(seen[d] for d in t.depends_on),
                            h(raw), 4, 7, 'MATCH', '0'*64)
            o = replace(o, evidence_sha256=observation_digest(o))
            rows.append(o); seen[t.id] = o.evidence_sha256
        self.rows = tuple(rows)

    def policy(self, r=None, reference=None, revoked=False, pe=4, we=7):
        return inspect_request(r or self.request, self.scope, reference or self.scope, self.plan, revoked, pe, we)

    def evidence(self, rows=None, reference=None, pe=4, we=7, revoked=False, outputs=None):
        rows = self.rows if rows is None else rows
        return inspect_evidence(self.scope, self.scope, self.plan, rows,
                                rows if reference is None else reference, pe, we, revoked,
                                self.outputs if outputs is None else outputs)

    def test_plan_deterministic(self):
        self.assertEqual(self.plan, compile_review(self.scope, self.roster))

    def test_parallel_qa_security(self):
        self.assertEqual(self.plan.waves[3], ('quality', 'security'))
        self.assertEqual(self.plan.tasks[5].depends_on, ('quality', 'security'))

    def test_plan_tampered(self):
        self.assertFalse(valid_plan(replace(self.plan, tasks=self.plan.tasks[:-1]), self.scope))

    def test_shared_principal(self):
        r = list(self.roster); r[3] = replace(r[3], principal_id=r[2].principal_id)
        with self.assertRaises(ValueError): compile_review(self.scope, tuple(r))

    def test_shared_custody(self):
        r = list(self.roster); r[5] = replace(r[5], custody_id=r[2].custody_id)
        with self.assertRaises(ValueError): compile_review(self.scope, tuple(r))

    def test_shared_execution(self):
        r = list(self.roster); r[5] = replace(r[5], execution_id=r[2].execution_id)
        with self.assertRaises(ValueError): compile_review(self.scope, tuple(r))

    def test_path_traversal(self):
        self.assertFalse(valid_scope(replace(self.scope, files=(FilePin('../model.py', None, h(b'new')),))))

    def test_protected_path(self):
        self.assertFalse(valid_scope(replace(self.scope, files=(FilePin('app/core/policy/denial.py', None, h(b'new')),))))

    def test_duplicate_path(self):
        self.assertFalse(valid_scope(replace(self.scope, files=self.scope.files*2)))

    def test_cross_company(self):
        self.assertFalse(valid_scope(replace(self.scope, company_id='other')))

    def test_bool_epoch(self):
        self.assertFalse(valid_scope(replace(self.scope, policy_epoch=True)))

    def test_match_never_allow(self):
        result = self.policy(); self.assertTrue(result.structural_match)
        self.assertEqual(result.decision, 'HOLD'); self.assertFalse(result.source_write_allowed)
        self.assertFalse(result.dispatch_allowed); self.assertFalse(result.release_allowed)

    def test_reference_mismatch(self):
        self.assertEqual(self.policy(reference=replace(self.scope, review_id='other')).decision, 'DENY')

    def test_revoked(self):
        self.assertEqual(self.policy(revoked=True).decision, 'DENY')

    def test_unknown_revocation(self):
        self.assertEqual(self.policy(revoked=None).decision, 'DENY')

    def test_stale_witness(self):
        self.assertEqual(self.policy(we=8).decision, 'DENY')

    def test_self_approval(self):
        self.assertEqual(self.policy(replace(self.request, task_id='quality', action='QUALITY_REVIEW')).decision, 'DENY')

    def test_source_write_action(self):
        self.assertEqual(self.policy(replace(self.request, action='SOURCE_WRITE')).decision, 'DENY')

    def test_wrong_plan_digest(self):
        self.assertEqual(self.policy(replace(self.request, plan_sha256='f'*64)).decision, 'DENY')

    def test_wrong_file_digest(self):
        self.assertEqual(self.policy(replace(self.request, files=(FilePin(self.path,None,h(b'evil')),))).decision, 'DENY')

    def test_patch_match_no_write(self):
        r = inspect_patch_bytes(self.scope,self.scope,b'manifest',(FileReadback(self.path,None,b'new'),))
        self.assertTrue(r.structural_match); self.assertFalse(r.source_write_allowed)

    def test_patch_add_collision(self):
        r = inspect_patch_bytes(self.scope,self.scope,b'manifest',(FileReadback(self.path,b'old',b'new'),))
        self.assertEqual(r.reason,'PATCH_ADD_COLLISION')

    def test_patch_parent_mismatch(self):
        r = inspect_patch_bytes(self.scope,self.scope,b'other',(FileReadback(self.path,None,b'new'),))
        self.assertEqual(r.reason,'PARENT_MANIFEST_BYTES_MISMATCH')

    def test_patch_tampered_bytes(self):
        r = inspect_patch_bytes(self.scope,self.scope,b'manifest',(FileReadback(self.path,None,b'evil'),))
        self.assertEqual(r.reason,'PATCH_AFTER_BYTES_MISMATCH')

    def test_evidence_match_not_authoritative(self):
        r = self.evidence(); self.assertTrue(r.structural_match); self.assertEqual(r.observed_tasks,7)
        self.assertFalse(r.authoritative); self.assertFalse(r.write_allowed); self.assertFalse(r.release_allowed)

    def test_missing_evidence(self):
        self.assertFalse(self.evidence(self.rows[:-1]).structural_match)

    def test_evidence_reorder(self):
        self.assertFalse(self.evidence(tuple(reversed(self.rows))).structural_match)

    def test_evidence_duplicate_id(self):
        r=list(self.rows); o=replace(r[1],evidence_id=r[0].evidence_id)
        r[1]=replace(o,evidence_sha256=observation_digest(o))
        self.assertFalse(self.evidence(tuple(r)).structural_match)

    def test_evidence_causal_bypass(self):
        r=list(self.rows); o=replace(r[5],input_digests=(r[3].evidence_sha256,))
        r[5]=replace(o,evidence_sha256=observation_digest(o))
        self.assertFalse(self.evidence(tuple(r)).structural_match)

    def test_evidence_unknown(self):
        r=list(self.rows); o=replace(r[0],verdict='UNKNOWN'); r[0]=replace(o,evidence_sha256=observation_digest(o))
        self.assertEqual(self.evidence(tuple(r)).reason,'EVIDENCE_REJECT_OR_UNKNOWN_HOLD')

    def test_evidence_stale_epoch(self):
        self.assertFalse(self.evidence(pe=5).structural_match)

    def test_evidence_mismatched_reference(self):
        r=list(self.rows); r[0]=replace(r[0],output_sha256='f'*64)
        self.assertEqual(self.evidence(reference=tuple(r)).reason,'EVIDENCE_REFERENCE_MISMATCH')

    def test_evidence_output_bytes(self):
        self.assertEqual(self.evidence(outputs=(b'evil',)+self.outputs[1:]).reason,'EVIDENCE_OUTPUT_BYTES_HOLD')

    def test_evidence_unknown_revocation(self):
        self.assertFalse(self.evidence(revoked=None).structural_match)
