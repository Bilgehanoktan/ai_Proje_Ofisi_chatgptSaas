"""Original R3 SQLite + real ASGI candidate. Run from exact reviewed R3 checkout only."""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import hashlib
import sqlite3
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
R3 = ROOT/'candidates'/'ORG-05R3'
PINS = {
    'org_model.py':'cdb33238bf9eaf2a66f1d895ded165cc0065a605',
    'staffing.py':'e0b9078284922d281996869daa15a455572c1785',
    'operations.py':'d6b314a402399fa7e133bccf2e8bb3a39848fead',
    'office_bridge.py':'98b2436dab43cbadf546d8e9e662c12080b83fd2',
    'integration_guard.py':'2cde13e048e0907ef06c104fc5883fe4c1b08271',
    'persistence.py':'4124099a497f5bc7fd34756664c7e293055e949e',
    'durable_ops.py':'43ed448c02904ab44b3cf8665f4aeafb0a38f10a',
    'schema.sql':'32b7609b18e8a53420f17d23f4b53544e7f6f6ad',
    'operations.sql':'3443f6581eb3a8d3894aea0b620f2b8d6dba9b2a',
    'studio.schema.json':'eed9627913502ebb09222cf404f867ca305a6a44',
    'test_durable_ops.py':'8f220550373b69c008ce66a4e74c4d1c45952efc',
}

def main():
    for name, expected in PINS.items():
        raw = (R3/name).read_bytes()
        actual = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if actual != expected: raise RuntimeError('R3_SOURCE_PIN_HOLD')
    sys.path.insert(0,str(R3))
    from test_durable_ops import DurableTests
    from durable_ops import ReadSession
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from studio_router import build_router, ServerReadContext, ROUTE, DENIAL

    class OriginalTests(unittest.TestCase):
        def setUp(self):
            self.f = DurableTests(); self.addCleanup(self.f.doCleanups); self.f.setUp()
            self.session = ReadSession(self.f.scope,'demo-reader',100,'org.preview.read')
            self.ctx = ServerReadContext(self.f.path,self.f.rev,lambda _:self.session,lambda:99)
            app = FastAPI(); app.include_router(build_router(lambda:self.ctx,R3/'studio.schema.json'))
            self.client = TestClient(app); self.addCleanup(self.client.close)
        def get(self): return self.client.get(ROUTE,headers={'Authorization':'Bearer opaque'})
        def dump(self):
            with closing(sqlite3.connect(self.f.path)) as db: return tuple(db.iterdump())
        def denied(self):
            r=self.get(); self.assertEqual((r.status_code,r.json()),(403,DENIAL))
        def test_original_reader_no_mutation(self):
            before=self.dump(); r=self.get(); self.assertEqual(r.status_code,200)
            self.assertEqual(r.json(),self.f.store.studio_view(self.f.rev))
            self.assertEqual(before,self.dump())
        def test_expiry(self):
            self.session=replace(self.session,expires=99); self.denied()
        def test_scope(self):
            self.session=replace(self.session,scope=replace(self.f.scope,tenant='synthetic-other')); self.denied()
        def test_permission(self):
            self.session=replace(self.session,permission='write'); self.denied()
        def test_stale_head(self):
            self.f.store.record(replace(self.f.s,previous=self.f.s.revision()),self.f.rev); self.denied()
        def test_corrupt_revision_notice(self):
            with closing(sqlite3.connect(self.f.path)) as db,db:
                db.execute('DROP TRIGGER org_notice_update'); db.execute("UPDATE org_notice SET digest='bad'")
            self.denied()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OriginalTests))
    return 0 if result.wasSuccessful() and result.testsRun==6 and not result.skipped else 1

if __name__=='__main__': sys.exit(main())
