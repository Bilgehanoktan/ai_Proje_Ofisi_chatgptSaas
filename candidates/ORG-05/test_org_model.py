import unittest
from dataclasses import replace
from org_model import *
class TestOrg(unittest.TestCase):
    def setUp(self):
        self.o=Org('demo-t','c',(Unit('c','company',None),Unit('d','department','c'),Unit('t','team','d')),(Seat('lead','d','lead'),Seat('worker','t','research','lead')))
    def test_valid(self): self.assertEqual(len(self.o.revision()),64)
    def test_order(self): self.assertEqual(self.o.revision(),replace(self.o,seats=self.o.seats[::-1]).revision())
    def test_duplicate(self):
        with self.assertRaises(ValueError): replace(self.o,seats=self.o.seats*2).revision()
    def test_cycle(self):
        with self.assertRaises(ValueError): replace(self.o,seats=(replace(self.o.seats[0],reports_to='worker'),self.o.seats[1])).revision()
    def test_foreign(self):
        with self.assertRaises(ValueError): replace(self.o,seats=(Seat('x','other','research'),)).revision()
    def test_iv(self):
        with self.assertRaises(ValueError): replace(self.o,seats=(Seat('x','d','independent-verifier'),)).revision()
    def test_stale(self):
        with self.assertRaises(ValueError): propose(self.o,'old','task','worker')
    def test_proposal(self):
        r=self.o.revision(); self.assertEqual(propose(self.o,r,'task','worker').decision,'HOLD'); self.assertEqual(self.o.revision(),r)
    def test_missing_parent(self):
        with self.assertRaises(ValueError): replace(self.o,seats=(Seat('x','d','research','missing'),)).revision()
    def test_scope_revision(self): self.assertNotEqual(self.o.revision(),replace(self.o,tenant='other').revision())
if __name__=='__main__': unittest.main()
