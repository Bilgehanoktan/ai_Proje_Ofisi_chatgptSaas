"""New Runtime/MEM-05E boundary tests; no crypto, provider or persistence execution."""
import sys
from dataclasses import dataclass, replace
from types import ModuleType
from unittest import TestCase
from unittest.mock import Mock, patch

from app.core.agent_runtime.lifecycle import ClockSample, LeaseObservation, RunObservation, RunState, Scope
from app.engines.model_gateway.invocation_route_binding import InvocationRouteContext
from app.engines.model_gateway import runtime_model_review as runtime

MEMORY_MODULE = 'app.core.agent_runtime.memory_gateway_review'


@dataclass(frozen=True)
class ReviewDouble:
    reason: str
    structural_match: bool = False
    decision: str = 'HOLD'
    provider_call_allowed: bool = False
    dispatch_allowed: bool = False
    spend_allowed: bool = False
    retry_allowed: bool = False


class RuntimeRecoveredMemoryLinkTests(TestCase):
    def setUp(self):
        scope = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',
                      'sha256:'+'a'*64,'research','demo-run','demo-agent','demo-principal')
        self.run = RunObservation(scope, RunState.RUNNING, 2, 0)
        self.lease = LeaseObservation(scope,'lease','grant',1,0,1,2,3,150,90)
        self.old_clock = ClockSample(100,2,3,30)
        self.now = ClockSample(105,2,3,30)
        # Non-consumed values are opaque sentinels: this tests the Runtime seam,
        # not the existing recovery or provider inspectors.
        self.ctx = InvocationRouteContext(None,(), 'a'*64, self.run, self.lease,
                                          self.old_clock,b'demo',None,'b'*64,(),(), 'c'*64,1)
        self.values = [object() for _ in range(10)]
        self.recovery = ModuleType(MEMORY_MODULE)
        self.recovery.MemoryGatewayReview = ReviewDouble
        self.recovery.inspect_recovered_memory_gateway = Mock(
            return_value=ReviewDouble('D0_RECOVERED_MEMORY_GATEWAY_MATCH_ONLY',True))
        self.bridge = self.recovery.inspect_recovered_memory_gateway
        self.patch = patch.dict(sys.modules,{MEMORY_MODULE:self.recovery})
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.ordinary = patch.object(runtime,'inspect_provider_preflight',
                                     side_effect=AssertionError('ordinary preflight fallback'))
        self.ordinary_mock = self.ordinary.start(); self.addCleanup(self.ordinary.stop)

    def call(self, **changes):
        args = dict(ctx=self.ctx,current_run=self.run,current_lease=self.lease,clock=self.now,
                    context=self.values[0],expected_joint_pin=self.values[1],memory_path=self.values[2],
                    reader=self.values[3],expected_witness=self.values[4],public_key=self.values[5],
                    snapshot=self.values[6],reference=self.values[7],budget_reference=self.values[8],
                    expected_owner_pin=self.values[9],checkpoint_body=b'body',
                    checkpoint_signature=b'signature',checkpoint_sha='d'*64)
        args.update(changes)
        return runtime.inspect_runtime_model_with_recovered_memory(**args)

    def test_latest_clock_and_all_owner_references_forwarded(self):
        result = self.call()
        self.assertIs(result,self.bridge.return_value)
        args, kw = self.bridge.call_args
        self.assertEqual(args[:2],tuple(self.values[:2]))
        self.assertEqual(args[2],replace(self.ctx,clock=self.now))
        self.assertIs(args[2].clock,self.now)
        self.assertIs(self.ctx.clock,self.old_clock)
        self.assertEqual(args[3:],tuple(self.values[2:]))
        self.assertEqual(kw,dict(checkpoint_body=b'body',checkpoint_signature=b'signature',checkpoint_sha='d'*64))
        self.ordinary_mock.assert_not_called()

    def test_run_version_drift_rejected_before_memory(self):
        result = self.call(current_run=replace(self.run,version=3))
        self.assertEqual(result.reason,'RUNTIME_MEMORY_MODEL_DRIFT_HOLD')
        self.bridge.assert_not_called()

    def test_lease_fence_drift_rejected_before_memory(self):
        result = self.call(current_lease=replace(self.lease,fence=2))
        self.assertEqual(result.reason,'RUNTIME_MEMORY_MODEL_DRIFT_HOLD')
        self.bridge.assert_not_called()

    def test_invalid_runtime_reference_never_calls_recovery(self):
        for change in ({'ctx':None},{'current_run':None},{'current_lease':None},{'clock':None}):
            with self.subTest(change=change):
                self.assertEqual(self.call(**change).reason,'RUNTIME_MEMORY_MODEL_REFERENCE_HOLD')
        self.bridge.assert_not_called()

    def test_memory_hold_is_not_replaced_by_ordinary_preflight(self):
        held=ReviewDouble('MEMORY_GATEWAY_RECOVERY_HOLD')
        self.bridge.return_value=held
        self.assertIs(self.call(),held)
        self.ordinary_mock.assert_not_called()

    def test_expired_latest_clock_not_replaced_by_old_clock(self):
        expired=replace(self.now,now_tick=150)
        held=ReviewDouble('MEMORY_GATEWAY_RECOVERY_HOLD')
        self.bridge.return_value=held
        self.assertIs(self.call(clock=expired),held)
        self.assertIs(self.bridge.call_args.args[2].clock,expired)
        self.ordinary_mock.assert_not_called()

    def test_missing_recovery_dependency_does_not_fallback(self):
        with patch.dict(sys.modules,{MEMORY_MODULE:None}):
            with self.assertRaises(ModuleNotFoundError): self.call()
        self.ordinary_mock.assert_not_called()
