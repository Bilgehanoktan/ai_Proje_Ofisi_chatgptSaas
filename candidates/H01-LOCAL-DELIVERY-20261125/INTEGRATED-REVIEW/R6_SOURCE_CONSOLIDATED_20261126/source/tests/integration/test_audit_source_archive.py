import hashlib
import json
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
from unittest import TestCase
import zipfile
from audit_source_archive import audit, blob


class ArchiveAuditTests(TestCase):
    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)/'test.zip'
        self.data = b'example only\n'
        self.raw = json.dumps({'files':{'a.txt':{'bytes':len(self.data),'sha256':hashlib.sha256(self.data).hexdigest()}}}).encode()
        self.pin = blob(self.raw)

    def make(self, entries, prefix='root/product/'):
        with zipfile.ZipFile(self.path, 'w') as z:
            z.writestr(prefix+'SOURCE_MANIFEST.json', self.raw)
            for name, data in entries:
                z.writestr(name, data)

    def check(self):
        return audit(self.path, self.pin, 1)

    def test_exact_root(self):
        self.make([('root/product/a.txt',self.data)])
        self.assertEqual(self.check()['status'],'SOURCE_MATCH_NOT_ACCEPTANCE')

    def test_exact_unprefixed(self):
        self.make([('product/a.txt',self.data)],'product/')
        self.assertEqual(self.check()['exact'],1)

    def test_wrong_manifest(self):
        self.make([('root/product/a.txt',self.data)])
        with self.assertRaisesRegex(ValueError,'MANIFEST_BLOB_MISMATCH'):audit(self.path,'0'*40,1)

    def test_missing_and_extra(self):
        self.make([('root/product/b.txt',self.data)])
        r=self.check();self.assertEqual((r['status'],r['missing'],r['extra']),('HOLD',['a.txt'],['b.txt']))

    def test_same_size_tamper(self):
        self.make([('root/product/a.txt',b'x'*len(self.data))])
        self.assertEqual(self.check()['mismatch'],['a.txt'])

    def test_case_alias(self):
        self.make([('root/product/a.txt',self.data),('root/product/A.txt',self.data)])
        with self.assertRaisesRegex(ValueError,'CASE_ALIAS'):self.check()

    def test_traversal(self):
        self.make([('root/product/../a.txt',self.data)])
        with self.assertRaisesRegex(ValueError,'UNSAFE_PATH'):self.check()

    def test_symlink(self):
        info=zipfile.ZipInfo('root/product/a.txt');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16
        self.make([(info,self.data)])
        with self.assertRaisesRegex(ValueError,'NONREGULAR'):self.check()

    def test_partial_package(self):
        with zipfile.ZipFile(self.path,'w') as z:z.writestr('PACKAGE_MANIFEST.json',self.raw)
        with self.assertRaisesRegex(ValueError,'FULL_PRODUCT_MANIFEST_MISSING'):self.check()
