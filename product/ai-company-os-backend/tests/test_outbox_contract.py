import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from jsonschema import Draft202012Validator
from app.core.development_review.outbox_claim_sample import OutboxReviewSample, read_projection

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT/'contracts/source/outbox.review.projection.schema.json'
CASES = ROOT/'tests/outbox_projection_cases.json'


class OutboxContractTests(unittest.TestCase):
    def setUp(self):
        schema=json.loads(SCHEMA.read_text())
        Draft202012Validator.check_schema(schema)
        self.validator=Draft202012Validator(schema)

    def test_shared_schema_bytes(self):
        self.assertEqual(SCHEMA.read_bytes(),(ROOT.parent/'ai-company-os-frontend/contracts/generated/outbox.review.projection.schema.json').read_bytes())

    def test_shared_vectors(self):
        for case in json.loads(CASES.read_text()):
            with self.subTest(case=case['name']): self.assertEqual(self.validator.is_valid(case['body']),case['valid'])

    def test_actual_projection_and_overflow(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'case.review.atomic.d0.sqlite'
            s=OutboxReviewSample(p); s.create(); s.renew('demo-owner',None,1,10); s.observe('demo-command','demo-owner',1,2,0)
            self.validator.validate(read_projection(p))
            s.claim_review('demo-command','demo-reviewer',3,5)
            self.validator.validate(read_projection(p))
            s.mark_unknown('demo-command','demo-reviewer',1,4)
            self.validator.validate(read_projection(p))
            s.record_readback('demo-command',1,'a'*64)
            self.validator.validate(read_projection(p))
            with closing(sqlite3.connect(p)) as db, db:
                db.execute('UPDATE local_review SET generation=?',(9007199254740991,))
            self.validator.validate(read_projection(p))
            with closing(sqlite3.connect(p)) as db, db:
                db.execute('UPDATE local_review SET generation=?',(9007199254740992,))
            with self.assertRaisesRegex(ValueError,'SAMPLE_PROJECTION_INVALID'): read_projection(p)
