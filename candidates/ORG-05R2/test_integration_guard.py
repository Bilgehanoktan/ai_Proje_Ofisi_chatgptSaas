import unittest
from dataclasses import replace
from org_model import Org, Unit, Seat
from staffing import Definition, Instance, Binding, Staffing
from operations import ProjectTeam, propose, append
from office_bridge import OfficeView, Room, MeetingProposal, project
from integration_guard import ReviewPin, D0, validate_staffing, inspect_runtime, verify_retained_history, review_office_successor


class GuardTests(unittest.TestCase):
    def setUp(self):
        t,c,e = D0
        o = Org(t,c,(Unit(c,'company',None),Unit('d','department',c),Unit('b','department',c)),(Seat('w','d','research'),Seat('x','b','research')))
        self.s = Staffing(o,(Definition('dr','research'),),(Instance('demo-w','dr',t,c),Instance('demo-x','dr',t,c)),(Binding('w','demo-w'),Binding('x','demo-x')))
        self.p = ReviewPin(t,c,e,self.s.revision(),'demo-project','sha256:'+'a'*64,'plan','demo-run','demo-w','demo-principal','research')
        self.team = ProjectTeam(t,c,self.s.revision(),'demo-project','w',('w','x'))
        self.history = append(self.s,self.team,(),propose(self.s,self.team,'plan','w','x','handoff'))
    def test_valid_revision_unchanged(self): self.assertEqual(validate_staffing(self.s),self.s.revision())
    def test_nonstring_scope(self):
        with self.assertRaises(ValueError): validate_staffing(replace(self.s,org=replace(self.s.org,tenant=123)))
    def test_whitespace_identifier(self):
        with self.assertRaises(ValueError): validate_staffing(replace(self.s,definitions=(Definition(' dr','research'),)))
    def test_aliases(self):
        for r in ('Independent-Verifier','independent_verifier','iv','pep','h01','w-a','policy-engine','research\n'):
            with self.subTest(role=r), self.assertRaises(ValueError): validate_staffing(replace(self.s,definitions=(Definition('dr',r),)))
    def test_role_in_seat(self):
        with self.assertRaises(ValueError): validate_staffing(replace(self.s,org=replace(self.s.org,seats=(Seat('w','d','iv'),self.s.org.seats[1]))))
    def test_reference_only(self):
        r=inspect_runtime(self.s,'w',self.p,self.p); self.assertTrue(r['structural_match']); self.assertEqual(r['decision'],'HOLD'); self.assertFalse(r['dispatch_allowed']); self.assertIsNone(r['agent_instance_id']); self.assertIsNone(r['principal_id'])
    def test_environment(self):
        p=replace(self.p,environment_id='PROD'); self.assertFalse(inspect_runtime(self.s,'w',p,p)['structural_match'])
    def test_mismatched_principal(self): self.assertFalse(inspect_runtime(self.s,'w',replace(self.p,principal_id='demo-other'),self.p)['structural_match'])
    def test_missing_expected(self): self.assertFalse(inspect_runtime(self.s,'w',self.p,None)['structural_match'])
    def test_stale_revision(self):
        p=replace(self.p,staffing_revision='b'*64); self.assertFalse(inspect_runtime(self.s,'w',p,p)['structural_match'])
    def test_wrong_seat(self): self.assertFalse(inspect_runtime(self.s,'x',self.p,self.p)['structural_match'])
    def test_non_demo(self):
        p=replace(self.p,run_id='run'); self.assertFalse(inspect_runtime(self.s,'w',p,p)['structural_match'])
    def test_history_pin(self): self.assertEqual(verify_retained_history(self.s,self.team,self.history,1,self.history[0].digest),self.history[0].digest)
    def test_truncated(self):
        with self.assertRaises(ValueError): verify_retained_history(self.s,self.team,(),1,self.history[0].digest)
    def test_rewritten(self):
        h=append(self.s,self.team,(),propose(self.s,self.team,'different','w','x','handoff'))
        with self.assertRaises(ValueError): verify_retained_history(self.s,self.team,h,1,self.history[0].digest)
    def test_bool_sequence(self):
        with self.assertRaises(ValueError): verify_retained_history(self.s,self.team,(replace(self.history[0],sequence=True),),1,self.history[0].digest)
    def test_meeting_invalidation(self):
        v=OfficeView(*D0[:2],'d0-world','layout-r1',(Room('d0-f1/m','d0-f1','MEETING'),),(),())
        m=(MeetingProposal(self.team,'d0-f1/m'),); prior=project(self.s,v,self.s.revision(),v.revision(),(),(),m)
        n=replace(self.s,previous=self.s.revision()); r=review_office_successor(self.s,n,v,prior,(),(),m)
        self.assertEqual(len(r['invalidatedMeetings']),1); self.assertIsNone(r['placement']); self.assertFalse(r['authoritative'])
    def test_meeting_tamper(self):
        v=OfficeView(*D0[:2],'d0-world','layout-r1',(Room('d0-f1/m','d0-f1','MEETING'),),(),())
        m=(MeetingProposal(self.team,'d0-f1/m'),); prior=project(self.s,v,self.s.revision(),v.revision(),(),(),m); prior['meetings'][0]['reserved']=True
        with self.assertRaises(ValueError): review_office_successor(self.s,replace(self.s,previous=self.s.revision()),v,prior,(),(),m)
