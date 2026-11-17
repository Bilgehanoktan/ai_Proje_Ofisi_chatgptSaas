"""W5 D0 tests against actual modules; no network or DB."""
import unittest
from dataclasses import replace
from hashlib import sha256
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, LeaseObservation, ClockSample
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.postgres_admission_mapping import ClaimSpec, SampleBudget, claim_digest
from app.core.transaction.postgres_transition_mapping import transaction_ref
from app.core.policy.gateway_review import EffectScope
from app.engines.budget_engine.reservation_review import BudgetSnapshot
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.provider_contract import ProviderRequest, ProviderKind
from app.engines.model_gateway.runtime_binding import InvocationEnvelope, invocation_digest
from app.engines.model_gateway.effect_budget_review import ReservationObservation, EffectBudgetReview, inspect_effect_budget

def fixture():
    d = "a"*64
    s = Scope("synthetic-tenant","synthetic-company","A0_SAMPLE_ONLY","sha256:"+d,"research","demo-run","demo-agent","demo-principal")
    lease = LeaseObservation(s,"lease","grant",1,0,1,2,3,100,10)
    run = RunObservation(s,RunState.RUNNING,3,0)
    raw = b"sample"
    primary = AdapterPin(s,"demo-model","v1",d,("text",),())
    alternate = replace(primary,adapter_id="demo-fallback")
    registry = (primary,alternate)
    request = ProviderRequest(s,ProviderKind.SAMPLE,sha256(raw).hexdigest(),("text",),(),100)
    env = InvocationEnvelope(run,lease,request,primary,alternate,"unbound-label","invoke-key",10)
    pin = invocation_digest(env,registry)
    b = SampleBudget("budget",1,"USD",100,0,0,False,2,3,d)
    claim = ClaimSpec(RunObservation(s,RunState.QUEUED,1,0),"admission",lease,b,20,d)
    intent = LogicalIntent(s,Operation.ADMISSION,1,claim_digest(claim),"admit-effect","admit-key","grant","lease","budget",2,3)
    reservation = ReservationObservation(s,"budget",2,20,"USD",intent.request_digest,transaction_ref(intent))
    budget = BudgetSnapshot(s,"budget",2,"USD",100,20,0,False,2,3,d)
    effect = EffectScope(s,"MODEL_SAMPLE_REVIEW","demo-model",pin,"grant","admission","lease","budget",2,3,1)
    return dict(envelope=env,registry=registry,invocation_pin=pin,current_run=run,current_lease=lease,clock=ClockSample(11,2,3,10),raw=raw,admission=intent,claim=claim,reservation=reservation,budget=budget,effect=effect)

class EffectBudgetReviewTests(unittest.TestCase):
    def check(self, changes, reason, match=False):
        args=fixture()
        args.update(changes)
        r=inspect_effect_budget(**args)
        self.assertEqual(r.reason,reason)
        self.assertEqual(r.structural_match,match)
        self.assertEqual(r.decision,"HOLD")
        self.assertFalse(r.provider_call_allowed or r.spend_allowed or r.dispatch_allowed)

    def test_matching_diagnostic_never_authorizes(self):
        self.check({},"D0_MATCH_ONLY_INVOCATION_RECEIPT_AND_AUTHORITY_ABSENT",True)

    def test_invalid_envelope(self):
        self.check({"envelope":None},"MODEL_ENVELOPE_HOLD")

    def test_missing_reservation(self):
        self.check({"reservation":None},"RESERVATION_MISSING_HOLD")

    def test_reservation_mutations(self):
        f=fixture()
        for field,value in [("budget_id","other"),("currency","EUR"),("amount_minor",19),("budget_revision",1),("request_digest","b"*64),("transaction_ref","other"),("scope",replace(f["reservation"].scope,run_id="demo-other"))]:
            with self.subTest(field=field):
                self.check({"reservation":replace(f["reservation"],**{field:value})},"RESERVATION_ROW_MISMATCH_HOLD")

    def test_budget_mutations(self):
        f=fixture()
        for field,value,reason in [("unknown_cost",True,"UNKNOWN_COST_HOLD"),("revision",1,"BUDGET_CAPACITY_HOLD"),("outstanding_minor",19,"BUDGET_CAPACITY_HOLD"),("limit_minor",19,"BUDGET_CAPACITY_HOLD"),("currency","EUR","CURRENT_BUDGET_SCOPE_HOLD"),("policy_epoch",4,"CURRENT_BUDGET_SCOPE_HOLD"),("witness_epoch",4,"CURRENT_BUDGET_SCOPE_HOLD")]:
            with self.subTest(field=field):
                self.check({"budget":replace(f["budget"],**{field:value})},reason)

    def test_effect_mutations(self):
        f=fixture()
        for field,value in [("effect_digest","b"*64),("admission_id","other"),("grant_id","other"),("lease_id","other"),("budget_id","other"),("fence",2),("action","OTHER"),("policy_epoch",4),("witness_epoch",4)]:
            with self.subTest(field=field):
                self.check({"effect":replace(f["effect"],**{field:value})},"MODEL_EFFECT_BINDING_HOLD")

    def test_input_and_lease(self):
        f=fixture()
        self.check({"raw":b"changed"},"MODEL_INPUT_DIGEST_HOLD")
        self.check({"clock":replace(f["clock"],now_tick=100)},"MODEL_LEASE_HOLD")
        self.check({"invocation_pin":"b"*64},"MODEL_INVOCATION_DIGEST_HOLD")

    def test_admission_digest(self):
        f=fixture()
        self.check({"admission":replace(f["admission"],request_digest="b"*64)},"ADMISSION_BINDING_HOLD")

    def test_missing_effect(self):
        self.check({"effect":None},"MODEL_EFFECT_MISSING_HOLD")

if __name__=="__main__":
    unittest.main()
