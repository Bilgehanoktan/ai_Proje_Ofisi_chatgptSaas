from contextlib import closing
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.development_review.office_workbench import read_office_workbench, _fixture, _digest, PLAN_DIGEST, PLAN_FILE, ORDER
from app.api.office_workbench_projection import router

# Exact schema from 0182 Workbench, fixture seeding is not writer execution.
DDL = """CREATE TABLE meta(profile TEXT PRIMARY KEY CHECK(profile='D0_WORKBENCH_0182'), tenant TEXT NOT NULL CHECK(tenant='synthetic-tenant'), company TEXT NOT NULL CHECK(company='synthetic-company'), plan_digest TEXT NOT NULL);
CREATE TABLE sample_task(id TEXT PRIMARY KEY, role TEXT NOT NULL, deps TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('PENDING','OBSERVED')), version INTEGER NOT NULL CHECK(version>=0));
CREATE TABLE sample_lease(task_id TEXT PRIMARY KEY REFERENCES sample_task(id), holder TEXT NOT NULL, fence INTEGER NOT NULL CHECK(fence>0), issued INTEGER NOT NULL CHECK(issued>=0), expires INTEGER NOT NULL CHECK(expires>issued));
CREATE TABLE sample_event(seq INTEGER PRIMARY KEY, command_id TEXT UNIQUE NOT NULL, request_sha TEXT NOT NULL, task_id TEXT NOT NULL REFERENCES sample_task(id), fence INTEGER NOT NULL, tick INTEGER NOT NULL, output_sha TEXT NOT NULL);"""


def seed(path, count):
    plan = _fixture('core.plan.projection.json',PLAN_FILE)
    observed = ORDER[:count]
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript(DDL)
        db.execute('INSERT INTO meta VALUES(?,?,?,?)',('D0_WORKBENCH_0182','synthetic-tenant','synthetic-company',PLAN_DIGEST))
        db.executemany('INSERT INTO sample_task VALUES(?,?,?,?,?)',[(t['id'],t['role'],json.dumps(t['depends_on']),'OBSERVED' if t['id'] in observed else 'PENDING',int(t['id'] in observed)) for t in plan['tasks']])
        for i,t in enumerate(observed,1):
            db.execute('INSERT INTO sample_lease VALUES(?,?,?,?,?)',(t,'demo-holder',1,i,i+10))
            db.execute('INSERT INTO sample_event VALUES(?,?,?,?,?,?,?)',(i,'demo-command-'+t,_digest([PLAN_DIGEST,t,'demo-holder',1,i]),t,1,i,_digest('Synthetic adapter review output; not a model response.')))


class OfficeWorkbenchTests(TestCase):
    def setUp(self):
        temp=TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/'workbench.d0.sqlite'
        app=FastAPI(); app.include_router(router); self.client=TestClient(app)

    def get(self):
        with patch.dict(os.environ,{'AICOS_D0_WORKBENCH_DB':str(self.path)}):
            return self.client.get('/demo/v1/office/workbench-projection')

    def test_all_six_prefixes(self):
        for n in range(6):
            with self.subTest(n=n):
                self.path.unlink(missing_ok=True); seed(self.path,n)
                x=read_office_workbench(self.path)
                self.assertEqual(x['sample_event_count'],n)
                self.assertEqual([r['observed'] for r in x['roles']],[int(n>=1),int(n>=3),int(n>=2)+int(n>=4),int(n>=5)])
                self.assertEqual([r['total'] for r in x['roles']],[1,1,2,1])
                self.assertEqual(x['iv'],'HOLD'); self.assertEqual(x['release'],'HOLD')
                self.assertEqual(x['geometry_join'],'HOLD'); self.assertIsNone(x['real_run_count'])
                for k in ('dispatch_allowed','provider_called','spend_allowed','release_ready'): self.assertIs(x[k],False)

    def tamper(self, sql):
        seed(self.path,5)
        with closing(sqlite3.connect(self.path)) as db, db: db.execute(sql)
        self.assertEqual(self.get().status_code,503)

    def test_scope(self): self.tamper("UPDATE meta SET plan_digest='other'")
    def test_task_role(self): self.tamper("UPDATE sample_task SET role='qa' WHERE id='research'")
    def test_dependency(self): self.tamper("UPDATE sample_task SET deps='[]' WHERE id='merge'")
    def test_task_state(self): self.tamper("UPDATE sample_task SET state='OBSERVED',version=1 WHERE id='iv'")
    def test_event_hash(self): self.tamper("UPDATE sample_event SET output_sha='wrong' WHERE seq=1")
    def test_request_hash(self): self.tamper("UPDATE sample_event SET request_sha='wrong' WHERE seq=1")
    def test_event_sequence(self): self.tamper("UPDATE sample_event SET seq=6 WHERE seq=1")
    def test_lease_fence(self): self.tamper("UPDATE sample_lease SET fence=2 WHERE task_id='plan'")
    def test_lease_owner(self): self.tamper("UPDATE sample_lease SET holder='demo-other' WHERE task_id='plan'")
    def test_missing(self):
        self.assertEqual(self.get().status_code,503); self.assertFalse(self.path.exists())
    def test_readonly(self):
        seed(self.path,5); before=sha256(self.path.read_bytes()).hexdigest()
        r=self.get(); self.assertEqual(r.status_code,200); self.assertEqual(r.headers['cache-control'],'no-store')
        self.assertEqual(r.json(),read_office_workbench(self.path)); self.assertEqual(sha256(self.path.read_bytes()).hexdigest(),before)
        self.assertEqual(self.client.post('/demo/v1/office/workbench-projection').status_code,405)
    def test_wrong_profile(self):
        with closing(sqlite3.connect(self.path)) as db,db: db.execute('CREATE TABLE other(id)')
        self.assertEqual(self.get().status_code,503)
    def test_symlink(self):
        target=self.path.with_name('target.d0.sqlite'); seed(target,1); self.path.symlink_to(target)
        self.assertEqual(self.get().status_code,503)
    def test_schema(self):
        from jsonschema import Draft202012Validator
        root=Path(__file__).resolve().parents[1]
        schema=root/'contracts/source/office.workbench.projection.schema.json'
        self.assertEqual(schema.read_bytes(),(root.parent/'ai-company-os-frontend/contracts/generated/office.workbench.projection.schema.json').read_bytes())
        v=Draft202012Validator(json.loads(schema.read_text()))
        for n in range(6):
            self.path.unlink(missing_ok=True); seed(self.path,n); x=read_office_workbench(self.path); v.validate(x)
            self.assertFalse(v.is_valid({**x,'dispatch_allowed':True}))
            self.assertFalse(v.is_valid({**x,'sample_event_count':6}))

    def test_shared_vectors(self):
        from jsonschema import Draft202012Validator
        root=Path(__file__).resolve().parents[1]
        v=Draft202012Validator(json.loads((root/'contracts/source/office.workbench.projection.schema.json').read_text()))
        for c in json.loads((root/'tests/office_workbench_cases.json').read_text()):
            with self.subTest(c=c['name']): self.assertEqual(v.is_valid(c['body']),c['valid'])
