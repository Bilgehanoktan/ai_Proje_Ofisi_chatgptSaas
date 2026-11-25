"""R7 pre-claim gate and transport fail-closed checks; no G5 wiring or PG."""
import inspect
import unittest
from unittest.mock import Mock, patch

from app.core.transaction import postgres_session as transport

HOLD = 'T1_STRICT_COMMIT_EXPIRY_UNPROVEN_HOLD'


class PreclaimGate(unittest.TestCase):
    def test_no_argument_or_enable_token(self):
        self.assertEqual(len(inspect.signature(transport.require_strict_postgres_commit).parameters), 0)
        with self.assertRaisesRegex(PermissionError, HOLD):
            transport.require_strict_postgres_commit()
        with self.assertRaises(TypeError):
            transport.require_strict_postgres_commit(allow=True)

    def test_preclaim_ordering_example_never_consumes(self):
        # Contract example only: this is NOT a test of an actual G5 caller.
        claim, stage, write = Mock(), Mock(), Mock()
        def proposed_owner_order():
            transport.require_strict_postgres_commit()
            claim()
            stage()
            write()
        with self.assertRaisesRegex(PermissionError, HOLD):
            proposed_owner_order()
        for step in (claim, stage, write):
            step.assert_not_called()

    def test_protected_transport_uses_same_gate(self):
        connect, mapping = Mock(), Mock()
        with patch.object(transport, 'require_strict_postgres_commit', wraps=transport.require_strict_postgres_commit) as gate:
            with self.assertRaisesRegex(PermissionError, HOLD):
                transport.protected_postgres_transaction(connect, mapping)
            gate.assert_called_once_with()
        connect.assert_not_called()
        self.assertEqual(mapping.mock_calls, [])

    def test_accidental_gate_return_still_denies_transport(self):
        connect, mapping = Mock(), Mock()
        with patch.object(transport, 'require_strict_postgres_commit', return_value=None), \
             patch.object(transport, 'postgres_transaction') as legacy:
            with self.assertRaisesRegex(PermissionError, 'T1_STRICT_COMMIT_TRANSPORT_UNIMPLEMENTED_HOLD'):
                transport.protected_postgres_transaction(connect, mapping)
            legacy.assert_not_called()
        connect.assert_not_called()
        self.assertEqual(mapping.mock_calls, [])

    def test_repeated_preflight_remains_hold(self):
        for _ in range(3):
            with self.assertRaisesRegex(PermissionError, HOLD):
                transport.require_strict_postgres_commit()


if __name__ == '__main__':
    unittest.main(verbosity=2)
