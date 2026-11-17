"""W5-I synthetic integration of original reviewers; real disposable SQLite only."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from contextlib import closing
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, LeaseObservation, ClockSample
from app.core.agent_runtime.joint_context import JointContext
from app.core.policy.gateway_review import EffectScope, GrantSample
from app.core.policy.witness_review import WitnessSample
from app.core.transaction.effect_fence_reference import D0EffectFenceReference, Head
from app.core.transaction.signed_consume_reference import ConsumeRequest, issue_fixture
from app.engines.memory_engine.snapshot_store import Snapshot, create_store, publish_snapshot
from app.engines.memory_engine.retrieval import Node, TombstoneView
from app.engines.memory_engine.runtime_binding import MemoryAclEntry, MemoryAclView
from app.engines.knowledge_engine.provenance import SourceVersion, ClaimSpan
from app.engines.skill_engine.manifest_review import SkillManifestSample
from app.engines.skill_engine.resolver import SourcePin
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.provider_contract import ProviderKind, ProviderRequest
from app.engines.model_gateway.runtime_binding import InvocationEnvelope, invocation_digest
from app.engines.model_gateway.profile_registry import ModelProfile, profile_digest, catalog_digest
from app.engines.model_gateway.capability_resolver import CapabilityQuery
from app.engines.model_gateway.cost_estimator import CostProfile
from app.engines.model_gateway.router import RouteMetric, RoutePolicy, metrics_digest, policy_digest
from app.engines.model_gateway.routing_decision import make_routing_decision, routing_decision_digest
from app.engines.model_gateway.invocation_route_binding import InvocationRouteContext
from app.engines.model_gateway.reservation_usage_receipt import make_receipt_lookup, ReceiptReadback
from app.engines.model_gateway.token_accounting import ReservationEvidence, UsageEvidence, accounting_evidence_digest
from app.engines.model_gateway.durable_receipt_adapter import OwnerReceiptSnapshot, owner_snapshot_digest
from app.engines.budget_engine.reservation_review import BudgetSnapshot
from receipt_pep_review import ReceiptEffectPin, receipt_effect_digest, consume_scope
import capability_runtime_review as candidate


def digest(raw):
    return sha256(raw).hexdigest()


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'memory.d0.sqlite'
        self.s=Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,
                     'task','demo-run','demo-agent','demo-principal')
        self.run=RunObservation(self.s,RunState.RUNNING,2,0)
        self.lease=LeaseObservation(self.s,'lease','grant',1,0,1,3,4,200,90)
        self.clock=ClockSample(100,3,4,20)
        raw=b'prefix bounded memory suffix'; self.raw=raw[7:21]
        source=SourceVersion(self.s,'source','r1',digest(raw))
        node=Node(self.s,'source','r1',source.raw_digest,())
        target=Node(self.s,'target','r1',digest(b'derived'),('source',))
        tomb=TombstoneView(self.s,1,1,(),True)
        acl=MemoryAclView(self.s,2,0,3,4,1,1,1,True,
                          tuple(MemoryAclEntry(n.node_id,n.revision,n.digest,'ALLOW_READ') for n in (node,target)))
        self.memory=Snapshot(self.run,(node,target),'target',tomb,acl,source,
                             ClaimSpan(source,7,21,digest(self.raw)),raw)
        create_store(self.path); self.mem_pin=publish_snapshot(self.path,self.memory,None)
        self.primary=AdapterPin(self.s,'demo-model','r1','b'*64,('summarize','demo-tool'),())
        self.alt=AdapterPin(self.s,'demo-fallback','r1','c'*64,('summarize','demo-tool'),())
        self.registry=(self.primary,self.alt)
        self.ctx=self.context(self.primary,self.alt,self.raw)
        self.joint=JointContext(self.mem_pin,self.ctx.envelope)
        self.budget=BudgetSnapshot(self.s,'budget',1,'USD',100,20,0,False,3,4,'d'*64)
        self.snapshot=self.owner(self.ctx)
        self.skill=SkillManifestSample(self.s,'skill','v1','e'*64,'f'*64,'1'*64,('demo-tool',))
        self.source=SourcePin('skill-source','v1','e'*64,'license','custody')
        self.tool=candidate.ToolReviewRequest('demo-tool',digest(b'opaque synthetic tool input'))
        self.witness=WitnessSample(self.s,'witness-root',4,5,'2'*64,95)
        self.args=self.args_for()

    def context(self, primary, alt, raw, *, requested=('summarize',), reservation='reservation', idem='invocation-idem'):
        registry=(primary,alt)
        request=ProviderRequest(self.s,ProviderKind.SAMPLE,digest(raw),requested,(),10)
        envelope=InvocationEnvelope(self.run,self.lease,request,primary,alt,reservation,idem,10)
        profiles=tuple(ModelProfile(a,ProviderKind.SAMPLE,f'model-{i}','r1',100,20,('synthetic',),
                                    ('local',),('simple',),f'cost-{i}',f'latency-{i}') for i,a in enumerate(registry))
        pins=tuple(profile_digest(p,registry) for p in profiles)
        metrics=tuple(RouteMetric(pin,CostProfile(pin,p.cost_profile_ref,'USD',10,1,1,0),
                                  p.latency_profile_ref,1) for p,pin in zip(profiles,pins))
        policy=RoutePolicy(self.s,'r1',catalog_digest(profiles,registry,self.s),pins,metrics_digest(metrics),'USD',
                           10,10,3,4)
        q=CapabilityQuery(self.s,requested,'synthetic','local','simple',3,10)
        record=make_routing_decision(q,profiles,registry,policy,policy_digest(policy),metrics,3,4)
        return InvocationRouteContext(envelope,registry,invocation_digest(envelope,registry),self.run,
                                      self.lease,self.clock,raw,record,routing_decision_digest(record),profiles,
                                      metrics,pins[0],3)

    def owner(self,ctx,budget=None,*,unknown=False,usage=False):
        b=self.budget if budget is None else budget
        lookup=make_receipt_lookup(ctx,b.budget_id)
        res=ReservationEvidence(lookup.binding,b.budget_id,lookup.reservation_id,20,'3'*64)
        u=UsageEvidence(lookup.binding,3,2,2,'4'*64) if usage else None
        rb=ReceiptReadback(lookup,b.revision,b.source_digest,res,u,outcome_unknown=unknown)
        return OwnerReceiptSnapshot('snapshot','owner-tx',1,b,rb,accounting_evidence_digest(res),
                                    accounting_evidence_digest(u) if u else None,None)

    def args_for(self,*,ctx=None,joint=None,snapshot=None,skill=None,source=None,tool=None,allowed_tools=None):
        ctx=self.ctx if ctx is None else ctx; joint=self.joint if joint is None else joint
        snapshot=self.snapshot if snapshot is None else snapshot; skill=self.skill if skill is None else skill
        source=self.source if source is None else source; tool=self.tool if tool is None else tool
        pin=candidate.capability_runtime_digest(joint,ctx,snapshot,skill,source,tool)
        effect=EffectScope(self.s,tool.action,tool.tool_id,pin,'grant','admission','lease',snapshot.budget.budget_id,3,4,1)
        grant=GrantSample(self.s,'grant','admission','lease',snapshot.budget.budget_id,(tool.action,),
                          (tool.tool_id,) if allowed_tools is None else allowed_tools,pin,3,4,1,180,False)
        return dict(joint=joint,ctx=ctx,snapshot=snapshot,owner_reference=snapshot,budget_reference=snapshot.budget,
                    owner_pin=owner_snapshot_digest(snapshot),skill=skill,skill_reference=skill,source=source,
                    source_reference=source,tool=tool,expected_pin=pin,path=self.path,current_run=self.run,
                    current_lease=self.lease,clock=self.clock,effect=effect,grant=grant,grant_reference=grant,
                    witness=self.witness,witness_reference=self.witness,witness_max_age=20)

    def assert_safe(self,r):
        self.assertEqual((r.decision,r.pep_decision),('HOLD','DENY'))
        for k in ('retrieval_allowed','release_allowed','provider_call_allowed','tool_allowed','skill_enabled',
                  'spend_allowed','dispatch_allowed','transition_allowed','retry_allowed','settlement_allowed',
                  'independent_verified'):
            self.assertIs(getattr(r,k),False,k)
        return r

    def review(self, args=None, **changes):
        return self.assert_safe(candidate.inspect_capability_runtime(**((self.args if args is None else args)|changes)))

    def held(self, args=None, **changes):
        r=self.review(args,**changes);self.assertFalse(r.structural_match);return r

    def test_all_four_original_reviewers_match_but_no_authority(self):
        before=self.path.read_bytes(); r=self.review()
        self.assertTrue(r.structural_match); self.assertEqual(r.stage,'complete');self.assertEqual(before,self.path.read_bytes())

    def test_scope_drift(self):
        for field in ('tenant_id','company_id','environment_id','plan_revision','task_id','run_id','agent_instance_id','principal_id'):
            with self.subTest(field=field): self.held(current_run=replace(self.run,scope=replace(self.s,**{field:'other'})))

    def test_run_attempt_state_version_drift(self):
        for kw in ({'attempt':1},{'version':3},{'state':RunState.VERIFYING}): self.held(current_run=replace(self.run,**kw))

    def test_lease_fence_or_revision_drift(self):
        for kw in ({'fence':2},{'lease_version':2},{'heartbeat_revision':1},{'grant_id':'other'}): self.held(current_lease=replace(self.lease,**kw))

    def test_clock_regression(self): self.assertEqual(self.held(clock=replace(self.clock,now_tick=99)).stage,'runtime')

    def test_expired_or_stale_lease(self):
        for t in (111,200): self.held(clock=replace(self.clock,now_tick=t))

    def test_policy_witness_epoch_drift(self):
        for kw in ({'policy_epoch':9},{'witness_epoch':9}): self.held(clock=replace(self.clock,**kw))

    def test_invalid_combined_pin(self): self.assertEqual(self.held(expected_pin='0'*64).stage,'pin')

    def test_mismatched_joint_envelope(self):
        self.held(joint=replace(self.joint,invocation=replace(self.ctx.envelope,idempotency_key='other')))

    def test_missing_store(self): self.assertEqual(self.held(path=Path(self.tmp.name)/'missing.d0.sqlite').stage,'memory-model')

    def test_owner_reference_drift(self): self.assertEqual(self.held(owner_reference=replace(self.snapshot,owner_revision=2)).stage,'model-receipt')

    def test_owner_missing(self): self.held(owner_reference=None)

    def test_owner_pin_mismatch(self): self.held(owner_pin='0'*64)

    def test_budget_unknown(self):
        snap=self.owner(self.ctx,replace(self.budget,unknown_cost=True));self.assertEqual(self.held(self.args_for(snapshot=snap)).reason,'UNKNOWN_COST_HOLD')

    def test_unknown_provider_outcome(self):
        snap=self.owner(self.ctx,unknown=True);self.assertEqual(self.held(self.args_for(snapshot=snap)).reason,'UNKNOWN_USAGE_HOLD')

    def test_used_reservation_is_not_preflight(self): self.held(self.args_for(snapshot=self.owner(self.ctx,usage=True)))

    def test_wrong_route_pin(self): self.held(self.args_for(ctx=replace(self.ctx,route_pin='0'*64)))

    def test_wrong_profile_pin(self): self.held(self.args_for(ctx=replace(self.ctx,profile_pin='0'*64)))

    def test_wrong_memory_bytes_even_when_model_repinned(self):
        ctx=self.context(self.primary,self.alt,b'different bytes');joint=JointContext(self.mem_pin,ctx.envelope)
        self.assertEqual(self.held(self.args_for(ctx=ctx,joint=joint,snapshot=self.owner(ctx))).reason,'JOINT_INPUT_SPAN_HOLD')

    def test_memory_revoked_ancestor(self):
        tomb=replace(self.memory.tombstone,sequence=2,keys=('source',))
        acl=replace(self.memory.acl,tombstone_sequence=2,acl_revision=2)
        new=publish_snapshot(self.path,replace(self.memory,tombstone=tomb,acl=acl),self.mem_pin)
        self.held();self.assertEqual(self.held(self.args_for(joint=replace(self.joint,memory_pin=new))).reason,'STALE_HOLD')

    def test_memory_acl_deny(self):
        acl=replace(self.memory.acl,acl_revision=2,entries=tuple(replace(e,decision='DENY_READ') for e in self.memory.acl.entries))
        new=publish_snapshot(self.path,replace(self.memory,acl=acl),self.mem_pin)
        self.assertEqual(self.held(self.args_for(joint=replace(self.joint,memory_pin=new))).reason,'MEMORY_ACL_DENY')

    def test_revocation_between_engine_checks(self):
        original=candidate.inspect_capabilities; done=False
        def during(*a,**k):
            nonlocal done
            if not done:
                done=True
                acl=replace(self.memory.acl,acl_revision=2)
                publish_snapshot(self.path,replace(self.memory,acl=acl),self.mem_pin)
            return original(*a,**k)
        with patch.object(candidate,'inspect_capabilities',side_effect=during):
            self.assertEqual(self.held().stage,'memory-recheck')

    def test_skill_enabled(self): self.assertEqual(self.held(self.args_for(skill=replace(self.skill,enabled=True))).stage,'skill')

    def test_skill_reference_drift(self): self.assertEqual(self.held(skill_reference=replace(self.skill,version='v2')).stage,'skill')

    def test_skill_source_mismatch(self): self.held(self.args_for(source=replace(self.source,raw_digest='0'*64)))

    def test_tool_outside_skill(self): self.assertEqual(self.held(self.args_for(skill=replace(self.skill,tool_ids=()))).reason,'CAPABILITY_HOLD')

    def test_tool_outside_grant(self): self.assertEqual(self.held(self.args_for(allowed_tools=('other',))).reason,'CAPABILITY_HOLD')

    def test_tool_outside_alternate_adapter(self):
        alt=replace(self.alt,capabilities=('summarize',)); ctx=self.context(self.primary,alt,self.raw)
        self.assertEqual(self.held(self.args_for(ctx=ctx,joint=JointContext(self.mem_pin,ctx.envelope),snapshot=self.owner(ctx))).stage,'skill')

    def test_tool_effect_not_model_grant(self):
        self.assertEqual(self.held(effect=replace(self.args['effect'],action='MODEL_SAMPLE_REVIEW')).stage,'tool-binding')

    def test_tool_effect_budget_and_payload_pin(self):
        for kw in ({'budget_id':'other'},{'effect_digest':'0'*64},{'tool_id':'other'}): self.held(effect=replace(self.args['effect'],**kw))
        self.held(tool=replace(self.tool,input_pin='0'*64))

    def test_grant_revoked_or_changed(self):
        for g in (replace(self.args['grant'],revoked=True),replace(self.args['grant'],expires_tick=100),
                  replace(self.args['grant'],allowed_actions=('other',))):
            self.assertEqual(self.held(grant=g,grant_reference=g).stage,'pep')
        self.held(grant_reference=replace(self.args['grant'],expires_tick=101))

    def test_witness_drift(self):
        for w in (replace(self.witness,epoch=5),replace(self.witness,observed_tick=50)):
            self.assertEqual(self.held(witness=w,witness_reference=w).stage,'pep')
        self.held(witness_reference=replace(self.witness,sequence=6))

    def hpin(self):
        e=EffectScope(self.s,'MODEL_SAMPLE_REVIEW',self.primary.adapter_id,self.ctx.invocation_pin,'grant','admission','lease','budget',3,4,1)
        return ReceiptEffectPin(self.run,self.lease,e,'project','model-effect',self.ctx.invocation_pin,self.ctx.route_pin,
                                self.ctx.profile_pin,self.ctx.envelope.reservation_ref,self.ctx.envelope.idempotency_key,
                                self.args['owner_pin'],self.snapshot.reservation_pin,'5'*64,'consume-tx','USD')

    def consumed(self, p=None, **kw):
        a=dict(ctx=self.ctx,snapshot=self.snapshot,owner_reference=self.snapshot,budget_reference=self.budget,
               owner_pin=self.args['owner_pin'],receipt_pin=self.hpin() if p is None else p,expected_membership_pin='5'*64,
               current_run=self.run,current_lease=self.lease,clock=self.clock)
        return self.assert_safe(candidate.inspect_consumed_model_binding(**(a|kw)))

    def test_h_typed_crosswalk_and_actual_signed_consumed_separate(self):
        p=self.hpin(); self.assertTrue(self.consumed(p).structural_match)
        self.assertNotEqual(p.transaction_ref,self.snapshot.transaction_ref)
        head=Head(1,'6'*64,4); req=ConsumeRequest(consume_scope(p),head,'7'*64,receipt_effect_digest(p),p.transaction_ref,p.invocation_pin,99,120)
        key=Ed25519PrivateKey.generate(); pub=key.public_key().public_bytes_raw()
        store=D0EffectFenceReference.create(Path(self.tmp.name)/'model.effect-reference.sqlite',head)
        signed=issue_fixture(store,key,req,100)
        grant=replace(self.args['grant'],allowed_actions=('MODEL_SAMPLE_REVIEW',),allowed_tools=(self.primary.adapter_id,),effect_digest=p.invocation_pin)
        a=dict(ctx=self.ctx,snapshot=self.snapshot,owner_reference=self.snapshot,budget_reference=self.budget,
               owner_pin=self.args['owner_pin'],receipt_pin=p,receipt_reference=p,expected_membership_pin='5'*64,
               expected_binding_pin=receipt_effect_digest(p),observation=signed,expected_consume=req,public_key=pub,
               expected_key_sha=digest(pub),current_head=head,current_run=self.run,current_lease=self.lease,clock=self.clock,
               grant=grant,grant_reference=grant,witness=self.witness,witness_reference=self.witness,
               witness_max_age=20,outcome_unknown=False)
        h=self.assert_safe(candidate.inspect_consumed_model(**a))
        self.assertTrue(h.structural_match); self.assertTrue(h.signature_match); self.assertTrue(h.pep_reference_match)
        self.assertEqual(h.reason,'D0_CONSUMED_MODEL_SIGNATURE_MATCH_ONLY_HOLD')
        self.held(effect=p.effect,grant=grant,grant_reference=grant)
        for changes in ({'receipt_reference':replace(p,reservation_pin='0'*64)},
                        {'observation':replace(signed,signature=b'0'*64)},
                        {'outcome_unknown':True},{'expected_binding_pin':'0'*64},
                        {'expected_membership_pin':'0'*64},{'grant_reference':replace(grant,revoked=True)},
                        {'grant':self.args['grant'],'grant_reference':self.args['grant']}):
            with self.subTest(changes=changes):
                rejected=self.assert_safe(candidate.inspect_consumed_model(**(a|changes)))
                self.assertFalse(rejected.structural_match)

    def test_h_mismatched_owner_pins(self):
        for k in ('owner_snapshot_pin','reservation_pin','route_pin','profile_pin','membership_pin'):
            self.assertFalse(self.consumed(replace(self.hpin(),**{k:'0'*64})).structural_match)
        self.assertFalse(self.consumed(expected_membership_pin=None).structural_match)

    def test_h_mismatched_invocation_identity(self):
        for kw in ({'reservation_id':'other'},{'invocation_idempotency_key':'other'},{'currency':'EUR'}):
            self.assertFalse(self.consumed(replace(self.hpin(),**kw)).structural_match)

    def test_h_unknown_owner_outcome(self):
        snap=self.owner(self.ctx,unknown=True)
        self.assertFalse(self.consumed(snapshot=snap,owner_reference=snap,owner_pin=owner_snapshot_digest(snap)).structural_match)


if __name__=='__main__':
    unittest.main(verbosity=2)
