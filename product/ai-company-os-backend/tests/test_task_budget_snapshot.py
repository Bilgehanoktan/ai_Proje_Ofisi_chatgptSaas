from contextlib import closing
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import os
import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.development_review.task_budget_snapshot import PLAN, _collect, new_pair_id, write_pair_marker
from app.api.task_budget_projection import router


class PairTests(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.w = Path(tmp.name)/'demo.workbench.d0.sqlite'
        self.a = Path(tmp.name)/'demo.admission.d0.sqlite'
        self.pair = new_pair_id()
        for p in (self.w,self.a):
            with closing(sqlite3.connect(p)) as db, db:
                write_pair_marker(db,self.pair)
        self.office = dict(tenant='synthetic-tenant',company='synthetic-company',plan_digest=PLAN,
                           sample_event_count=5,dispatch_allowed=False,provider_called=False,spend_allowed=False,release_ready=False)
        self.budget = dict(tenant='synthetic-tenant',company='synthetic-company',version=1,admission='DENY',
                           dispatch_allowed=False,spend_allowed=False,release_ready=False,authoritative=False)

    def read(self):
        return _collect(self.w,self.a,lambda _:dict(self.office),lambda _:dict(self.budget))

    def change(self, path, sql, args=()):
        with closing(sqlite3.connect(path)) as db, db: db.execute(sql,args)

    def test_stable_and_readonly(self):
        hashes = [sha256(p.read_bytes()).hexdigest() for p in (self.w,self.a)]
        r = self.read()
        self.assertEqual((r['pair_id'],r['research_event_seq'],r['admission_version']),(self.pair,3,1))
        self.assertEqual(r['consistency'],'STABLE_DOUBLE_READ_NOT_ATOMIC')
        self.assertEqual(r['causality'],'UNPROVEN')
        self.assertEqual(hashes,[sha256(p.read_bytes()).hexdigest() for p in (self.w,self.a)])
        self.assertFalse(r['dispatch_allowed'])

    def test_cross_pair(self):
        self.change(self.a,'UPDATE sample_pair SET pair_id=?',(new_pair_id(),))
        with self.assertRaisesRegex(ValueError,'MISMATCH'): self.read()

    def test_scope(self):
        self.change(self.a,"UPDATE sample_pair SET task_id='draft'")
        with self.assertRaisesRegex(ValueError,'SCOPE'): self.read()

    def test_legacy(self):
        self.change(self.a,'DROP TABLE sample_pair')
        with self.assertRaises(sqlite3.Error): self.read()

    def test_change_between_collects(self):
        values = iter([self.office,{**self.office,'sample_event_count':4}])
        with self.assertRaisesRegex(ValueError,'CHANGED'):
            _collect(self.w,self.a,lambda _:next(values),lambda _:self.budget)

    def test_false_authority(self):
        self.budget['spend_allowed'] = True
        with self.assertRaisesRegex(ValueError,'AUTHORITY'): self.read()

    def test_invalid_version(self):
        self.budget['version'] = True
        with self.assertRaisesRegex(ValueError,'VERSION'): self.read()

    def test_pending(self):
        self.office['sample_event_count'] = 2; self.budget['version'] = 0
        r = self.read()
        self.assertIsNone(r['research_event_seq']); self.assertIsNone(r['sample_admission_ref'])

    def test_marker_change_during_read(self):
        def change(_):
            self.change(self.a,'UPDATE sample_pair SET pair_id=?',(new_pair_id(),))
            return self.office
        with self.assertRaisesRegex(ValueError,'CHANGED'):
            _collect(self.w,self.a,change,lambda _:self.budget)

    def test_api_contract(self):
        app = FastAPI(); app.include_router(router); client = TestClient(app)
        url = '/demo/v1/task-budget/sample-projection'
        with patch.dict(os.environ,{'AICOS_D0_WORKBENCH_DB':str(self.w),'AICOS_D0_ADMISSION_DB':str(self.a)}), patch('app.api.task_budget_projection.read_task_budget_snapshot',side_effect=lambda *_:self.read()):
            r = client.get(url); self.assertEqual(r.status_code,200); self.assertEqual(r.headers['cache-control'],'no-store')
            self.assertEqual(client.post(url).status_code,405)
            self.change(self.a,'DELETE FROM sample_pair')
            self.assertEqual(client.get(url).status_code,503)
        with patch.dict(os.environ,{'AICOS_D0_WORKBENCH_DB':'','AICOS_D0_ADMISSION_DB':''}):
            self.assertEqual(client.get(url+'?path=other').status_code,503)
