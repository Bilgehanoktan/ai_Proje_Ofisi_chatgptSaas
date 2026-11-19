"""Isolated protocol tests of exact MEM-05E source, using explicit reader doubles.
Not SQLite, cryptographic, owner, or protected transaction acceptance.
"""
import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace, ModuleType
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parent

@dataclass(frozen=True)
class JointContext:
    invocation: object

@dataclass(frozen=True)
class InvocationRouteContext:
    envelope: object
    current_run: object
    current_lease: object
    clock: object

@dataclass(frozen=True)
class MemoryRecoveryReview:
    reason: str = 'D0_MEMORY_RECOVERY_HEAD_MATCH_ONLY'
    history_match: bool = True
    checkpoint_match: bool = True
    pending_observation: str = 'NONE_OBSERVED'
    decision: str = 'HOLD'
    quarantine_required: bool = True
    retrieval_allowed: bool = False
    release_allowed: bool = False
    provider_call_allowed: bool = False
    dispatch_allowed: bool = False
    spend_allowed: bool = False
    settlement_allowed: bool = False
    transition_allowed: bool = False
    retry_allowed: bool = False
    replay_allowed: bool = False
    publish_allowed: bool = False
    clear_pending_allowed: bool = False
    prune_allowed: bool = False
    independent_verified: bool = False
    atomicity_verified: bool = False


def stub(name, **attrs):
    m = ModuleType(name)
    m.__dict__.update(attrs)
    return m


def fail(*args):
    raise AssertionError('original reader must be replaced by test double')


def digest_ok(x):
    return type(x) is str and len(x) == 64 and all(v in '0123456789abcdef' for v in x)


DEPS = {
    'app.core.agent_runtime.joint_context': stub('joint', JointContext=JointContext, joint_context_digest=fail),
    'app.core.agent_runtime.memory_witness': stub('witness', WitnessedReview=object, inspect_witnessed_context=fail),
    'app.core.transaction.review': stub('review', digest_ok=digest_ok),
    'app.engines.model_gateway.invocation_route_binding': stub('route', InvocationRouteContext=InvocationRouteContext),
    'app.engines.model_gateway.provider_preflight': stub('preflight', ProviderPreflightReview=object, inspect_provider_preflight=fail),
    'app.engines.model_gateway.runtime_binding': stub('binding', invocation_digest=fail),
    'app.core.agent_runtime.memory_recovery_review': stub('recovery', MemoryRecoveryReview=MemoryRecoveryReview, inspect_memory_recovery=fail),
}
with patch.dict(sys.modules, DEPS):
    spec = importlib.util.spec_from_file_location('tested_gateway', ROOT/'memory_gateway_review.py')
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)


class CompositionProtocol(unittest.TestCase):
    def setUp(self):
        self.env = SimpleNamespace(lease='envelope_lease')
        self.ctx = InvocationRouteContext(self.env, 'run', 'current_lease', 'clock')
        self.j = JointContext(self.env)
        self.args = dict(context=self.j, expected_joint_pin='a'*64, ctx=self.ctx,
                         memory_path='db', reader='reader', expected_witness='witness',
                         public_key='pub', snapshot='snapshot', reference='ref',
                         budget_reference='budget', expected_owner_pin='b'*64,
                         checkpoint_body=b'checkpoint', checkpoint_signature=b'signature',
                         checkpoint_sha='c'*64)
        self.calls = []
        self.recovery = Mock(side_effect=lambda *a: self.calls.append('recovery') or MemoryRecoveryReview())
        self.gateway = Mock(side_effect=lambda *a: self.calls.append('gateway') or bridge.MemoryGatewayReview('D0_MEMORY_GATEWAY_MATCH_ONLY', True))
        self.addCleanup(patch.stopall)
        patch.object(bridge, 'inspect_memory_recovery', self.recovery).start()
        patch.object(bridge, 'inspect_memory_gateway', self.gateway).start()

    def review(self, **changes):
        a = self.args | changes
        r = bridge.inspect_recovered_memory_gateway(**a)
        self.assertIs(type(r), bridge.MemoryGatewayReview)
        self.assertEqual(r.decision, 'HOLD')
        for k in ('retrieval_allowed', 'release_allowed', 'provider_call_allowed', 'dispatch_allowed', 'spend_allowed', 'settlement_allowed', 'transition_allowed', 'retry_allowed', 'independent_verified', 'atomicity_verified'):
            self.assertIs(getattr(r, k), False)
        return r

    def test_order_and_exact_shared_inputs(self):
        r = self.review()
        self.assertTrue(r.structural_match)
        self.assertEqual(r.reason, 'D0_RECOVERED_MEMORY_GATEWAY_MATCH_ONLY')
        self.assertEqual(self.calls, ['recovery','gateway','recovery'])
        self.assertEqual(self.recovery.call_args_list[0], self.recovery.call_args_list[1])
        self.assertEqual(self.recovery.call_args.args, ('db','reader','witness','pub',b'checkpoint',b'signature','c'*64,'run','current_lease','envelope_lease','clock'))
        self.assertEqual(self.gateway.call_args.args, (self.j,'a'*64,self.ctx,'db','reader','witness','pub','snapshot','ref','budget','b'*64))

    def test_pending_even_with_match(self):
        for state in ('BASE_ONLY','TARGET_OBSERVED','UNVERIFIED'):
            self.recovery.side_effect = None
            self.recovery.return_value = MemoryRecoveryReview(pending_observation=state)
            self.assertEqual(self.review().reason,'MEMORY_GATEWAY_RECOVERY_HOLD')
        self.gateway.assert_not_called()

    def test_missing_full_history_or_checkpoint(self):
        for r in (MemoryRecoveryReview(history_match=False),MemoryRecoveryReview(checkpoint_match=False),None):
            self.recovery.side_effect = None
            self.recovery.return_value = r
            self.assertFalse(self.review().structural_match)
        self.gateway.assert_not_called()

    def test_any_recovery_permission_rejected(self):
        for flag in ('retry_allowed','publish_allowed','clear_pending_allowed','replay_allowed','atomicity_verified','independent_verified','provider_call_allowed'):
            self.recovery.side_effect = None
            self.recovery.return_value = MemoryRecoveryReview(**{flag:True})
            self.assertFalse(self.review().structural_match)
        self.gateway.assert_not_called()

    def test_quarantine_or_decision_changed(self):
        self.recovery.side_effect = None
        for r in (MemoryRecoveryReview(quarantine_required=False), MemoryRecoveryReview(decision='ALLOW')):
            self.recovery.return_value = r
            self.assertFalse(self.review().structural_match)
        self.gateway.assert_not_called()

    def test_gateway_failure_no_second_recovery(self):
        self.gateway.side_effect = None
        self.gateway.return_value = bridge.MemoryGatewayReview('MEMORY_GATEWAY_PREFLIGHT_HOLD')
        self.assertEqual(self.review().reason,'MEMORY_GATEWAY_RECOVERY_PREFLIGHT_HOLD')
        self.assertEqual(self.recovery.call_count,1)

    def test_gateway_forged_positive_flag_rejected(self):
        bad = bridge.MemoryGatewayReview('D0_MEMORY_GATEWAY_MATCH_ONLY',True)
        object.__setattr__(bad,'dispatch_allowed',True)
        self.gateway.side_effect = None
        self.gateway.return_value = bad
        self.assertFalse(self.review().structural_match)
        self.assertEqual(self.recovery.call_count,1)

    def test_second_recovery_pending(self):
        self.recovery.side_effect = [MemoryRecoveryReview(), MemoryRecoveryReview(pending_observation='TARGET_OBSERVED')]
        self.assertEqual(self.review().reason,'MEMORY_GATEWAY_RECOVERY_RECHECK_HOLD')

    def test_second_recovery_error(self):
        self.recovery.side_effect = [MemoryRecoveryReview(), RuntimeError('sensitive')]
        r=self.review()
        self.assertEqual(r.reason,'MEMORY_GATEWAY_RECOVERY_ERROR_HOLD')
        self.assertNotIn('sensitive',repr(r))

    def test_input_mismatch_no_read(self):
        for changes in (dict(context=JointContext(object())),dict(ctx=None),dict(checkpoint_sha='bad')):
            self.assertEqual(self.review(**changes).reason,'MEMORY_GATEWAY_RECOVERY_INPUT_HOLD')
        self.recovery.assert_not_called()
        self.gateway.assert_not_called()

    def test_gateway_exception_no_leak(self):
        self.gateway.side_effect = RuntimeError('private')
        self.assertEqual(self.review().reason,'MEMORY_GATEWAY_RECOVERY_ERROR_HOLD')
        self.assertEqual(self.recovery.call_count,1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
