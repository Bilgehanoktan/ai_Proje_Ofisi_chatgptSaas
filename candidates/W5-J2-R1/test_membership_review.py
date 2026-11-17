import unittest
from membership_review import BINDING, ROW, review_membership


def fixture():
    e=dict(tenant_id='synthetic-tenant',company_id='synthetic-company',environment_id='A0_SAMPLE_ONLY',
        plan_revision='sha256:'+'a'*64,task_id='task-1',run_id='demo-run',agent_instance_id='demo-agent',
        principal_id='demo-principal',attempt=1,project_id='project-1',effect_id='effect-1',
        invocation_pin='1'*64,route_pin='2'*64,profile_pin='3'*64,budget_id='budget-1',reservation_id='reservation-1',
        invocation_idempotency_key='invoke-1',currency='USD',reserved_minor=20,admission_id='admit-1',
        admission_tx='tx-a',admission_request_digest='4'*64,reservation_tx='tx-r',reservation_budget_revision=2,
        lease_id='lease-1',grant_id='grant-1',fence=3,policy_epoch=4,witness_epoch=5,membership_pin='5'*64,
        reservation_pin='6'*64)
    r=dict.fromkeys(ROW);r.update(e,state='RESERVED')
    b=dict(tenant_id=e['tenant_id'],company_id=e['company_id'],environment_id=e['environment_id'],budget_id=e['budget_id'],
        revision=2,currency='USD',limit_minor=100,outstanding_minor=20,recognized_cost_minor=0,unknown_cost=False,
        policy_epoch=4,witness_epoch=5,source_digest='7'*64)
    return e,r,b


def consumed(r): return dict(r,state='CONSUMED',consume_tx='tx-c',consume_receipt_pin='8'*64)
def usage(r): return dict(consumed(r),state='USAGE_KNOWN',usage_tx='tx-u',usage_pin='9'*64,actual_minor=12,input_tokens=4,output_tokens=5)
def reconciled(r): return dict(usage(r),state='RECONCILED',reconciliation_tx='tx-q',reconciliation_pin='b'*64,recognized_minor=12,released_minor=8)


class ReviewTests(unittest.TestCase):
    def setUp(self): self.e,self.r,self.b=fixture()
    def check(self,reason,*,e=None,rows=None,b=None,ref=None,match=False,quarantine=False):
        b=self.b if b is None else b
        v=review_membership(self.e if e is None else e,(self.r,) if rows is None else rows,b,dict(b) if ref is None else ref)
        self.assertEqual(v.reason,reason)
        self.assertEqual(v.structural_match,match);self.assertEqual(v.quarantine_required,quarantine)
        self.assertEqual(v.decision,'HOLD')
        self.assertFalse(any((v.provider_call_allowed,v.spend_allowed,v.retry_allowed,v.settlement_allowed,v.receipt_available)))
    def test_reserved(self): self.check('D0_RESERVED_MEMBERSHIP_MATCH_ONLY',match=True)
    def test_consumed(self): self.check('D0_CONSUMED_MEMBERSHIP_MATCH_ONLY',rows=(consumed(self.r),),match=True)
    def test_usage(self): self.check('D0_USAGE_KNOWN_MEMBERSHIP_MATCH_ONLY',rows=(usage(self.r),),match=True)
    def test_reconciled(self): self.check('D0_RECONCILED_MEMBERSHIP_MATCH_ONLY',rows=(reconciled(self.r),),b=dict(self.b,outstanding_minor=0,recognized_cost_minor=12,revision=3),match=True)
    def test_no_membership(self): self.check('MEMBERSHIP_MISSING_HOLD',rows=())
    def test_duplicate(self): self.check('MEMBERSHIP_AMBIGUOUS_HOLD',rows=(self.r,dict(self.r)))
    def test_duplicate_retry(self): self.check('MEMBERSHIP_AMBIGUOUS_HOLD',rows=(self.r,dict(self.r,attempt=2,route_pin='c'*64)))
    def test_reservation_alias(self): self.check('MEMBERSHIP_AMBIGUOUS_HOLD',rows=(self.r,dict(self.r,invocation_idempotency_key='other',invocation_pin='c'*64,membership_pin='d'*64)))
    def test_idempotency_alias(self): self.check('MEMBERSHIP_AMBIGUOUS_HOLD',rows=(self.r,dict(self.r,reservation_id='other',invocation_pin='c'*64,membership_pin='d'*64)))
    def test_invocation_alias(self): self.check('MEMBERSHIP_AMBIGUOUS_HOLD',rows=(self.r,dict(self.r,reservation_id='other',invocation_idempotency_key='other',membership_pin='d'*64)))
    def test_membership_alias(self): self.check('MEMBERSHIP_AMBIGUOUS_HOLD',rows=(self.r,dict(self.r,reservation_id='other',invocation_idempotency_key='other',invocation_pin='c'*64)))
    def test_binding_mismatch(self):
        for key,val in [('attempt',2),('route_pin','c'*64),('profile_pin','c'*64),('reservation_tx','other'),('admission_tx','other'),('admission_request_digest','c'*64),('fence',4),('policy_epoch',5),('witness_epoch',6),('project_id','other'),('effect_id','other'),('principal_id','demo-other'),('reserved_minor',21),('reservation_budget_revision',1)]:
            with self.subTest(key=key): self.check('MEMBERSHIP_BINDING_HOLD',rows=(dict(self.r,**{key:val}),))
    def test_unknown_no_ack(self): self.check('UNKNOWN_OUTCOME_HOLD',rows=(dict(self.r,state='UNKNOWN'),),quarantine=True)
    def test_unknown_after_consume(self): self.check('UNKNOWN_OUTCOME_HOLD',rows=(dict(consumed(self.r),state='UNKNOWN'),),quarantine=True)
    def test_unknown_not_zero(self): self.check('OWNER_ROW_SHAPE_OR_PHASE_HOLD',rows=(dict(self.r,state='UNKNOWN',actual_minor=0),))
    def test_unknown_budget(self): self.check('UNKNOWN_COST_HOLD',b=dict(self.b,unknown_cost=True),quarantine=True)
    def test_stale_budget(self): self.check('BUDGET_REVISION_HOLD',b=dict(self.b,revision=1))
    def test_budget_reference(self): self.check('BUDGET_REFERENCE_HOLD',ref=dict(self.b,revision=3))
    def test_budget_currency(self): self.check('BUDGET_SCOPE_CURRENCY_EPOCH_HOLD',b=dict(self.b,currency='EUR'))
    def test_budget_epoch(self): self.check('BUDGET_SCOPE_CURRENCY_EPOCH_HOLD',b=dict(self.b,witness_epoch=6))
    def test_balance(self): self.check('OUTSTANDING_BALANCE_HOLD',b=dict(self.b,outstanding_minor=19))
    def test_recognized_balance(self): self.check('RECOGNIZED_BALANCE_HOLD',rows=(reconciled(self.r),),b=dict(self.b,outstanding_minor=0,recognized_cost_minor=11))
    def test_budget_limit(self): self.check('BUDGET_REFERENCE_HOLD',b=dict(self.b,limit_minor=19))
    def test_transaction_alias(self): self.check('OWNER_ROW_SHAPE_OR_PHASE_HOLD',rows=(dict(consumed(self.r),consume_tx=self.r['reservation_tx']),))
    def test_receipt_alias(self): self.check('OWNER_ROW_SHAPE_OR_PHASE_HOLD',rows=(dict(usage(self.r),usage_pin=self.r['reservation_pin']),))
    def test_overrun(self): self.check('OWNER_ROW_SHAPE_OR_PHASE_HOLD',rows=(dict(usage(self.r),actual_minor=21),))
    def test_conservation(self): self.check('OWNER_ROW_SHAPE_OR_PHASE_HOLD',rows=(dict(reconciled(self.r),released_minor=9),))
    def test_partial_usage(self): self.check('OWNER_ROW_SHAPE_OR_PHASE_HOLD',rows=(dict(usage(self.r),usage_pin=None),))
    def test_orphan_reconciliation(self): self.check('OWNER_ROW_SHAPE_OR_PHASE_HOLD',rows=(dict(self.r,reconciliation_pin='b'*64),))
    def test_wrong_scope(self): self.check('OWNER_ROW_SHAPE_OR_PHASE_HOLD',rows=(dict(self.r,tenant_id='other'),))
    def test_bool_amount(self): self.check('EXPECTED_BINDING_HOLD',e=dict(self.e,reserved_minor=True))
    def test_rowset_type(self): self.check('OWNER_ROWSET_HOLD',rows=[self.r])
    def test_rowset_cap(self): self.check('OWNER_ROWSET_HOLD',rows=(self.r,)*4097)
    def test_unrelated(self): self.check('D0_RESERVED_MEMBERSHIP_MATCH_ONLY',rows=(self.r,dict(self.r,reservation_id='other',invocation_idempotency_key='other',invocation_pin='c'*64,membership_pin='d'*64)),match=True)
    def test_key_namespaces(self): self.check('D0_RESERVED_MEMBERSHIP_MATCH_ONLY',rows=(self.r,dict(self.r,reservation_id='other',invocation_idempotency_key='other',invocation_pin='c'*64,membership_pin=self.r['invocation_pin'])),match=True)
    def test_no_mutation(self):
        e,r,b=fixture();before=(dict(e),dict(r),dict(b));review_membership(e,(r,),b,dict(b));self.assertEqual((e,r,b),before)
    def test_zero_known_usage(self): self.check('D0_USAGE_KNOWN_MEMBERSHIP_MATCH_ONLY',rows=(dict(usage(self.r),actual_minor=0,input_tokens=0,output_tokens=0),),match=True)

if __name__=='__main__': unittest.main(verbosity=2)
