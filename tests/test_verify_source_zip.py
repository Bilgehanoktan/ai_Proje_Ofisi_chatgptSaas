import hashlib,json,stat,tempfile,unittest,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_source_zip import verify_zip,git_blob
class Preflight(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'sample.zip';self.content=b'fixture only'; self.raw=json.dumps({'files':{'a.txt':{'bytes':len(self.content),'sha256':hashlib.sha256(self.content).hexdigest()}}}).encode();self.pin=git_blob(self.raw)
    def make(self, content=None, extra=None, root='repo/'):
        with zipfile.ZipFile(self.path,'w') as z:
            z.writestr(root+'product/SOURCE_MANIFEST.json',self.raw);z.writestr(root+'product/a.txt',self.content if content is None else content)
            if extra: z.writestr(*extra)
    def test_match(self): self.make();self.assertEqual(verify_zip(self.path,self.pin,1)['source_integrity'],'MATCH')
    def test_flat(self): self.make(root='');self.assertEqual(verify_zip(self.path,self.pin,1)['product_files'],2)
    def test_pin(self):
        self.make();self.assertRaisesRegex(ValueError,'PIN_MISMATCH',verify_zip,self.path,'0'*40,1)
    def test_changed(self):
        self.make(content=b'fixture fail');self.assertRaisesRegex(ValueError,'HASH_MISMATCH',verify_zip,self.path,self.pin,1)
    def test_extra(self):
        self.make(extra=('repo/product/extra.txt',b'x'));self.assertRaisesRegex(ValueError,'PATH_SET',verify_zip,self.path,self.pin,1)
    def test_traversal(self):
        self.make(extra=('repo/../evil',b'x'));self.assertRaisesRegex(ValueError,'UNSAFE_PATH',verify_zip,self.path,self.pin,1)
    def test_collision(self):
        self.make(extra=('repo/product/A.txt',b'x'));self.assertRaisesRegex(ValueError,'COLLISION',verify_zip,self.path,self.pin,1)
    def test_symlink(self):
        i=zipfile.ZipInfo('repo/link');i.create_system=3;i.external_attr=(stat.S_IFLNK|0o777)<<16
        self.make(extra=(i,b'a.txt'));self.assertRaisesRegex(ValueError,'UNSAFE_ENTRY',verify_zip,self.path,self.pin,1)
    def test_windows_reserved(self):
        self.make(extra=('repo/CON.txt',b'x'));self.assertRaisesRegex(ValueError,'UNSAFE_PATH',verify_zip,self.path,self.pin,1)
    def test_manifest_count(self):
        self.make();self.assertRaisesRegex(ValueError,'COUNT_MISMATCH',verify_zip,self.path,self.pin,2)
if __name__=='__main__':unittest.main()
