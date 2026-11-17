import unittest
from dataclasses import replace
from scope_contract import Binding, Scope, SessionFacts, review_checkout, review_release


class ScopeContractTests(unittest.TestCase):
    def setUp(self):
        self.scope = Scope('tenant-a', 'company-a', 'test')
        self.binding = Binding(self.scope, 'principal-a', 'role-a', 3)
        self.facts = SessionFacts('role-a', 'role-a', 'd4', True, True, False, False, False, False)

    def check(self, **kw):
        args = dict(binding=self.binding, reference=self.binding, request_scope=self.scope,
                    request_principal='principal-a', facts=self.facts, database='d4')
        args.update(kw)
        return review_checkout(**args)

    def test_match_not_authorization(self):
        self.assertEqual(self.check(), 'MATCH_REVIEW_ONLY')

    def test_missing_reference(self):
        self.assertEqual(self.check(reference=None), 'HOLD_MISSING_REFERENCE')

    def test_cross_scope(self):
        for field in ('tenant', 'company', 'environment'):
            with self.subTest(field=field):
                self.assertEqual(self.check(request_scope=replace(self.scope, **{field: 'other'})), 'HOLD_SCOPE_OR_REVISION')

    def test_wrong_principal(self):
        self.assertEqual(self.check(request_principal='other'), 'HOLD_SCOPE_OR_REVISION')

    def test_stale_revision(self):
        self.assertEqual(self.check(reference=replace(self.binding, revision=4)), 'HOLD_SCOPE_OR_REVISION')

    def test_invalid_revision(self):
        self.assertEqual(self.check(binding=replace(self.binding, revision=True)), 'HOLD_INVALID_BINDING')

    def test_wrong_session_identity(self):
        for field in ('session_user', 'current_user', 'database'):
            with self.subTest(field=field):
                self.assertEqual(self.check(facts=replace(self.facts, **{field: 'other'})), 'HOLD_SESSION')

    def test_elevated_roles(self):
        for field in ('superuser', 'bypassrls', 'owner_membership', 'other_scope_membership'):
            with self.subTest(field=field):
                self.assertEqual(self.check(facts=replace(self.facts, **{field: True})), 'HOLD_SESSION')

    def test_dirty_or_rls_off(self):
        for field in ('idle', 'row_security'):
            with self.subTest(field=field):
                self.assertEqual(self.check(facts=replace(self.facts, **{field: False})), 'HOLD_SESSION')

    def release(self, **kw):
        args = dict(outcome='COMMITTED', rollback_ok=True, reset_ok=True, idle=True, identity_match=True, clean_state=True)
        args.update(kw)
        return review_release(**args)

    def test_no_pool_reuse(self):
        self.assertEqual(self.release(), 'CLOSE_DEDICATED_REVIEW_ONLY')

    def test_unknown_quarantine(self):
        self.assertEqual(self.release(outcome='UNKNOWN'), 'QUARANTINE_RECONCILE')

    def test_cleanup_failure(self):
        for field in ('rollback_ok', 'reset_ok', 'idle', 'identity_match', 'clean_state'):
            with self.subTest(field=field):
                self.assertEqual(self.release(**{field: False}), 'DISCARD')

    def test_unknown_status_denied(self):
        self.assertEqual(self.release(outcome='RETRY'), 'DISCARD')


if __name__ == '__main__':
    unittest.main()
