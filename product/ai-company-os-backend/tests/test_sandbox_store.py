from contextlib import closing
import copy
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from app.core.development_review.sandbox_store import Workbench
from app.core.agent_runtime.lifecycle import Scope
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.sample_adapter import sample_model, SampleOutput

PLAN = json.loads((Path(__file__).resolve().parents[1]/'fixtures/core.preview.json').read_text(encoding='utf-8'))['plan']


class TestWorkbench(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)/'sample.d0.sqlite'
        self.w = Workbench(self.path, PLAN)
        self.w.create()
    def complete(self, task, now=1):
        f = self.w.lease(task,'demo-holder',now,10)
        return self.w.observe(task,'demo-holder',f,now,'cmd-'+task)
    def test_reopen(self):
        self.complete('plan')
        s = Workbench(self.path,PLAN).snapshot()
        self.assertIn(('plan','OBSERVED',1),s['tasks'])
        self.assertEqual(len(s['events']),1)
        self.assertEqual(s['admission'],'DENY')
        for k in ('dispatch_allowed','release_ready','provider_called','spend_allowed','independent_accepted'):
            self.assertIs(s[k],False)
    def test_no_overwrite(self):
        with self.assertRaises(FileExistsError): self.w.create()
    def test_wrong_scope(self):
        with self.assertRaisesRegex(ValueError,'SCOPE_DENY'): Workbench(self.path,PLAN,'other')
        with self.assertRaisesRegex(ValueError,'SCOPE_DENY'): Workbench(self.path,PLAN,company='other')
    def test_plan_mismatch(self):
        p=copy.deepcopy(PLAN);p['tasks'][0]['label']='changed'
        with self.assertRaisesRegex(ValueError,'SCOPE_MISMATCH'): Workbench(self.path,p).snapshot()
    def test_dependency(self):
        with self.assertRaisesRegex(ValueError,'DEPENDENCY_HOLD'): self.w.lease('research','demo-holder',1,5)
        self.complete('plan');self.assertEqual(self.complete('research',2),'SAMPLE_OBSERVED')
    def test_iv_release_never_observed(self):
        for t in ('plan','research','draft','merge','qa'): self.complete(t)
        for t in ('iv','release'):
            with self.assertRaisesRegex(ValueError,'ROLE_HOLD'): self.w.lease(t,'demo-holder',1,5)
        self.assertEqual(len(self.w.snapshot()['events']),5)
    def test_lease_busy(self):
        self.w.lease('plan','demo-holder',10,5)
        with self.assertRaisesRegex(ValueError,'LEASE_BUSY'): self.w.lease('plan','demo-other',14,5)
    def test_expiry_and_fence(self):
        f=self.w.lease('plan','demo-holder',10,5)
        with self.assertRaisesRegex(ValueError,'LEASE_STALE'): self.w.observe('plan','demo-holder',f,15,'cmd')
        f2=self.w.lease('plan','demo-other',15,5);self.assertEqual(f2,f+1)
        with self.assertRaisesRegex(ValueError,'LEASE_STALE'): self.w.observe('plan','demo-holder',f,16,'cmd')
        self.assertEqual(self.w.observe('plan','demo-other',f2,16,'cmd'),'SAMPLE_OBSERVED')
    def test_future_lease(self):
        f=self.w.lease('plan','demo-holder',10,5)
        with self.assertRaisesRegex(ValueError,'LEASE_STALE'): self.w.observe('plan','demo-holder',f,9,'cmd')
    def test_duplicate_and_conflict(self):
        f=self.w.lease('plan','demo-holder',1,5)
        self.w.observe('plan','demo-holder',f,1,'cmd')
        self.assertEqual(self.w.observe('plan','demo-holder',f,1,'cmd'),'DUPLICATE_IGNORED')
        with self.assertRaisesRegex(ValueError,'IDEMPOTENCY_CONFLICT'): self.w.observe('plan','demo-holder',f,2,'cmd')
        self.assertEqual(len(self.w.snapshot()['events']),1)
    def test_terminal(self):
        self.complete('plan')
        with self.assertRaisesRegex(ValueError,'TASK_TERMINAL'): self.w.lease('plan','demo-holder',20,5)
    def test_rollback(self):
        f=self.w.lease('plan','demo-holder',1,5)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER fail_event BEFORE INSERT ON sample_event BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.w.observe('plan','demo-holder',f,1,'cmd')
        self.assertIn(('plan','PENDING',0),self.w.snapshot()['tasks']);self.assertEqual(self.w.snapshot()['events'],[])
    def test_concurrent_claim(self):
        def claim(i):
            try: return self.w.lease('plan',f'demo-{i}',1,5)
            except ValueError as e: return str(e)
        with ThreadPoolExecutor(2) as e: results=list(e.map(claim,[1,2]))
        self.assertCountEqual(results,[1,'SAMPLE_LEASE_BUSY'])
    def test_adapter_guard(self):
        f=self.w.lease('plan','demo-holder',1,5)
        with patch('app.core.development_review.sandbox_store.sample_model',return_value=SampleOutput('BAD','x',True)):
            with self.assertRaisesRegex(ValueError,'ADAPTER_HOLD'): self.w.observe('plan','demo-holder',f,1,'cmd')
        self.assertEqual(self.w.snapshot()['events'],[])
    def test_adapter_pin(self):
        d='a'*64;s=Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+d,'plan','demo-run','demo-agent','demo-principal')
        a=AdapterPin(s,'demo-model','v1',d,('demo-tool',),());b=AdapterPin(s,'demo-fallback','v1',d,('demo-tool',),())
        self.assertEqual(sample_model(a,b,(a,b)).reason,'FIXED_SAMPLE_ONLY')
        self.assertIsNone(sample_model(a,b,(a,)).output)
    def test_invalid_inputs(self):
        for args in [('plan','real-holder',1,5),('plan','demo-holder',True,5),('plan','demo-holder',1,0)]:
            with self.assertRaisesRegex(ValueError,'LEASE_INVALID'): self.w.lease(*args)
        with self.assertRaisesRegex(ValueError,'PATH_INVALID'): Workbench(self.path.with_suffix('.db'),PLAN)
