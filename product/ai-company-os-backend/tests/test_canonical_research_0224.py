"""Actual SQLite composition candidate. Uses original SQL, T1, 0221 archive/journal.
No real provider, PostgreSQL acceptance, independent receipt or success path.
"""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import test_admission_mapping_0195 as admission
import test_company_terminal_0212 as company_fixture
import test_result_reference_0221 as result_fixture
from test_transition_mapping_0194 import SQLiteConnectionShim, SQLiteCursorShim
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, LeaseObservation
from app.core.orchestrator.engine import canonical_plan
from app.core.event_store.company_coordination import SCOPE, Member, Pool, Allocation
from app.core.event_store.plan_history_review import RunHistoryPin
from app.core.event_store.history_readback import OrdinaryPin
from app.core.event_store.retained_history import ReferenceStore
from app.core.transaction.postgres_admission_mapping import ClaimSpec, commit_scheduled_admission
from app.core.transaction.postgres_lifecycle_mapping import AdmissionBinding
from app.core.transaction.postgres_session import CommitOutcomeUnknown
from app.core.transaction.fenced_transition import SampleResultPin
from app.core.development_review.research_slice import (RESEARCH_REVISION, ResearchResultEvidence,
    inspect_research_slice)


class ResearchFixture:
    """Reuse the original company mapping helpers, but seed the actual UI plan."""
    execute = company_fixture.CompanyTerminalTests.execute
    ordinary = company_fixture.CompanyTerminalTests.ordinary
    dump = company_fixture.CompanyTerminalTests.dump
    company = company_fixture.CompanyTerminalTests.company

    def __init__(self, owner):
        self.plan = json.loads((Path(__file__).resolve().parents[1]/'fixtures/core.preview.json').read_text(encoding='utf-8'))['plan']
        assert canonical_plan(self.plan)['revision'] == RESEARCH_REVISION
        self.project = 'demo-research-project'
        # Existing helper event() uses project-a; override it below with the pinned project.
        self.tmp = tempfile.TemporaryDirectory(); owner.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'research.d0.sqlite'
        self.initials = tuple(RunObservation(Scope(*SCOPE,RESEARCH_REVISION,t,'demo-run-'+t,
            'demo-agent-'+t,'demo-principal-'+t),RunState.QUEUED,0,0)
            for t in ('draft','merge','plan','qa','research'))
        self.before = next(r for r in self.initials if r.scope.task_id=='plan')
        self.lease = LeaseObservation(self.before.scope,'lease-plan','grant-plan',1,0,1,2,3,20,10)
        self.anchor = self.budget = admission.BUDGET
        self.initial = ClaimSpec(self.before,'admission-plan',self.lease,self.budget,20,canonical_plan(self.plan)['digest'])
        self.admit = admission.intent_for(self.initial); self.binding = AdmissionBinding(self.initial,self.admit)
        self.clock = replace(admission.CLOCK,now_tick=11)
        self.members = tuple(Member(self.project,r.scope.plan_revision,r.scope.task_id,r.scope.run_id,
            r.scope.agent_instance_id,r.scope.principal_id,r.version) for r in self.initials)
        b=self.anchor; self.pool=Pool(b.budget_id,b.currency,b.limit_minor,b.revision,b.policy_epoch,b.witness_epoch,
            b.source_digest,(Allocation(self.project,b.limit_minor),))
        self.history=(); self.commands=(); self.archive=ReferenceStore(self.path.with_name('references.sqlite'))
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('PRAGMA foreign_keys=ON')
            for path in ('0192/candidate_event_outbox_fence.sql','0193/candidate_run_head.sql',
                         '0194/candidate_transition_roles.sql','0195/candidate_admission_budget.sql',
                         '0196L/candidate_lease_settlement.sql','0203T/terminal_command_anchors.sql',
                         '0204C/company_event_order.sql'):
                sql=(admission.ROOT/'database'/path).read_text().replace('CREATE SCHEMA t1_candidate;','').replace('t1_candidate.','')
                db.executescript(sql)
            for r in self.initials:
                s=r.scope
                db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',(*SCOPE,s.plan_revision,s.task_id,
                    s.run_id,s.agent_instance_id,s.principal_id,r.state.value,r.version,r.attempt))
            db.execute('INSERT INTO sample_budgets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(*SCOPE,b.budget_id,b.revision,
                b.currency,b.limit_minor,b.outstanding_minor,b.recognized_cost_minor,b.unknown_cost,b.policy_epoch,b.witness_epoch,b.source_digest))
            for m in self.members: db.execute('INSERT INTO company_run_membership VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,*m.row()))
            db.execute('INSERT INTO company_stream_heads VALUES (?,?,?,0)',SCOPE)

    def event(self, intent, kind, budget_rev=None, amount=0):
        return replace(company_fixture.CompanyTerminalTests.event(self,intent,kind,budget_rev,amount),project_id=self.project)

    def pins(self):
        return tuple(RunHistoryPin(r,self.binding if r.scope.task_id=='plan' and self.history else None,
            self.commands if r.scope.task_id=='plan' else ()) for r in self.initials)

    def admit_root(self, **kw):
        args=dict(connect=lambda:SQLiteConnectionShim(self.path),plan=self.plan,spec=self.initial,intent=self.admit,
            clock=lambda:admission.CLOCK,members=self.members,pool=self.pool,history=self.history,history_pins=self.pins())
        args.update(kw); receipt=commit_scheduled_admission(**args)
        self.history+=(self.event(self.admit,'D0_RUN_ADMISSION',0,20),)
        self.before=replace(self.before,state=RunState.ADMITTED,version=1)
        self.budget=replace(self.budget,revision=1,outstanding_minor=20)
        return receipt

    def prepare_result(self):
        self.admit_root(); self.ordinary(RunState.RUNNING)
        f=result_fixture.ResultReferenceTests(); f.prepare_result_context(self)
        pin=SampleResultPin(f.cap,self.archive.put(f.body()))
        e=ResearchResultEvidence(f.context,f.registry,f.witness,f.wb,f.company,f.cp,pin,self.archive,
            f.clock,f.raw,f.journal)
        return f,e

    def record_verifying(self, f):
        self.history+=(f.company.event,)
        self.commands+=(OrdinaryPin(f.intent,self.before,RunState.VERIFYING,self.lease),)
        self.before=replace(self.before,state=RunState.VERIFYING,version=3)

    def read(self, **kw):
        args=dict(plan=self.plan,expected_revision=RESEARCH_REVISION,project_id=self.project,pins=self.pins(),
            members=self.members,pool=self.pool,events=self.history,anchor=self.anchor)
        args.update(kw)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            with SQLiteCursorShim(db) as c: return inspect_research_slice(c,**args)


class CanonicalResearchTests(unittest.TestCase):
    def setUp(self): self.f=ResearchFixture(self)
    def held(self, r):
        self.assertIsNone(r.request_id); self.assertFalse(r.request_linked)
        self.assertEqual(r.decision,'HOLD'); self.assertFalse(r.dispatch_allowed or r.release_ready or
            r.independent_verified or r.retry_allowed or r.provider_called or r.tool_called or r.spend_allowed)
        self.assertEqual((r.qa_status,r.iv_status,r.release_status),('DEPENDENCY_HOLD','INDEPENDENT_RECEIPT_HOLD','H01_HOLD'))
    def completed_prefix(self):
        f,e=self.f.prepare_result(); self.assertTrue(f.invoke(e.result).historical_match)
        self.f.record_verifying(f); return e
    def test_canonical_prefix_and_result(self):
        for version,state in ((0,'QUEUED'),(1,'ADMITTED'),(2,'RUNNING')):
            if version==1:self.f.admit_root()
            if version==2:self.f.ordinary(RunState.RUNNING)
            before=self.f.dump(); r=self.f.read(); self.held(r)
            self.assertTrue(r.structural_match); self.assertEqual((r.root_version,r.root_state),(version,state))
            self.assertIsNone(r.evidence_sha); self.assertEqual(self.f.dump(),before)
        # prepare the exact result context on the already-running root.
        f=result_fixture.ResultReferenceTests(); f.prepare_result_context(self.f)
        pin=SampleResultPin(f.cap,self.f.archive.put(f.body()))
        e=ResearchResultEvidence(f.context,f.registry,f.witness,f.wb,f.company,f.cp,pin,self.f.archive,f.clock,f.raw,f.journal)
        self.assertTrue(f.invoke(pin).historical_match); self.f.record_verifying(f)
        before=self.f.dump(); r=self.f.read(evidence=e); self.held(r)
        self.assertTrue(r.structural_match); self.assertEqual(r.evidence_sha,pin.evidence_sha)
        self.assertEqual((r.root_state,r.event_count,r.project_id),('VERIFYING',3,self.f.project))
        self.assertEqual(self.f.dump(),before)
        self.assertEqual({t.task_id:t.state for t in r.tasks},dict(draft='QUEUED',merge='QUEUED',plan='VERIFYING',qa='QUEUED',research='QUEUED',iv=None,release=None))
    def test_dependency_not_verified_no_write(self):
        r=next(x for x in self.f.initials if x.scope.task_id=='research')
        l=replace(self.f.lease,scope=r.scope,lease_id='lease-research',grant_id='grant-research')
        s=replace(self.f.initial,before=r,lease=l,admission_id='admission-research')
        before=self.f.dump()
        with self.assertRaisesRegex(ValueError,'PREDECESSOR_PROOF'):
            self.f.admit_root(spec=s,intent=admission.intent_for(s))
        self.assertEqual(self.f.dump(),before)
    def test_wrong_project_rejected(self):
        r=self.f.read(project_id='demo-other'); self.held(r); self.assertFalse(r.structural_match)
    def test_missing_archive_before_claim_no_write(self):
        f,e=self.f.prepare_result(); before=self.f.dump()
        with self.assertRaises(ValueError): f.invoke(replace(e.result,evidence_sha='0'*64))
        self.assertEqual(self.f.dump(),before)
    def test_wrong_result_digest_readback(self):
        e=self.completed_prefix(); r=self.f.read(evidence=replace(e,result=replace(e.result,evidence_sha='0'*64)))
        self.held(r); self.assertFalse(r.structural_match); self.assertIsNone(r.evidence_sha)
    def test_result_archive_cannot_share_journal_file(self):
        e=self.completed_prefix()
        # Deliberately create a matching archive object inside the disposable
        # journal file. Content match alone must not satisfy store separation.
        alias=ReferenceStore(e.journal.path)
        self.assertEqual(alias.put(e.result_reader.read(e.result.evidence_sha)),e.result.evidence_sha)
        r=self.f.read(evidence=replace(e,result_reader=alias))
        self.held(r); self.assertFalse(r.structural_match); self.assertIsNone(r.evidence_sha)
    def test_result_archive_drift_rejected_on_recheck(self):
        e=self.completed_prefix(); body=e.result_reader.read(e.result.evidence_sha)
        with patch.object(type(e.result_reader),'read',side_effect=[body,b'changed']) as read:
            r=self.f.read(evidence=e)
        self.assertEqual(read.call_count,2)
        self.held(r); self.assertFalse(r.structural_match); self.assertIsNone(r.evidence_sha)
    def test_missing_result_does_not_imply_success(self):
        self.completed_prefix(); r=self.f.read(); self.held(r); self.assertTrue(r.structural_match); self.assertIsNone(r.evidence_sha)
    def test_tampered_head_rejected(self):
        e=self.completed_prefix()
        with closing(sqlite3.connect(self.f.path)) as db,db: db.execute("UPDATE run_heads SET state='SUCCEEDED' WHERE task_id='plan'")
        r=self.f.read(evidence=e); self.held(r); self.assertFalse(r.structural_match)
    def test_unknown_commit_quarantined(self):
        f,e=self.f.prepare_result()
        with self.assertRaises(CommitOutcomeUnknown): f.invoke(e.result,unknown=True)
        self.f.record_verifying(f); r=self.f.read(evidence=e); self.held(r); self.assertFalse(r.structural_match)
        before=self.f.dump()
        with self.assertRaises(ValueError): f.invoke(e.result)
        self.assertEqual(self.f.dump(),before)
