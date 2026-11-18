"""Offline recovery mechanics only, not the 50 original product tests."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import shutil
import recover_and_run as r

ROOT = Path(__file__).resolve().parents[2]


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def copy_delta(self):
        d = self.root/'delta'
        for relative in ['product/'+k for k in r.DELTA]+[r.RUNNER]:
            dst = d/relative
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,dst)
        return d

    def test_exact_local_delta(self):
        records,runner = r.verify_delta(ROOT)
        self.assertEqual(set(records),set(r.DELTA))
        self.assertEqual(r.blob(runner),r.RUNNER_BLOB)

    def test_changed_product_source_rejected(self):
        d = self.copy_delta()
        (d/'product'/next(iter(r.DELTA))).write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError,'DELTA_PIN_HOLD'):
            r.verify_delta(d)

    def test_changed_original_runner_rejected(self):
        d = self.copy_delta()
        (d/r.RUNNER).write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError,'RUNNER_PIN_HOLD'):
            r.verify_delta(d)

    def test_missing_base_before_staging(self):
        stage = self.root/'stage'; stage.mkdir()
        with self.assertRaisesRegex(ValueError,'SOURCE_PATH_HOLD'):
            r.stage_exact(self.root/'missing',ROOT,stage)
        self.assertEqual(list(stage.iterdir()),[])

    def test_wrong_manifest_rejected(self):
        with self.assertRaisesRegex(ValueError,'BASE_MANIFEST_HOLD'):
            r.rebuild_manifest(b'{}')

    def test_evidence_inside_base_rejected(self):
        with self.assertRaisesRegex(ValueError,'EVIDENCE_PATH_HOLD'):
            r.main(['--base',str(self.root),'--delta',str(ROOT),'--out',str(self.root/'out')])
        self.assertFalse((self.root/'out').exists())

    def test_blocked_run_records_no_product_tests(self):
        out = self.root/'out'
        with patch.object(r,'version',return_value='46.0.4'):
            self.assertEqual(r.main(['--base',str(self.root/'missing'),'--delta',str(ROOT),'--out',str(out)]),2)
        report = json.loads((out/'report.json').read_text())
        self.assertEqual((report['status'],report['tests'],report['exit_code']),('BLOCKED','NOT_RUN',2))
        self.assertFalse((out/'regression.log').exists())
        self.assertEqual((out/'exit_code.txt').read_text(),'2\n')

    def test_reconstructed_manifest_must_match_target_pin(self):
        # Artificial metadata only; no product bytes or real manifest verification here.
        files = {r.BACKEND+f'fixture-{i}.py':{'bytes':0,'sha256':hashlib.sha256(b'').hexdigest()} for i in range(236)}
        files.update({f'fixture/{i}.json':{'bytes':0,'sha256':hashlib.sha256(b'').hexdigest()} for i in range(155)})
        files[r.BACKEND+'app/core/transaction/intent_authority.py']={'bytes':7835,'sha256':'1f9e3c675062601be45e933be9ce21e9cb11fa88f8abf545df54336afab7a392'}
        m={'version':'fixture','doc_revision':'0225','status':'fixture','parent_candidate_sha256':None,
           'parent_git_commit':'fixture','source_git_commit':None,'files':files,
           'parent_source_manifest_blob':'fixture','source_git_commit_note':'fixture'}
        raw=(json.dumps(m,indent=2)+'\n').encode()
        with patch.object(r,'BASE_MANIFEST',r.blob(raw)):
            with self.assertRaisesRegex(ValueError,'TARGET_MANIFEST_HOLD'):
                r.rebuild_manifest(raw)


if __name__=='__main__':
    unittest.main(verbosity=2)
