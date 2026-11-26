"""Exact canonical fixture, actual scheduler, no DB/persistence claim."""
from dataclasses import replace
from pathlib import Path
import json
import unittest
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState
from app.core.development_review.research_slice import RESEARCH_REVISION, review_research_roster
from app.core.orchestrator.engine import canonical_plan


class ResearchRosterTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((Path(__file__).resolve().parents[1]/'fixtures/core.preview.json').read_text(encoding='utf-8'))['plan']
        self.initial = tuple(RunObservation(Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',
            RESEARCH_REVISION,t,'demo-run-'+t,'demo-agent-'+t,'demo-principal-'+t),RunState.QUEUED,0,0)
            for t in ('draft','merge','plan','qa','research'))

    def check(self, current=None, initial=None, plan=None, revision=RESEARCH_REVISION, project='demo-research-project'):
        r = review_research_roster(self.plan if plan is None else plan,revision,project,
                                  self.initial if initial is None else initial,self.initial if current is None else current)
        self.assertEqual(r.decision,'HOLD'); self.assertFalse(r.dispatch_allowed)
        return r

    def update(self, task, **kw):
        return tuple(replace(r,**kw) if r.scope.task_id==task else r for r in self.initial)

    def reject(self, **kw):
        r=self.check(**kw); self.assertFalse(r.structural_match); self.assertEqual(r.ready,()); self.assertIsNone(r.root_state)

    def test_plan_pin(self):
        self.assertEqual(canonical_plan(self.plan)['revision'],RESEARCH_REVISION)
        r=self.check(); self.assertTrue(r.structural_match); self.assertEqual(r.ready,('plan',)); self.assertEqual(r.root_version,0)
    def test_admitted(self):
        r=self.check(self.update('plan',state=RunState.ADMITTED,version=1)); self.assertTrue(r.structural_match); self.assertEqual(r.ready,())
    def test_running(self):
        r=self.check(self.update('plan',state=RunState.RUNNING,version=2)); self.assertEqual(r.root_state,'RUNNING'); self.assertTrue(r.structural_match)
    def test_verifying_not_success(self):
        r=self.check(self.update('plan',state=RunState.VERIFYING,version=3)); self.assertEqual(r.root_state,'VERIFYING'); self.assertEqual(r.ready,())
    def test_wrong_revision(self): self.reject(revision='sha256:'+'a'*64)
    def test_wrong_project_profile(self): self.reject(project='project-a')
    def test_missing_roster(self): self.reject(current=self.initial[:-1])
    def test_duplicate_roster(self): self.reject(current=self.initial+(self.initial[0],))
    def test_forged_success(self): self.reject(current=self.update('plan',state=RunState.SUCCEEDED,version=4))
    def test_dependency_bypass(self): self.reject(current=self.update('research',state=RunState.RUNNING,version=2))
    def test_wrong_version(self): self.reject(current=self.update('plan',state=RunState.VERIFYING,version=2))
    def test_changed_attempt(self): self.reject(current=self.update('plan',attempt=1))
    def test_changed_agent(self):
        r=self.initial[2]; self.reject(current=self.update('plan',scope=replace(r.scope,agent_instance_id='demo-other')))
    def test_iv_not_agent(self):
        r=self.initial[0]; self.reject(current=self.initial+(replace(r,scope=replace(r.scope,task_id='iv',run_id='demo-iv')),))
    def test_wrong_initial(self): self.reject(initial=self.update('plan',version=1))
    def test_scope_drift(self):
        r=self.initial[2]; self.reject(current=self.update('plan',scope=replace(r.scope,company_id='other')))
    def test_plan_content_drift(self):
        plan=json.loads(json.dumps(self.plan)); plan['tasks'][0]['label']+=' changed'; self.reject(plan=plan)
    def test_no_terminal_failure_profile(self): self.reject(current=self.update('plan',state=RunState.FAILED,version=4))
