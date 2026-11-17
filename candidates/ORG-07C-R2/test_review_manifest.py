import copy
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from review_manifest import review_delta,overlay

CANDIDATE=Path(os.environ['ORG07C_CANDIDATE'])

class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.delta=review_delta(CANDIDATE)
    def base(self):
        rows=dict(self.delta['base_rows'])
        rows.update({f'untouched/{i}':{'bytes':0,'sha256':'0'*64} for i in range(500)})
        return {'files':rows,'version':'fixture'}
    def test_exact_candidate(self):
        self.assertEqual(len(self.delta['changes']),7)
        self.assertEqual(sum(v['before'] is None for v in self.delta['changes'].values()),4)
    def test_preservation(self):
        base=self.base(); before=copy.deepcopy(base); result=overlay(base,self.delta)
        self.assertEqual(base,before); self.assertEqual(len(result['files']),508)
        self.assertEqual(result['status'],'D0_REVIEW_ONLY_NOT_APPLIED')
        self.assertIsNone(result['source_git_commit'])
        for k,v in base['files'].items():
            if k not in self.delta['changes']: self.assertEqual(v,result['files'][k])
    def test_old_row_drift(self):
        base=self.base(); key=next(iter(self.delta['base_rows']));base['files'][key]={'bytes':1,'sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'MANIFEST_ROW_HOLD'): overlay(base,self.delta)
    def test_new_path_collision(self):
        base=self.base(); key=next(k for k,v in self.delta['changes'].items() if v['before'] is None)
        base['files'].pop('untouched/0');base['files'][key]={'bytes':1,'sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'MANIFEST_COLLISION_HOLD'): overlay(base,self.delta)
    def test_count(self):
        base=self.base();base['files'].pop('untouched/0')
        with self.assertRaisesRegex(ValueError,'MANIFEST_COUNT_HOLD'): overlay(base,self.delta)
    def test_status(self):
        delta=copy.deepcopy(self.delta);delta['status']='ACCEPTED'
        with self.assertRaisesRegex(ValueError,'DELTA_HOLD'): overlay(self.base(),delta)
    def test_base_tamper(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'c';shutil.copytree(CANDIDATE,target)
            p=target/'base'/'projectionRead.ts';p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'BASE_PIN_HOLD'): review_delta(target)
    def test_scope_tamper(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'c';shutil.copytree(CANDIDATE,target)
            p=target/'PRODUCT_SCOPE.json';p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'SCOPE_PIN_HOLD'): review_delta(target)
    def test_staged_tamper(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'c';shutil.copytree(CANDIDATE,target)
            p=target/'staged'/'features/organization/organizationProxy.ts';p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'STAGED_PIN_HOLD'): review_delta(target)

if __name__=='__main__': unittest.main(verbosity=2)
