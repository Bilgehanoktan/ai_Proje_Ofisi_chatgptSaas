import unittest
from dataclasses import replace
from org_model import Org,Unit,Seat
from staffing import Staffing,Definition,Instance,Binding
from operations import ProjectTeam
from office_bridge import *

class BridgeTest(unittest.TestCase):
    def setUp(self):
        o=Org('t','c',(Unit('c','company',None),Unit('a','department','c'),Unit('b','department','c')),(Seat('w','a','research'),Seat('x','b','research'),Seat('y','b','research')))
        self.s=Staffing(o,(Definition('dr','research'),),(Instance('iw','dr','t','c'),Instance('ix','dr','t','c')),(Binding('w','iw'),Binding('x','ix')))
        self.v=OfficeView('t','c','d0-world','layout-r1',(Room('d0-f1/r','d0-f1','WORK'),Room('d0-f2/r','d0-f2','WORK'),Room('d0-f1/m','d0-f1','MEETING')),(Station('d0-f1/s','d0-f1/r','research'),Station('d0-f2/s','d0-f2/r','research')),(Avatar('d0-visual-w','d0-f1/s','research'),Avatar('d0-visual-x','d0-f2/s','research')))
        self.links=(RoomLink('a','d0-f1/r'),RoomLink('b','d0-f2/r'))
        self.pairs=(PairProposal('iw','w','d0-visual-w','d0-f1/s'),PairProposal('ix','x','d0-visual-x','d0-f2/s'))
        self.team=ProjectTeam('t','c',self.s.revision(),'p','w',('w','x'))
    def p(self,**kw):
        args=dict(s=self.s,view=self.v,staffing_revision=self.s.revision(),office_revision=self.v.revision(),links=self.links,pairs=self.pairs); args.update(kw); return project(**args)
    def test_valid(self):
        p=self.p(); self.assertEqual(len(p['pairs']),2); self.assertFalse(p['authoritative']); self.assertIsNone(p['placement']); self.assertTrue(all(x['agentInstanceId'] is None for x in p['pairs']))
    def test_many_to_many(self): self.assertEqual(len(self.p(links=self.links+(RoomLink('a','d0-f2/r'),RoomLink('b','d0-f1/r')))['roomLinks']),4)
    def test_no_auto_map(self): self.assertEqual(self.p(pairs=())['unmappedInstances'],['iw','ix'])
    def test_scope(self):
        with self.assertRaises(ValueError): self.p(view=replace(self.v,tenant='other'))
    def test_stale_staffing(self):
        with self.assertRaises(ValueError): self.p(staffing_revision='bad')
    def test_stale_office(self):
        with self.assertRaises(ValueError): self.p(view=replace(self.v,layout_revision='r2'))
    def test_duplicate_room(self):
        with self.assertRaises(ValueError): self.p(links=self.links+self.links)
    def test_wrong_department(self):
        with self.assertRaises(ValueError): self.p(links=self.links[:1])
    def test_wrong_seat(self):
        with self.assertRaises(ValueError): self.p(pairs=(replace(self.pairs[0],seat='x'),))
    def test_wrong_home(self):
        with self.assertRaises(ValueError): self.p(pairs=(replace(self.pairs[0],station='d0-f2/s'),))
    def test_duplicate_pair(self):
        with self.assertRaises(ValueError): self.p(pairs=self.pairs+self.pairs)
    def test_live_id_rejected(self):
        with self.assertRaises(ValueError): replace(self.v,avatars=(replace(self.v.avatars[0],agent_instance_id='real'),)).revision()
    def test_passive_rejected(self):
        with self.assertRaises(ValueError): replace(self.v,stations=(replace(self.v.stations[0],kind='PASSIVE'),)).revision()
    def test_bad_role(self):
        with self.assertRaises(ValueError): replace(self.v,avatars=(replace(self.v.avatars[0],role='qa'),)).revision()
    def test_meeting(self):
        p=self.p(meetings=(MeetingProposal(self.team,'d0-f1/m'),)); self.assertFalse(p['meetings'][0]['reserved']); self.assertEqual(p['meetings'][0]['decision'],'HOLD')
    def test_meeting_stale(self):
        with self.assertRaises(ValueError): self.p(meetings=(MeetingProposal(replace(self.team,revision='bad'),'d0-f1/m'),))
    def test_wrong_meeting_room(self):
        with self.assertRaises(ValueError): self.p(meetings=(MeetingProposal(self.team,'d0-f1/r'),))
    def test_determinism(self): self.assertEqual(self.p(),self.p(links=self.links[::-1],pairs=self.pairs[::-1]))
    def test_change(self):
        n=replace(self.s,bindings=(Binding('y','iw'),Binding('x','ix')),previous=self.s.revision()); p=review_change(self.s,n,self.v,self.p()); self.assertEqual(p['changedInstances'],['iw']); self.assertEqual(len(p['invalidatedActors']),2); self.assertIsNone(p['placement'])
    def test_change_tamper(self):
        n=replace(self.s,previous=self.s.revision()); p=self.p(); p['geometryJoin']='ALLOW'
        with self.assertRaises(ValueError): review_change(self.s,n,self.v,p)
    def test_change_unlinked(self):
        with self.assertRaises(ValueError): review_change(self.s,self.s,self.v,self.p())
    def test_detached(self):
        p=self.p(); p['pairs'].clear(); self.assertEqual(len(self.p()['pairs']),2)

class A5ShapeTest(unittest.TestCase):
    def snapshot(self):
        return {'mode':'D0_SYNTHETIC_WORLD','authoritative':False,'geometryJoin':'HOLD','token':{'revision':'d0-r1','sequence':0},'floors':[{'floorId':'d0-f1','layoutRevision':'D0-HYBRID-A1-reference-r1-A2','lifecycle':'ACTIVE','rooms':[{'id':'d0-f1/F1-RSCH','kind':'SEMI_OPEN_POD'},{'id':'d0-f1/F1-BRIEF','kind':'MEETING_ZONE'},{'id':'d0-f1/F1-EXP','kind':'RESERVED_POD'}],'stations':[{'stationId':'d0-f1/d0-r','floorId':'d0-f1','roomId':'d0-f1/F1-RSCH','roleTemplateId':'research','kind':'CORE','agentInstanceId':None},{'stationId':'d0-f1/d0-reserve-1','floorId':'d0-f1','roomId':'d0-f1/F1-EXP','roleTemplateId':None,'kind':'PASSIVE','agentInstanceId':None}]}],'actors':[{'visualActorId':'d0-visual-r','roleTemplateId':'research','floorId':'d0-f1','agentInstanceId':None,'home':{'floorId':'d0-f1','stationId':'d0-f1/d0-r'}}]}
    def test_shape(self):
        v=from_a5_metadata('t','c','d0-world',self.snapshot()); self.assertEqual(len(v.stations),1); self.assertEqual(v.rooms[1].kind,'MEETING'); self.assertIsNone(v.avatars[0].agent_instance_id)
    def test_live_rejected(self):
        x=self.snapshot(); x['actors'][0]['agentInstanceId']='live'
        with self.assertRaises(ValueError): from_a5_metadata('t','c','d0-world',x)
    def test_authority_rejected(self):
        x=self.snapshot(); x['authoritative']=True
        with self.assertRaises(ValueError): from_a5_metadata('t','c','d0-world',x)
    def test_sequence_no_motion_join(self):
        x=self.snapshot(); a=from_a5_metadata('t','c','d0-world',x); x['token']['sequence']=1; x['actors'][0]['cell']=[3,4]; self.assertEqual(a,from_a5_metadata('t','c','d0-world',x))
    def test_passive_floor(self):
        x=self.snapshot(); x['floors'][0]['lifecycle']='DRAFT'; x['actors']=[]; v=from_a5_metadata('t','c','d0-world',x); self.assertEqual(v.rooms,()); self.assertEqual(v.stations,())
