"""Adapter mechanics only: fake parent, no product build or browser claim."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

p = Path(__file__).with_name('w8_unified_u3.py')
spec = importlib.util.spec_from_file_location('u3', p)
u3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u3)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.stage = Path(self.tmp.name)
        self.events = []
        self.approval = 'a'*64
        self.mode = 'good'
        self.w = SimpleNamespace(MANIFEST_BLOB=u3.MANIFEST)
        self.w.checked_path = lambda root, name: root/name
        self.w.verify_aux = lambda root: {}
        self.w.installed = lambda stage, approval: self.events.append('installed')
        self.w.reviewed = lambda stage, approval: self.events.append('reviewed')
        self.w.frontend = lambda stage: stage/'frontend'
        self.w.env_local = lambda: {}
        self.w.node = lambda: 'node'
        self.w.python = lambda stage: 'python'
        def run(args, cwd, env=None):
            self.events.append(list(map(str,args)))
            if self.mode == 'test-fail':
                raise RuntimeError('diagnostic failure')
            if len(args)>1 and str(args[1]) == str(self.stage/u3.BROWSER):
                if self.mode == 'browser-fail':
                    raise RuntimeError('browser failure')
                out = self.stage/'unified-u3-browser'
                out.mkdir()
                for i in range(5):
                    (out/f'{i}.png').write_bytes(b'fake')
                report = {'status':'PASS','shared_reads':3,'actual_browser':True,'same_document':True,'screenshots':5,'join':'HOLD'}
                if self.mode == 'wrong-report':
                    report['shared_reads'] = 4
                (out/'U3_BROWSER_REPORT.json').write_text(json.dumps(report))
        self.w.run = run
        def test(stage, approval):
            self.events.append('parent-test')
            if self.mode != 'no-build-marker':
                (stage/'BUILD_TEST_OK').write_text(approval)
        self.w.test = test
        def smoke(stage, approval, chromium, frontend_port, backend_port):
            self.events.append('parent-smoke')
            if self.mode != 'no-browser-call':
                self.w.run(['python',stage/u3.LAST_SMOKE],stage,{})
            if self.mode == 'duplicate-browser':
                self.w.run(['python',stage/u3.LAST_SMOKE],stage,{})
            for name in ('SMOKE_OK','HYBRID_NATIVE_OK'):
                (stage/name).write_text(approval)
        self.w.smoke = smoke

    def bind(self, extra=None):
        self.enterContext(patch.object(u3, 'EXTRA', extra if extra is not None else {}))
        return u3.extend(self.w)

    def stale(self):
        for name in u3.MARKERS:
            (self.stage/name).write_text('stale')

    def test_wrong_manifest_refused(self):
        self.w.MANIFEST_BLOB = 'wrong'
        with self.assertRaisesRegex(ValueError,'U3_MANIFEST_HOLD'):
            self.bind()

    def test_aux_pin_validated(self):
        data = self.stage/'sample'
        data.write_bytes(b'exact')
        pin = u3.blob(data)
        w = self.bind({'sample':pin})
        self.assertEqual(w.verify_aux(self.stage),{'sample':pin})
        data.write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError,'U3_AUX_PIN_HOLD'):
            w.verify_aux(self.stage)

    def test_aux_collision_refused(self):
        self.w.verify_aux = lambda root: {'sample':'wrong'}
        w = self.bind({'sample':'exact'})
        with self.assertRaisesRegex(ValueError,'U3_AUX_COLLISION_HOLD'):
            w.verify_aux(self.stage)

    def test_all_seven_calls_and_parent_build(self):
        self.stale()
        w = self.bind()
        w.test(self.stage,self.approval)
        self.assertEqual(sum(isinstance(x,list) for x in self.events),7)
        self.assertLess(self.events.index('parent-test'),self.events.index('reviewed'))
        self.assertEqual((self.stage/'BUILD_TEST_OK').read_text(),self.approval)
        self.assertFalse((self.stage/'SMOKE_OK').exists())

    def test_failed_diagnostic_removes_stale_markers(self):
        self.stale()
        self.mode = 'test-fail'
        w = self.bind()
        with self.assertRaises(RuntimeError):
            w.test(self.stage,self.approval)
        self.assertTrue(all(not (self.stage/n).exists() for n in u3.MARKERS))
        self.assertNotIn('parent-test',self.events)

    def test_missing_build_marker_refused(self):
        self.mode = 'no-build-marker'
        w = self.bind()
        with self.assertRaises(OSError):
            w.test(self.stage,self.approval)
        self.assertFalse((self.stage/'BUILD_TEST_OK').exists())

    def test_smoke_hook_one_call_and_restore(self):
        w = self.bind()
        original = w.run
        w.smoke(self.stage,self.approval,'chromium')
        self.assertIs(w.run,original)
        self.assertEqual(sum(isinstance(x,list) and len(x)>1 and x[1]==str(self.stage/u3.BROWSER) for x in self.events),1)
        self.assertEqual((self.stage/'SMOKE_OK').read_text(),self.approval)

    def test_smoke_missing_call_refused(self):
        self.mode = 'no-browser-call'
        w = self.bind()
        with self.assertRaisesRegex(ValueError,'U3_BROWSER_REQUIRED_HOLD'):
            w.smoke(self.stage,self.approval,'chromium')
        self.assertFalse((self.stage/'SMOKE_OK').exists())

    def test_smoke_duplicate_refused(self):
        self.mode = 'duplicate-browser'
        w = self.bind()
        with self.assertRaisesRegex(ValueError,'U3_BROWSER_CALL_HOLD'):
            w.smoke(self.stage,self.approval,'chromium')
        self.assertFalse((self.stage/'HYBRID_NATIVE_OK').exists())

    def test_smoke_failure_and_wrong_report_refused(self):
        self.mode = 'wrong-report'
        w = self.bind()
        original = w.run
        with self.assertRaisesRegex(ValueError,'U3_BROWSER_REPORT_HOLD'):
            w.smoke(self.stage,self.approval,'chromium')
        self.assertIs(w.run,original)
        self.assertFalse((self.stage/'SMOKE_OK').exists())


if __name__ == '__main__':
    unittest.main()
