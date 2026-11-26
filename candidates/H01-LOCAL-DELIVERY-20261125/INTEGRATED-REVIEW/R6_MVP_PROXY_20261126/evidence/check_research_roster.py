"""R6 existing Research roster seam diagnostic, no SQL, no grants, no dispatch."""
from dataclasses import replace
from pathlib import Path
import json
import unittest
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState
from app.core.orchestrator.engine import canonical_plan
from app.core.development_review.research_slice import RESEARCH_REVISION, review_research_roster

PLAN = json.loads(Path('fixtures/core.preview.json').read_text(encoding='utf-8'))['plan']
PROJECTION = canonical_plan(PLAN)
ROSTER = tuple(RunObservation(Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',
    RESEARCH_REVISION,t['id'],'demo-run-'+t['id'],'demo-agent-'+t['id'],'demo-principal-'+t['id']),
    RunState.QUEUED,0,0) for t in PROJECTION['tasks'] if t['role'] not in ('independent-verifier','human-authority'))

class ResearchRosterSeam(unittest.TestCase):
    def review(self, rows=ROSTER, pins=ROSTER, plan=PLAN, rev=RESEARCH_REVISION, project='demo-project'):
        r=review_research_roster(plan,rev,project,pins,rows)
        self.assertEqual(r.decision,'HOLD'); self.assertIs(r.dispatch_allowed,False)
        return r
    def change(self, task, **kw):
        return tuple(replace(r,**kw) if r.scope.task_id==task else r for r in ROSTER)
    def test_existing_plan_digest_and_waves(self):
        self.assertEqual(PROJECTION['revision'],RESEARCH_REVISION)
        self.assertEqual(PROJECTION['waves'],[['plan'],['draft','research'],['merge'],['qa'],['iv'],['release']])
        self.assertIs(PROJECTION['dispatch_allowed'],False)
    def test_root_queue_only(self):
        r=self.review(); self.assertTrue(r.structural_match); self.assertEqual(r.ready,('plan',)); self.assertEqual(r.root_version,0)
    def test_root_admitted(self):
        r=self.review(self.change('plan',state=RunState.ADMITTED,version=1)); self.assertTrue(r.structural_match); self.assertEqual(r.ready,()); self.assertEqual(r.root_version,1)
    def test_root_running(self):
        r=self.review(self.change('plan',state=RunState.RUNNING,version=2)); self.assertTrue(r.structural_match); self.assertEqual(r.ready,()); self.assertEqual(r.root_version,2)
    def test_root_verifying(self):
        r=self.review(self.change('plan',state=RunState.VERIFYING,version=3)); self.assertTrue(r.structural_match); self.assertEqual(r.ready,()); self.assertEqual(r.root_version,3)
    def test_bare_success_not_release(self):
        self.assertFalse(self.review(self.change('plan',state=RunState.SUCCEEDED,version=4)).structural_match)
    def test_same_version_state_rejected(self):
        self.assertFalse(self.review(self.change('plan',state=RunState.ADMITTED)).structural_match)
    def test_child_cannot_run_early(self):
        self.assertFalse(self.review(self.change('research',state=RunState.RUNNING,version=2)).structural_match)
    def test_child_pin_version_drift_rejected(self):
        self.assertFalse(self.review(self.change('draft',version=1)).structural_match)
    def test_missing_agent_rejected(self):
        self.assertFalse(self.review(tuple(r for r in ROSTER if r.scope.task_id!='qa')).structural_match)
    def test_plan_content_change_rejected(self):
        p=json.loads(json.dumps(PLAN));p['tasks'][0]['label']+=' changed'; self.assertFalse(self.review(plan=p).structural_match)
    def test_foreign_principal_rejected(self):
        r=next(r for r in ROSTER if r.scope.task_id=='plan');self.assertFalse(self.review(self.change('plan',scope=replace(r.scope,principal_id='demo-other'))).structural_match)

if __name__=='__main__': unittest.main(verbosity=2)
