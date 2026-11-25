from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import os
import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.development_review.admission_sample import AdmissionSample, OWNER, read_admission
from app.api.admission_projection import router


class AdmissionSampleTests(TestCase):
    def setUp(self):
        tmp=TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/'test.admission.d0.sqlite'
        self.s=AdmissionSample(self.path); self.s.create()
        app=FastAPI(); app.include_router(router); self.client=TestClient(app)

    def admit(self): return self.s.apply(OWNER,'ADMIT',0)
    def read(self): return read_admission(self.path)
    def get(self):
        with patch.dict(os.environ,{'AICOS_D0_ADMISSION_DB':str(self.path)}):
            return self.client.get('/demo/v1/admission/sample-projection')

    def test_admission_and_reopen(self):
        self.assertEqual(self.admit(),'RESERVED')
        self.assertEqual(AdmissionSample(self.path).apply(OWNER,'ADMIT',0),'DUPLICATE_IGNORED')
        x=self.read(); self.assertEqual((x['version'],x['sample_reserved_minor'],x['sample_remaining_minor']),(1,100,900))
        for k in ('dispatch_allowed','spend_allowed','release_ready','authoritative'): self.assertIs(x[k],False)
        self.assertIsNone(x['actual_cost_minor'])

    def test_known_sample(self):
        self.admit(); self.assertEqual(self.s.apply(OWNER,'KNOWN_SAMPLE',1),'SETTLED_SAMPLE')
        x=self.read(); self.assertEqual((x['sample_reserved_minor'],x['sample_observed_minor'],x['sample_remaining_minor']),(0,60,940))

    def test_unknown_retains_reservation(self):
        self.admit(); self.s.apply(OWNER,'UNKNOWN',1)
        self.assertEqual(self.read()['sample_reserved_minor'],100)
        self.assertEqual(self.read()['phase'],'UNKNOWN_HOLD')
        with self.assertRaises(ValueError): self.s.apply(OWNER,'KNOWN_SAMPLE',1)

    def test_scope_and_cas(self):
        for owner in (('other',*OWNER[1:]),(OWNER[0],'other',OWNER[2]),(*OWNER[:2],'other')):
            with self.assertRaises(ValueError): self.s.apply(owner,'ADMIT',0)
        with self.assertRaises(ValueError): self.s.apply(OWNER,'KNOWN_SAMPLE',1)
        with self.assertRaises(ValueError): self.s.apply(OWNER,'ADMIT',True)
        self.assertEqual(self.read()['phase'],'PENDING')

    def test_concurrent_admission(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(lambda _:self.admit(),range(2))),['RESERVED','DUPLICATE_IGNORED'])

    def test_concurrent_settlement(self):
        self.admit()
        def attempt(kind):
            try: return self.s.apply(OWNER,kind,1)
            except ValueError: return 'HOLD'
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(attempt,['KNOWN_SAMPLE','UNKNOWN']))
        self.assertIn('HOLD',results); self.assertIn(self.read()['phase'],results)

    def test_rollback(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER fail BEFORE INSERT ON sample_outbox BEGIN SELECT RAISE(ABORT,'sample'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.admit()
        self.assertEqual(self.read()['phase'],'PENDING')

    def test_settlement_rollback(self):
        self.admit()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER fail BEFORE INSERT ON sample_outbox BEGIN SELECT RAISE(ABORT,'sample'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.s.apply(OWNER,'KNOWN_SAMPLE',1)
        self.assertEqual(self.read()['phase'],'RESERVED')

    def test_no_overwrite(self):
        with self.assertRaises(FileExistsError): self.s.create()

    def test_scope_tamper(self):
        with closing(sqlite3.connect(self.path)) as db, db: db.execute('DELETE FROM membership')
        self.assertEqual(self.get().status_code,503)
        with self.assertRaises(ValueError): self.admit()

    def test_binding_tamper(self):
        self.admit()
        with closing(sqlite3.connect(self.path)) as db, db: db.execute('DELETE FROM sample_audit')
        self.assertEqual(self.get().status_code,503)

    def test_http_readonly(self):
        self.admit(); before=sha256(self.path.read_bytes()).hexdigest(); r=self.get()
        self.assertEqual(r.status_code,200); self.assertEqual(r.headers['cache-control'],'no-store')
        self.assertEqual(r.json(),self.read()); self.assertEqual(sha256(self.path.read_bytes()).hexdigest(),before)
        self.assertEqual(self.client.post('/demo/v1/admission/sample-projection').status_code,405)

    def test_http_missing(self):
        self.path.unlink(); self.assertEqual(self.get().status_code,503); self.assertFalse(self.path.exists())
        with patch.dict(os.environ,{'AICOS_D0_ADMISSION_DB':''}):
            self.assertEqual(self.client.get('/demo/v1/admission/sample-projection?path='+str(self.path)).status_code,503)

    def test_schema_and_actual_states(self):
        import json
        from jsonschema import Draft202012Validator
        root=Path(__file__).resolve().parents[1]
        source=root/'contracts/source/admission.sample.projection.schema.json'
        self.assertEqual(source.read_bytes(),(root.parent/'ai-company-os-frontend/contracts/generated/admission.sample.projection.schema.json').read_bytes())
        schema=json.loads(source.read_text()); Draft202012Validator.check_schema(schema)
        v=Draft202012Validator(schema)
        v.validate(self.read()); self.admit(); v.validate(self.read())
        self.s.apply(OWNER,'UNKNOWN',1); x=self.read(); v.validate(x)
        self.assertFalse(v.is_valid({**x,'sample_reserved_minor':0}))
        self.assertFalse(v.is_valid({**x,'spend_allowed':True}))
        self.assertFalse(v.is_valid({**x,'actual_cost_minor':60}))
