"""Offline adapter controls with fake parent; no product or npm execution."""
import hashlib
from pathlib import Path
import shutil
import tempfile
import types
import unittest
from unittest.mock import patch
import w8_mi_common_02 as m


def blob(p):
    raw = p.read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


class Controls(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.repo, self.stage = self.root/'repo', self.root/'stage'
        self.repo.mkdir()
        self.raw = b'X'*33618
        self.lock = self.repo/m.LOCK
        self.lock.parent.mkdir(parents=True)
        self.lock.write_bytes(self.raw)
        self.pin = blob(self.lock)
        self.sha = hashlib.sha256(self.raw).hexdigest()
        for k, v in {'LOCK_BLOB':self.pin,'LOCK_SHA':self.sha,'EXTRA':{m.LOCK:self.pin}}.items():
            patcher = patch.object(m,k,v)
            patcher.start(); self.addCleanup(patcher.stop)
        self.calls = []
        w = self.w = types.SimpleNamespace(MANIFEST_BLOB=m.MANIFEST)
        w.blob = blob
        def checked(root,name):
            p = root/name
            if p.resolve()!=p.absolute() or not p.resolve().is_relative_to(root.resolve()): raise ValueError('unsafe')
            return p
        w.checked_path=checked
        w.frontend=lambda root: root/'product/ai-company-os-frontend'
        w.npm=lambda: 'npm'
        w.node=lambda: 'node'
        w.env_local=lambda: {}
        w.verify_aux=lambda root: {}
        w.lock_inventory=lambda stage: {'npm_lock_sha256': hashlib.sha256((w.frontend(stage)/'package-lock.json').read_bytes()).hexdigest()}
        w.run=lambda args,cwd,env=None: self.calls.append(list(map(str,args)))
        w.installed=lambda stage,approval: None
        w.reviewed=lambda stage,approval: None
        self.legacy=['npm','install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org']
        def prepare(repo,stage):
            w.frontend(stage).mkdir(parents=True,exist_ok=False)
            p=stage/m.LOCK; p.parent.mkdir(parents=True); shutil.copyfile(repo/m.LOCK,p)
            w.run(self.legacy,w.frontend(stage))
            w.run(['python','-m','pip','--isolated','download'],stage)
            return w.lock_inventory(stage)
        w.prepare=prepare
        def original_test(stage,approval):
            self.calls.append(['parent-test'])
            (stage/'BUILD_TEST_OK').write_text(approval)
        w.test=original_test

    def test_exact_lock_copy_no_npm_regeneration(self):
        original_run=self.w.run
        m.extend(self.w).prepare(self.repo,self.stage)
        self.assertEqual((self.w.frontend(self.stage)/'package-lock.json').read_bytes(),self.raw)
        self.assertEqual(self.calls,[['python','-m','pip','--isolated','download']])
        self.assertIs(self.w.run,original_run)

    def test_source_lock_tamper_stops_before_stage(self):
        self.lock.write_bytes(b'Y'*33618)
        with self.assertRaisesRegex(ValueError,'AUX_PIN_HOLD'): m.extend(self.w).prepare(self.repo,self.stage)
        self.assertFalse(self.stage.exists()); self.assertEqual(self.calls,[])

    def test_stage_lock_tamper_denied(self):
        m.extend(self.w).prepare(self.repo,self.stage)
        (self.w.frontend(self.stage)/'package-lock.json').write_bytes(b'Y'*33618)
        with self.assertRaisesRegex(ValueError,'LOCK_PIN_HOLD'): self.w.lock_inventory(self.stage)

    def test_unexpected_regeneration_call_denied_and_hook_restored(self):
        self.legacy.append('--force')
        original_run=self.w.run
        with self.assertRaisesRegex(ValueError,'PREPARE_CALL_HOLD'): m.extend(self.w).prepare(self.repo,self.stage)
        self.assertIs(self.w.run,original_run); self.assertEqual(self.calls,[])

    def test_manifest_pin_drift(self):
        self.w.MANIFEST_BLOB='0'*40
        with self.assertRaisesRegex(ValueError,'MANIFEST_HOLD'): m.extend(self.w)

    def test_original_tests_before_parent(self):
        self.stage.mkdir(); (self.stage/m.ORG).mkdir(parents=True)
        m.extend(self.w).test(self.stage,'review')
        self.assertEqual(len(self.calls),5); self.assertEqual(self.calls[-1],['parent-test'])
        self.assertEqual((self.stage/'BUILD_TEST_OK').read_text(),'review')
        self.assertIn(str(self.stage/m.SKILL),self.calls[3])

    def test_failure_clears_markers_and_skips_parent(self):
        self.stage.mkdir(); (self.stage/m.ORG).mkdir(parents=True)
        for name in m.MARKERS: (self.stage/name).write_text('old')
        def fail(*args,**kw): raise RuntimeError('test failure')
        self.w.run=fail
        with self.assertRaisesRegex(RuntimeError,'test failure'): m.extend(self.w).test(self.stage,'review')
        self.assertTrue(all(not (self.stage/name).exists() for name in m.MARKERS)); self.assertEqual(self.calls,[])

if __name__=='__main__': unittest.main(verbosity=2)
