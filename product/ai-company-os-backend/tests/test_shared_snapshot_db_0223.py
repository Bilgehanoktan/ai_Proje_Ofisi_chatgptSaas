"""Actual persisted fixed-prefix -> existing router integration; no DB-reader mock."""
import hashlib
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_lifecycle_prefix_p03 import export_prefix_fixture
from app.api.lifecycle_prefix_projection import router
from app.core.development_review.shared_snapshot import build_shared_replay
from app.core.development_review.lifecycle_prefix_wire import prefix_wire


class SharedSnapshotDBTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name).resolve() / 'lifecycle-prefix.d0.sqlite'

    def read(self, **kwargs):
        with patch.dict(os.environ, {'AICOS_D0_LIFECYCLE_PREFIX_DB': str(self.path)}):
            return self.client.get('/demo/v1/lifecycle/shared-snapshot', **kwargs)

    def test_real_four_prefixes(self):
        for version in range(1, 5):
            with self.subTest(version=version):
                export_prefix_fixture(self.path, version)
                before = hashlib.sha256(self.path.read_bytes()).hexdigest()
                response = self.read()
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers['cache-control'], 'no-store')
                self.assertEqual(response.text, build_shared_replay(prefix_wire(version)))
                self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)
                self.path.unlink()

    def test_tampered_db_holds(self):
        export_prefix_fixture(self.path, 3)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE run_heads SET principal_id='forged' WHERE task_id='a'")
        self.assertEqual(self.read().status_code, 503)

    def test_missing_db_holds(self):
        self.assertEqual(self.read().status_code, 503)

    def test_resume_denied(self):
        export_prefix_fixture(self.path, 2)
        self.assertEqual(self.read(headers={'Last-Event-ID':'1'}).status_code,503)
