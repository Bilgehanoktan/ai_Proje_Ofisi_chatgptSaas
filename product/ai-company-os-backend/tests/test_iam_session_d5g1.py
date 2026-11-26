import secrets
import unittest
from dataclasses import replace
from app.core.iam_session import D0_SCOPE, D0SessionResolver, SessionRecord, credential_digest


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.secret = secrets.token_urlsafe(32)
        self.now = 100
        self.record = SessionRecord('demo-session', credential_digest(self.secret), 'demo-person',
                                    'HUMAN', D0_SCOPE, None, 100, 200)
        self.resolver = D0SessionResolver((self.record,), clock=lambda: self.now)

    def resolve(self, secret=None, scope=D0_SCOPE):
        return self.resolver.resolve(self.secret if secret is None else secret, expected_scope=scope)

    def test_valid_no_grant(self):
        obs = self.resolve()
        self.assertEqual((obs.principal_id, obs.kind, obs.revision), ('demo-person', 'HUMAN', 1))
        self.assertEqual(obs.decision, 'HOLD')
        self.assertFalse(obs.grant_allowed or obs.dispatch_allowed)
        self.assertNotIn(self.secret, repr(obs))
        self.assertNotIn(self.record.credential_sha256, repr(self.record))

    def test_wrong_secret(self):
        self.assertIsNone(self.resolve(secrets.token_urlsafe(32)))

    def test_malformed(self):
        for value in ('', 'demo-person', 'A'*42+'B', 'A'*44, 42, self.record.credential_sha256):
            with self.subTest(value=type(value)):
                self.assertIsNone(self.resolve(value))

    def test_scope_mismatch(self):
        for scope in (('other', *D0_SCOPE[1:]), (D0_SCOPE[0], 'other', D0_SCOPE[2]),
                      (*D0_SCOPE[:2], 'PROD'), list(D0_SCOPE)):
            self.assertIsNone(self.resolve(scope=scope))

    def test_agent_identity(self):
        agent = replace(self.record, kind='AGENT', agent_instance_id='demo-agent')
        obs = D0SessionResolver((agent,), clock=lambda: 101).resolve(self.secret, expected_scope=D0_SCOPE)
        self.assertEqual((obs.kind, obs.agent_instance_id), ('AGENT', 'demo-agent'))
        self.assertFalse(obs.grant_allowed)

    def test_kind_mismatch(self):
        for record in (replace(self.record, agent_instance_id='demo-agent'), replace(self.record, kind='AGENT'),
                       replace(self.record, kind='IV'), replace(self.record, principal_id='real-person')):
            with self.assertRaises(ValueError):
                D0SessionResolver((record,))

    def test_duplicate_session_or_secret(self):
        for record in (replace(self.record, credential_sha256='a'*64), replace(self.record, session_id='demo-other')):
            with self.assertRaises(ValueError):
                D0SessionResolver((self.record, record))

    def test_invalid_bootstrap(self):
        for record in (replace(self.record, expires=100), replace(self.record, expires=1001),
                       replace(self.record, scope=('x', 'y', 'z')), replace(self.record, issued=True)):
            with self.assertRaises(ValueError):
                D0SessionResolver((record,))

    def test_future_issue(self):
        self.now = 99
        self.assertIsNone(self.resolve())

    def test_exact_expiry(self):
        self.now = 199
        self.assertIsNotNone(self.resolve())
        self.now = 200
        self.assertIsNone(self.resolve())

    def test_clock_rollback_latches(self):
        self.assertIsNotNone(self.resolve())
        self.now = 99
        self.assertIsNone(self.resolve())
        self.now = 101
        self.assertIsNone(self.resolve())

    def test_clock_exception_latches(self):
        def clock():
            if self.now == 100:
                raise RuntimeError('clock failed')
            return self.now
        self.resolver = D0SessionResolver((self.record,), clock=clock)
        self.assertIsNone(self.resolve())
        self.now = 101
        self.assertIsNone(self.resolve())

    def test_revocation_cas(self):
        self.assertFalse(self.resolver.revoke_local('demo-session', expected_revision=2))
        self.assertIsNotNone(self.resolve())
        self.assertTrue(self.resolver.revoke_local('demo-session', expected_revision=1))
        self.assertIsNone(self.resolve())
        self.assertFalse(self.resolver.revoke_local('demo-session', expected_revision=2))

    def test_other_session_survives(self):
        secret = secrets.token_urlsafe(32)
        other = replace(self.record, session_id='demo-other', credential_sha256=credential_digest(secret))
        self.resolver = D0SessionResolver((self.record, other), clock=lambda: self.now)
        self.assertTrue(self.resolver.revoke_local('demo-session', expected_revision=1))
        self.assertEqual(self.resolve(secret).revision, 2)


if __name__ == '__main__':
    unittest.main()
