import unittest
from copy import deepcopy
from probe_inventory import TABLES, SCOPES, EXPECTED_COUNT, expected_ids, verify_check_set
from readiness import GATES, CORE_SCOPE, ORG_SCOPES, review_gates, scope_review, outcome_review


class InventoryTests(unittest.TestCase):
    def setUp(self): self.ids=list(expected_ids(SCOPES,TABLES))
    def test_total(self): self.assertEqual(len(self.ids),454); self.assertEqual(EXPECTED_COUNT,454)
    def test_unique(self): self.assertEqual(len(set(self.ids)),454)
    def test_breakdown(self):
        self.assertEqual([sum(x.startswith(k+'.') for x in self.ids) for k in 'abcd'],[112,107,107,107])
        self.assertEqual(sum(x.startswith('unmapped.') for x in self.ids),16)
        self.assertEqual(len(self.ids[-5:]),5)
    def test_order(self):
        self.assertEqual(self.ids[:6],['a.events.visible','a.events.force',*[f'a.events.foreign.{SCOPES[k]}' for k in 'bcd'],'a.events.no_truncate'])
        self.assertEqual(self.ids[-1],'stream_rollback_unchanged')
    def test_exact(self): self.assertEqual(verify_check_set(self.ids,SCOPES,TABLES),454)
    def test_old_count(self):
        with self.assertRaises(ValueError): verify_check_set(self.ids[:450],SCOPES,TABLES)
    def test_duplicate(self):
        with self.assertRaises(ValueError): verify_check_set(self.ids[:-1]+self.ids[:1],SCOPES,TABLES)
    def test_same_count_wrong_id(self):
        with self.assertRaises(ValueError): verify_check_set(self.ids[:-1]+['forged'],SCOPES,TABLES)
    def test_same_count_wrong_order(self):
        with self.assertRaises(ValueError): verify_check_set(self.ids[::-1],SCOPES,TABLES)
    def test_scope_drift(self):
        s=deepcopy(SCOPES);s['a'][0]='other'
        with self.assertRaises(ValueError): expected_ids(s,TABLES)
    def test_scope_order_drift(self):
        with self.assertRaises(ValueError): expected_ids(dict(reversed(list(SCOPES.items()))),TABLES)
    def test_table_drift(self):
        with self.assertRaises(ValueError): expected_ids(SCOPES,TABLES[:-1]+('fake',))


class ReadinessTests(unittest.TestCase):
    def test_missing(self): self.assertEqual(review_gates({}).missing,GATES)
    def test_false_gate(self):
        g=dict.fromkeys(GATES,True);g[GATES[0]]=False
        self.assertEqual(review_gates(g).missing,(GATES[0],))
    def test_truthy_not_true(self):
        g=dict.fromkeys(GATES,True);g[GATES[0]]=1
        self.assertFalse(review_gates(g).structural_complete)
    def test_complete_never_activation(self):
        r=review_gates(dict.fromkeys(GATES,True));self.assertTrue(r.structural_complete)
        self.assertEqual(r.decision,'HOLD');self.assertFalse(r.activation_allowed or r.retry_allowed)
    def test_extra_gate(self):
        g=dict.fromkeys(GATES,True);g['fake']=True;self.assertFalse(review_gates(g).structural_complete)
    def test_existing_org_scopes(self):
        for s in ORG_SCOPES: self.assertEqual(scope_review(CORE_SCOPE,s),'D4_COMMON_SCOPE_HOLD')
    def test_proposed_common_only(self): self.assertEqual(scope_review(CORE_SCOPE,CORE_SCOPE),'D4_COMMON_SCOPE_MATCH_REVIEW_ONLY')
    def test_no_alias(self): self.assertEqual(scope_review(ORG_SCOPES[0],ORG_SCOPES[0]),'D4_COMMON_SCOPE_HOLD')
    def test_unknown_exact(self): self.assertEqual(outcome_review('UNKNOWN',True),'QUARANTINE_EXACT_READBACK_HOLD')
    def test_unknown_absent(self): self.assertEqual(outcome_review('UNKNOWN',False),'QUARANTINE_UNRESOLVED_HOLD')
    def test_pending(self): self.assertEqual(outcome_review('PENDING',False),'QUARANTINE_UNRESOLVED_HOLD')
    def test_normal_close(self): self.assertEqual(outcome_review('COMMITTED',True),'CLOSE_DEDICATED_HOLD')


if __name__=='__main__': unittest.main()
