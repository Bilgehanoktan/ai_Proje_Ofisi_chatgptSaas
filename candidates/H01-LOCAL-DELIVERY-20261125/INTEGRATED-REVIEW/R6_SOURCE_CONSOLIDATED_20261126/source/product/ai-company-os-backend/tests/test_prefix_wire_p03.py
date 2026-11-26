import unittest
from app.core.development_review.lifecycle_prefix_wire import prefix_wire

class PrefixWireTests(unittest.TestCase):
    def test_all_prefixes(self):
        for v,state in enumerate(('ADMITTED','RUNNING','RUNNING','VERIFYING'),1):
            with self.subTest(v=v):
                x=prefix_wire(v)
                self.assertEqual(x['state'],state)
                self.assertEqual([e['version'] for e in x['timeline']],list(range(1,v+1)))
                self.assertEqual(x['head_version'],v)
    def test_renewal(self):
        for v in (1,2,3,4):
            x=prefix_wire(v)
            self.assertEqual((x['lease_version'],x['heartbeat_revision'],x['heartbeat_tick'],x['expires_tick'],x['sample_budget_revision']), (1,0,10,20,1) if v<3 else (2,1,11,31,2))
    def test_no_live_authority(self):
        for v in range(1,5):
            x=prefix_wire(v)
            for k in ('dispatch_allowed','provider_called','spend_allowed','release_ready','authoritative'):self.assertIs(x[k],False)
            for k in ('geometry_join','model_binding','memory_acl','independent_acceptance','decision'):self.assertEqual(x[k],'HOLD')
            self.assertIsNone(x['real_run_count']);self.assertEqual(x['lease_freshness'],'UNKNOWN')
    def test_bad_version(self):
        for v in (True,False,0,5,-1,3.0,'3',None):
            with self.subTest(v=v),self.assertRaises(ValueError):prefix_wire(v)
    def test_reservation_not_cost(self):
        for v in range(1,5):
            x=prefix_wire(v);self.assertEqual(x['sample_outstanding_minor'],20);self.assertEqual(x['sample_recognized_minor'],0)
    def test_fresh_copy(self):
        x=prefix_wire(3);x['timeline'][0]['state']='FORGED';self.assertEqual(prefix_wire(3)['timeline'][0]['state'],'ADMITTED')
