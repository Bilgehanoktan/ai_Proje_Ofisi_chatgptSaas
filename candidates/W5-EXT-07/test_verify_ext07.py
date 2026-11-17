import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import verify_ext07 as v

class PreflightTests(unittest.TestCase):
    def test_blob(self):
        self.assertEqual(v.blob(b''),'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')
    def test_sha(self):
        self.assertEqual(v.sha(b''),'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
    def test_valid_file(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'a').write_bytes(b'ok'); self.assertEqual(v.read(root,'a'),b'ok')
    def test_path_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ('../escape','/etc/passwd','a\\b','./a','a//b',''):
                with self.subTest(name=name),self.assertRaises(ValueError): v.safe_file(Path(d),name)
    def test_missing(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaisesRegex(ValueError,'MISSING'):
            v.safe_file(Path(d),'absent')
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'a').symlink_to('/etc/passwd')
            with self.assertRaisesRegex(ValueError,'SYMLINK'):v.safe_file(root,'a')
    def test_wrong_head(self):
        with tempfile.TemporaryDirectory() as d,patch.object(v.subprocess,'check_output',side_effect=['bad','']):
            r=v.verify(d);self.assertIn('BASE_MISMATCH',r['errors']);self.assertFalse(r['execution_allowed']);self.assertEqual(r['status'],'HOLD')
    def test_dirty_checkout(self):
        with tempfile.TemporaryDirectory() as d,patch.object(v.subprocess,'check_output',side_effect=[v.BASE,' M product/file']):
            r=v.verify(d);self.assertIn('DIRTY_CHECKOUT',r['errors']);self.assertEqual(r['status'],'HOLD');self.assertEqual(r['independent_acceptance'],'HOLD')

if __name__=='__main__':unittest.main()
