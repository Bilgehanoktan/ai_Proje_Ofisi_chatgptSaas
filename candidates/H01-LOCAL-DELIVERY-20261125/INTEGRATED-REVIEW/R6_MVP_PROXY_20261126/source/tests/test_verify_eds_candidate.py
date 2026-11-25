import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('verify_eds_candidate', Path(__file__).resolve().parents[1] / 'scripts/verify_eds_candidate.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestPreflight(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'a.txt').write_bytes(b'abc')
        self.row = {'path':'a.txt','size':3,'sha':hashlib.sha1(b'blob 3\0abc').hexdigest()}
        self.manifest = {'files':[self.row]}
    def test_exact(self):
        self.assertEqual(mod.verify(self.root,self.manifest)['status'],'PASS')
    def test_same_size_tamper(self):
        (self.root/'a.txt').write_bytes(b'abd')
        self.assertIn('HASH:a.txt',mod.verify(self.root,self.manifest)['errors'])
    def test_size(self):
        (self.root/'a.txt').write_bytes(b'ab')
        self.assertIn('SIZE:a.txt',mod.verify(self.root,self.manifest)['errors'])
    def test_missing(self):
        (self.root/'a.txt').unlink()
        self.assertIn('MISSING:a.txt',mod.verify(self.root,self.manifest)['errors'])
    def test_extra(self):
        (self.root/'extra.txt').touch()
        self.assertIn('EXTRA:extra.txt',mod.verify(self.root,self.manifest)['errors'])
    def test_symlink(self):
        (self.root/'link').symlink_to(self.root/'a.txt')
        self.assertIn('SYMLINK:link',mod.verify(self.root,self.manifest)['errors'])
    def test_traversal(self):
        for p in ('../a.txt','/a.txt','x/../a.txt','x\\a.txt','C:a.txt','x//a.txt'):
            with self.assertRaises(ValueError): mod.verify(self.root,{'files':[{**self.row,'path':p}]})
    def test_duplicate(self):
        with self.assertRaises(ValueError): mod.verify(self.root,{'files':[self.row,self.row]})
    def test_case_collision(self):
        with self.assertRaises(ValueError): mod.verify(self.root,{'files':[self.row,{**self.row,'path':'A.txt'}]})
    def test_empty(self):
        with self.assertRaises(ValueError): mod.verify(self.root,{'files':[]})
    def test_invalid_hash(self):
        with self.assertRaises(ValueError): mod.verify(self.root,{'files':[{**self.row,'sha':'bad'}]})
    def test_no_grant(self):
        self.assertEqual(mod.verify(self.root,self.manifest)['authority'],'NOT_GRANTED_BY_PREFLIGHT')

if __name__ == '__main__': unittest.main()
