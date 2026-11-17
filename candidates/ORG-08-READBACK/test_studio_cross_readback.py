"""Run exact ORG-07A ASGI transport against synthetic owner responses, NOT live IAM."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from dataclasses import replace
from fastapi import FastAPI
from fastapi.testclient import TestClient
import preview_boundary as b
from test_preview_boundary import fixture, SCHEMA_DIR, Scope

ROUTER = Path(os.environ.get('ORG08_STUDIO_ROUTER_DIR',str(Path(__file__).resolve().parents[1]/'ORG-07A')))/'studio_router.py'
PIN='eda507f8e5933c27568064455eccc4cf85bbba0c'

def load_router():
    raw=ROUTER.read_bytes()
    if b.blob(raw)!=PIN: raise RuntimeError('ORG07A_ROUTER_PIN_HOLD')
    spec=importlib.util.spec_from_file_location('org07a_pinned_router',ROUTER)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module

class CrossReadbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.router=load_router()
    def setUp(self):
        self.p,self.s,self.c,self.binding=fixture(); self.read_calls=[]
        ctx=self.router.ServerReadContext(Path(__file__).resolve(),self.p.org_revision,lambda _:SimpleNamespace(scope=Scope()),lambda:99)
        def reader(path,credential,resolve,head,now):
            self.read_calls.append('studio'); resolve(credential); return 200,self.s
        app=FastAPI(); app.include_router(self.router.build_router(lambda:ctx,SCHEMA_DIR/'studio.schema.json',reader=reader))
        self.client=TestClient(app); self.addCleanup(self.client.close)
    def get(self): return self.client.get(self.router.ROUTE,headers={'Authorization':'Bearer opaque'})
    def test_same_head_transport_and_internal_review(self):
        response=self.get(); self.assertEqual(response.status_code,200)
        self.assertEqual(response.headers['cache-control'],'no-store')
        # Independent trusted fixture inputs; HTTP output is only compared, not used as authority.
        result=b.join_historical(SCHEMA_DIR,self.p,self.s,self.c,self.binding)
        self.assertEqual(result['org_revision'],response.json()['revision'])
        self.assertEqual(result['decision'],'HOLD'); self.assertFalse(result['dispatch_allowed'])
    def test_studio_success_cannot_create_office_route_or_grant(self):
        self.assertEqual(self.get().status_code,200)
        self.assertEqual(self.client.get('/demo/v1/organization/office-readback',headers={'Authorization':'Bearer opaque'}).status_code,404)
        self.assertEqual(self.read_calls,['studio'])
        result=b.join_historical(SCHEMA_DIR,self.p,self.s,self.c,self.binding)
        self.assertFalse(result['authoritative']); self.assertIsNone(result['runtime_binding']); self.assertFalse(result['release_ready'])
    def test_studio_success_does_not_override_combined_head(self):
        self.assertEqual(self.get().status_code,200)
        self.c['org_revision']='f'*64
        with self.assertRaises(b.Hold): b.join_historical(SCHEMA_DIR,self.p,self.s,self.c,self.binding)

if __name__=='__main__': unittest.main(verbosity=2)
