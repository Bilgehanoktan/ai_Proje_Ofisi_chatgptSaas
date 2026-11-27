"""Direction A structural readback tests; no DB, grant, receipt, or actual dispatch."""
from dataclasses import replace
import json
from pathlib import Path
import unittest

from app.core.orchestrator.engine import canonical_plan
from app.core.orchestrator.research_command_review import bind_research_command
from app.core.transaction.review import BASE_ROLES, WorkItemScopeDraft, valid_intent
from app.core.transaction.readback_review import (WorkItemReadbackPin, WorkItemRoleReadback,
                                                  inspect_workitem_readback)


class WorkItemReadbackTests(unittest.TestCase):
    def setUp(self):
        plan = json.loads((Path(__file__).resolve().parents[1] /
                           'fixtures/core.preview.json').read_text(encoding='utf-8'))['plan']
        rev = canonical_plan(plan)['revision']
        body = dict(worktype='RESEARCH', project_ref='demo-research-project',
                    plan_ref=plan['id'], expected_plan_revision=rev)
        binding = bind_research_command(json.dumps(body).encode(), 'key-1', max_body_bytes=4096,
                                        project_ref=body['project_ref'], approved_revision=rev,
                                        retained_plan=plan)
        scope = WorkItemScopeDraft('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY',
                                   body['project_ref'], 'demo-human')
        self.draft = binding.to_workitem_draft(scope, project_revision='project-v1',
                                               worktype_version='research-v1', workowner_ref='demo-owner')
        self.pin = WorkItemReadbackPin(self.draft, 'demo-request', 'demo-tx', 1, 'a'*64, 'b'*64,
                                       'demo-publish', 'demo-entitlement', 'demo-issuer', 'demo-session',
                                       'authz-v1', 2, 3)
        self.rows = tuple(WorkItemRoleReadback(role, self.pin.request_id if role == 'HEAD' else 'row-'+role,
                                               self.pin, 'demo-event' if role in ('EVENT','OUTBOX') else None)
                          for role in sorted(BASE_ROLES))

    def check(self, **changes):
        args = dict(draft=self.draft, expected=self.pin, observed=self.pin,
                    rows=self.rows, outcome_unknown=False)
        args.update(changes)
        result = inspect_workitem_readback(**args)
        self.assertFalse(result.atomicity_proven or result.committed or result.commit_allowed)
        self.assertEqual(result.physical_mapping, 'PHYSICAL_MAPPING_HOLD')
        self.assertFalse(hasattr(result, 'request_id'))
        return result

    def change_role(self, target_role, **changes):
        return tuple(replace(r, **changes) if r.role == target_role else r for r in self.rows)

    def test_match_stays_hold_and_no_commit_intent(self):
        result = self.check()
        self.assertTrue(result.structural_match)
        self.assertEqual(result.reason, 'D0_WORKITEM_READBACK_MATCH_AUTHORITY_UNPROVEN')
        self.assertFalse(valid_intent(self.draft))
        self.assertFalse(valid_intent(self.pin))

    def test_each_role_required_and_duplicate_rejected(self):
        for r in self.rows:
            with self.subTest(role=r.role):
                self.assertFalse(self.check(rows=tuple(x for x in self.rows if x != r)).structural_match)
        self.assertEqual(self.check(rows=self.rows[:-1]+(self.rows[0],)).reason,
                         'WORKITEM_DUPLICATE_ROLE_HOLD')
        self.assertFalse(self.check(rows=self.change_role('AUDIT', record_id='row-EVENT')).structural_match)

    def test_identity_scope_and_plan_drift(self):
        for scope_change in (dict(tenant_id='other'),dict(company_id='other'),
                             dict(environment_id='PROD'),dict(project_ref='other-project'),
                             dict(principal_id='demo-other')):
            with self.subTest(scope_change=scope_change):
                other = replace(self.draft, scope=replace(self.draft.scope, **scope_change))
                self.assertFalse(self.check(observed=replace(self.pin, draft=other)).structural_match)
        for changes in (dict(project_revision='project-v2'),dict(worktype_version='research-v2'),
                        dict(workowner_ref='demo-other'),dict(plan_ref='other-plan'),
                        dict(plan_digest='c'*64),dict(idempotency_key='key-2')):
            with self.subTest(changes=changes):
                self.assertFalse(self.check(observed=replace(self.pin, draft=replace(self.draft, **changes))).structural_match)

    def test_expected_draft_and_readback_digest(self):
        for changes in (dict(request_id='other-request'),dict(transaction_ref='other-tx'),
                        dict(version=2),dict(version=True),dict(request_digest='c'*64),
                        dict(worktype_digest='c'*64),dict(publish_ref='other-publish'),
                        dict(entitlement_ref='other-entitlement'),dict(issuer_ref='other-issuer'),
                        dict(session_ref='other-session'),dict(authz_revision='authz-v2'),
                        dict(policy_epoch=3),dict(witness_epoch=4)):
            with self.subTest(changes=changes):
                self.assertFalse(self.check(observed=replace(self.pin, **changes)).structural_match)
        self.assertFalse(self.check(expected=None).structural_match)
        self.assertFalse(self.check(observed=None).structural_match)
        self.assertFalse(self.check(draft=replace(self.draft, idempotency_key='other-key')).structural_match)

    def test_each_role_bound_to_same_pin(self):
        for role in BASE_ROLES:
            with self.subTest(role=role):
                self.assertFalse(self.check(rows=self.change_role(role, pin=replace(self.pin, transaction_ref='other-tx'))).structural_match)
                self.assertFalse(self.check(rows=self.change_role(role, pin=replace(self.pin, request_digest='c'*64))).structural_match)
        self.assertEqual(self.check(rows=self.change_role('HEAD', record_id='other-head')).reason,
                         'WORKITEM_HEAD_REFERENCE_HOLD')

    def test_event_outbox_link_and_no_dispatch(self):
        self.assertEqual(self.check(rows=self.change_role('OUTBOX', event_ref='other-event')).reason,
                         'WORKITEM_EVENT_OUTBOX_LINK_HOLD')
        self.assertFalse(self.check(rows=self.change_role('EVENT', event_ref=None)).structural_match)
        self.assertFalse(self.check(rows=self.change_role('OUTBOX', dispatchable=True)).structural_match)
        self.assertFalse(self.check(rows=self.change_role('AUDIT', event_ref='demo-event')).structural_match)
        self.assertFalse(self.check(rows=self.change_role('AUDIT', role='ADMISSION')).structural_match)

    def test_unknown_and_absence_never_match(self):
        self.assertEqual(self.check(outcome_unknown=True).reason, 'WORKITEM_UNKNOWN_RECONCILIATION_HOLD')
        self.assertFalse(self.check(outcome_unknown=None).structural_match)
        self.assertFalse(self.check(rows=()).structural_match)
        self.assertFalse(self.check(rows=list(self.rows)).structural_match)


if __name__ == '__main__':
    unittest.main()
