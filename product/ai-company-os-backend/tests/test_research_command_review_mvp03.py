"""H01-MVP03-01 D0 binder checks; no route, identity proof, write, or durable dedup."""
from copy import deepcopy
from dataclasses import replace
from unittest.mock import Mock
import json
from pathlib import Path
import unittest

from app.core.orchestrator.engine import canonical_plan
from app.core.orchestrator.research_command_review import (
    ResearchCommandError, bind_research_command, bind_research_publication_draft,
)

from app.core.agent_runtime.lifecycle import Scope
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.review import (BASE_ROLES, LogicalIntent, Operation, WorkItemScopeDraft,
                                         inspect_workitem_request, required_roles, valid_intent)


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


    def workitem_draft(self, binding=None, scope=None, **overrides):
        refs = dict(project_revision="project-rev-1", worktype_version="research-v1",
                    workowner_ref="demo-owner")
        refs.update(overrides)
        if scope is None:
            scope = WorkItemScopeDraft("synthetic-tenant", "synthetic-company", "A0_SAMPLE_ONLY",
                                       self.body["project_ref"], "demo-human")
        return (binding or self.bind()).to_workitem_draft(scope, **refs)

    def test_workitem_review_is_connected_without_transaction(self):
        binding = self.bind()
        draft = self.workitem_draft(binding)
        factory = Mock(side_effect=AssertionError("transaction opened"))
        result = LogicalT1Coordinator(factory).review_workitem_request(draft)
        self.assertEqual(draft.operation, "WORKITEM_REQUEST")
        self.assertEqual(draft.plan_digest, binding.plan_digest)
        self.assertEqual(draft.idempotency_key, binding.idempotency_key)
        self.assertEqual(draft.expected_version, 0)
        self.assertEqual(draft.scope.project_ref, binding.project_ref)
        self.assertTrue(result.structural_match)
        self.assertEqual(set(result.missing_roles), BASE_ROLES)
        self.assertEqual(result.decision, "HOLD")
        self.assertEqual(result.physical_mapping, "PHYSICAL_MAPPING_HOLD")
        self.assertIsNone(result.committed_version)
        self.assertFalse(result.committed or result.commit_allowed or result.dispatch_allowed)
        self.assertFalse(any(hasattr(draft, key) for key in ("request_id", "run_id", "grant_ref", "lease_ref", "budget_ref")))
        factory.assert_not_called()

    def test_workitem_cannot_enter_existing_commit(self):
        draft = self.workitem_draft()
        factory = Mock(side_effect=AssertionError("transaction opened"))
        coordinator = LogicalT1Coordinator(factory)
        self.assertFalse(valid_intent(draft))
        with self.assertRaisesRegex(ValueError, "T1_INTENT_INVALID"):
            coordinator.commit(draft)
        factory.assert_not_called()

    def test_workitem_scope_and_project_mismatch(self):
        scope = self.workitem_draft().scope
        for changes in (dict(tenant_id="other"), dict(company_id="other"),
                        dict(environment_id="PROD"), dict(principal_id="real-human"),
                        dict(project_ref="other-project")):
            with self.subTest(changes=changes), self.assertRaises(ResearchCommandError):
                self.workitem_draft(scope=replace(scope, **changes))

    def test_workitem_invalid_reference_and_plan_pins(self):
        draft = self.workitem_draft()
        for change in (dict(project_revision=""), dict(worktype_version=None), dict(workowner_ref="a b"),
                       dict(plan_digest="0"*64), dict(idempotency_key="a b")):
            with self.subTest(change=change):
                result = inspect_workitem_request(replace(draft, **change))
                self.assertEqual(result.decision, "DENY")
                self.assertFalse(result.structural_match or result.commit_allowed)
        with self.assertRaises(ResearchCommandError):
            self.workitem_draft(binding=replace(self.bind(), plan_ref="other-plan"))
        with self.assertRaises(ResearchCommandError):
            self.workitem_draft(project_revision="")

    def test_workitem_opaque_key_distinction_not_durable_dedup(self):
        draft = self.workitem_draft(self.bind(key="request-1"))
        other = self.workitem_draft(self.bind(key="request-2"))
        self.assertNotEqual(draft, other)
        self.assertNotIn("request-1", repr(draft))
        self.assertEqual(draft, self.workitem_draft())
        self.assertEqual(inspect_workitem_request(other).decision, "HOLD")

    def test_workitem_does_not_extend_run_operations(self):
        scope = Scope("synthetic-tenant", "synthetic-company", "A0_SAMPLE_ONLY", self.revision,
                      "plan", "demo-run", "demo-agent", "demo-principal")
        intent = LogicalIntent(scope, Operation.ADMISSION, 0, "a"*64, "effect", "idem",
                               "grant", "lease", "budget", 1, 1)
        self.assertEqual(set(Operation), {Operation.ADMISSION, Operation.STATE_MUTATION, Operation.TERMINAL})
        self.assertTrue(valid_intent(intent))
        self.assertEqual(required_roles(intent), BASE_ROLES | {"ADMISSION", "LEASE", "BUDGET"})
        self.assertEqual(required_roles(replace(intent, operation=Operation.TERMINAL)), BASE_ROLES | {"LEASE", "BUDGET"})
        self.assertEqual(required_roles(replace(intent, operation=Operation.STATE_MUTATION)), BASE_ROLES)
        self.assertFalse(valid_intent(replace(intent, lease_ref="")))
        self.assertFalse(valid_intent(replace(intent, grant_ref="")))



    def publication_draft(self, package=None, binding=None, plan=None, scope=None):
        if package is None:
            package = (Path(__file__).resolve().parents[1] /
                       'fixtures/research.worktype.publication_candidate.json').read_bytes()
        if scope is None:
            scope = WorkItemScopeDraft('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY',
                                      self.body['project_ref'], 'demo-human')
        return bind_research_publication_draft(self.bind() if binding is None else binding,
                                               package, self.plan if plan is None else plan, scope,
                                               project_revision='project-v1', workowner_ref='demo-owner')

    def test_publication_exact_candidate_binds_version_without_authority(self):
        candidate, draft = self.publication_draft()
        self.assertEqual(candidate.worktype_id, 'RESEARCH')
        self.assertEqual(candidate.version, 'mvp03-request-1-rc1')
        self.assertEqual(candidate.content_digest, '10f87e6cdb8a6b1db7be79db92ff1fef40d79a999b6be7080ca2382c5b57fd3f')
        self.assertNotEqual(candidate.content_digest, draft.plan_digest)
        self.assertEqual(candidate.source_commit, '325ee3009b80f1d1651013e3261c9a03dd7fe4bb')
        self.assertEqual(candidate.plan_revision, draft.plan_revision)
        self.assertEqual(candidate.version, draft.worktype_version)
        self.assertEqual(candidate.decision, 'HOLD')
        self.assertFalse(candidate.published or candidate.activation_allowed or candidate.admission_allowed or candidate.persistence_allowed)
        self.assertFalse(valid_intent(draft))
        self.assertFalse(inspect_workitem_request(draft).commit_allowed)

    def test_publication_mutations_rejected(self):
        raw = (Path(__file__).resolve().parents[1] /
               'fixtures/research.worktype.publication_candidate.json').read_bytes()
        for value in (raw.replace(b'mvp03-request-1-rc1', b'mvp03-request-2-rc1'),
                      raw.replace(b'REVIEW_CANDIDATE_NOT_PUBLISHED', b'PUBLISHED'),
                      raw.replace(b'325ee3009b80f1d1651013e3261c9a03dd7fe4bb', b'0'*40),
                      raw + b' ', b'', bytearray(raw)):
            with self.subTest(value_type=type(value)), self.assertRaisesRegex(ResearchCommandError, 'PUBLICATION_PACKAGE_PIN_MISMATCH'):
                self.publication_draft(package=value)

    def test_publication_plan_and_binding_drift_rejected(self):
        changed = deepcopy(self.plan)
        changed['tasks'][0]['label'] = 'Changed'
        with self.assertRaisesRegex(ResearchCommandError, 'PUBLICATION_PLAN_PIN_MISMATCH'):
            self.publication_draft(plan=changed)
        with self.assertRaisesRegex(ResearchCommandError, 'PUBLICATION_PLAN_PIN_MISMATCH'):
            self.publication_draft(binding=replace(self.bind(), plan_digest='0'*64))
        with self.assertRaisesRegex(ResearchCommandError, 'PUBLICATION_BINDING_INVALID'):
            self.publication_draft(binding={})

    def test_publication_cannot_bypass_scope_and_commit(self):
        for scope in (WorkItemScopeDraft('other', 'synthetic-company', 'A0_SAMPLE_ONLY', self.body['project_ref'], 'demo-human'),
                      WorkItemScopeDraft('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY', 'other-project', 'demo-human')):
            with self.subTest(scope=scope), self.assertRaises(ResearchCommandError):
                self.publication_draft(scope=scope)
        _, draft = self.publication_draft()
        factory = Mock(side_effect=AssertionError('transaction opened'))
        with self.assertRaisesRegex(ValueError, 'T1_INTENT_INVALID'):
            LogicalT1Coordinator(factory).commit(draft)
        factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
