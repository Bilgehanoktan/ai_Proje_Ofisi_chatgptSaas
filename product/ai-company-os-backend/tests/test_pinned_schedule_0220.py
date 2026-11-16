"""Exact pure scheduler checks for 0220; no database or real dispatch."""
from dataclasses import replace
from unittest import TestCase
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState
from app.core.agent_runtime.scheduler_review import inspect_schedule, inspect_pinned_schedule
from app.core.orchestrator.engine import canonical_plan

PLAN={'id':'plan-0220','worktype':'RESEARCH','tasks':[
    {'id':'a','label':'Research','role':'research','depends_on':[]},
    {'id':'b','label':'Analysis','role':'engineer','depends_on':['a']},
    {'id':'q','label':'QA','role':'qa','depends_on':['b']},
    {'id':'v','label':'IV','role':'independent-verifier','depends_on':['q']},
    {'id':'h','label':'Release','role':'human-authority','depends_on':['v']}]}

def initial():
    rev=canonical_plan(PLAN)['revision']
    return tuple(RunObservation(Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',
        rev,t,'demo-run-'+t,'demo-agent-'+t,'demo-principal-'+t),RunState.QUEUED,0,0)
        for t in ('a','b','q'))

class PinnedScheduleTests(TestCase):
    def test_root_ready_only_no_grant(self):
        rows=initial(); r=inspect_pinned_schedule(PLAN,rows,rows)
        self.assertEqual(r.ready,('a',))
        self.assertEqual(r.decision,'HOLD')
        self.assertFalse(r.claim_allowed or r.dispatch_allowed)
    def test_bare_success_legacy_vs_pinned(self):
        rows=initial(); changed=(replace(rows[0],state=RunState.SUCCEEDED,version=4),*rows[1:])
        self.assertEqual(inspect_schedule(PLAN,changed).ready,('b',))
        with self.assertRaisesRegex(ValueError,'SUCCESS_PROOF'):
            inspect_pinned_schedule(PLAN,changed,rows)
    def test_running_root_blocks_children(self):
        rows=initial(); changed=(replace(rows[0],state=RunState.RUNNING,version=2),*rows[1:])
        self.assertEqual(inspect_pinned_schedule(PLAN,changed,rows).ready,())
    def test_failed_root_blocks_children(self):
        rows=initial(); changed=(replace(rows[0],state=RunState.FAILED,version=3),*rows[1:])
        self.assertEqual(inspect_pinned_schedule(PLAN,changed,rows).ready,())
    def test_wrong_principal(self):
        rows=initial(); changed=(replace(rows[0],scope=replace(rows[0].scope,principal_id='demo-other')),*rows[1:])
        with self.assertRaisesRegex(ValueError,'IDENTITY'):
            inspect_pinned_schedule(PLAN,changed,rows)
    def test_wrong_agent(self):
        rows=initial(); changed=(replace(rows[0],scope=replace(rows[0].scope,agent_instance_id='demo-other')),*rows[1:])
        with self.assertRaisesRegex(ValueError,'IDENTITY'):
            inspect_pinned_schedule(PLAN,changed,rows)
    def test_wrong_attempt(self):
        rows=initial(); changed=(replace(rows[0],attempt=1),*rows[1:])
        with self.assertRaisesRegex(ValueError,'IDENTITY'):
            inspect_pinned_schedule(PLAN,changed,rows)
    def test_regressed_version(self):
        rows=initial(); pins=(replace(rows[0],version=2),*rows[1:])
        with self.assertRaisesRegex(ValueError,'IDENTITY'):
            inspect_pinned_schedule(PLAN,rows,pins)
    def test_missing_roster(self):
        rows=initial()
        with self.assertRaisesRegex(ValueError,'INCOMPLETE_RUN_SET'):
            inspect_pinned_schedule(PLAN,rows[:-1],rows)
    def test_wrong_initial_state(self):
        rows=initial(); pins=(replace(rows[0],state=RunState.RUNNING),*rows[1:])
        with self.assertRaisesRegex(ValueError,'INITIAL'):
            inspect_pinned_schedule(PLAN,rows,pins)
    def test_forged_descendant(self):
        rows=initial(); changed=(rows[0],replace(rows[1],state=RunState.RUNNING,version=2),rows[2])
        with self.assertRaisesRegex(ValueError,'CAUSAL_ORDER'):
            inspect_pinned_schedule(PLAN,changed,rows)
    def test_wrong_revision(self):
        rows=initial(); changed=(replace(rows[0],scope=replace(rows[0].scope,plan_revision='sha256:'+'0'*64)),*rows[1:])
        with self.assertRaisesRegex(ValueError,'RUN_BINDING'):
            inspect_pinned_schedule(PLAN,changed,rows)
