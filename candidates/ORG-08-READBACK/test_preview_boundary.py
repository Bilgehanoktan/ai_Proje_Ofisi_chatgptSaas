"""Actual local protocol/schema tests; original owner stores are mocked in adapter tests."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from dataclasses import dataclass, replace
from types import SimpleNamespace
from unittest.mock import patch
import preview_boundary as b
import preview_reader as r

SCHEMA_DIR=Path(os.environ.get('ORG08_SCHEMA_DIR',str(r.R3)))
H='a'*64; O='b'*64; P='sha256:'+'c'*64

def fixture():
    pins=b.ReviewPins(H,'demo-project',P,'research','worker','research',0,b.ZERO,O)
    scope=dict(zip(b.SCOPE_KEYS,b.COMMON_SCOPE))
    studio={'schema':'org.studio.preview.v0-D0','scope':scope,'revision':H,'sequence':1,'previous_revision':None,
        'units':[{'id':'ops','kind':'department','parent':None}],
        'positions':[{'id':'worker','unit':'ops','role':'research','reports_to':None,'occupied':True}],
        'decision':'HOLD','authoritative':False,'identity_owner':'HOLD','geometry_join':'HOLD','runtime_binding':None,'dispatch_allowed':False}
    combined={'schema':'org.combined.preview.v0-D0','scope':dict(scope),'org_revision':H,'staffing_revision':'d'*64,'project':pins.project_id,
        'history':{'count':0,'head':b.ZERO},'proposals':[],'office_revision':O,'office_pairs':1,'meeting_proposed':False,
        'geometry_join':'HOLD','runtime_binding':None,'decision':'HOLD','authoritative':False,'dispatch_allowed':False}
    binding={'reason':'D0_HISTORICAL_REFERENCE_MATCH_ONLY','structural_match':True,'org_revision':H,'plan_revision':P,'project_id':pins.project_id,
        'task_id':pins.task_id,'seat_id':pins.seat_id,'role':pins.role,'decision':'HOLD','freshness':'HISTORICAL_SAMPLE','authoritative':False,
        'runtime_binding':None,'geometry_join':'HOLD','dispatch_allowed':False,'release_ready':False}
    return pins,studio,combined,binding

class BoundaryTests(unittest.TestCase):
    def setUp(self): self.p,self.s,self.c,self.r=fixture()
    def join(self): return b.join_historical(SCHEMA_DIR,self.p,self.s,self.c,self.r)
    def denied(self):
        with self.assertRaises(b.Hold): self.join()
    def test_exact_schema_pins(self):
        for n,h in b.SCHEMAS.items(): self.assertEqual(b.blob((SCHEMA_DIR/n).read_bytes()),h); b.schema_validator(SCHEMA_DIR,n)
    def test_good_is_hold(self):
        x=self.join(); self.assertTrue(x['structural_match']); self.assertEqual(x['decision'],'HOLD'); self.assertFalse(x['atomic_cross_store']); self.assertIsNone(x['runtime_binding']); self.assertFalse(x['dispatch_allowed'])
    def test_studio_scope(self): self.s['scope']['environment_id']='A0_REVIEW_ONLY'; self.denied()
    def test_old_pg_scope(self): self.c['scope']={'tenant_id':'synthetic-tenant-a','company_id':'synthetic-company-a','environment_id':'ORG_R4_SAMPLE_ONLY'}; self.denied()
    def test_stale_studio(self): self.s['revision']='f'*64; self.denied()
    def test_stale_combined(self): self.c['org_revision']='f'*64; self.denied()
    def test_wrong_project(self): self.c['project']='demo-other'; self.denied()
    def test_wrong_task(self): self.r['task_id']='other'; self.denied()
    def test_wrong_plan(self): self.r['plan_revision']='sha256:'+'f'*64; self.denied()
    def test_wrong_role(self): self.s['positions'][0]['role']='qa'; self.denied()
    def test_empty_seat(self): self.s['positions'][0]['occupied']=False; self.denied()
    def test_duplicate_seat(self): self.s['positions']*=2; self.denied()
    def test_bad_unit(self): self.s['positions'][0]['unit']='unknown'; self.denied()
    def test_office_revision(self): self.c['office_revision']='f'*64; self.denied()
    def test_office_count(self): self.c['office_pairs']=2; self.denied()
    def test_history_count(self): self.c['history']['count']=1; self.denied()
    def test_history_head(self): self.c['history']['head']='f'*64; self.denied()
    def test_nonempty_history_and_sanitization(self):
        self.p=replace(self.p,history_count=1,history_head='e'*64)
        self.c['history']={'count':1,'head':'e'*64}; self.c['proposals']=[{'sequence':1,'plan_revision':P,'task':'research','sender':'lead','recipient':'worker','kind':'delegation','decision':'HOLD','digest':'e'*64}]
        out=self.join(); self.assertEqual(out['history_count'],1); self.assertNotIn('proposals',out); self.assertNotIn('sender',str(out)); self.c['proposals'][0]['sequence']=2; self.denied()
    def test_schema_extra_identity(self): self.s['principal_id']='demo-forged'; self.denied()
    def test_combined_extra_geometry(self): self.c['placement']={'station':'secret'}; self.denied()
    def test_runtime_extra_identity(self): self.r['agent_instance_id']='demo-forged'; self.denied()
    def test_no_authority(self):
        for k,v in [('decision','ALLOW'),('authoritative',True),('runtime_binding','demo-run'),('dispatch_allowed',True),('release_ready',True),('freshness','LIVE'),('geometry_join','ALLOW'),('structural_match',1)]:
            with self.subTest(k=k):
                old=self.r[k]; self.r[k]=v; self.denied(); self.r[k]=old
    def test_boolean_history_count(self): self.c['history']['count']=False; self.denied()
    def test_bad_schema_file(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'studio.schema.json'; p.write_text('{}')
            with self.assertRaisesRegex(b.Hold,'SCHEMA_PIN_HOLD'): b.schema_validator(t,p.name)
    def test_internal_output_schema(self):
        import json
        from jsonschema import Draft202012Validator
        schema=json.loads(Path(__file__).with_name("readback.schema.json").read_text()); Draft202012Validator.check_schema(schema)
        v=Draft202012Validator(schema); out=self.join(); self.assertTrue(v.is_valid(out))
        for k,value in (("principal_id","demo-principal"),("authoritative",True),("atomic_cross_store",True),("geometry_join","ALLOW")):
            self.assertFalse(v.is_valid({**out,k:value}))
    def test_no_input_mutation(self):
        old=copy.deepcopy((self.p,self.s,self.c,self.r)); self.join(); self.assertEqual(old,(self.p,self.s,self.c,self.r))

@dataclass(frozen=True)
class Scope:
    value:tuple=b.COMMON_SCOPE
    def key(self): return self.value
@dataclass(frozen=True)
class History:
    count:int=0
    head:str=b.ZERO
@dataclass(frozen=True)
class OfficePin:
    scope:Scope=Scope()
    world:str='d0-world'
    revision:str=O
class Office:
    world='d0-world'
    def revision(self): return O
@dataclass(frozen=True)
class Binding:
    reason:str; structural_match:bool; org_revision:str; plan_revision:str; project_id:str; task_id:str; seat_id:str; role:str; decision:str; freshness:str; authoritative:bool; runtime_binding:object; geometry_join:str; dispatch_allowed:bool; release_ready:bool
class Store:
    _key=b.COMMON_SCOPE
    def studio_view(self,head): return fixture()[1]
    def combined(self,*args): return fixture()[2]

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.p,self.s,self.c,self.binding=fixture(); self.calls=[]
        def bridge(*args,**kw): self.calls.append('bridge'); return Binding(**self.binding)
        self.ops=SimpleNamespace(OperationsStore=Store,HistoryPin=History,OfficePin=OfficePin,check_pin=lambda x:None)
        self.bridge=SimpleNamespace(BindingReview=Binding,review_research_binding=bridge)
        self.patch=patch.object(r,'owners',return_value=(self.ops,SimpleNamespace(Scope=Scope),SimpleNamespace(OfficeView=Office),self.bridge));self.patch.start();self.addCleanup(self.patch.stop)
        self.patch2=patch.object(r,'R3',SCHEMA_DIR);self.patch2.start();self.addCleanup(self.patch2.stop)
    def project(self,**kw):
        args=dict(store=Store(),pins=self.p,history_pin=History(),office=Office(),office_pin=OfficePin(),plan=None,run_pins=(),members=(),pool=None,events=(),anchor=None);args.update(kw);return r.review_project(None,**args)
    def test_internal_project(self): self.assertTrue(self.project()['structural_match']); self.assertEqual(self.calls,['bridge'])
    def test_stale_history(self): self.assertEqual(self.project(history_pin=History(1,'e'*64)),b.hold_preview());self.assertEqual(self.calls,[])
    def test_wrong_office(self): self.assertEqual(self.project(office_pin=OfficePin(world='other')),b.hold_preview());self.assertEqual(self.calls,[])
    def test_bridge_hold(self): self.binding['structural_match']=False;self.assertEqual(self.project(),b.hold_preview())
    def test_schema_violation(self): self.binding['authoritative']=True;self.assertEqual(self.project(),b.hold_preview())
    def test_untrusted_store(self): self.assertEqual(self.project(store=object()),b.hold_preview());self.assertEqual(self.calls,[])

if __name__=='__main__': unittest.main(verbosity=2)
