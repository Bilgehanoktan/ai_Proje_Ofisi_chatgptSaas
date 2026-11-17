import hashlib,json,tempfile,unittest,struct,zlib
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace
from w8_ext07r3 import lock_bytes,lock_command,browser_report,CASES,exact,blob,extend,MANIFEST

def tiny_png():
    def chunk(k,v):return struct.pack('>I',len(v))+k+v+struct.pack('>I',zlib.crc32(k+v)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\0\0\0'))+chunk(b'IEND',b'')

class Mechanics(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_lock_match(self):
        p=self.p/'lock';p.write_bytes(b'example');self.assertEqual(lock_bytes(p,hashlib.sha256(b'example').hexdigest()),b'example')
    def test_lock_mismatch(self):
        p=self.p/'lock';p.write_bytes(b'example');self.assertRaisesRegex(ValueError,'LOCK_HASH',lock_bytes,p)
    def test_missing_lock(self):self.assertRaisesRegex(ValueError,'LOCK_MISSING',lock_bytes,None)
    def test_lock_command(self):
        w=SimpleNamespace(npm=lambda:'npm',frontend=lambda stage:stage/'frontend');a=['npm','install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org']
        self.assertTrue(lock_command(w,a,self.p/'frontend',self.p));self.assertFalse(lock_command(w,a,self.p,self.p));self.assertFalse(lock_command(w,a+['--force'],self.p/'frontend',self.p))
    def test_blob(self):
        p=self.p/'f';p.write_bytes(b'abc');exact(p,blob(p));self.assertRaisesRegex(ValueError,'SOURCE_PIN',exact,p,'0'*40)
    def test_manifest_rejected(self):self.assertRaisesRegex(ValueError,'MANIFEST',extend,SimpleNamespace(MANIFEST_BLOB='bad'),None)
    def report(self):
        (self.p/'EXT07R3_BROWSER_REPORT.json').write_text(json.dumps({'status':'PASS','cases':CASES,'screenshots':3,'actual_browser':True,'independent_acceptance':'HOLD'}))
        for name in ['01-dark-detail.png','02-light.png','03-mobile.png']:(self.p/name).write_bytes(tiny_png())
    def test_report_fixture(self):self.report();browser_report(self.p)
    def test_report_missing(self):self.report();(self.p/'03-mobile.png').unlink();self.assertRaisesRegex(ValueError,'CAPTURE',browser_report,self.p)
    def test_report_corrupted_png(self):
        self.report();(self.p/'03-mobile.png').write_bytes(tiny_png()[:-1]);self.assertRaisesRegex(ValueError,'CAPTURE',browser_report,self.p)
    def test_report_forged(self):
        self.report();(self.p/'EXT07R3_BROWSER_REPORT.json').write_text('{"status":"PASS"}');self.assertRaisesRegex(ValueError,'REPORT',browser_report,self.p)

    def fake_parent(self,duplicate=False):
        w=SimpleNamespace(MANIFEST_BLOB=MANIFEST,npm=lambda:'npm',frontend=lambda stage:stage/'frontend',verify_aux=lambda root:{},reviewed=lambda stage,approval:None,test=lambda *args:None,smoke=lambda *args:None)
        ran=[]
        def run(args,cwd,env=None):ran.append(list(map(str,args)))
        w.run=run
        def prepare(repo,stage):
            w.frontend(stage).mkdir(parents=True)
            command=['npm','install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org']
            w.run(command,w.frontend(stage))
            if duplicate:w.run(command,w.frontend(stage))
            w.run(['python','-m','pip','download'],stage)
        w.prepare=prepare
        return w,ran,run
    @patch('w8_ext07r3.lock_bytes',return_value=b'reviewed-fixture')
    def test_prepare_intercepts_only_lock(self,_):
        w,ran,run=self.fake_parent();extend(w,self.p/'lock');stage=self.p/'stage';w.prepare(self.p,stage)
        self.assertEqual((stage/'frontend/package-lock.json').read_bytes(),b'reviewed-fixture');self.assertEqual(ran,[['python','-m','pip','download']]);self.assertIs(w.run,run)
    @patch('w8_ext07r3.lock_bytes',return_value=b'reviewed-fixture')
    def test_duplicate_lock_call_stops_and_restores(self,_):
        w,ran,run=self.fake_parent(True);extend(w,self.p/'lock');self.assertRaisesRegex(ValueError,'DUPLICATE_LOCK',w.prepare,self.p,self.p/'stage');self.assertEqual(ran,[]);self.assertIs(w.run,run)

if __name__=='__main__':unittest.main()
