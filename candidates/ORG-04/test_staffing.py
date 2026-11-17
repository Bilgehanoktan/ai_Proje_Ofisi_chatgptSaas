import unittest
from dataclasses import replace
from org_model import Org, Unit, Seat
from staffing import *
class TestStaffing(unittest.TestCase):
    def setUp(self):
        o=Org('t','c',(Unit('c','company',None),Unit('d','department','c')),(Seat('l','d','lead'),Seat('w','d','research','l')))
        self.s=Staffing(o,(Definition('dl','lead'),Definition('dw','research')),(Instance('il','dl','t','c'),Instance('iw','dw','t','c')),(Binding('l','il'),Binding('w','iw')))
    def test_valid(self): self.assertEqual(len(self.s.revision()),64)
    def test_order(self): self.assertEqual(self.s.revision(),replace(self.s,bindings=self.s.bindings[::-1]).revision())
    def test_scope(self):
        with self.assertRaises(ValueError): replace(self.s,instances=(replace(self.s.instances[0],tenant='foreign'),self.s.instances[1])).revision()
    def test_duplicate(self):
        with self.assertRaises(ValueError): replace(self.s,definitions=self.s.definitions*2).revision()
    def test_occupancy(self):
        with self.assertRaises(ValueError): replace(self.s,bindings=self.s.bindings*2).revision()
    def test_role(self):
        with self.assertRaises(ValueError): replace(self.s,bindings=(Binding('l','iw'),)).revision()
    def test_trust(self):
        with self.assertRaises(ValueError): replace(self.s,definitions=self.s.definitions+(Definition('iv','independent-verifier'),)).revision()
    def test_delegate(self):
        r=self.s.revision(); self.assertEqual(delegate(self.s,r,'task','l','w').decision,'HOLD'); self.assertEqual(self.s.revision(),r)
    def test_reverse(self):
        with self.assertRaises(ValueError): delegate(self.s,self.s.revision(),'task','w','l')
    def test_stale(self):
        with self.assertRaises(ValueError): delegate(self.s,'old','task','l','w')
    def test_vacant(self):
        s=replace(self.s,bindings=self.s.bindings[:1])
        with self.assertRaises(ValueError): delegate(s,s.revision(),'task','l','w')
    def test_history(self): self.assertEqual(verify_successor(self.s,replace(self.s,previous=self.s.revision())),replace(self.s,previous=self.s.revision()).revision())
    def test_bad_history(self):
        with self.assertRaises(ValueError): verify_successor(self.s,self.s)
