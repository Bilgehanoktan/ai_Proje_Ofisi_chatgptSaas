"""Actual G5 fixture through the existing authority entry; no PostgreSQL."""
from contextlib import closing
from dataclasses import replace
import sqlite3
import unittest
from unittest.mock import Mock, patch

import test_iam_org_d5g5 as g5
from app.core.transaction.intent_authority import (
    D0IntentAuthority, execute_authority_fenced_transition,
)
from app.core.transaction.org_membership_review import ProtectedOrgTransition
from app.core.transaction import postgres_session as transport

STRICT = 'T1_STRICT_COMMIT_EXPIRY_UNPROVEN_HOLD'
REVIEW = 'D5C_R8_ORG_SESSION_REVIEW_HOLD'
REF = 'D5C_R8_PROTECTED_REFERENCE_HOLD'
STOP = 'D5C_R8_PROTECTED_EXECUTION_UNIMPLEMENTED_HOLD'


class ProtectedOrgT1Tests(unittest.TestCase):
    def setUp(self):
        self.g = g5.OrgSessionTests()
        self.addCleanup(self.g.doCleanups)
        self.g.setUp()
        g, f = self.g, self.g.f
        self.authority = f.resolver._authority
        self.reference = ProtectedOrgTransition(
            resolver=f.resolver, credential=f.secrets[0], initial=f.initial,
            session=f.ref, session_sha=f.sha, read_latest=lambda: f.initial,
            store=g.store, org_reference=g.org, org_sha=g.org_sha,
            org_head=g.head, seat='worker', role='research',
            history_pin=g.history, root=f.root, owner_pin=f.pin, domain='demo-clock')
        self.journal = Mock()
        self.connect = Mock()
        self.clock = Mock()

    def snapshot(self):
        # Actual fixture DBs, not mocked row counts; no new DB schema.
        with closing(self.authority._db()) as a, closing(sqlite3.connect(self.g.db)) as o:
            return tuple(a.iterdump()), tuple(o.iterdump())

    def invoke(self, reference, authority=None):
        return execute_authority_fenced_transition(
            authority=self.authority if authority is None else authority,
            intent=self.g.f.intent, context=None, registry=None, witness=None,
            expected_binding=None, memory_path=None, reader=None, public_key=None,
            raw=None, journal=self.journal, connect=self.connect, clock=self.clock,
            protected_org=reference)

    def deny(self, reference, reason, authority=None):
        before = self.snapshot()
        with patch.object(D0IntentAuthority, 'claim_and_fence',
                          side_effect=AssertionError('claim must not be entered')) as claim:
            with self.assertRaisesRegex(PermissionError, reason):
                self.invoke(reference, authority)
            claim.assert_not_called()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.journal.mock_calls, [])
        self.connect.assert_not_called()
        self.clock.assert_not_called()

    def test_exact_g5_readback_reaches_common_strict_hold(self):
        self.assertTrue(self.g.review().structural_match)
        with patch.object(transport, 'require_strict_postgres_commit',
                          wraps=transport.require_strict_postgres_commit) as gate:
            self.deny(self.reference, STRICT)
            gate.assert_called_once_with()

    def test_invalid_org_digest_denied_before_gate(self):
        with patch.object(transport, 'require_strict_postgres_commit') as gate:
            self.deny(replace(self.reference, org_sha='f'*64), REVIEW)
            gate.assert_not_called()

    def test_revoked_session_denied_before_gate(self):
        self.assertTrue(self.g.f.resolver.revoke_local('demo-session-0', expected_revision=1))
        with patch.object(transport, 'require_strict_postgres_commit') as gate:
            self.deny(self.reference, REVIEW)
            gate.assert_not_called()

    def test_same_principal_other_session_denied(self):
        self.deny(replace(self.reference, credential=self.g.f.secrets[1]), REVIEW)

    def test_wrong_authority_denied(self):
        self.deny(self.reference, REF, authority=Mock())

    def test_malformed_reference_never_falls_back(self):
        self.deny(False, REF)

    def test_accidental_gate_return_never_falls_back(self):
        with patch.object(transport, 'require_strict_postgres_commit', return_value=None):
            self.deny(self.reference, STOP)

    def test_accidental_adapter_return_never_falls_back(self):
        with patch('app.core.transaction.org_membership_review.require_protected_org_commit',
                   return_value=None):
            self.deny(self.reference, STOP)

    def test_repeated_hold_never_consumes_claim(self):
        self.deny(self.reference, STRICT)
        self.deny(self.reference, STRICT)

    def test_legacy_iam_claim_requires_session_check(self):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'D0_IAM_CHECK_REQUIRED_HOLD'):
            with self.authority.claim_and_fence(self.g.f.root, '1'*64, '2'*64, 'tx', '3'*64):
                self.fail('legacy IAM claim must not yield')
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
