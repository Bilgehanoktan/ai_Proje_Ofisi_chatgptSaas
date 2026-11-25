"""D0 two-project shared budget: actual SQLite transactions, NOT PostgreSQL/RLS.
Uses original admission mapping + CompanyCoordinatedMapping. No grant/effects.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from threading import Barrier
import copy
import sqlite3
from unittest import TestCase
import test_admission_mapping_0195 as base
import test_company_terminal_0212 as previous
from test_transition_mapping_0194 import PLAN, SQLiteConnectionShim, obs
from app.core.agent_runtime.lifecycle import RunObservation, RunState
from app.core.orchestrator.engine import canonical_plan
from app.core.event_store.company_coordination import Member, Allocation, CompanyEvent, CompanyCoordinatedMapping, inspect_company, replay_company
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction
from app.core.transaction.postgres_admission_mapping import D0PostgresAdmissionMapping, claim_digest
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.postgres_transition_mapping import transaction_ref


class TwoProjectTests(TestCase):
    admission = previous.CompanyTerminalTests.admission
    event = previous.CompanyTerminalTests.event
    execute = previous.CompanyTerminalTests.execute
    company = previous.CompanyTerminalTests.company
    dump = previous.CompanyTerminalTests.dump

    def setUp(self):
        previous.CompanyTerminalTests.setUp(self)
        self.plan_b=copy.deepcopy(PLAN)
        self.plan_b['id']='plan-b'
        self.rev_b=canonical_plan(self.plan_b)['revision']
        self.members_b=[]
        for task in 'abcq':
            before=obs(task)
            scope=replace(before.scope,plan_revision=self.rev_b,run_id='demo-b-'+task)
            m=Member('project-b',scope.plan_revision,scope.task_id,scope.run_id,scope.agent_instance_id,scope.principal_id,0)
            self.members_b.append(m)
            with closing(sqlite3.connect(self.path)) as db,db:
                db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',(scope.tenant_id,scope.company_id,scope.environment_id,scope.plan_revision,scope.task_id,scope.run_id,scope.agent_instance_id,scope.principal_id,'QUEUED',0,0))
                db.execute('INSERT INTO company_run_membership VALUES (?,?,?,?,?,?,?,?,?,?)',('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',*m.row()))
        self.members=(*self.members,*self.members_b)
        self.pool=replace(self.pool,allocations=(Allocation('project-a',60),Allocation('project-b',40)))

    def _claim_b(self, amount=20, budget=None):
        original=base.spec_for()
        b=replace(original.before,scope=replace(original.before.scope,plan_revision=self.rev_b,run_id='demo-b-a'))
        l=replace(original.lease,scope=b.scope,lease_id='lease-b-a',grant_id='grant-b-a')
        spec=replace(original,before=b,lease=l,budget=budget or self.pool_budget(),amount_minor=amount,plan_digest=canonical_plan(self.plan_b)['digest'],admission_id='admission-b-a')
        intent=LogicalIntent(b.scope,Operation.ADMISSION,0,claim_digest(spec),'effect-b-a','idem-b-a',l.grant_id,l.lease_id,spec.budget.budget_id,2,3)
        return spec,intent

    def pool_budget(self):
        with closing(sqlite3.connect(self.path)) as db:
            r=db.execute('SELECT revision,currency,limit_minor,outstanding_minor,recognized_cost_minor,unknown_cost,policy_epoch,witness_epoch,source_digest FROM sample_budgets').fetchone()
        return base.SampleBudget(self.pool.budget_id,*r[:5],bool(r[5]),*r[6:])

    def _event(self, intent, project, history, amount):
        return CompanyEvent(len(history)+1,project,intent.scope.run_id,1,transaction_ref(intent),intent.request_digest,'D0_RUN_ADMISSION',() if not history else (history[-1].transaction_ref,),len(history),amount)

    def _commit(self,plan,spec,intent,event,history,unknown=False):
        mapping=CompanyCoordinatedMapping(D0PostgresAdmissionMapping(plan,spec,lambda:base.CLOCK),self.members,self.pool,history,event)
        return LogicalT1Coordinator(lambda:postgres_transaction(lambda:SQLiteConnectionShim(self.path,unknown),mapping)).commit(intent)

    def test_two_projects_actual_shared_budget(self):
        self.admission()
        spec,intent=self._claim_b()
        event=self._event(intent,'project-b',self.history,20)
        self._commit(self.plan_b,spec,intent,event,self.history)
        self.history+=(event,)
        r=self.company()
        self.assertTrue(r.structural_match, r.reason)
        self.assertEqual((r.event_count,r.pool_revision,r.outstanding_minor,r.project_outstanding),(2,2,40,(('project-a',20),('project-b',20))))

    def test_project_b_cap_rejected_before_write(self):
        self.admission()
        spec,intent=self._claim_b(amount=41)
        event=self._event(intent,'project-b',self.history,41)
        before=self.dump()
        with self.assertRaisesRegex(ValueError,'PROJECT_CAP'):
            self._commit(self.plan_b,spec,intent,event,self.history)
        self.assertEqual(self.dump(),before)

    def test_two_projects_stale_concurrent_budget_single_winner(self):
        first_a=base.spec_for(amount=20)
        first_i=base.intent_for(first_a)
        first_e=self._event(first_i,'project-a',(),20)
        second_b,second_i=self._claim_b(amount=20)
        second_e=self._event(second_i,'project-b',(),20)
        gate=Barrier(2,timeout=3)
        def attempt(plan,spec,intent,event):
            gate.wait()
            try:
                self._commit(plan,spec,intent,event,())
                return 'COMMIT'
            except ValueError as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as executor:
            result=list(executor.map(lambda arg:attempt(*arg),[(PLAN,first_a,first_i,first_e),(self.plan_b,second_b,second_i,second_e)]))
        self.assertEqual(result.count('COMMIT'),1)
        self.assertEqual(len(result),2)
        self.assertEqual(self.pool_budget().outstanding_minor,20)
        # Strict readback pin is the winner, not a union of two divergent histories.

    def test_different_project_wrong_plan_hold(self):
        spec,intent=self._claim_b()
        event=self._event(intent,'project-b',(),20)
        with self.assertRaisesRegex(ValueError,'PLAN_HOLD'):
            self._commit(PLAN,spec,intent,event,())
