from contextlib import closing
import hashlib
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.outbox_projection import router
from app.core.development_review.outbox_claim_sample import OutboxReviewSample


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'sample.review.atomic.d0.sqlite'
        self.store=OutboxReviewSample(self.path)
        self.store.create()
        app=FastAPI()
        app.include_router(router)
        self.client=TestClient(app)
        self.url='/demo/v1/outbox/review-projection'

    def read(self):
        with patch.dict(os.environ,{'AICOS_D0_REVIEW_DB':str(self.path)}): return self.client.get(self.url)

    def observe(self):
        self.store.renew('demo-owner',None,1,5)
        self.store.observe('demo-command','demo-owner',1,2,0)

    def test_no_configuration(self):
        with patch.dict(os.environ,{'AICOS_D0_REVIEW_DB':''}):
            self.assertEqual(self.client.get(self.url+'?path='+str(self.path)).status_code,503)

    def test_unobserved_hold(self): self.assertEqual(self.read().status_code,503)

    def test_lifecycle_and_readonly(self):
        self.observe()
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        r=self.read()
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.headers['cache-control'],'no-store')
        self.assertEqual(r.json()['phase'],'LOCAL_HOLD')
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)
        self.store.claim_review('demo-command','demo-reviewer',3,5)
        self.assertEqual(self.read().json()['phase'],'CLAIMED')
        self.store.mark_unknown('demo-command','demo-reviewer',1,4)
        self.assertEqual(self.read().json()['phase'],'UNKNOWN_HOLD')
        self.store.record_readback('demo-command',1,'a'*64)
        body=self.read().json()
        self.assertEqual(body['phase'],'READBACK_HOLD')
        self.assertTrue(body['readback_recorded'])
        self.assertNotIn('readback_sha',body)
        self.assertNotIn('reviewer',body)
        for k in ['dispatch_allowed','retry_allowed','reconciled','provider_called','release_ready']: self.assertIs(body[k],False)

    def test_missing_db_no_creation(self):
        self.path.unlink()
        self.assertEqual(self.read().status_code,503)
        self.assertFalse(self.path.exists())

    def test_no_mutation_routes(self):
        self.assertEqual(self.client.post(self.url).status_code,405)

    def test_wrong_profile_hold(self):
        import sqlite3
        self.observe()
        with closing(sqlite3.connect(self.path)) as db, db: db.execute('DELETE FROM meta')
        self.assertEqual(self.read().status_code,503)
