"""Candidate oracles only; not executed."""
import unittest
from dataclasses import replace
from app.core.development_review.identity_registry import RegistrySnapshot, registry_digest, inspect_registry
from app.core.development_review.trusted_policy import PolicySnapshot, policy_digest, inspect_policy
from app.core.development_review.coordinator import CoordinationReview, inspect_coordination
from app.core.development_review.evidence import Observation, subject_digest, observation_digest
from app.core.development_review.policy import FileReadback
from app.core.development_review.evidence_store import initialize_staging, stage_batch, inspect_staged
from hashlib import sha256
import sqlite3
from contextlib import closing
from app.core.development_review.model import FilePin, ReviewScope, PrincipalPin, ROLES, scope_digest
from app.core.development_review.planner import compile_review

class RegistryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.scope = ReviewScope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','demo-review','a'*40,'b'*64,4,7,(FilePin('app/core/development_review/model.py',None,'c'*64),))
        self.roster = tuple(PrincipalPin(r,'demo-p-'+r,'demo-c-'+r,'demo-e-'+r) for r in ROLES)
        self.plan = compile_review(self.scope,self.roster)
        self.registry = RegistrySnapshot(scope_digest(self.scope),1,'demo-owner','demo-owner-custody',self.roster,4,7)
        self.policy = PolicySnapshot(scope_digest(self.scope),self.plan.plan_sha256,registry_digest(self.registry),1,'demo-owner','demo-owner-custody',4,7,10,20,False)

        self.manifest = b'manifest'
        self.new = b'candidate'
        self.scope = replace(self.scope,parent_manifest_sha256=sha256(self.manifest).hexdigest(),files=(FilePin('app/core/development_review/model.py',None,sha256(self.new).hexdigest()),))
        self.plan = compile_review(self.scope,self.roster)
        self.registry = replace(self.registry,scope_sha256=scope_digest(self.scope))
        self.policy = replace(self.policy,scope_sha256=scope_digest(self.scope),plan_sha256=self.plan.plan_sha256,registry_sha256=registry_digest(self.registry))
        self.outputs=tuple(t.id.encode() for t in self.plan.tasks)
        seen={}; rows=[]
        for t,raw in zip(self.plan.tasks,self.outputs):
            actor=next(p for p in self.roster if p.role==t.role)
            o=Observation('e-'+t.id,scope_digest(self.scope),self.plan.plan_sha256,t.id,actor,subject_digest(self.scope),tuple(seen[d] for d in t.depends_on),sha256(raw).hexdigest(),4,7,'MATCH','0'*64)
            o=replace(o,evidence_sha256=observation_digest(o)); rows.append(o); seen[t.id]=o.evidence_sha256
        self.rows=tuple(rows)

    def inspect(self,p=None,now=12,revoked=False):
        p = self.policy if p is None else p
        return inspect_policy(p,p,policy_digest(p),self.registry,self.registry,self.scope,self.plan,now,4,7,revoked)

    def test_registry_match(self):
        self.assertTrue(inspect_registry(self.registry,self.registry,registry_digest(self.registry),self.scope))

    def test_registry_wrong_digest(self):
        self.assertFalse(inspect_registry(self.registry,self.registry,'0'*64,self.scope))

    def test_registry_issuer_is_producer(self):
        r=replace(self.registry,issuer=self.roster[2].principal_id)
        self.assertFalse(inspect_registry(r,r,registry_digest(r),self.scope))

    def test_registry_shared_custody(self):
        r=replace(self.registry,issuer_custody=self.roster[5].custody_id)
        self.assertFalse(inspect_registry(r,r,registry_digest(r),self.scope))

    def test_policy_match_only(self):
        self.assertEqual(self.inspect(),'D0_POLICY_MATCH_ONLY')

    def test_policy_expired(self):
        self.assertEqual(self.inspect(now=20),'POLICY_PIN_TIME_EPOCH_MISMATCH')

    def test_policy_not_yet_valid(self):
        self.assertEqual(self.inspect(now=9),'POLICY_PIN_TIME_EPOCH_MISMATCH')

    def test_revocation_unknown(self):
        self.assertEqual(self.inspect(revoked=None),'POLICY_INVALID_OR_REVOKED')

    def test_policy_registry_pin(self):
        self.assertEqual(self.inspect(replace(self.policy,registry_sha256='0'*64)),'REGISTRY_PIN_HOLD')

    def test_policy_issuer_mismatch(self):
        self.assertEqual(self.inspect(replace(self.policy,issuer='demo-other')),'POLICY_REGISTRY_SOD_HOLD')

    def test_coordinator_no_effect_flags(self):
        r=CoordinationReview('D0_REVIEW_MATCH_NO_AUTHORITY',('policy','patch','evidence'))
        self.assertEqual(r.decision,'HOLD'); self.assertFalse(r.source_write_allowed)
        self.assertFalse(r.dispatch_allowed); self.assertFalse(r.release_allowed)

    def coord(self, data=None):
        return inspect_coordination(self.scope,self.scope,self.plan,self.registry,self.registry,self.policy,self.policy,policy_digest(self.policy),12,4,7,False,self.manifest,(FileReadback(self.scope.files[0].path,None,self.new if data is None else data),),self.rows,self.rows,self.outputs)

    def test_coordinator_chain(self):
        self.assertEqual(self.coord().matched_steps,('policy','patch','evidence'))
        self.assertFalse(self.coord().source_write_allowed)

    def test_coordinator_patch_tamper(self):
        self.assertEqual(self.coord(b'wrong').reason,'PATCH_AFTER_BYTES_MISMATCH')

    def stage(self,db,rows=None):
        rows=self.rows if rows is None else rows
        return stage_batch(db,self.scope,self.scope,self.plan,rows,rows,self.outputs,4,7,False)

    def readback(self,db):
        return inspect_staged(db,self.scope,self.scope,self.plan,self.rows,self.rows,self.outputs,4,7,False)

    def test_staging_complete_readback(self):
        with closing(sqlite3.connect(':memory:')) as db, db:
            initialize_staging(db)
            self.assertEqual(self.stage(db),'D0_BATCH_STAGED_NOT_AUTHORITY')
            self.assertEqual(self.readback(db),'D0_STAGING_READBACK_MATCH_ONLY')

    def test_staging_duplicate(self):
        with closing(sqlite3.connect(':memory:')) as db, db:
            initialize_staging(db); self.stage(db)
            self.assertEqual(self.stage(db),'STAGING_DUPLICATE_HOLD')

    def test_staging_reject_incomplete(self):
        with closing(sqlite3.connect(':memory:')) as db, db:
            initialize_staging(db)
            self.assertEqual(self.stage(db,self.rows[:-1]),'STAGING_HOLD')
            self.assertEqual(self.readback(db),'STAGING_INCOMPLETE_HOLD')

    def test_staging_update_denied(self):
        with closing(sqlite3.connect(':memory:')) as db, db:
            initialize_staging(db); self.stage(db)
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('UPDATE development_evidence_d0 SET body=?',('tampered',))

    def test_staging_delete_denied(self):
        with closing(sqlite3.connect(':memory:')) as db, db:
            initialize_staging(db); self.stage(db)
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('DELETE FROM development_evidence_d0')
