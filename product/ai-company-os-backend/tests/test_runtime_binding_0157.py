"""Unexecuted R3/0156 bridge oracles."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from app.core.runtime_plan_binding import inspect_plan_binding

class BindingTests(unittest.TestCase):
    def setUp(self):
        self.p=json.loads((Path(__file__).resolve().parents[1]/'fixtures/core.plan.projection.json').read_text(encoding='utf-8'))
    def test_reference(self):
        r=inspect_plan_binding(self.p,'research','research')
        self.assertEqual(r['reason'],'CANONICAL_D0_PLAN_ONLY_INSTANCE_AND_ADMISSION_REQUIRED')
        self.assertFalse(r['binding_created'])
    def test_label_tamper_rejected(self):
        p=copy.deepcopy(self.p);p['tasks'][0]['label'] += ' changed'
        r=inspect_plan_binding(p,'research','research')
        self.assertEqual(r['reason'],'PLAN_DIGEST_MISMATCH')
        self.assertFalse(r['binding_created'])
    def test_forged_rehashed_waves(self):
        p=copy.deepcopy(self.p);p['waves']=[['release']]
        body={k:v for k,v in p.items() if k not in ('digest','revision')}
        p['digest']=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
        p['revision']='sha256:'+p['digest']
        self.assertEqual(inspect_plan_binding(p,'research','research')['reason'],'CANONICAL_PLAN_MISMATCH')
