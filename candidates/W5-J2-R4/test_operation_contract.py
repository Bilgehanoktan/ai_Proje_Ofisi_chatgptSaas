import unittest
from dataclasses import replace
from operation_contract import (ParentObservation, RoleObservation, economic_keys, run_scope_pin,
    plan_operation, plan_digest, inspect_operation, inspect_aliases, BASE, EXTRA, LOCKS)
from test_allocation_fixture import binding,pin

class OperationContractTests(unittest.TestCase):
    def setUp(self):
        self.b=binding();self.root=ParentObservation(run_scope_pin(self.b),pin('parent'),pin('record'),pin('key'),5,pin('lease'),pin('grant'),100)
    def plan(self,phase='ALLOCATE',b=None,parent=None,**kw):
        b=self.b if b is None else b; parent=self.root if parent is None else parent
        d=dict(tx=b['reservation_tx'] if phase=='ALLOCATE' else phase.lower()+'-1',request_digest=pin('request-'+phase),head_before=7,budget_before=2,now_tick=10)
        if phase=='CLOSE_PARTIAL': d['terminal_subject']=run_scope_pin(b)
        d.update(kw); return plan_operation(b,parent,phase,**d)
    def rows(self,p):
        return tuple(RoleObservation(r,'record-'+str(i),p.tx,p.request_digest,p.scope_sha,p.phase_key,p.head_before,p.head_before+1,p.budget_before,p.budget_before+1) for i,r in enumerate(p.roles))
    def check(self,p=None,b=None,rows=None,parent=None,tick=11,expected_pin=None,match=True):
        p=self.plan() if p is None else p; b=self.b if b is None else b
        result=inspect_operation(p,b,plan_digest(p) if expected_pin is None else expected_pin,self.rows(p) if rows is None else rows,self.root if parent is None else parent,tick)
        self.assertEqual(result.structural_match,match);self.assertEqual(result.decision,'HOLD')
        self.assertFalse(any((result.commit_allowed,result.provider_call_allowed,result.retry_allowed,result.settlement_allowed)))
        return result
    def test_all_phase_roles_exact(self):
        for phase,extra in EXTRA.items():
            with self.subTest(phase=phase):
                p=self.plan(phase); self.assertEqual(set(p.roles),set(BASE+extra));self.assertEqual(p.locks,LOCKS);self.check(p)
                self.assertFalse(p.commit_allowed or p.provider_call_allowed or p.spend_allowed or p.retry_allowed or p.settlement_allowed)
    def test_no_fake_canonical_operation(self):
        for phase in ('STATE_MUTATION','ADMISSION','TERMINAL','CLOSE_UNUSED','EXECUTE'):
            with self.subTest(phase=phase),self.assertRaises(ValueError): self.plan(phase)
    def test_wrong_parent_scope(self):
        with self.assertRaises(ValueError):self.plan(parent=replace(self.root,scope_sha=pin('other')))
    def test_wrong_epoch(self):
        with self.assertRaises(ValueError):self.plan(parent=replace(self.root,recovery_epoch=6))
    def test_expired_initial(self):
        with self.assertRaises(ValueError):self.plan(now_tick=100)
    def test_expired_before_readback(self): self.check(tick=100,match=False)
    def test_clock_regression(self): self.check(tick=9,match=False)
    def test_root_revoked_or_changed(self):
        for key in ('record_sha','key_sha','lease_digest','grant_digest','parent_claim_pin'):
            with self.subTest(key=key): self.check(parent=replace(self.root,**{key:pin('changed')}),match=False)
    def test_admission_alias(self):
        with self.assertRaises(ValueError):self.plan(tx=self.b['admission_tx'])
        with self.assertRaises(ValueError):self.plan(request_digest=self.b['admission_request_digest'])
    def test_allocation_tx_revision(self):
        with self.assertRaises(ValueError):self.plan(tx='other')
        with self.assertRaises(ValueError):self.plan(budget_before=3)
    def test_reservation_alias_later(self):
        with self.assertRaises(ValueError):self.plan('CONSUME',tx=self.b['reservation_tx'])
    def test_missing_role(self):
        p=self.plan();self.check(p,rows=self.rows(p)[:-1],match=False)
    def test_extra_duplicate_role(self):
        p=self.plan();self.check(p,rows=self.rows(p)+(self.rows(p)[0],),match=False)
    def test_role_order(self):
        p=self.plan();self.check(p,rows=tuple(reversed(self.rows(p))),match=False)
    def test_duplicate_row_id(self):
        p=self.plan();r=self.rows(p);self.check(p,rows=r[:-1]+(replace(r[-1],record_id=r[0].record_id),),match=False)
    def test_role_binding_mutations(self):
        p=self.plan();r=self.rows(p)
        for k,v in [('transaction_ref','other'),('request_digest',pin('wrong')),('scope_sha',pin('wrong')),('phase_key',pin('wrong')),('head_before',8),('head_after',9),('budget_before',3),('budget_after',4),('budget_before',False)]:
            with self.subTest(k=k,v=v):self.check(p,rows=(replace(r[0],**{k:v}),)+r[1:],match=False)
    def test_expected_plan_pin(self): self.check(expected_pin=pin('wrong'),match=False)
    def test_forged_plan_roles(self): self.check(replace(self.plan(),roles=('HEAD',)),match=False)
    def test_forged_economic_keys(self): self.check(replace(self.plan(),economic_keys=()),match=False)
    def test_binding_drift(self): self.check(b=dict(self.b,route_pin=pin('new')),match=False)
    def test_identity_stable_across_attempt_route_profile_effect_tx(self):
        b=dict(self.b,attempt=2,route_pin=pin('new'),profile_pin=pin('profile'),effect_id='other',reservation_tx='other')
        self.assertEqual(economic_keys(b),economic_keys(self.b));self.assertEqual(run_scope_pin(b),run_scope_pin(self.b))
        self.assertEqual(inspect_aliases(b,(self.b,)).reason,'ECONOMIC_ALIAS_HOLD')
    def test_alias_across_run(self):
        b=dict(binding(run=2),reservation_id=self.b['reservation_id']);self.assertNotEqual(run_scope_pin(b),run_scope_pin(self.b));self.assertEqual(inspect_aliases(b,(self.b,)).reason,'ECONOMIC_ALIAS_HOLD')
    def test_distinct_invocation_same_run(self):
        b=binding(2);self.assertEqual(run_scope_pin(b),run_scope_pin(self.b));self.assertEqual(inspect_aliases(b,(self.b,)).reason,'ECONOMIC_ABSENCE_UNPROVEN_HOLD')
    def test_phase_key_separation(self):
        keys=[self.plan(p).phase_key for p in EXTRA];self.assertEqual(len(set(keys)),len(EXTRA))
    def test_consume_key_stable_retry(self):
        p=self.plan('CONSUME');b=dict(self.b,attempt=2,route_pin=pin('new'),reservation_tx='new-tx');q=self.plan('CONSUME',b=b,tx='retry-tx')
        self.assertEqual(p.phase_key,q.phase_key);self.assertNotEqual(p.binding_pin,q.binding_pin)
    def test_terminal_identity_run_level(self):
        p=self.plan('CLOSE_PARTIAL');q=self.plan('CLOSE_PARTIAL',b=binding(2),tx='terminal-other');self.assertEqual(p.phase_key,q.phase_key);self.assertEqual(p.subject_pin,run_scope_pin(self.b));self.assertEqual(p.economic_keys,())
    def test_terminal_scope_wrong(self):
        with self.assertRaises(ValueError):self.plan('CLOSE_PARTIAL',terminal_subject=pin('other'))
    def test_bad_history(self):self.assertEqual(inspect_aliases(self.b,({},)).reason,'ALIAS_HISTORY_SHAPE_HOLD')
    def test_invalid_bool_revisions(self):
        for k in ('head_before','budget_before','now_tick'):
            with self.subTest(k=k),self.assertRaises(ValueError):self.plan(**{k:True})
