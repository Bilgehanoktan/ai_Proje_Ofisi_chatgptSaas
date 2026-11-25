"""Actual original D0 writers -> fixed historical reader -> mounted FastAPI routes.
No live grants, full ASGI app, PostgreSQL, or browser acceptance.
"""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.agent_runtime.lifecycle import ClockSample, RunState
from app.core.orchestrator.engine import canonical_plan
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction
from app.core.transaction.postgres_admission_mapping import D0PostgresAdmissionMapping
from app.core.transaction.postgres_lifecycle_mapping import (D0AdmissionBoundTransitionMapping,
    D0PostgresLifecycleMapping, LifecycleSpec)
from app.core.development_review.lifecycle_projection import fixed_chain, read_lifecycle_projection
from app.core.development_review.lifecycle_prefix_projection import read_lifecycle_prefix
from app.core.development_review.lifecycle_prefix_wire import prefix_wire
from app.core.development_review.shared_snapshot import build_shared_replay
from app.api.lifecycle_prefix_projection import router
from test_research_t1_integration_0225 import SQLiteConnection
from test_research_company_snapshot_0224 import ROOT, SQL

# Same canonical historical fixture as 0194; never join it to Research UI plan.
PLAN={'id':'plan','worktype':'RESEARCH','tasks':[
    {'id':'a','label':'Plan','role':'orchestrator','depends_on':[]},
    {'id':'b','label':'Research','role':'research','depends_on':['a']},
    {'id':'c','label':'Engineer','role':'engineer','depends_on':['a']},
    {'id':'q','label':'QA','role':'qa','depends_on':['b','c']},
    {'id':'v','label':'IV','role':'independent-verifier','depends_on':['q']},
    {'id':'h','label':'H01','role':'human-authority','depends_on':['v']}]}


def write_fixture(path, version):
    if not 1<=version<=5 or path.exists(): raise ValueError('D0_FIXTURE_HOLD')
    terminal,_,chain=fixed_chain(); binding=terminal.binding; claim=binding.claim
    assert canonical_plan(PLAN)['revision']==claim.before.scope.plan_revision
    s=claim.before.scope; b=claim.budget; l=claim.lease
    with closing(sqlite3.connect(path)) as db,db:
        db.execute('PRAGMA foreign_keys=ON')
        for p in SQL[:5]:
            db.executescript((ROOT/'database'/p).read_text().replace('CREATE SCHEMA t1_candidate;','').replace('t1_candidate.',''))
        for t in 'abcq':
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',(s.tenant_id,s.company_id,s.environment_id,
                s.plan_revision,t,'demo-'+t,s.agent_instance_id,s.principal_id,'QUEUED',0,0))
        db.execute('INSERT INTO sample_budgets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(s.tenant_id,s.company_id,s.environment_id,
            b.budget_id,b.revision,b.currency,b.limit_minor,b.outstanding_minor,b.recognized_cost_minor,b.unknown_cost,b.policy_epoch,b.witness_epoch,b.source_digest))
    before=claim.before
    for idx,(intent,kind,_,after,lease) in enumerate(chain[:version]):
        clock=lambda:ClockSample(10 if idx==0 else 11,2,3,5)
        if idx==0:
            m=D0PostgresAdmissionMapping(PLAN,claim,clock)
        elif idx==2:
            m=D0PostgresLifecycleMapping(LifecycleSpec(before,l,binding,replace(b,revision=1,outstanding_minor=20),lease),clock)
        elif idx==4:
            m=D0PostgresLifecycleMapping(terminal,clock)
        else:
            m=D0AdmissionBoundTransitionMapping(binding,lease,clock)
        c=LogicalT1Coordinator(lambda:postgres_transaction(lambda:SQLiteConnection(path),m))
        receipt=c.commit_transition(intent,before,RunState(after)) if idx in (1,3) else c.commit(intent)
        assert receipt.committed_version==idx+1
        before=replace(before,state=RunState(after),version=receipt.committed_version)
    return path


def make_app():
    app=FastAPI();app.include_router(router);return app


class LifecycleDBHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name).resolve()/'lifecycle-prefix.d0.sqlite'
        self.client=TestClient(make_app());self.addCleanup(self.client.close)
    def request(self,**kwargs):
        with patch.dict(os.environ,{'AICOS_D0_LIFECYCLE_PREFIX_DB':str(self.path)}):
            return self.client.get('/demo/v1/lifecycle/shared-snapshot',**kwargs)
    def test_all_four_real_writer_prefixes(self):
        for v in range(1,5):
            with self.subTest(version=v):
                write_fixture(self.path,v); old=sha256(self.path.read_bytes()).hexdigest()
                self.assertEqual(read_lifecycle_prefix(self.path),prefix_wire(v))
                r=self.request();self.assertEqual(r.status_code,200);self.assertEqual(r.headers['cache-control'],'no-store')
                self.assertEqual(r.text,build_shared_replay(prefix_wire(v)))
                self.assertEqual(sha256(self.path.read_bytes()).hexdigest(),old)
                self.path.unlink()
    def test_tampered_audit_holds(self):
        write_fixture(self.path,4)
        with closing(sqlite3.connect(self.path)) as db,db:db.execute("UPDATE run_audit SET lease_digest='forged' WHERE version=2")
        self.assertEqual(self.request().status_code,503)
    def test_missing_db_holds(self): self.assertEqual(self.request().status_code,503)
    def test_resume_rejected(self):
        write_fixture(self.path,2);self.assertEqual(self.request(headers={'Last-Event-ID':'1'}).status_code,503)
    def test_terminal_failure_real_writer(self):
        p=write_fixture(self.path.with_name('lifecycle.d0.sqlite'),5);r=read_lifecycle_projection(p)
        self.assertEqual((r['state'],r['sample_released_minor'],r['sample_recognized_minor']),('FAILED',20,0))
        self.assertFalse(r['dispatch_allowed'] or r['release_ready'] or r['provider_called'])
