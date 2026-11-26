"""Local adapter mechanics with a doubled inherited runner, never a product acceptance."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import w8_p10j20 as m

class Adapter(unittest.TestCase):
    def setup(self,mode='ok'):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);stage=Path(temp.name)
        calls=[];w=SimpleNamespace(MANIFEST_BLOB=m.CANDIDATE_MANIFEST,HARNESS={'browser_0187_w1.py':m.OLD_BROWSER})
        def run(args,cwd,env=None):
            calls.append(str(args[1]))
            if mode=='native_fail' and str(args[1]).endswith(m.NATIVE):raise RuntimeError('native')
            if mode=='test_fail' and str(args[1])=='--test':raise RuntimeError('test')
        w.run=run;w.installed=lambda *_:None;w.reviewed=lambda *_:None;w.verify_aux=lambda *_:None
        w.python=lambda _: 'python';w.node=lambda:'node';w.frontend=lambda _:stage;w.env_local=lambda:{}
        def smoke(s,a,c,fp,bp):
            if mode!='missing':w.run(['python',s/m.LAST_SMOKE],s,{})
            if mode=='duplicate':w.run(['python',s/m.LAST_SMOKE],s,{})
            (s/'SMOKE_OK').write_text(a if mode!='bad_marker' else 'wrong')
            if mode=='parent_fail':raise RuntimeError('parent')
        def test(s,a):(s/'BUILD_TEST_OK').write_text(a)
        w.smoke,w.test=smoke,test
        return stage,calls,w,run
    def test_rebind_and_success(self):
        s,c,w,r=self.setup();m.extend_candidate(w);w.smoke(s,'a','chrome');self.assertEqual((s/'HYBRID_NATIVE_OK').read_text(),'a');self.assertEqual(sum(x.endswith(m.NATIVE) for x in c),1);self.assertIs(w.run,r);self.assertEqual(w.HARNESS[m.NATIVE],m.NATIVE_BLOB)
    def test_wrong_manifest(self):
        s,c,w,r=self.setup();w.MANIFEST_BLOB='wrong';self.assertRaises(ValueError,m.extend_candidate,w)
    def test_smoke_fail_closed(self):
        for mode in ['missing','duplicate','native_fail','parent_fail','bad_marker']:
            with self.subTest(mode=mode):
                s,c,w,r=self.setup(mode);m.extend_candidate(w);(s/'HYBRID_NATIVE_OK').write_text('old');self.assertRaises(Exception,w.smoke,s,'a','chrome');self.assertIs(w.run,r);self.assertTrue(all(not (s/n).exists() for n in m.MARKERS))
    def test_test_success(self):
        s,c,w,r=self.setup();m.extend_candidate(w);w.test(s,'a');self.assertEqual((s/'BUILD_TEST_OK').read_text(),'a');self.assertIn('--test',c)
    def test_test_failure_clears_markers(self):
        s,c,w,r=self.setup('test_fail');m.extend_candidate(w)
        for name in ('BUILD_TEST_OK',*m.MARKERS):(s/name).write_text('old')
        self.assertRaises(RuntimeError,w.test,s,'a');self.assertTrue(all(not (s/n).exists() for n in ('BUILD_TEST_OK',*m.MARKERS)))

if __name__=='__main__':unittest.main(verbosity=2)
