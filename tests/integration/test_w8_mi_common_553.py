"""Only synthetic helper checks: original 553 W8 is NOT executed."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

BRIDGE = Path(__file__).with_name("w8_mi_common_553.py")
spec = importlib.util.spec_from_file_location("mi01_w8_553_review", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class AdapterIntegrityTests(unittest.TestCase):
    def test_manifest_pin_is_exact_new_candidate(self):
        self.assertEqual(bridge.CANDIDATE_MANIFEST_BLOB,
                         "27b4eb5816265d4e6e6d2458acb6220db7dd0c76")
        self.assertNotEqual(bridge.CANDIDATE_MANIFEST_BLOB, bridge.PARENT_MANIFEST_BLOB)

    def test_refuses_missing_original_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "PARENT_FILE_HOLD"):
                bridge.load_pinned_parent(Path(tmp)/"missing.py")

    def test_refuses_modified_original_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"w8_mi_common_02.py"
            path.write_text("MANIFEST = 'bad'\n")
            with self.assertRaisesRegex(ValueError, "PARENT_PIN_HOLD"):
                bridge.load_pinned_parent(path)

    def test_refuses_symlink_original_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/"target.py"
            target.write_text("MANIFEST = 'bad'\n")
            link = Path(tmp)/"w8_mi_common_02.py"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("symlink unavailable on test environment")
            with self.assertRaisesRegex(ValueError, "PARENT_FILE_HOLD"):
                bridge.load_pinned_parent(link)

    def test_new_manifest_fails_closed(self):
        class FakeOriginal:
            MANIFEST = bridge.PARENT_MANIFEST_BLOB
            def load_candidate(self):
                class FakeW8:
                    MANIFEST_BLOB = "wrong-539-source"
                return FakeW8()
        with patch.object(bridge, "load_pinned_parent", return_value=FakeOriginal()):
            with self.assertRaisesRegex(ValueError, "NEW_MANIFEST_HOLD"):
                bridge.load_candidate()

    def test_manifest_override_only(self):
        observed = []
        class FakeOriginal:
            MANIFEST = bridge.PARENT_MANIFEST_BLOB
            def load_candidate(self):
                observed.append(self.MANIFEST)
                class FakeW8:
                    MANIFEST_BLOB = bridge.CANDIDATE_MANIFEST_BLOB
                return FakeW8()
        with patch.object(bridge, "load_pinned_parent", return_value=FakeOriginal()):
            bridge.load_candidate()
        self.assertEqual(observed, [bridge.CANDIDATE_MANIFEST_BLOB])


if __name__ == "__main__":
    unittest.main()
