import copy
import json
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.api.mvp_diagnostics import inspect_mvp
from app.core.agent_runtime.lifecycle import Scope
from app.engines.budget_engine.reservation_review import BudgetSnapshot, ReservationRequest, inspect_reservation

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = json.loads((ROOT / 'fixtures/core.preview.json').read_text(encoding='utf-8'))
ROUTE = '/demo/v1/mvp/diagnostics'


class TestMvpDiagnostics(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
    def test_seven_get_routes(self):
        for route in ('/demo/v1/status', '/demo/v1/catalog', '/demo/v1/authority', '/demo/v1/core/preview',
                      '/demo/v1/core/plan-projection', '/demo/v1/office/worlds/demo-world/snapshot', ROUTE):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 200)
    def test_contract_and_cache(self):
        r = self.client.get(ROUTE); self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers['cache-control'], 'no-store')
        b = r.json(); self.assertEqual(b['schema_version'], 'mvp.diagnostics.v1-D0')
        self.assertEqual(b['admission'], 'DENY')
        for k in ('dispatch_allowed', 'release_ready', 'provider_called', 'spend_allowed', 'independent_accepted'):
            self.assertIs(b[k], False)
        for k in ('real_run_count', 'actual_cost_minor', 'revenue_minor'):
            self.assertIsNone(b[k])
    def test_engines(self):
        b = self.client.get(ROUTE).json(); s = b['sections']
        self.assertEqual(s['orchestrator'], 'CANONICAL_D0_PLAN_ONLY_INSTANCE_AND_ADMISSION_REQUIRED')
        self.assertEqual(s['runtime'], 'RUN_LEASE_BINDING_MISSING')
        self.assertEqual(s['event_store'], 'SQLITE_MEMORY_READBACK_ONLY')
        self.assertEqual(s['model'], 'D0_REFERENCE_MATCH_ONLY')
        self.assertEqual(s['gateway'], 'MODEL_EGRESS_DISABLED')
        self.assertEqual(s['tools'], 'INDEPENDENT_RECEIPTS_ABSENT')
        self.assertEqual(s['verifier'], 'IV_TRUST_ROOT_UNPROVEN')
        self.assertEqual(s['finance'], 'UNVERIFIED')
        self.assertEqual(b['sample_event_rows'], 3)
        self.assertEqual(b['diagnostic_remaining_minor'], 6900)
    def test_plan_digest_matches_existing_api(self):
        self.assertEqual(self.client.get(ROUTE).json()['plan_digest'], self.client.get('/demo/v1/core/plan-projection').json()['digest'])
    def test_mutations_rejected(self):
        for method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            self.assertEqual(self.client.request(method, ROUTE).status_code, 405)
        self.assertEqual(self.client.get('/demo/v1/office/worlds/other/snapshot').status_code, 404)
    def test_repeat_no_mutation(self):
        self.assertEqual(self.client.get(ROUTE).json(), self.client.get(ROUTE).json())
    def test_gap_holds(self):
        sample = copy.deepcopy(SAMPLE); sample['events'].pop(1)
        b = inspect_mvp(sample); self.assertEqual(b['sections']['event_store'], 'REPLAY_HOLD'); self.assertIsNone(b['sample_event_rows'])
    def test_wrong_tenant_holds(self):
        sample = copy.deepcopy(SAMPLE); sample['events'][0]['tenant_id'] = 'other'
        b = inspect_mvp(sample); self.assertEqual(b['sections']['event_store'], 'REPLAY_HOLD'); self.assertIsNone(b['sample_event_rows'])
    def test_budget_cross_scope_and_unknown(self):
        d = 'a'*64; scope = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+d,'task','demo-run','demo-agent','demo-principal')
        snapshot = BudgetSnapshot(scope,'demo-budget',0,'TRY',10000,1000,2000,True,0,0,d)
        q = ReservationRequest(scope,'demo-budget',0,'TRY',100,'demo-reservation',0,0)
        self.assertEqual(inspect_reservation(q,snapshot,snapshot).reason, 'UNKNOWN_COST_HOLD')
        other = Scope('other','synthetic-company','A0_SAMPLE_ONLY','sha256:'+d,'task','demo-run','demo-agent','demo-principal')
        q = ReservationRequest(other,'demo-budget',0,'TRY',100,'demo-reservation',0,0)
        self.assertEqual(inspect_reservation(q,snapshot,snapshot).reason, 'BUDGET_REQUEST_INVALID')
    def test_schema_validation(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((ROOT / 'contracts/source/mvp.diagnostics.schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        body = self.client.get(ROUTE).json()
        self.assertTrue(validator.is_valid(body))
        self.assertFalse(validator.is_valid({**body, 'dispatch_allowed': True}))
    def test_unexpected_effect_projection_rejected(self):
        from dataclasses import replace
        from unittest.mock import patch
        from app.engines.model_gateway.fallback import ModelReview
        with patch('app.api.mvp_diagnostics.inspect_fallback', return_value=replace(ModelReview('HOLD'), provider_call_allowed=True)):
            self.assertEqual(self.client.get(ROUTE).status_code, 409)
            with self.assertRaisesRegex(ValueError, 'D0_EFFECT_BOUNDARY_HOLD'):
                inspect_mvp(SAMPLE)
