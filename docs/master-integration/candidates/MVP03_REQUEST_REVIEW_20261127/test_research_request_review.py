import json
import unittest
from copy import deepcopy
from app.core.orchestrator.engine import canonical_plan
from research_request_review import inspect_research_request, MAX_BODY_BYTES


class RequestReviewTests(unittest.TestCase):
    def setUp(self):
        rows = [
            ('plan', 'Talebi ayrıştır', 'orchestrator', []),
            ('research', 'Kaynak incelemesi', 'research', ['plan']),
            ('draft', 'Çıktı taslağı', 'engineer', ['plan']),
            ('merge', 'Taslağı birleştir', 'engineer', ['research', 'draft']),
            ('qa', 'Kalite incelemesi', 'qa', ['merge']),
            ('iv', 'Bağımsız doğrulama sınırı', 'independent-verifier', ['qa']),
            ('release', 'Yayın kapısı', 'human-authority', ['iv']),
        ]
        self.plan = {'id': 'demo-plan-research', 'worktype': 'RESEARCH', 'tasks': [
            dict(id=i, label=l, role=r, depends_on=d) for i, l, r, d in rows]}
        self.body = dict(worktype='RESEARCH', project_ref='demo-project',
                         plan_ref=self.plan['id'], expected_plan_revision=canonical_plan(self.plan)['revision'])

    def check(self, *, raw=None, key='request-1', project='demo-project', plan=None, match=False):
        result = inspect_research_request(json.dumps(self.body).encode() if raw is None else raw,
                                          key, server_project_ref=project,
                                          server_plan=self.plan if plan is None else plan)
        self.assertEqual(result.structural_match, match)
        self.assertEqual(result.decision, 'HOLD')
        self.assertFalse(result.persistence_allowed)
        self.assertFalse(result.dispatch_allowed)
        self.assertFalse(result.committed)
        return result.reason

    def test_fixed_reference_only(self):
        self.assertEqual(self.check(match=True), 'D0_REQUEST_REFERENCE_MATCH_ONLY')

    def test_wrong_project(self):
        self.check(project='another-project')

    def test_wrong_revision(self):
        self.body['expected_plan_revision'] = 'sha256:' + '0'*64
        self.check()

    def test_changed_server_plan(self):
        altered = deepcopy(self.plan)
        altered['tasks'][0]['label'] = 'Changed'
        self.check(plan=altered)

    def test_invalid_graph(self):
        altered = deepcopy(self.plan)
        altered['tasks'][0]['depends_on'] = ['release']
        self.check(plan=altered)

    def test_unknown_fields_and_authority_injection(self):
        for field in ('principal', 'grant_ref', 'tenant_id', 'agent', 'dispatch_allowed', 'goal'):
            with self.subTest(field=field):
                self.body[field] = 'forged'
                self.check()
                del self.body[field]

    def test_duplicate_keys(self):
        raw = json.dumps(self.body).encode().replace(b'{', b'{"worktype":"RESEARCH",', 1)
        self.check(raw=raw)

    def test_invalid_json(self):
        for raw in (b'\xff', b'{', b'[]', b'null', b'{"x":NaN}', b'\xef\xbb\xbf{}'):
            with self.subTest(raw=raw): self.check(raw=raw)

    def test_oversize_and_nonbytes(self):
        for raw in (b'x'*(MAX_BODY_BYTES+1), '{}', b''):
            with self.subTest(kind=type(raw)): self.check(raw=raw)

    def test_invalid_key(self):
        for key in (None, '', 'a b', 'x'*129):
            with self.subTest(key=key): self.check(key=key)

    def test_wrong_worktype_or_plan(self):
        self.body['worktype'] = 'EXCEL_W1'
        self.check()
        self.body['worktype'] = 'RESEARCH'
        self.body['plan_ref'] = 'other-plan'
        self.check()

    def test_repeat_has_no_receipt(self):
        self.assertEqual(self.check(match=True), self.check(match=True))


if __name__ == '__main__':
    unittest.main()
