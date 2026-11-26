"""Actual disposable 0196-L fixture regression; no PG or real authority."""
import hashlib
import json
import os
import shutil
import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import test_lifecycle_mapping_0196 as lifecycle
from app.core.agent_runtime.lifecycle import RunState
from app.core.development_review.lifecycle_projection import read_lifecycle_projection
from app.api.lifecycle_projection import lifecycle_projection

def export_sample(f,path):
    running=f.running();s=f.renewal(running);r=f.execute(s)
    running=replace(running,version=r.committed_version)
    verifying=f.ordinary(running,s.renewal,RunState.VERIFYING)
    terminal=f.failure(replace(running,state=RunState.VERIFYING,version=verifying.committed_version),s.renewal,replace(f.budget,revision=2))
    f.execute(terminal)
    with open(f.path,'rb') as source,open(path,'xb') as destination:
        shutil.copyfileobj(source,destination)

class LifecycleProjectionTests(unittest.TestCase):
    def setUp(self):
        f=lifecycle.LifecycleTests();f.setUp();self.addCleanup(f.doCleanups)
        self.path=Path(f.path).with_name('lifecycle.d0.sqlite').resolve()
        export_sample(f,self.path)
    def change(self,sql):
        with closing(sqlite3.connect(self.path)) as db,db: db.execute(sql)
    def test_exact_terminal_readback_unchanged(self):
        digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
        x=read_lifecycle_projection(self.path)
        self.assertEqual((x['state'],x['head_version'],x['sample_released_minor']),('FAILED',5,20))
        self.assertFalse(x['authoritative']);self.assertFalse(x['dispatch_allowed'])
        self.assertEqual(digest,hashlib.sha256(self.path.read_bytes()).hexdigest())
    def test_ordinary_history_tamper(self):
        self.change("UPDATE run_audit SET lease_digest='forged' WHERE version=2")
        with self.assertRaises(ValueError):read_lifecycle_projection(self.path)
    def test_renewal_history_tamper(self):
        self.change("UPDATE run_lease_renewals SET request_digest='forged'")
        with self.assertRaises(ValueError):read_lifecycle_projection(self.path)
    def test_terminal_tamper(self):
        self.change("UPDATE sample_settlements SET released_minor=19")
        with self.assertRaises(ValueError):read_lifecycle_projection(self.path)
    def test_wrong_head(self):
        self.change("UPDATE run_heads SET state='RUNNING' WHERE task_id='a'")
        with self.assertRaises(ValueError):read_lifecycle_projection(self.path)
    def test_api_exact(self):
        with patch.dict(os.environ,{'AICOS_D0_LIFECYCLE_DB':str(self.path)}):
            response=lifecycle_projection()
        self.assertEqual(response.status_code,200)
        self.assertEqual(json.loads(response.body),read_lifecycle_projection(self.path))
        self.assertEqual(response.headers['cache-control'],'no-store')
    def test_missing_api_hold(self):
        with patch.dict(os.environ,{'AICOS_D0_LIFECYCLE_DB':''}):
            self.assertEqual(lifecycle_projection().status_code,503)
    def test_wrong_file_hold(self):
        with self.assertRaises(ValueError):read_lifecycle_projection(self.path.with_name('wrong.d0.sqlite'))

def export_fixture(path):
    """Explicit test-only fixture exporter, never called by GET handlers."""
    p=Path(path)
    if not p.is_absolute() or p.resolve()!=p or p.name!='lifecycle.d0.sqlite' or p.exists() or not p.parent.is_dir():
        raise ValueError('D0_LIFECYCLE_EXPORT_PATH_HOLD')
    fixture=lifecycle.LifecycleTests()
    try:
        fixture.setUp()
        export_sample(fixture,p)
        read_lifecycle_projection(p)
    finally:
        fixture.doCleanups()
