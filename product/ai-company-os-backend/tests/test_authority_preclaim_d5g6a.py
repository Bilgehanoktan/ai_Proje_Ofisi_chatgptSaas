"""Selected D0 preclaim controls; real authority SQLite, no live T1 or PG."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from hashlib import sha256
from inspect import signature
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from app.core.transaction import intent_authority as ia
from app.core.transaction import postgres_session as pg


class ProtectedAuthorityTests(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name).resolve() / 'g6a.authority.sqlite'
        self.root = ia.RootPin('a'*64, 'b'*64, 1)
        self.authority = ia.D0IntentAuthority.create(self.path, self.root)
        self.connect = Mock(side_effect=AssertionError('connection must not open'))
        self.clock = Mock(side_effect=AssertionError('clock must not run'))
        self.journal = Mock(spec=['stage'])
        self.journal.stage.side_effect = AssertionError('journal must not stage')

    def args(self, authority=None):
        return dict(authority=self.authority if authority is None else authority,
                    intent=object(), context=object(), registry=object(), witness=object(),
                    expected_binding=object(), memory_path=object(), reader=object(),
                    public_key=object(), raw=object(), journal=self.journal,
                    connect=self.connect, clock=self.clock)

    def snapshot(self, path=None):
        p = self.path if path is None else path
        with closing(sqlite3.connect(p.as_uri()+'?mode=ro', uri=True)) as db:
            roots = db.execute('SELECT * FROM roots ORDER BY seq').fetchall()
            claims = db.execute('SELECT * FROM claims ORDER BY scope_sha').fetchall()
        return roots, claims, sha256(p.read_bytes()).hexdigest()

    def denied(self, reason='T1_STRICT_COMMIT_EXPIRY_UNPROVEN_HOLD', authority=None):
        with self.assertRaisesRegex(PermissionError, reason):
            ia.execute_protected_authority_fenced_transition(**self.args(authority))
        self.connect.assert_not_called()
        self.clock.assert_not_called()
        self.journal.stage.assert_not_called()

    def test_real_gate_before_claim_or_legacy(self):
        before = self.snapshot()
        with patch.object(ia.D0IntentAuthority, 'claim_and_fence', side_effect=AssertionError('claim')) as claim, \
             patch.object(ia, 'execute_authority_fenced_transition', side_effect=AssertionError('fallback')) as legacy:
            self.denied()
            claim.assert_not_called()
            legacy.assert_not_called()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(before[1], [])

    def test_gate_return_still_denied(self):
        before = self.snapshot()
        with patch.object(pg, 'require_strict_postgres_commit', return_value=None) as gate, \
             patch.object(ia, 'execute_authority_fenced_transition', side_effect=AssertionError('fallback')) as legacy:
            self.denied('T1_PROTECTED_AUTHORITY_COMPOSITION_UNIMPLEMENTED_HOLD')
            gate.assert_called_once_with()
            legacy.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_existing_claim_preserved(self):
        with self.authority.claim_and_fence(self.root, 'c'*64, 'd'*64, 'demo-tx', 'e'*64):
            pass
        before = self.snapshot()
        self.assertEqual(len(before[1]), 1)
        self.denied()
        self.assertEqual(self.snapshot(), before)

    def test_partial_iam_store_unchanged(self):
        path = self.path.with_name('iam.authority.sqlite')
        authority = ia.D0IntentAuthority.create(path, self.root, iam_bootstrap=True)
        before = self.snapshot(path)
        self.denied(authority=authority)
        self.assertEqual(self.snapshot(path), before)
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as db:
            self.assertEqual(db.execute('SELECT id FROM iam_bootstrap').fetchall(), [(1,)])

    def test_concurrent_denials_no_claim(self):
        before = self.snapshot()
        def attempt():
            try:
                ia.execute_protected_authority_fenced_transition(**self.args())
            except PermissionError as exc:
                return str(exc)
            return 'UNEXPECTED_RETURN'
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: attempt(), range(8)))
        self.assertEqual(results, ['T1_STRICT_COMMIT_EXPIRY_UNPROVEN_HOLD']*8)
        self.assertEqual(self.snapshot(), before)
        self.connect.assert_not_called()
        self.journal.stage.assert_not_called()

    def test_legacy_signature_preserved(self):
        legacy = signature(ia.execute_authority_fenced_transition)
        protected = signature(ia.execute_protected_authority_fenced_transition)
        self.assertEqual(legacy.parameters, protected.parameters)
