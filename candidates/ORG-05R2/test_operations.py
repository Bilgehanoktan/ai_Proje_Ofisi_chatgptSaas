import unittest
from dataclasses import replace
from org_model import Org, Unit, Seat
from staffing import Staffing, Definition, Instance, Binding
from operations import *
class OperationsTest(unittest.TestCase):
    def setUp(self):
        o=Org('t','c',(Unit('c','company',None),Unit('a','department','c'),Unit('b','department','c')),(Seat('l','a','lead'),Seat('w','a','research','l'),Seat('x','b','research')))
        self.s=Staffing(o,(Definition('dl','lead'),Definition('dr','research')),(Instance('il','dl','t','c'),Instance('iw','dr','t','c'),Instance('ix','dr','t','c')),(Binding('l','il'),Binding('w','iw'),Binding('x','ix')))
        self.t=ProjectTeam('t','c',self.s.revision(),'p','l',('l','w','x'))
    def p(self): return propose(self.s,self.t,'task','w','x','handoff')
    def test_handoff(self): self.assertEqual(self.p().decision,'HOLD')
    def test_delegate(self): self.assertEqual(propose(self.s,self.t,'task','l','w','delegation').decision,'HOLD')
    def test_same_department(self):
        with self.assertRaises(ValueError): propose(self.s,self.t,'task','l','w','handoff')
    def test_reverse(self):
        with self.assertRaises(ValueError): propose(self.s,self.t,'task','w','l','delegation')
    def test_scope(self):
        with self.assertRaises(ValueError): context(self.s,replace(self.t,tenant='other'))
    def test_stale(self):
        with self.assertRaises(ValueError): context(self.s,replace(self.t,revision='old'))
    def test_duplicate(self):
        with self.assertRaises(ValueError): context(self.s,replace(self.t,members=('l','l')))
    def test_nonmember(self):
        with self.assertRaises(ValueError): propose(self.s,replace(self.t,members=('l','w')),'task','w','x','handoff')
    def test_vacant(self):
        s=replace(self.s,bindings=self.s.bindings[:2]); t=replace(self.t,revision=s.revision())
        with self.assertRaises(ValueError): context(s,t)
    def test_history(self):
        h=append(self.s,self.t,(),self.p()); self.assertEqual(verify_history(self.s,self.t,h),h[0].digest)
    def test_replay(self):
        h=append(self.s,self.t,(),self.p())
        with self.assertRaises(ValueError): append(self.s,self.t,h,self.p())
    def test_tamper(self):
        h=append(self.s,self.t,(),self.p())
        with self.assertRaises(ValueError): verify_history(self.s,self.t,(replace(h[0],digest='bad'),))
    def test_authority(self):
        with self.assertRaises(ValueError): append(self.s,self.t,(),replace(self.p(),decision='ALLOW'))
    def test_project(self):
        with self.assertRaises(ValueError): append(self.s,replace(self.t,project='other'),(),self.p())
    def test_unchanged(self):
        r=self.s.revision(); self.p(); self.assertEqual(self.s.revision(),r)
    def test_office(self):
        p=office_projection(self.s); self.assertFalse(p['authority']); self.assertIsNone(p['placement']); self.assertEqual(len(p['rows']),3)
    def test_team_binding(self):
        with self.assertRaises(ValueError): append(self.s,replace(self.t,coordinator='w'),(),self.p())
