"""Pure offline, stdlib guard checks for the Windows PC launcher; not product tests."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import aios_pc_runner as target


class PCToolSafetyGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_git_blob_empty_bytes(self):
        self.assertEqual(target.blob(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")

    def test_sha256_pin_accepts_exact_data(self):
        p=self.root/"x.py"
        p.write_bytes(b"sample")
        target.must_equal(p,"af2bdbe1aa9b6ec1e2ade1d694f41fc71a831d0268e9891562113d8a62add1bf","sha256")

    def test_sha256_pin_rejects_wrong_source(self):
        p=self.root/"x.py"
        p.write_bytes(b"different")
        with self.assertRaisesRegex(RuntimeError,"SOURCE_PIN_HOLD"):
            target.must_equal(p,"a"*64,"sha256")

    def test_symlink_never_accepted(self):
        f=self.root/"target"; f.write_bytes(b"")
        link=self.root/"link"
        try: link.symlink_to(f)
        except OSError: self.skipTest("symlink privilege unavailable")
        with self.assertRaisesRegex(RuntimeError,"MISSING_OR_LINK_HOLD"):
            target.must_equal(link,target.blob(f.read_bytes()))

    def test_missing_source_fail_closed(self):
        with self.assertRaisesRegex(RuntimeError,"MISSING_OR_LINK_HOLD"):
            target.must_equal(self.root/"missing.py","0"*40)

    def test_initial_statuses_are_hold_and_not_run(self):
        s=target.Session(self.root/"s")
        self.assertEqual(s.status["W8_C05"],"HOLD_OWNER_REVIEW")
        self.assertEqual(s.status["INDEPENDENT_SECURITY_IV"],"HOLD")
        self.assertEqual(s.status["W8_C08"],"NOT_RUN")
        self.assertEqual(s.status["G7_CURRENT_ORG_7"],"NOT_RUN")

    def test_checkout_rejects_existing_untrusted_directory(self):
        s=target.Session(self.root/"s")
        s.g7_dir.mkdir()
        with self.assertRaisesRegex(RuntimeError,"NON_GIT_EXISTING_DIR_HOLD"):
            s.checkout(s.g7_dir,target.G7,"G7")

    def test_w8full_does_not_install_without_owner_review(self):
        s=target.Session(self.root/"s")
        with patch.object(s,"w8_audit",return_value=self.root/"owner_w8.py"),patch.object(s,"run") as execute:
            with self.assertRaisesRegex(RuntimeError,"C05_OWNER_APPROVED_REVIEW_SHA256_REQUIRED"):
                s.w8_full("",self.root/"chromium.exe")
            execute.assert_not_called()

    def test_w8full_does_not_install_with_wrong_review_hash(self):
        s=target.Session(self.root/"s")
        (s.w8_stage/"locks").mkdir(parents=True)
        (s.w8_stage/"locks/REVIEW.json").write_text("{}")
        with patch.object(s,"w8_audit",return_value=self.root/"owner_w8.py"),patch.object(s,"run") as execute:
            with self.assertRaisesRegex(RuntimeError,"SOURCE_PIN_HOLD"):
                s.w8_full("a"*64,self.root/"chromium.exe")
            execute.assert_not_called()

    def test_pg_probe_is_readonly_when_binary_absent(self):
        s=target.Session(self.root/"s")
        with patch.object(target.shutil,"which",return_value=None),patch.object(s,"run") as execute:
            s.pg_probe()
            execute.assert_not_called()
            self.assertIn("HOLD",s.status["POSTGRES_LOOPBACK"])
            self.assertEqual(s.status["POSTGRES_PROTECTED_RLS_RESTORE"],"HOLD")

    def test_no_live_pg_or_issuer_gate_upgrades_on_report(self):
        s=target.Session(self.root/"s")
        p=s.save()
        j=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(j["AUTHORITY_ROOT_SINK"],"HOLD")
        self.assertEqual(j["INDEPENDENT_SECURITY_IV"],"HOLD")
        self.assertEqual(j["MVP_ACCEPTANCE"],"HOLD_0_OF_11")

    def test_run_failure_stays_failure_and_writes_raw_logs(self):
        s=target.Session(self.root/"s")
        with self.assertRaisesRegex(RuntimeError,"RUN_FAILED"):
            s.run("FAIL",[target.sys.executable,"-c","import sys;sys.exit(3)"])
        self.assertEqual(s.status["logs"][0]["exit"],3)
        self.assertTrue((s.logs/"FAIL.stderr.log").is_file())

if __name__=="__main__":
    unittest.main(verbosity=2)
