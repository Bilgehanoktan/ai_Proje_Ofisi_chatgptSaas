"""A4R2 harness tests; doubles do not execute the native product."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import unittest
import w8_ux_a4r2 as a
import native_ux_a4r2 as n


class Helpers(unittest.TestCase):
    def test_loopback(self):
        self.assertEqual(n.local_origin('http://127.0.0.1:17300/'),'http://127.0.0.1:17300')
        for bad in ['https://127.0.0.1:17300','http://localhost:17300','http://127.0.0.1:17300/x','http://127.0.0.1:17300/?x=1','http://127.0.0.1','http://u@127.0.0.1:17300']:
            with self.subTest(bad=bad),self.assertRaises(ValueError):n.local_origin(bad)

    def test_metrics(self):
        m=n.frame_metrics([10]*114+[20]*6)
        self.assertEqual(m['samples'],120)
        self.assertEqual(m['p95_delta_ms'],10)
        self.assertEqual(m['max_delta_ms'],20)
        self.assertAlmostEqual(m['estimated_update_hz'],1000/10.5)

    def test_invalid_samples(self):
        for bad in [[],[1]*121,[1]*29,[1]*29+[0],[1]*29+[float('nan')],[1]*29+[True]]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):n.frame_metrics(bad)

    def test_native_pin(self):
        root=Path(__file__).resolve().parents[2]
        self.assertEqual(a.checked_pin(root,a.NATIVE_PATH,a.NATIVE_BLOB),root/a.NATIVE_PATH)
        with self.assertRaises(ValueError):a.checked_pin(root,a.NATIVE_PATH,'0'*40)

    def test_unsafe_path(self):
        with tempfile.TemporaryDirectory() as tmp,self.assertRaises(ValueError):a.checked_pin(Path(tmp),'../x','0'*40)


class GuardDoubles(unittest.TestCase):
    def smoke_case(self,mode):
        with tempfile.TemporaryDirectory() as tmp:
            stage=Path(tmp);calls=[]
            for name in a.MARKERS:(stage/name).write_text('old')
            def run(args,cwd,env=None):
                calls.append(str(args[1]))
                if mode=='native_fail' and str(args[1])==str(stage/a.NATIVE_PATH):raise ValueError('native failed')
            def smoke(*args):
                self.assertFalse(any((stage/m).exists() for m in a.MARKERS))
                if mode!='absent':w.run(['python',stage/a.LAST_SMOKE],stage)
                if mode=='duplicate':w.run(['python',stage/a.LAST_SMOKE],stage)
                for name in a.MARKERS[:2]:(stage/name).write_text('wrong' if mode=='marker' else 'ok')
                if mode=='parent_fail':raise ValueError('parent failed')
            w=SimpleNamespace(verify_aux=lambda root:{},test=lambda *x:None,smoke=smoke,installed=lambda *x:None,reviewed=lambda *x:None,run=run,python=lambda s:'python',env_local=lambda:{})
            a.extend_candidate(w)
            with patch.object(a,'checked_pin',return_value=None):
                if mode=='success':
                    w.smoke(stage,'ok',Path('chrome'))
                    self.assertEqual([str(stage/a.LAST_SMOKE),str(stage/a.NATIVE_PATH)],calls)
                    self.assertTrue(all((stage/m).read_text()=='ok' for m in a.MARKERS))
                else:
                    with self.assertRaises(ValueError):w.smoke(stage,'ok',Path('chrome'))
                    self.assertFalse(any((stage/m).exists() for m in a.MARKERS))
            self.assertIs(w.run,run)

    def test_success(self):self.smoke_case('success')
    def test_absent_hook(self):self.smoke_case('absent')
    def test_duplicate_hook(self):self.smoke_case('duplicate')
    def test_native_failure(self):self.smoke_case('native_fail')
    def test_parent_failure(self):self.smoke_case('parent_fail')
    def test_marker_mismatch(self):self.smoke_case('marker')

    def test_build_failure_clears_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage=Path(tmp)
            for name in ('BUILD_TEST_OK',*a.MARKERS):(stage/name).write_text('old')
            def run(*args):raise ValueError('compile failed')
            w=SimpleNamespace(verify_aux=lambda root:{},test=lambda *x:None,smoke=lambda *x:None,installed=lambda *x:None,frontend=lambda s:s,node=lambda:'node',env_local=lambda:{},run=run)
            a.extend_candidate(w)
            with self.assertRaises(ValueError):w.test(stage,'ok')
            self.assertFalse(any((stage/m).exists() for m in ('BUILD_TEST_OK',*a.MARKERS)))


if __name__=='__main__':unittest.main(verbosity=2)
