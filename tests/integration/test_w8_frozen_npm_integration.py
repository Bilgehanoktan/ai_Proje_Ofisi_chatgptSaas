"""Integration-shaped synthetic checks for the exact immutable W8 npm helper."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import w8_frozen_npm as helper


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()


class FakeW8:
    def __init__(self,root,extra_npm=False,raise_after=False):
        self.root=root
        self.events=[]
        self.extra_npm=extra_npm
        self.raise_after=raise_after
        self.run=self.original_run

    def frontend(self,root):
        return root/'product/ai-company-os-frontend'

    def npm(self):
        return 'npm'

    def original_run(self,args,cwd,env=None):
        self.events.append(('external',tuple(map(str,args))))

    def prepare(self,repo,stage):
        (self.frontend(stage)).mkdir(parents=True)
        (stage/'locks').mkdir()
        args=['npm','install','--package-lock-only','--ignore-scripts','--no-audit',
              '--no-fund','--registry=https://registry.npmjs.org']
        self.run(args,self.frontend(stage))
        if self.extra_npm:
            self.run(args,self.frontend(stage))
        self.run(['python','-m','pip','download'],stage)
        (stage/'locks/REVIEW.json').write_text('simulated review, not owner approval')
        if self.raise_after:
            raise OSError('synthetic dependency failure')


class W8AdapterIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        front=self.root/'product/ai-company-os-frontend'
        front.mkdir(parents=True)
        lock_path=self.root/helper.LOCK_PATH
        lock_path.parent.mkdir(parents=True)
        pkg={'name':'stub','version':'0.1','dependencies':{'pkg':'1.0'},
             'devDependencies':{},'overrides':{'postcss':'8.5.32'}}
        locked={'name':'stub','version':'0.1','lockfileVersion':3,'packages':{
            '':{'dependencies':pkg['dependencies'],'devDependencies':{}},
            'node_modules/postcss':{'version':'8.5.32',
                'resolved':'https://registry.npmjs.org/postcss/-/postcss-8.5.32.tgz',
                'integrity':'sha512-'+('A'*72)}}}
        self.pkg_bytes=json.dumps(pkg).encode('utf-8')
        self.lock_bytes=json.dumps(locked).encode('utf-8')
        (front/'package.json').write_bytes(self.pkg_bytes)
        lock_path.write_bytes(self.lock_bytes)
        self.patcher=patch.multiple(helper,LOCK_BLOB=blob(self.lock_bytes),
                    LOCK_SHA256=hashlib.sha256(self.lock_bytes).hexdigest(),
                    LOCK_BYTES=len(self.lock_bytes),PACKAGE_BLOB=blob(self.pkg_bytes),
                    PACKAGE_COUNT=1)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_prepare_writes_exact_lock_before_pip_without_npm_resolution(self):
        w=FakeW8(self.root)
        original=w.run
        helper.install_into_w8(w)
        stage=self.root/'stage'
        w.prepare(self.root,stage)
        self.assertEqual((w.frontend(stage)/'package-lock.json').read_bytes(),self.lock_bytes)
        self.assertEqual(w.events,[('external',('python','-m','pip','download'))])
        self.assertIs(w.run,original)
        self.assertTrue((stage/'locks/REVIEW.json').exists())

    def test_wrong_package_input_blocks_before_stage_creation(self):
        w=FakeW8(self.root)
        helper.install_into_w8(w)
        (w.frontend(self.root)/'package.json').write_bytes(b'{"tampered":true}')
        stage=self.root/'stage'
        with self.assertRaisesRegex(ValueError,'PACKAGE_PIN_HOLD'):
            w.prepare(self.root,stage)
        self.assertFalse(stage.exists())
        self.assertFalse(w.events)

    def test_second_npm_generation_rejected_and_review_removed(self):
        w=FakeW8(self.root,extra_npm=True)
        original=w.run
        helper.install_into_w8(w)
        stage=self.root/'stage'
        with self.assertRaisesRegex(ValueError,'NPM_CALL_HOLD'):
            w.prepare(self.root,stage)
        self.assertIs(w.run,original)
        self.assertFalse((stage/'locks/REVIEW.json').exists())
        self.assertFalse(w.events)

    def test_pip_failure_restores_runner_and_clears_marker(self):
        w=FakeW8(self.root,raise_after=True)
        original=w.run
        helper.install_into_w8(w)
        stage=self.root/'stage'
        with self.assertRaisesRegex(OSError,'synthetic dependency failure'):
            w.prepare(self.root,stage)
        self.assertIs(w.run,original)
        self.assertFalse((stage/'locks/REVIEW.json').exists())
        self.assertEqual(len(w.events),1)


if __name__=='__main__':
    unittest.main()
