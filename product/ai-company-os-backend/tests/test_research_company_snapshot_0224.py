"""Actual SQLite company roster/order readback; direct fixture seeds, NOT T1 writes."""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState
from app.core.development_review.research_slice import RESEARCH_REVISION, inspect_research_company_roster
from app.core.event_store.company_coordination import SCOPE, Member, Pool, Allocation, CompanyEvent

ROOT = Path(__file__).resolve().parents[3]
SQL = ('0192/candidate_event_outbox_fence.sql','0193/candidate_run_head.sql',
       '0194/candidate_transition_roles.sql','0195/candidate_admission_budget.sql',
       '0196L/candidate_lease_settlement.sql','0203T/terminal_command_anchors.sql',
       '0204C/company_event_order.sql')

class SelectCursor:
    def __init__(self, db): self.c=db.cursor()
    def execute(self, sql, params=()):
        if not sql.startswith('SELECT ') or ';' in sql or 'FOR UPDATE' in sql:
            raise ValueError('SELECT_ONLY')
        return self.c.execute(sql.replace('t1_candidate.','').replace('%s','?'),params)
    def fetchone(self): return self.c.fetchone()


class ResearchCompanySnapshotTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((Path(__file__).resolve().parents[1]/'fixtures/core.preview.json').read_text(encoding='utf-8'))['plan']
        self.project='demo-research-project'
        self.initial=tuple(RunObservation(Scope(*SCOPE,RESEARCH_REVISION,t,'demo-run-'+t,
            'demo-agent-'+t,'demo-principal-'+t),RunState.QUEUED,0,0) for t in ('draft','merge','plan','qa','research'))
        self.members=tuple(Member(self.project,r.scope.plan_revision,r.scope.task_id,r.scope.run_id,
            r.scope.agent_instance_id,r.scope.principal_id,r.version) for r in self.initial)
        self.pool=Pool('sample-budget','USD',100,0,2,3,'a'*64,(Allocation(self.project,100),))
        self.events=()
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); self.path=Path(temp.name)/'research.sqlite'
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('PRAGMA foreign_keys=ON')
            for p in SQL:
                db.executescript((ROOT/'database'/p).read_text().replace('CREATE SCHEMA t1_candidate;','').replace('t1_candidate.',''))
            for r in self.initial:
                s=r.scope
                db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',(*SCOPE,s.plan_revision,s.task_id,s.run_id,s.agent_instance_id,s.principal_id,r.state.value,r.version,r.attempt))
            for m in self.members: db.execute('INSERT INTO company_run_membership VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,*m.row()))
            db.execute('INSERT INTO company_stream_heads VALUES (?,?,?,0)',SCOPE)
            db.execute('INSERT INTO sample_budgets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(*SCOPE,'sample-budget',0,'USD',100,0,0,False,2,3,'a'*64))

    def read(self, **kw):
        args=dict(plan=self.plan,expected_revision=RESEARCH_REVISION,project_id=self.project,
                  initial=self.initial,members=self.members,pool=self.pool,events=self.events)
        args.update(kw); before=sha256(self.path.read_bytes()).hexdigest()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            r=inspect_research_company_roster(SelectCursor(db),**args)
        self.assertEqual(before,sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(r.decision,'HOLD'); self.assertFalse(r.dispatch_allowed or r.spend_allowed or r.independent_verified)
        return r

    def change(self, sql):
        with closing(sqlite3.connect(self.path)) as db,db: db.execute(sql)

    def test_exact_zero_event_roster(self):
        r=self.read(); self.assertTrue(r.structural_match); self.assertEqual((r.event_count,r.outstanding_minor),(0,0))
    def test_wrong_project(self): self.assertFalse(self.read(project_id='demo-other').structural_match)
    def test_wrong_member_pin(self):
        self.assertFalse(self.read(members=(replace(self.members[0],principal_id='demo-other'),*self.members[1:])).structural_match)
    def test_tampered_db_head(self):
        self.change("UPDATE run_heads SET agent_instance_id='demo-other' WHERE task_id='plan'"); self.assertFalse(self.read().structural_match)
    def test_budget_tamper(self):
        self.change('UPDATE sample_budgets SET outstanding_minor=1'); self.assertFalse(self.read().structural_match)
    def test_stream_tamper(self):
        self.change('UPDATE company_stream_heads SET sequence=1'); self.assertFalse(self.read().structural_match)
    def test_extra_member(self):
        self.change("UPDATE company_run_membership SET project_id='demo-other' WHERE task_id='plan'"); self.assertFalse(self.read().structural_match)
    def test_seeded_admission_company_only(self):
        # Direct fixture writes are intentionally NOT the original T1 writer.
        e=CompanyEvent(1,self.project,'demo-run-plan',1,'d0-tx-'+'b'*64,'c'*64,'D0_RUN_ADMISSION',(),0,20)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute("UPDATE run_heads SET state='ADMITTED',version=1 WHERE task_id='plan'")
            db.execute('INSERT INTO run_admissions VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,e.run_id,'admission-plan',e.transaction_ref,e.request_digest,'lease-plan','grant-plan','sample-budget'))
            db.execute('UPDATE sample_budgets SET revision=1,outstanding_minor=20')
            db.execute('INSERT INTO sample_reservations VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,e.run_id,'sample-budget',1,20,'USD',e.request_digest,e.transaction_ref))
            db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?)',(*SCOPE,e.run_id,e.version,e.transaction_ref,e.kind,e.request_digest))
            db.execute('INSERT INTO company_event_order VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,*e.order_row()))
            db.execute('UPDATE company_stream_heads SET sequence=1')
        self.events=(e,); r=self.read(); self.assertTrue(r.structural_match); self.assertEqual((r.event_count,r.outstanding_minor),(1,20))
        self.change("UPDATE company_event_order SET request_digest='"+'d'*64+"'")
        self.assertFalse(self.read().structural_match)
