"""H01-MVP03-01 D0 binder checks; no route, identity proof, write, or durable dedup."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from app.core.orchestrator.engine import canonical_plan
from app.core.orchestrator.research_command_review import (
    ResearchCommandError, bind_research_command,
)


class ResearchCommandReviewTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((Path(__file__).resolve().parents[1] /
                                "fixtures/core.preview.json").read_text(encoding="utf-8"))["plan"]
        self.revision = canonical_plan(self.plan)["revision"]
        self.body = dict(worktype="RESEARCH", project_ref="demo-research-project",
                         plan_ref=self.plan["id"], expected_plan_revision=self.revision)

    def bind(self, raw=None, key="request-1", **kwargs):
        params = dict(max_body_bytes=4096, project_ref="demo-research-project",
                      approved_revision=self.revision, retained_plan=self.plan)
        params.update(kwargs)
        return bind_research_command(json.dumps(self.body).encode() if raw is None else raw,
                                     key, **params)

    def test_fixed_reference_is_hold_not_receipt(self):
        result = self.bind()
        self.assertEqual(result.plan_revision, self.revision)
        self.assertEqual(result.plan_digest, self.revision[7:])
        self.assertEqual(result.root_task_id, "plan")
        self.assertEqual(result.idempotency_key, "request-1")
        self.assertNotIn("request-1", repr(result))
        other = self.bind(key="request-2")
        self.assertEqual(other.idempotency_key, "request-2")
        self.assertNotEqual(result, other)
        self.assertFalse(other.persistence_allowed or other.committed)
        self.assertEqual(result.decision, "HOLD")
        self.assertFalse(result.persistence_allowed)
        self.assertFalse(result.dispatch_allowed)
        self.assertFalse(result.committed)
        self.assertEqual(result, self.bind())  # purity, not durable deduplication

    def test_reject_scope_and_stale_revision(self):
        for params in (dict(project_ref="another-project"), dict(project_ref=None),
                       dict(approved_revision="sha256:" + "0"*64)):
            with self.subTest(params=params), self.assertRaises(ResearchCommandError):
                self.bind(**params)

    def test_reject_changed_or_invalid_plan(self):
        changed = deepcopy(self.plan)
        changed["tasks"][0]["label"] = "Changed"
        invalid = deepcopy(self.plan)
        invalid["tasks"][0]["depends_on"] = ["release"]
        for plan in (changed, invalid, None):
            with self.subTest(plan=plan), self.assertRaises(ResearchCommandError):
                self.bind(retained_plan=plan)

    def test_other_internally_consistent_plan_is_not_fixed_reference(self):
        changed = deepcopy(self.plan)
        changed["tasks"][0]["label"] = "Changed"
        revision = canonical_plan(changed)["revision"]
        self.body["expected_plan_revision"] = revision
        with self.assertRaises(ResearchCommandError):
            self.bind(approved_revision=revision, retained_plan=changed)

    def test_reject_extra_fields(self):
        for field in ("principal", "grant_ref", "tenant_id", "agent", "dispatch_allowed", "goal"):
            self.body[field] = "forged"
            with self.subTest(field=field), self.assertRaises(ResearchCommandError):
                self.bind()
            del self.body[field]

    def test_reject_malformed_json(self):
        duplicate = json.dumps(self.body).encode().replace(b"{", b'{"worktype":"RESEARCH",', 1)
        for raw in (duplicate, b"\xff", b"{", b"[]", b"null", b'{"x":NaN}', b'{"x":Infinity}', b"\xef\xbb\xbf{}"):
            with self.subTest(raw=raw), self.assertRaises(ResearchCommandError):
                self.bind(raw=raw)

    def test_reject_limit_and_invalid_keys(self):
        for limit in (0, 4097, True):
            with self.subTest(limit=limit), self.assertRaises(ResearchCommandError):
                self.bind(max_body_bytes=limit)
        for key in (None, "", "a b", "x"*129):
            with self.subTest(key=key), self.assertRaises(ResearchCommandError):
                self.bind(key=key)
        for raw in (b"x"*4097, "", b""):
            with self.subTest(raw=raw), self.assertRaises(ResearchCommandError):
                self.bind(raw=raw)

    def test_reject_worktype_and_plan(self):
        self.body["worktype"] = "EXCEL_W1"
        with self.assertRaises(ResearchCommandError):
            self.bind()
        self.body["worktype"] = "RESEARCH"
        self.body["plan_ref"] = "other-plan"
        with self.assertRaises(ResearchCommandError):
            self.bind()


if __name__ == "__main__":
    unittest.main()
