from contextlib import closing
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from app.core.development_review.admission_sample import AdmissionSample, OWNER
from app.core.development_review.sandbox_store import Workbench
from app.core.development_review.task_budget_snapshot import new_pair_id, read_task_budget_snapshot
from app.api.task_budget_projection import router


class RealWriterPairTests(TestCase):
    def test_pair_roundtrip_and_schema(self):
        root=Path(__file__).resolve().parents[1]
        plan=json.loads((root/'fixtures/core.preview.json').read_text(encoding='utf-8'))['plan']
        source=root/'contracts/source/task.budget.snapshot.schema.json'
        self.assertEqual(source.read_bytes(),(root.parent/'ai-company-os-frontend/contracts/generated/task.budget.snapshot.schema.json').read_bytes())
        schema=json.loads(source.read_text()); Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema)
        with TemporaryDirectory() as d:
            w=Path(d)/'test.workbench.d0.sqlite'; a=Path(d)/'test.admission.d0.sqlite'
            pair=new_pair_id(); wb=Workbench(w,plan); admission=AdmissionSample(a)
            wb.create(pair_id=pair); admission.create(pair_id=pair)
            validator.validate(read_task_budget_snapshot(w,a))
            admission.apply(OWNER,'ADMIT',0)
            for tick, task in enumerate(('plan','draft','research','merge','qa'),1):
                fence=wb.lease(task,'demo-holder',tick,10)
                wb.observe(task,'demo-holder',fence,tick,'demo-command-'+task)
                validator.validate(read_task_budget_snapshot(w,a))
            admission.apply(OWNER,'UNKNOWN',1)
            hashes=[sha256(p.read_bytes()).hexdigest() for p in (w,a)]
            x=read_task_budget_snapshot(w,a); validator.validate(x)
            self.assertEqual((x['pair_id'],x['research_event_seq'],x['budget']['phase']),(pair,3,'UNKNOWN_HOLD'))
            self.assertEqual(x['budget']['sample_reserved_minor'],100)
            self.assertFalse(validator.is_valid({**x,'admission_version':1}))
            app=FastAPI(); app.include_router(router)
            with patch.dict(os.environ,{'AICOS_D0_WORKBENCH_DB':str(w),'AICOS_D0_ADMISSION_DB':str(a)}):
                client=TestClient(app); url='/demo/v1/task-budget/sample-projection'
                self.assertEqual(client.get(url).json(),x)
                self.assertEqual(hashes,[sha256(p.read_bytes()).hexdigest() for p in (w,a)])
                with closing(sqlite3.connect(a)) as db,db: db.execute('UPDATE sample_pair SET pair_id=?',(new_pair_id(),))
                self.assertEqual(client.get(url).status_code,503)
