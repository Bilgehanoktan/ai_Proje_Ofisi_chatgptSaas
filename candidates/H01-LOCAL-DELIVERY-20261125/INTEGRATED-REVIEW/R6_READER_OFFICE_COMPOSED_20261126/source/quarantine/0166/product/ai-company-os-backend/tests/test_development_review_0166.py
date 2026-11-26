"""Unexecuted candidate tests; no actual trust root, database or external effect."""
import unittest
from dataclasses import replace, asdict
from hashlib import sha256
from app.core.development_review.model import FilePin, ReviewScope, PrincipalPin, ROLES, digest, scope_digest
from app.core.development_review.planner import compile_review
from app.core.development_review.identity_registry import RegistrySnapshot, registry_digest
from app.core.development_review.trusted_policy import PolicySnapshot, policy_digest
from app.core.development_review.trust_boundary import TrustPin, trust_digest, inspect_trust
from app.core.development_review.staging_readback import ReplayPin, BatchPin, expected_rows, inspect_batch
from app.core.development_review.evidence import Observation, observation_digest, subject_digest
from app.core.development_review.policy import FileReadback
from app.core.development_review.coordination_readback import inspect_readback, project_readback


def h(b):
    return sha256(b).hexdigest()


class ReadbackCandidateTests(unittest.TestCase):
    def setUp(self):
        self.manifest, self.source, self.schema = b'manifest', b'new', b'ddl-candidate'
        self.scope = ReviewScope('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY',
            'review-166', 'a'*40, h(self.manifest), 4, 7,
            (FilePin('app/core/development_review/model.py', None, h(self.source)),))
        self.roster = tuple(PrincipalPin(r, 'demo-p-'+r, 'demo-c-'+r, 'demo-e-'+r) for r in ROLES)
        self.plan = compile_review(self.scope, self.roster)
        self.registry = RegistrySnapshot(scope_digest(self.scope), 1, 'demo-owner', 'demo-root', self.roster, 4, 7)
        self.policy = PolicySnapshot(scope_digest(self.scope), self.plan.plan_sha256, registry_digest(self.registry),
                                     1, 'demo-owner', 'demo-root', 4, 7, 10, 20, False)
        self.trust = TrustPin(scope_digest(self.scope), self.plan.plan_sha256, registry_digest(self.registry),
                            policy_digest(self.policy), 'demo-owner', 'demo-root', 'demo-key', 1, 4, 7, 11, 'd'*64, 11)
        self.outputs = tuple(t.id.encode() for t in self.plan.tasks)
        seen, obs = {}, []
        for t, raw in zip(self.plan.tasks, self.outputs):
            actor = next(p for p in self.roster if p.role == t.role)
            o = Observation('e-'+t.id, scope_digest(self.scope), self.plan.plan_sha256, t.id, actor,
                subject_digest(self.scope), tuple(seen[d] for d in t.depends_on), h(raw), 4, 7, 'MATCH', '0'*64)
            o = replace(o, evidence_sha256=observation_digest(o)); obs.append(o); seen[t.id] = o.evidence_sha256
        self.obs = tuple(obs)
        self.rows = expected_rows(self.scope, self.plan, self.obs)
        self.replay = tuple(sorted((ReplayPin(o.evidence_id, scope_digest(self.scope), o.evidence_sha256)
                                     for o in self.obs), key=lambda r: r.evidence_id))
        self.batch = BatchPin(trust_digest(self.trust), scope_digest(self.scope), self.plan.plan_sha256,
            policy_digest(self.policy), h(self.schema), 7, 11, 'd'*64, 12, self.rows[-1].entry_sha,
            digest([asdict(r) for r in self.replay]))

    def trust_review(self, pin=None, ref=None, now=12, revoked=False):
        pin = self.trust if pin is None else pin
        ref = pin if ref is None else ref
        return inspect_trust(pin, ref, trust_digest(pin), self.scope, self.plan, self.registry, self.registry,
                             self.policy, self.policy, now, 2, 4, 7, revoked)

    def batch_review(self, pin=None, rows=None, replay=None, schema=None):
        pin = self.batch if pin is None else pin
        return inspect_batch(self.scope, self.scope, self.plan, self.obs, self.obs, self.outputs, self.trust,
            pin, pin, self.rows if rows is None else rows, self.schema if schema is None else schema,
            h(self.schema), self.replay if replay is None else replay, self.replay, 4, 7, False)

    def coord(self, rows=None):
        return inspect_readback(self.scope, self.scope, self.plan, self.registry, self.registry,
            self.policy, self.policy, self.trust, self.trust, trust_digest(self.trust), 12, 2, 4, 7, False,
            self.manifest, (FileReadback(self.scope.files[0].path, None, self.source),), self.obs, self.obs,
            self.outputs, self.batch, self.batch, self.rows if rows is None else rows,
            self.schema, h(self.schema), self.replay, self.replay)

    def test_trust_match_never_authenticates(self):
        r = self.trust_review(); self.assertTrue(r.structural_match); self.assertFalse(r.authenticated)
        self.assertFalse(r.grant_allowed)

    def test_trust_stale(self):
        self.assertEqual(self.trust_review(now=14).reason, 'TRUST_FRESHNESS_HOLD')

    def test_trust_future(self):
        self.assertEqual(self.trust_review(now=10).reason, 'TRUST_FRESHNESS_HOLD')

    def test_trust_reference(self):
        self.assertEqual(self.trust_review(ref=replace(self.trust, key_revision=2)).reason, 'TRUST_REFERENCE_HOLD')

    def test_trust_wrong_issuer(self):
        self.assertEqual(self.trust_review(pin=replace(self.trust, issuer='demo-other')).reason, 'TRUST_ISSUER_REGISTRY_HOLD')

    def test_trust_revocation_unknown(self):
        self.assertEqual(self.trust_review(revoked=None).reason, 'POLICY_INVALID_OR_REVOKED')

    def test_batch_match_no_authority(self):
        r = self.batch_review(); self.assertTrue(r.structural_match); self.assertFalse(r.authoritative)
        self.assertFalse(r.write_allowed)

    def test_batch_restore_head(self):
        self.assertEqual(self.batch_review(pin=replace(self.batch, previous_head='f'*64)).reason, 'BATCH_RESTORE_OR_SEQUENCE_HOLD')

    def test_batch_replay_sequence(self):
        self.assertEqual(self.batch_review(pin=replace(self.batch, sequence=11)).reason, 'BATCH_RESTORE_OR_SEQUENCE_HOLD')

    def test_batch_policy_mismatch(self):
        self.assertEqual(self.batch_review(pin=replace(self.batch, policy_sha='f'*64)).reason, 'BATCH_SCOPE_EPOCH_HOLD')

    def test_batch_schema_tamper(self):
        self.assertEqual(self.batch_review(schema=b'altered').reason, 'BATCH_SCHEMA_HOLD')

    def test_batch_row_missing(self):
        self.assertEqual(self.batch_review(rows=self.rows[:-1]).reason, 'BATCH_ROW_READBACK_HOLD')

    def test_batch_row_tamper(self):
        self.assertEqual(self.batch_review(rows=(replace(self.rows[0], body='evil'),)+self.rows[1:]).reason, 'BATCH_ROW_READBACK_HOLD')

    def test_batch_cross_scope_replay(self):
        self.assertEqual(self.batch_review(replay=(replace(self.replay[0], scope_sha='f'*64),)+self.replay[1:]).reason, 'BATCH_REPLAY_INDEX_HOLD')

    def test_coordinator_complete_no_write(self):
        r = self.coord(); self.assertEqual(r.matched, ('trust-shape', 'patch-shape', 'staging-shape'))
        self.assertFalse(r.source_write_allowed); self.assertFalse(r.dispatch_allowed); self.assertFalse(r.release_allowed)

    def test_coordinator_requires_staging(self):
        self.assertEqual(self.coord(rows=()).matched, ('trust-shape', 'patch-shape'))

    def test_projection_never_pass(self):
        p = project_readback(self.coord()); self.assertEqual(p['decision'], 'HOLD')
        self.assertEqual(p['runtime'], 'NOT_RUN'); self.assertIsNone(p['actual_agent_count'])
