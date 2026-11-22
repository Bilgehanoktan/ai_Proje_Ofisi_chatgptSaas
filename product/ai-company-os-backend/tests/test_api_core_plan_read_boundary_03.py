"""03API — focused D0 API read boundary regression; no real IAM or T1."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.api import demo
from app.core.task_engine.dag import GraphError

ROUTE = "/demo/v1/core/plan-projection"


class CorePlanReadBoundaryTests(TestCase):
    def setUp(self):
        self.client = TestClient(demo.app)
        self.addCleanup(self.client.close)

    def test_existing_frontend_wire_remains_exact(self):
        response = self.client.get(ROUTE)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        expected = json.loads((demo.FIXTURE.parent / "core.plan.projection.json").read_text(encoding="utf-8"))
        self.assertEqual(response.json(), expected)
        self.assertIs(response.json()["dispatch_allowed"], False)
        self.assertIs(response.json()["release_ready"], False)

    def test_tampered_source_and_expected_output_fail_closed(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name in demo._CORE_PLAN_FILES:
                (directory / name).write_bytes((demo.FIXTURE.parent / name).read_bytes())
            with patch.object(demo, "FIXTURE", directory / "office.snapshot.json"):
                for name in demo._CORE_PLAN_FILES:
                    path = directory / name
                    original = path.read_bytes()
                    path.write_bytes(original + b" ")
                    response = self.client.get(ROUTE)
                    self.assertEqual(response.status_code, 503)
                    self.assertEqual(response.json(), {"mode": "D0_PLAN_READBACK_HOLD"})
                    self.assertEqual(response.headers["cache-control"], "no-store")
                    path.write_bytes(original)

    def test_unavailable_source_fails_closed(self):
        with patch.object(demo, "_pinned_plan_json", side_effect=OSError("missing")):
            response = self.client.get(ROUTE)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"mode": "D0_PLAN_READBACK_HOLD"})

    def test_compiler_schema_drift_fails_closed(self):
        with patch.object(demo, "canonical_plan", return_value={"dispatch_allowed": True}):
            response = self.client.get(ROUTE)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_graph_conflict_keeps_409_contract(self):
        with patch.object(demo, "canonical_plan", side_effect=GraphError("TEST_GRAPH_CONFLICT")):
            response = self.client.get(ROUTE)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"]["mode"], "D0_PLAN_HOLD")
        self.assertIs(response.json()["detail"]["dispatch_allowed"], False)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_unsupported_methods_are_405(self):
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                self.assertEqual(self.client.request(method, ROUTE).status_code, 405)
