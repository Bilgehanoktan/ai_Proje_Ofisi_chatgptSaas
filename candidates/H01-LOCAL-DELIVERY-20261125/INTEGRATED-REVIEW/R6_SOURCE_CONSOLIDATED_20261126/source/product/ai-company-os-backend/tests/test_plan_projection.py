"""D0 offline test candidates. NOT_RUN; run only under separately authorized test scope."""
import copy
import json
from pathlib import Path
import unittest
from app.core.dag import GraphError
from app.core.orchestrator import canonical_plan, preview_plan

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

class PlanProjectionTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((FIXTURES / "core.preview.json").read_text(encoding="utf-8"))["plan"]

    def test_reference_and_v0(self):
        result = canonical_plan(self.plan)
        expected = json.loads((FIXTURES / "core.plan.projection.json").read_text(encoding="utf-8"))
        self.assertEqual(result, expected)
        self.assertEqual(preview_plan(self.plan)["waves"], result["waves"])
        self.assertFalse(result["dispatch_allowed"])
        self.assertFalse(result["release_ready"])
        self.assertTrue(all(t["state"] == "HOLD" and t["run_id"] is None for t in result["tasks"]))

    def test_permutation_and_content_change(self):
        other = copy.deepcopy(self.plan)
        other["tasks"].reverse()
        for t in other["tasks"]:
            t["depends_on"].reverse()
        self.assertEqual(canonical_plan(other), canonical_plan(self.plan))
        other["tasks"][0]["label"] += " changed"
        self.assertNotEqual(canonical_plan(other)["digest"], canonical_plan(self.plan)["digest"])

    def test_bad_graphs(self):
        for deps, code in [(["release"], "DAG_CYCLE"), (["missing"], "DEPENDENCY_MISSING"), (["plan"], "DEPENDENCY_INVALID")]:
            with self.subTest(code=code):
                other = copy.deepcopy(self.plan)
                other["tasks"][0]["depends_on"] = deps
                with self.assertRaisesRegex(GraphError, code):
                    canonical_plan(other)

    def test_qa_bypass(self):
        other = copy.deepcopy(self.plan)
        tasks = {t["id"]: t for t in other["tasks"]}
        tasks["qa"]["depends_on"] = ["research"]
        tasks["iv"]["depends_on"] = ["qa", "merge"]
        with self.assertRaisesRegex(GraphError, "PRODUCER_QA_BYPASS"):
            canonical_plan(other)

    def test_malformed_and_empty(self):
        for value in ([], [{"id": "a"}], [dict(self.plan["tasks"][0], depends_on="bad")]):
            with self.subTest(value=value):
                other = dict(self.plan, tasks=value)
                with self.assertRaises(GraphError):
                    canonical_plan(other)
