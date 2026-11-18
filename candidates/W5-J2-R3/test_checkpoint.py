import json
import shutil
import tempfile
import unittest
from pathlib import Path
from checkpoint import verify_plan,verify_parent_manifests,local_checkpoint,PLAN_IDS,BLOCKERS
ROOT=Path(__file__).resolve().parent.parent
PLAN=ROOT/'W5-J2-R2'/'PG_ACCEPTANCE_PLAN.json'
class CheckpointTests(unittest.TestCase):
    def test_exact_inventory(self):self.assertEqual(tuple(c['id'] for c in verify_plan(PLAN.read_bytes())),PLAN_IDS)
    def test_tampered_plan(self):
        with self.assertRaises(ValueError):verify_plan(PLAN.read_bytes()+b' ')
    def test_pass_forgery(self):
        raw=PLAN.read_bytes().replace(b'NOT_RUN',b'PASS')
        with self.assertRaises(ValueError):verify_plan(raw)
    def test_no_parent(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaises(OSError):verify_parent_manifests(p)
    def test_manifest_repin_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'W5-J2-R1';shutil.copytree(ROOT/'W5-J2-R1',target)
            manifest=target/'SOURCE_MANIFEST.json';manifest.write_bytes(manifest.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'PARENT_MANIFEST_PIN_HOLD'):verify_parent_manifests(d)
    def test_exact_parent_manifest(self):self.assertEqual(verify_parent_manifests(ROOT),19)
    def test_no_gate_promotion(self):
        r=local_checkpoint(ROOT);self.assertEqual((r['status'],r['decision'],r['pg_executed'],r['pg_passed']),('BLOCKED','HOLD',0,0))
        self.assertEqual(tuple(r['blockers']),BLOCKERS)
        self.assertTrue(all(not r[k] for k in ('commit_allowed','provider_call_allowed','spend_allowed','retry_allowed','settlement_allowed','independent_accepted')))
    def test_all_22_not_run(self):
        r=local_checkpoint(ROOT);self.assertEqual(len(r['pg_cases']),22);self.assertTrue(all(c['status']=='NOT_RUN' for c in r['pg_cases']))
