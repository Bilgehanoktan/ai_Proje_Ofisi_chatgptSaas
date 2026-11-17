import unittest
from dataclasses import replace
from scale import fixture, run, SIZES
from staffing import Instance, Binding
from operations import office_projection

class ScaleTests(unittest.TestCase):
    def test_sizes(self):
        for n in SIZES:
            with self.subTest(n=n):
                s=fixture(n); self.assertEqual(len(s.bindings),n); self.assertEqual(len(office_projection(s)['rows']),n)
    def test_catalog_only(self):
        s=fixture(0,267); self.assertEqual(len(s.definitions),267); self.assertEqual(s.instances,()); self.assertEqual(office_projection(s)['rows'],[])
    def test_deterministic(self):
        for n in SIZES: self.assertEqual(fixture(n).revision(),fixture(n).revision())
    def test_collision_at_scale(self):
        s=fixture(100)
        with self.assertRaises(ValueError): replace(s,bindings=s.bindings+(Binding('p99','a0'),)).revision()
    def test_scope_at_scale(self):
        s=fixture(100)
        with self.assertRaises(ValueError): replace(s,instances=s.instances[:-1]+(Instance('a99','d3','other','company'),)).revision()
    def test_no_267_actors(self):
        with self.assertRaises(ValueError): fixture(267)
    def test_separate_catalog(self):
        with self.assertRaises(ValueError): fixture(100,267)
    def test_probe_no_authority(self):
        r=run(12,repeats=2); self.assertEqual(r['actual_runtime'],'NOT_RUN'); self.assertEqual(r['actual_render'],'NOT_RUN')
