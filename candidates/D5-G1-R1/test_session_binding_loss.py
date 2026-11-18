"""D5-G1-R1 diagnostic: deliberately lossy projection, never production wiring."""
import hashlib
import importlib.util
from pathlib import Path
import secrets
import sys
import unittest
from dataclasses import replace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PINS = (
    ('iam_session', 'product/ai-company-os-backend/app/core/iam_session.py', '864fe30c72ebcc6783575c62f98748fb2d9cfff6'),
    ('identity_binding', 'candidates/D4-R4/identity_binding.py', 'e1e977880324664bb359eee3286223a796878f44'),
)


def load_exact(name, path, pin):
    p = ROOT / path
    if not p.is_file():
        p = HERE / 'source' / (name + '.py')
    raw = p.read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if actual != pin:
        raise RuntimeError('SOURCE_PIN_HOLD: ' + path)
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


I, D = [load_exact(*pin) for pin in PINS]


class SessionBindingLoss(unittest.TestCase):
    def setUp(self):
        self.a, self.b = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        self.r1 = I.SessionRecord('demo-s1', I.credential_digest(self.a), 'demo-principal',
                                  'AGENT', I.D0_SCOPE, 'demo-agent', 100, 200)
        self.r2 = replace(self.r1, session_id='demo-s2', credential_sha256=I.credential_digest(self.b))
        self.req = D.Request(I.D0_SCOPE, 'demo-project', 'sha256:' + 'a'*64, 'demo-task',
                             'demo-run', 'demo-agent', 'demo-principal', 'b'*64, 1, 1)

    def resolver(self, r2=None):
        return I.D0SessionResolver((self.r1, self.r2 if r2 is None else r2), clock=lambda: 101)

    def read(self, resolver, credential):
        return resolver.resolve(credential, expected_scope=I.D0_SCOPE)

    def lossy(self, observation):
        # Deliberately incomplete mapping; all other owner fields are synthetic constants.
        return D.Binding(self.req, observation.principal_id, 1, 1, 1, 1,
                         '1'*64, '2'*64, '3'*64, '4'*64, 'demo_role', 'demo_db',
                         'demo_cluster', observation.expires, True)

    def assert_diagnostic_match(self, first, last):
        x, y = self.lossy(first), self.lossy(last)
        self.assertEqual(D.binding_digest(x), D.binding_digest(y))
        review = D.review_binding(self.req, x, y, 101)
        self.assertTrue(review.structural_match)
        self.assertEqual(review.decision, 'HOLD')
        self.assertFalse(review.commit_allowed or review.dispatch_allowed or review.retry_allowed)

    def test_distinct_session_ids_lost_in_binding(self):
        r = self.resolver()
        a, b = self.read(r, self.a), self.read(r, self.b)
        self.assertNotEqual(a.session_id, b.session_id)
        self.assert_diagnostic_match(a, b)

    def test_revoked_session_replaced_by_other_session_in_lossy_binding(self):
        r = self.resolver()
        old = self.read(r, self.a)
        self.assertTrue(r.revoke_local(old.session_id, expected_revision=old.revision))
        self.assertIsNone(self.read(r, self.a))
        other = self.read(r, self.b)
        self.assertGreater(other.revision, old.revision)
        self.assert_diagnostic_match(old, other)

    def test_human_agent_kind_lost_in_binding(self):
        human = replace(self.r2, kind='HUMAN', agent_instance_id=None)
        r = self.resolver(human)
        a, b = self.read(r, self.a), self.read(r, self.b)
        self.assertNotEqual(a.kind, b.kind)
        self.assertNotEqual(a.agent_instance_id, b.agent_instance_id)
        self.assert_diagnostic_match(a, b)

    def test_distinct_agent_instance_lost_in_binding(self):
        r = self.resolver(replace(self.r2, agent_instance_id='demo-other-agent'))
        a, b = self.read(r, self.a), self.read(r, self.b)
        self.assertNotEqual(a.agent_instance_id, b.agent_instance_id)
        self.assert_diagnostic_match(a, b)

    def test_existing_d4_controls_still_reject(self):
        r = self.resolver()
        old = self.lossy(self.read(r, self.a))
        for bad, tick in ((replace(old, active=False), 101), (old, 200),
                          (replace(old, registry_revision=2), 101),
                          (replace(old, authenticated_principal='demo-other'), 101)):
            with self.subTest(tick=tick):
                review = D.review_binding(self.req, old, bad, tick)
                self.assertFalse(review.structural_match or review.commit_allowed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
