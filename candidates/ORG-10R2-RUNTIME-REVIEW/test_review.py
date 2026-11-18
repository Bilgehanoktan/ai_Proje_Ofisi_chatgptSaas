import unittest, tempfile
from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
from review_runtime_archives import archive_map,compare,sha_file,unique,find_file

class Tests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.z=self.root/'x.zip'
    def tearDown(self): self.tmp.cleanup()
    def make(self,rows):
        with ZipFile(self.z,'w') as z:
            for k,v in rows: z.writestr(k,v)
        return sha_file(self.z)
    def test_pg(self):
        h=self.make([('pgsql/bin/postgres.exe',b'a'),('pgsql/share/a',b'b'),('pgsql/include/c',b'c')]); self.assertEqual(archive_map(self.z,h,'pg'),{'bin/postgres.exe':sha256(b'a').hexdigest(),'share/a':sha256(b'b').hexdigest()})
    def test_pin(self):
        self.make([('pgsql/bin/a',b'a')]); self.assertRaises(ValueError,archive_map,self.z,'0'*64,'pg')
    def test_badpath(self):
        h=self.make([('pgsql/../a',b'a')]); self.assertRaises(ValueError,archive_map,self.z,h,'pg')
    def test_collision(self):
        h=self.make([('pgsql/bin/a',b'a'),('pgsql/bin/A',b'b')]); self.assertRaises(ValueError,archive_map,self.z,h,'pg')
    def test_wheel(self):
        h=self.make([('psycopg/a.py',b'a')]); self.assertIn('Lib/site-packages/psycopg/a.py',archive_map(self.z,h,'wheel'))
    def test_metadata(self):
        self.assertEqual(compare({'x/a':'a','x.dist-info/RECORD':'b','x.dist-info/INSTALLER':'c'},{'x/a':'a','x.dist-info/RECORD':'z'},True)['status'],'MATCH')
    def test_mismatch(self):
        r=compare({'x':'a','y':'b'},{'x':'b','z':'c'}); self.assertEqual((r['status'],r['missing'],r['extra'],r['mismatch']),('HOLD',['z'],['y'],['x']))
    def test_unique(self): self.assertRaises(ValueError,unique,[('a',1),('a',2)])
    def test_find(self):
        h=self.make([('a',b'a')]); self.assertEqual(find_file([self.root],('x.zip',),h),self.z)
    def test_missing(self): self.assertRaises(ValueError,find_file,[self.root],('none',),'0'*64)

if __name__=='__main__': unittest.main(verbosity=2)
