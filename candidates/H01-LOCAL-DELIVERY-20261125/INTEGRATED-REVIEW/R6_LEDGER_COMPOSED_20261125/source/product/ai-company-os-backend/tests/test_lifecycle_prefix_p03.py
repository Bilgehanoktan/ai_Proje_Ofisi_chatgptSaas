"""Prepared 0196-L persisted fixture integration tests, not real PostgreSQL."""
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
from app.core.development_review.lifecycle_prefix_projection import read_lifecycle_prefix
from app.core.development_review.lifecycle_prefix_wire import prefix_wire
from app.api.lifecycle_prefix_projection import lifecycle_prefix_projection

def export_prefix(f,path,version):
    prefix_wire(version)
    if version>=2:
        running=f.running()
    if version>=3:
        s=f.renewal(running);r=f.execute(s)
        running=replace(running,version=r.committed_version)
    if version>=4:
        f.ordinary(running,s.renewal,RunState.VERIFYING)
    with open(f.path,'rb') as source,open(path,'xb') as destination:
        shutil.copyfileobj(source,destination)

def export_prefix_fixture(path,version=3):
    p=Path(path)
    if not p.is_absolute() or p.resolve()!=p or p.name!='lifecycle-prefix.d0.sqlite' or p.exists() or not p.parent.is_dir():
        raise ValueError('D0_PREFIX_EXPORT_PATH_HOLD')
    fixture=lifecycle.LifecycleTests()
    try:
        fixture.setUp()
        export_prefix(fixture,p,version)
        read_lifecycle_prefix(p)
    finally:fixture.doCleanups()

class PrefixProjectionTests(unittest.TestCase):
    def sample(self,v=3):
        f=lifecycle.LifecycleTests();f.setUp();self.addCleanup(f.doCleanups)
        p=Path(f.path).with_name('lifecycle-prefix.d0.sqlite').resolve()
        export_prefix(f,p,v);return p
    def change(self,p,sql):
        with closing(sqlite3.connect(p)) as db,db:db.execute(sql)
    def test_all_four(self):
        for v in range(1,5):
            with self.subTest(v=v):
                p=self.sample(v);before=hashlib.sha256(p.read_bytes()).hexdigest()
                self.assertEqual(read_lifecycle_prefix(p),prefix_wire(v))
                self.assertEqual(before,hashlib.sha256(p.read_bytes()).hexdigest())
    def test_scope_tamper(self):
        p=self.sample();self.change(p,"UPDATE run_heads SET principal_id='demo-forged' WHERE task_id='a'")
        with self.assertRaises(ValueError):read_lifecycle_prefix(p)
    def test_audit_tamper(self):
        p=self.sample();self.change(p,"UPDATE run_audit SET lease_digest='forged' WHERE version=2")
        with self.assertRaises(ValueError):read_lifecycle_prefix(p)
    def test_budget_tamper(self):
        p=self.sample();self.change(p,"UPDATE sample_budgets SET outstanding_minor=19")
        with self.assertRaises(ValueError):read_lifecycle_prefix(p)
    def test_lease_tamper(self):
        p=self.sample();self.change(p,"UPDATE run_leases SET heartbeat_tick=12")
        with self.assertRaises(ValueError):read_lifecycle_prefix(p)
    def test_terminal_not_prefix(self):
        p=self.sample();self.change(p,"UPDATE run_heads SET version=5,state='FAILED' WHERE task_id='a'")
        with self.assertRaises(ValueError):read_lifecycle_prefix(p)
    def test_api(self):
        p=self.sample()
        with patch.dict(os.environ,{'AICOS_D0_LIFECYCLE_PREFIX_DB':str(p)}):
            x=lifecycle_prefix_projection()
        self.assertEqual(x.status_code,200);self.assertEqual(json.loads(x.body),prefix_wire(3))
        self.assertEqual(x.headers['cache-control'],'no-store')
    def test_missing(self):
        with patch.dict(os.environ,{'AICOS_D0_LIFECYCLE_PREFIX_DB':''}):
            self.assertEqual(lifecycle_prefix_projection().status_code,503)
    def test_vectors(self):
        cases=json.loads(Path(__file__).with_name('lifecycle_prefix_cases.json').read_text(encoding='utf-8'))
        self.assertEqual(cases,[prefix_wire(v) for v in range(1,5)])
