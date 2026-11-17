import copy
import json
import unittest
from review_pg_evidence import IDS, R3_PINS, SCHEMA, DRIVER, ReviewHold, inspect_report

H='a'*64

def fixture():
    details={1:{'tables':12,'policies':25,'cluster':'aicos_org_r5_disposable'},2:{'revision':H,'loser':['sqlstate','23505']},3:H,4:H,5:{'sqlstate':'23514','counts':[0,0]},6:{'same_scope':'55P03','other_scope':'PASS'},7:{'count':1,'head':H,'loser':['hold','HISTORY_CAS']},8:'HISTORY_CAS',9:{'count':2,'head':H},12:'42501',13:'42501',14:'42501',15:'23503',16:'42501',17:'42501',18:{'reader':'42501','unmapped':'42501'},19:'TASK_REFERENCE',20:H,21:'STALE_ORG',23:'STALE_HEAD',25:'HEAD_MISMATCH'}
    return {'profile':'ORG-05R5_DISPOSABLE_ONLY','source_pins':dict(R3_PINS),'schema_sha256':SCHEMA,'driver':DRIVER,'checks':[{'id':x,'status':'PASS','detail':details.get(i),'elapsed_ms':0} for i,x in enumerate(IDS,1)],'status':'PASS_DISPOSABLE_FIXTURE_ONLY'}

def raw(x): return json.dumps(x).encode()

class ReviewTests(unittest.TestCase):
    def rejected(self, mutate):
        f=fixture(); mutate(f)
        with self.assertRaises(ReviewHold): inspect_report(raw(f))
    def test_complete_never_accepts_pg(self):
        result=inspect_report(raw(fixture())); self.assertEqual(result['reported_pass'],26); self.assertEqual(result['actual_pg_acceptance'],'HOLD'); self.assertEqual(result['product_acceptance'],'HOLD')
    def test_partial_hold(self):
        f=fixture(); f['checks']=f['checks'][:5]; f['status']='FAIL_OR_INCOMPLETE'; self.assertEqual(inspect_report(raw(f))['review'],'INCOMPLETE_REPORT_HOLD')
    def test_failure_hold(self):
        f=fixture(); f['checks']=f['checks'][:1]+[{'id':IDS[1],'status':'FAIL','error_type':'Hold','sqlstate':None}]; f['status']='FAIL_OR_INCOMPLETE'; self.assertEqual(inspect_report(raw(f))['reported_pass'],1)
    def test_false_complete(self): self.rejected(lambda f:f['checks'].pop())
    def test_duplicate_id(self): self.rejected(lambda f:f['checks'][1].update(id=IDS[0]))
    def test_order(self): self.rejected(lambda f:f['checks'].reverse())
    def test_wrong_schema(self): self.rejected(lambda f:f.update(schema_sha256=H))
    def test_wrong_driver(self): self.rejected(lambda f:f.update(driver='3.0'))
    def test_wrong_source_pin(self): self.rejected(lambda f:f['source_pins'].update({'durable_ops.py':H}))
    def test_wrong_cas(self): self.rejected(lambda f:f['checks'][6]['detail'].update(count=2))
    def test_wrong_rollback(self): self.rejected(lambda f:f['checks'][4]['detail'].update(counts=[1,0]))
    def test_wrong_lock(self): self.rejected(lambda f:f['checks'][5]['detail'].update(same_scope='PASS'))
    def test_wrong_denial(self): self.rejected(lambda f:f['checks'][11].update(detail='23505'))
    def test_wrong_status(self): self.rejected(lambda f:f.update(status='FAIL_OR_INCOMPLETE'))
    def test_boolean_elapsed(self): self.rejected(lambda f:f['checks'][0].update(elapsed_ms=True))
    def test_failure_middle(self): self.rejected(lambda f:f['checks'][0].update(status='FAIL',error_type='Hold',sqlstate=None))
    def test_duplicate_json(self):
        with self.assertRaises(ReviewHold): inspect_report(b'{"profile":1,"profile":2}')
    def test_invalid_utf8(self):
        with self.assertRaises(ReviewHold): inspect_report(b'\xff')
    def test_size(self):
        with self.assertRaises(ReviewHold): inspect_report(b' '*65537)
    def test_nan(self):
        with self.assertRaises(ReviewHold): inspect_report(b'{"x":NaN}')

if __name__=='__main__': unittest.main(verbosity=2)
