import unittest
from parallel_preflight import compare

A, B, C = 'a'*40, 'b'*40, 'c'*40
class ParallelPreflightTests(unittest.TestCase):
    def test_unchanged(self):
        self.assertEqual(compare({'a': A}, {'a': A}, {'a': A})['rows'], [])
    def test_disjoint(self):
        r = compare({}, {'local.ts': A}, {'incoming.py': B})
        self.assertEqual([x['status'] for x in r['rows']], ['INCOMING_ONLY', 'LOCAL_ONLY'])
        self.assertFalse(r['merge_authorized'])
    def test_diverged(self):
        self.assertTrue(compare({'a': A}, {'a': B}, {'a': C})['rows'][0]['manual_review'])
    def test_same_change(self):
        self.assertEqual(compare({'a': A}, {'a': B}, {'a': B})['rows'][0]['status'], 'SAME_CHANGE')
    def test_shared_manifest(self):
        p = 'product/SOURCE_MANIFEST.json'
        self.assertEqual(compare({p: A}, {p: A}, {p: B})['manual_count'], 1)
    def test_deleted(self):
        self.assertTrue(compare({'a': A}, {'a': A}, {})['rows'][0]['manual_review'])
    def test_path_traversal(self):
        with self.assertRaises(ValueError): compare({}, {}, {'../a': A})
    def test_case_alias_in_input(self):
        with self.assertRaises(ValueError): compare({}, {'A': A, 'a': B}, {})
    def test_case_alias_across_branches(self):
        self.assertEqual(compare({}, {'A': A}, {'a': B})['case_collisions'], [['A', 'a']])
    def test_invalid_pin(self):
        with self.assertRaises(ValueError): compare({}, {}, {'a': 'bad'})
    def test_contract_review(self):
        self.assertEqual(compare({}, {}, {'product/frontend/contracts/a.json': A})['manual_count'], 1)
    def test_empty_never_grants(self):
        self.assertFalse(compare({}, {}, {})['merge_authorized'])

if __name__ == '__main__': unittest.main()
