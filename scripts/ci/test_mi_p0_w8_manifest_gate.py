"""Isolated diagnostic tests: no repo/product code or W8 full chain invoked."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("gate", Path(__file__).with_name("mi_p0_w8_manifest_gate.py"))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def manifest(paths):
    return json.dumps({"files": {k: {"bytes": i+1, "sha256": f"{i:064x}"} for i, k in enumerate(paths)}}, sort_keys=True).encode()


def adapter(pin, prefix=""):
    return (prefix + f"MANIFEST = {pin!r}\ndef extend(w):\n    if w.MANIFEST_BLOB != MANIFEST:\n        raise ValueError('U3_MANIFEST_HOLD')\n    return w\n").encode()


def run(old, new, src):
    return g.assess(old, new, src, canonical_blob=g.git_blob(old), candidate_blob=g.git_blob(new), adapter_blob=g.git_blob(src))


class ManifestGateTests(unittest.TestCase):
    def setUp(self):
        self.old = manifest(["alpha.py", "beta.py"])
        self.new = manifest(["alpha.py", "beta.py", "gamma.py"])
        self.src = adapter(g.git_blob(self.old))

    def test_canonical_pin_match_only_not_acceptance(self):
        out = run(self.old, self.old, self.src)
        self.assertEqual(out["status"], "MANIFEST_PRECHECK_MATCH_ONLY")
        self.assertEqual(out["product_acceptance"], "HOLD")

    def test_candidate_added_path_fails_closed(self):
        out = run(self.old, self.new, self.src)
        self.assertEqual(out["gate"], "U3_MANIFEST_HOLD")
        self.assertEqual(out["added"], ["gamma.py"])

    def test_candidate_modified_hash_fails_closed(self):
        new = self.old.replace(b'"bytes": 1', b'"bytes": 3')
        out = run(self.old, new, self.src)
        self.assertEqual(out["changed"], ["alpha.py"])
        self.assertEqual(out["status"], "HOLD")

    def test_candidate_deleted_path_fails_closed(self):
        out = run(self.old, manifest(["alpha.py"]), self.src)
        self.assertEqual(out["removed"], ["beta.py"])

    def test_unreviewed_old_manifest_tamper_rejected(self):
        with self.assertRaisesRegex(g.GateHold, "INPUT_GIT_BLOB_HOLD"):
            g.assess(self.old+b' ', self.new, self.src, canonical_blob=g.git_blob(self.old), candidate_blob=g.git_blob(self.new), adapter_blob=g.git_blob(self.src))

    def test_unreviewed_w8_adapter_tamper_rejected(self):
        with self.assertRaisesRegex(g.GateHold, "INPUT_GIT_BLOB_HOLD"):
            g.assess(self.old, self.new, self.src+b' ', canonical_blob=g.git_blob(self.old), candidate_blob=g.git_blob(self.new), adapter_blob=g.git_blob(self.src))

    def test_w8_missing_guard_fails(self):
        bad = (f"MANIFEST = {g.git_blob(self.old)!r}\ndef extend(w):\n    return w\n").encode()
        with self.assertRaisesRegex(g.GateHold, "W8_GUARD_ORDER_HOLD"):
            run(self.old, self.new, bad)

    def test_w8_guard_after_side_effect_fails(self):
        bad = adapter(g.git_blob(self.old)).replace(b'def extend(w):\n', b'def extend(w):\n    print("bad")\n')
        with self.assertRaisesRegex(g.GateHold, "W8_GUARD_ORDER_HOLD"):
            run(self.old, self.new, bad)

    def test_w8_inverted_guard_fails(self):
        bad = adapter(g.git_blob(self.old)).replace(b' != MANIFEST', b' == MANIFEST')
        with self.assertRaisesRegex(g.GateHold, "W8_GUARD_CONDITION_HOLD"):
            run(self.old, self.new, bad)

    def test_w8_wrong_exception_fails(self):
        bad = adapter(g.git_blob(self.old)).replace(b'U3_MANIFEST_HOLD', b'bad')
        with self.assertRaisesRegex(g.GateHold, "W8_FAIL_CLOSED_HOLD"):
            run(self.old, self.new, bad)

    def test_invalid_manifest_schema(self):
        invalid = b'{"files": []}'
        with self.assertRaisesRegex(g.GateHold, "MANIFEST_FILES_HOLD"):
            run(invalid, self.new, self.src)

    def test_duplicate_manifest_key(self):
        invalid = b'{"files":{"same.py":{"bytes":1,"sha256":"'+b'0'*64+b'"},"same.py":{"bytes":1,"sha256":"'+b'0'*64+b'"}}}'
        with self.assertRaisesRegex(g.GateHold, "DUPLICATE_JSON_KEY_HOLD"):
            run(invalid, self.new, self.src)

    def test_invalid_manifest_path(self):
        invalid = manifest(["../escape.py"])
        with self.assertRaisesRegex(g.GateHold, "INVALID_MANIFEST_PATH_HOLD"):
            run(invalid, self.new, self.src)

    def test_w8_pin_different_from_base_fails(self):
        src = adapter(g.git_blob(self.new))
        out = run(self.old, self.new, src)
        self.assertEqual(out["gate"], "W8_BASE_PIN_MISMATCH_HOLD")

    def test_fail_closed_on_invalid_utf8(self):
        with self.assertRaisesRegex(g.GateHold, "INVALID_MANIFEST_HOLD"):
            run(b'\xff', self.new, self.src)

    def test_manifest_byte_count_is_not_acceptance(self):
        out = run(self.old, self.new, self.src)
        self.assertEqual(out["original_w8_build"], "NOT_RUN")
        self.assertEqual(out["independent_security_acceptance"], "HOLD")


if __name__ == "__main__":
    unittest.main()
