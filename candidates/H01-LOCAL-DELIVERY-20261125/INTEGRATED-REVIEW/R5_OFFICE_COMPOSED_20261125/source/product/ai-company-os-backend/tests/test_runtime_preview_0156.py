"""Unexecuted oracle candidates; no real test authorization or external effects."""
import unittest
from dataclasses import replace
from app.core.runtime_preview import (Scope, LeaseObservation, ClockSample, RunObservation,
    RunState, inspect_lease, inspect_renewal, inspect_transition)
from app.core.outbox_review import Phase, OutboxObservation, inspect_outbox
from app.core.runtime_plan_binding import inspect_plan_binding


class RuntimePreviewTests(unittest.TestCase):
    def setUp(self):
        self.scope = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',
                           'sha256:'+'a'*64,'research','demo-run','demo-agent','demo-principal')
        self.lease = LeaseObservation(self.scope,'demo-lease','demo-grant',1,1,1,2,3,60,40)
        self.clock = ClockSample(50,2,3,20)
        self.run = RunObservation(self.scope,RunState.RUNNING,4,0)
        self.box = OutboxObservation(self.scope,'effect-1','b'*64,'event-1','outbox-1','commit-1',
                    Phase.CLAIMED,1,'demo-principal','demo-lease',1,2,3)

    def test_reference_match_is_not_grant(self):
        r=inspect_lease(self.lease,self.lease,self.clock)
        self.assertEqual(r.freshness,'FRESH'); self.assertFalse(r.dispatch_allowed)
        self.assertEqual(r.decision,'HOLD')

    def test_forged_expiry(self):
        r=inspect_lease(replace(self.lease,expires_tick=100),self.lease,replace(self.clock,now_tick=70))
        self.assertEqual(r.freshness,'STALE'); self.assertFalse(r.dispatch_allowed)

    def test_bad_expected_numeric_and_future_heartbeat(self):
        self.assertEqual(inspect_lease(self.lease,replace(self.lease,witness_epoch=True),self.clock).freshness,'UNKNOWN')
        l=replace(self.lease,heartbeat_tick=55)
        self.assertEqual(inspect_lease(l,l,self.clock).reason,'HEARTBEAT_IN_FUTURE')

    def test_stale_witness_and_expiry(self):
        self.assertEqual(inspect_lease(self.lease,self.lease,replace(self.clock,witness_epoch=4)).reason,'ERR_WA_EPOCH_STALE')
        self.assertEqual(inspect_lease(self.lease,self.lease,replace(self.clock,now_tick=60)).reason,'LEASE_EXPIRED')

    def test_renewal_is_read_only(self):
        self.assertEqual(inspect_renewal(self.lease,self.lease,self.clock).reason,'LIVE_GRANT_WA_AND_CAS_REQUIRED')

    def test_transition_cas_and_terminal(self):
        self.assertFalse(inspect_transition(self.run,RunState.VERIFYING,3,self.lease,self.lease,self.clock).structural_edge)
        self.assertFalse(inspect_transition(replace(self.run,state=RunState.FAILED),RunState.RUNNING,4,self.lease,self.lease,self.clock).structural_edge)

    def test_unknown_cancel_and_success_hold(self):
        r=inspect_transition(self.run,RunState.CANCELLED,4,self.lease,self.lease,self.clock,True)
        self.assertEqual(r.reason,'ERR_PROVIDER_RESULT_UNKNOWN'); self.assertFalse(r.commit_allowed)
        r=inspect_transition(replace(self.run,state=RunState.VERIFYING),RunState.SUCCEEDED,4,self.lease,self.lease,self.clock)
        self.assertFalse(r.commit_allowed); self.assertIsNone(r.next_version)

    def test_outbox_no_effect_on_fresh_claim(self):
        r=inspect_outbox(self.box,self.box,self.lease,self.lease,self.clock)
        self.assertEqual(r.decision,'DENY'); self.assertFalse(r.effect_allowed)

    def test_outbox_send_marker_and_ack_loss(self):
        for b in (replace(self.box,send_intent_ref='intent-1'),replace(self.box,phase=Phase.ACK_LOST),replace(self.box,reconciliation_ref='fake-1')):
            r=inspect_outbox(b,self.box,self.lease,self.lease,self.clock)
            self.assertEqual(r.classification,'UNKNOWN_HOLD'); self.assertFalse(r.retry_allowed); self.assertFalse(r.reconciled)

    def test_outbox_claim_generation_and_owner(self):
        b=replace(self.box,claim_generation=2)
        self.assertEqual(inspect_outbox(b,self.box,self.lease,self.lease,self.clock).reason,'OUTBOX_REFERENCE_MISMATCH')
        b=replace(self.box,claim_owner='demo-other')
        self.assertEqual(inspect_outbox(b,b,self.lease,self.lease,self.clock).reason,'CLAIM_LEASE_BINDING_MISMATCH')

    def test_plan_bridge_rejects_fake(self):
        r=inspect_plan_binding({'digest':'a'*64},'research','research')
        self.assertFalse(r['binding_created']); self.assertFalse(r['dispatch_allowed'])
