"""Standalone adapter protocol tests; parent runner substituted, not product W8."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import w8_p10j as adapter

PARENT = b'# synthetic parent fixture\n'
PIN = hashlib.sha1(b'blob '+str(len(PARENT)).encode()+b'\0'+PARENT).hexdigest()

class Parent:
    def __init__(self, reject=False):
        self.reject = reject
        self.events = []
        self.test = self.original_test
    def installed(self, stage, approval):
        self.events.append(('gate', approval))
        if self.reject:
            raise ValueError('LOCK_HOLD')
    def frontend(self, stage): return stage/'frontend'
    def env_local(self): return {}
    def node(self): return 'node'
    def run(self, args, cwd, env): self.events.append(('run', list(map(str,args))))
    def original_test(self, stage, approval): self.events.append(('parent', approval))

class AdapterTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root/'w8_p10i.py').write_bytes(PARENT)
        self.addCleanup(patch.stopall)
        patch.object(adapter, '__file__', str(self.root/'w8_p10j.py')).start()
        patch.object(adapter, 'P10I_BLOB', PIN).start()
    def load(self, runner):
        from types import SimpleNamespace
        parent = SimpleNamespace(load_candidate=lambda:runner)
        patch.object(adapter.importlib.util, 'module_from_spec', return_value=parent).start()
        patch.object(adapter.importlib.util, 'spec_from_file_location', return_value=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _:None))).start()
        w = adapter.load_candidate()
        self.assertEqual(parent.CANDIDATE_MANIFEST, adapter.CANDIDATE_MANIFEST)
        return w
    def test_pin_mismatch(self):
        (self.root/'w8_p10i.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'PIN_HOLD'): adapter.load_candidate()
    def test_missing_parent(self):
        (self.root/'w8_p10i.py').unlink()
        with self.assertRaises(FileNotFoundError): adapter.load_candidate()
    def test_gate_rejects_before_work(self):
        runner = self.load(Parent(reject=True))
        with self.assertRaisesRegex(ValueError,'LOCK_HOLD'): runner.test(self.root,'review')
        self.assertEqual(runner.events,[('gate','review')])
    def test_markers_and_order(self):
        runner = self.load(Parent())
        for marker in ('BUILD_TEST_OK','SMOKE_OK'): (self.root/marker).write_text('old')
        runner.test(self.root,'review')
        self.assertEqual([x[0] for x in runner.events],['gate','run','run','parent'])
        self.assertIn('tests/ui-p10j-model.test.cjs',runner.events[2][1])
        self.assertFalse((self.root/'BUILD_TEST_OK').exists())
        self.assertFalse((self.root/'SMOKE_OK').exists())

if __name__ == '__main__': unittest.main()
