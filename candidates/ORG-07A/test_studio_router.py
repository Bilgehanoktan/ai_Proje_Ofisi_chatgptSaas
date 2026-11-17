"""Transport tests: real FastAPI ASGI stack, simulated R3 reader/resolver."""
from dataclasses import dataclass, replace
from pathlib import Path
from copy import deepcopy
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from studio_router import build_router, ServerReadContext, ROUTE, DENIAL, load_validator

ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT/'studio.schema.json'
if not SCHEMA.exists():
    SCHEMA = ROOT.parent/'ORG-05R3'/'studio.schema.json'
HEAD = 'a'*64
KEY = ('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
TOKEN = 'opaque-test-token'

@dataclass(frozen=True)
class Scope:
    values: tuple = KEY
    def key(self): return self.values

@dataclass(frozen=True)
class Session:
    scope: Scope = Scope()


def projection():
    return {'schema':'org.studio.preview.v0-D0','scope':dict(zip(('tenant_id','company_id','environment_id'),KEY)),
            'revision':HEAD,'sequence':1,'previous_revision':None,
            'units':[{'id':'synthetic-company','kind':'company','parent':None}],
            'positions':[{'id':'lead','unit':'synthetic-company','role':'orchestrator','reports_to':None,'occupied':True}],
            'decision':'HOLD','authoritative':False,'identity_owner':'HOLD','geometry_join':'HOLD',
            'runtime_binding':None,'dispatch_allowed':False}

class Tests(unittest.TestCase):
    def setUp(self):
        self.calls=[]; self.body=projection(); self.status=200; self.session=Session()
        self.ctx=ServerReadContext(ROOT/'disposable.sqlite',HEAD,self.resolve,lambda:99)
        self.mode='normal'
        app=FastAPI(); app.include_router(build_router(lambda:self.ctx,SCHEMA,reader=self.read))
        self.client=TestClient(app); self.addCleanup(self.client.close)
    def resolve(self,token):
        self.calls.append(('resolve',token)); return self.session
    def read(self,path,token,resolve,head,now):
        self.calls.append(('read',path,head,now))
        if self.mode=='raise': raise ValueError('secret /private/db')
        if self.mode!='noresolve': resolve(token)
        if self.mode=='twice': resolve(token)
        if self.mode=='wrongtoken': resolve('other')
        return self.status,self.body
    def get(self,headers=None,url=ROUTE,**kwargs):
        return self.client.get(url,headers={'Authorization':'Bearer '+TOKEN} if headers is None else headers,**kwargs)
    def denied(self,r):
        self.assertEqual((r.status_code,r.json()),(403,DENIAL)); self.assertEqual(r.headers['cache-control'],'no-store')
        self.assertNotIn(TOKEN,r.text); self.assertNotIn('/private/db',r.text)
    def test_success(self):
        r=self.get(); self.assertEqual(r.status_code,200); self.assertEqual(r.json(),self.body)
        self.assertEqual(r.headers['vary'],'Authorization'); self.assertEqual(r.headers['cache-control'],'no-store')
        self.assertEqual(self.calls,[('read',self.ctx.path,HEAD,99),('resolve',TOKEN)])
    def test_missing_header(self): self.denied(self.get({})); self.assertEqual(self.calls,[])
    def test_bad_scheme(self): self.denied(self.get({'Authorization':'Basic abc'}))
    def test_blank(self): self.denied(self.get({'Authorization':'Bearer '}))
    def test_duplicate(self): self.denied(self.get([('Authorization','Bearer abc'),('Authorization','Bearer def')]))
    def test_long(self): self.denied(self.get({'Authorization':'Bearer '+'a'*4097}))
    def test_query_scope(self): self.denied(self.get(url=ROUTE+'?tenant_id=synthetic-other')); self.assertEqual(self.calls,[])
    def test_query_revision(self): self.denied(self.get(url=ROUTE+'?revision='+HEAD))
    def test_body(self): self.denied(self.client.request('GET',ROUTE,headers={'Authorization':'Bearer '+TOKEN},content=b'{}'))
    def test_post(self): self.assertEqual(self.client.post(ROUTE).status_code,405); self.assertEqual(self.calls,[])
    def test_reader_denies(self): self.status=403; self.denied(self.get())
    def test_reader_error(self): self.mode='raise'; self.denied(self.get())
    def test_no_resolver(self): self.mode='noresolve'; self.denied(self.get())
    def test_double_resolver(self): self.mode='twice'; self.denied(self.get())
    def test_wrong_resolver_token(self): self.mode='wrongtoken'; self.denied(self.get())
    def test_wrong_scope(self): self.body['scope']['tenant_id']='synthetic-other'; self.denied(self.get())
    def test_wrong_revision(self): self.body['revision']='b'*64; self.denied(self.get())
    def test_unknown_field(self): self.body['principal']='demo-leak'; self.denied(self.get())
    def test_nested_identity(self): self.body['positions'][0]['agent_instance_id']='demo-leak'; self.denied(self.get())
    def test_authority(self): self.body['authoritative']=True; self.denied(self.get())
    def test_dispatch(self): self.body['dispatch_allowed']=True; self.denied(self.get())
    def test_binding(self): self.body['runtime_binding']='demo-binding'; self.denied(self.get())
    def test_bad_clock(self): self.ctx=replace(self.ctx,clock=lambda:True); self.denied(self.get())
    def test_relative_path(self): self.ctx=replace(self.ctx,path=Path('a.sqlite')); self.denied(self.get())
    def test_schema_pin(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'schema'; p.write_bytes(SCHEMA.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'STUDIO_SCHEMA_PIN_HOLD'): load_validator(p)

if __name__=='__main__': unittest.main(verbosity=2)
