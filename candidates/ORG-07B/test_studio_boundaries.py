"""Supplemental ORG-07B real SQLite/ASGI tests; no new IAM or product mount."""
from dataclasses import replace
from pathlib import Path
import hashlib
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
R3 = ROOT/'candidates'/'ORG-05R3'
A = ROOT/'candidates'/'ORG-07A'


def git_blob(path):
    raw = path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def main():
    for name, expected in {'studio_router.py':'eda507f8e5933c27568064455eccc4cf85bbba0c',
                           'test_studio_original.py':'b928799ddc46fb0f49ee2b6e05199fa173777813'}.items():
        if git_blob(A/name) != expected:
            raise RuntimeError('ORG07A_SOURCE_PIN_HOLD')
    sys.path.insert(0,str(A))
    from test_studio_original import PINS
    for name, expected in PINS.items():
        if git_blob(R3/name) != expected:
            raise RuntimeError('R3_SOURCE_PIN_HOLD')
    sys.path.insert(0,str(R3))
    from test_durable_ops import DurableTests
    from durable_ops import ReadSession
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from studio_router import build_router, ServerReadContext, ROUTE, DENIAL

    class BoundaryTests(unittest.TestCase):
        def setUp(self):
            self.f = DurableTests(); self.addCleanup(self.f.doCleanups); self.f.setUp()
            self.session = ReadSession(self.f.scope,'demo-reader',100,'org.preview.read')
            self.calls = 0
            self.ctx = ServerReadContext(self.f.path,self.f.rev,self.resolve,lambda:99)
            self.app = FastAPI(); self.app.include_router(build_router(lambda:self.ctx,R3/'studio.schema.json'))
            self.client = TestClient(self.app); self.addCleanup(self.client.close)
        def resolve(self, token):
            self.calls += 1
            if token != 'opaque': return None
            return self.session
        def get(self, token='opaque'):
            return self.client.get(ROUTE,headers={'Authorization':'Bearer '+token})
        def denied(self, r):
            self.assertEqual((r.status_code,r.json()),(403,DENIAL))
            self.assertEqual(r.headers['cache-control'],'no-store')
        def test_wrong_company(self):
            self.session=replace(self.session,scope=replace(self.f.scope,company='synthetic-other'))
            self.denied(self.get())
        def test_wrong_environment(self):
            self.session=replace(self.session,scope=replace(self.f.scope,environment='A0_REVIEW_ONLY'))
            self.denied(self.get())
        def test_non_demo_principal(self):
            self.session=replace(self.session,principal='untrusted-reader'); self.denied(self.get())
        def test_unrecognized_credential(self):
            self.denied(self.get('unknown')); self.assertEqual(self.calls,1)
        def test_fresh_revision_server_owned(self):
            new_head=self.f.store.record(replace(self.f.s,previous=self.f.s.revision()),self.f.rev)
            self.denied(self.get())
            self.ctx=replace(self.ctx,expected_head=new_head)
            result=self.get(); self.assertEqual(result.status_code,200)
            self.assertEqual(result.json()['revision'],new_head)
            self.assertEqual(result.json()['previous_revision'],self.f.rev)
            self.assertEqual(result.json()['decision'],'HOLD')
        def test_byte_stability_and_no_identity_fields(self):
            before=self.f.path.read_bytes(); first=self.get(); second=self.get()
            self.assertEqual(first.status_code,200); self.assertEqual(first.json(),second.json())
            self.assertEqual(self.f.path.read_bytes(),before)
            self.assertEqual(self.calls,2)
            self.assertNotIn('demo-reader',first.text)
            for token in ('demo-l','demo-w','demo-x','agent_instance_id','principal_id','run_id'):
                self.assertNotIn(token,first.text)
            self.assertFalse(first.json()['dispatch_allowed'])
            self.assertIsNone(first.json()['runtime_binding'])
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BoundaryTests))
    return 0 if result.wasSuccessful() and result.testsRun==6 and not result.skipped else 1


if __name__=='__main__': sys.exit(main())
