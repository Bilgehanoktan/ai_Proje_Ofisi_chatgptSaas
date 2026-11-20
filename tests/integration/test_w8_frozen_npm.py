"""Synthetic fail-closed unit checks only, not the original W8 fullchain."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from w8_frozen_npm import FrozenNpmPrepareHook, verify_frozen_npm_inputs, install_into_w8


def sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


class FrozenNpmTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.front = self.root/'product/ai-company-os-frontend'
        self.front.mkdir(parents=True)
        self.src = self.root/'tests/integration/locks/mi01-frozen-npm/package-lock.json'
        self.src.parent.mkdir(parents=True)
        self.pkg = {'name':'fixture','version':'0.1','dependencies':{'next':'1'},'devDependencies':{'typescript':'2'},'overrides':{'sharp':'1.2.3'}}
        self.lock = {'name':'fixture','version':'0.1','lockfileVersion':3,'packages':{'':{'dependencies':dict(self.pkg['dependencies']),'devDependencies':dict(self.pkg['devDependencies'])},'node_modules/sharp':{'version':'1.2.3','resolved':'https://registry.npmjs.org/sharp/-/sharp-1.2.3.tgz','integrity':'sha512-'+'A'*60}}}
        self.write()

    def write(self):
        self.pkg_raw=json.dumps(self.pkg).encode()
        self.lock_raw=json.dumps(self.lock).encode()
        (self.front/'package.json').write_bytes(self.pkg_raw)
        self.src.write_bytes(self.lock_raw)

    def verify(self, **kw):
        baseline=dict(lock_path='tests/integration/locks/mi01-frozen-npm/package-lock.json',lock_blob=sha(self.lock_raw),lock_sha256=hashlib.sha256(self.lock_raw).hexdigest(),lock_bytes=len(self.lock_raw),package_blob=sha(self.pkg_raw),package_count=1)
        baseline.update(kw)
        return verify_frozen_npm_inputs(self.root,self.front,**baseline)

    def test_exact_valid_lock(self):
        self.assertEqual(self.verify(),self.lock_raw)

    def test_reject_tampered_hash(self):
        self.assertRaisesRegex(ValueError,'LOCK_PIN',self.verify,lock_sha256='0'*64)

    def test_reject_unpinned_package(self):
        self.assertRaisesRegex(ValueError,'PACKAGE_PIN',self.verify,package_blob='1'*40)

    def test_reject_package_direct_drift(self):
        self.lock['packages']['']['dependencies']['next']='4';self.write()
        self.assertRaisesRegex(ValueError,'DIRECT_PIN',self.verify)

    def test_reject_override_drift(self):
        self.lock['packages']['node_modules/sharp']['version']='2';self.write()
        self.assertRaisesRegex(ValueError,'OVERRIDE',self.verify)

    def test_reject_non_registry_url(self):
        self.lock['packages']['node_modules/sharp']['resolved']='https://evil.example/sharp';self.write()
        self.assertRaisesRegex(ValueError,'PROVENANCE',self.verify)

    def test_reject_missing_integrity(self):
        del self.lock['packages']['node_modules/sharp']['integrity'];self.write()
        self.assertRaisesRegex(ValueError,'PROVENANCE',self.verify)

    def test_reject_empty_or_symlink(self):
        self.src.unlink();self.src.symlink_to(self.front/'package.json')
        self.assertRaisesRegex(ValueError,'SYMLINK',self.verify)

    def test_reject_wrong_package_count(self):
        self.assertRaisesRegex(ValueError,'GRAPH',self.verify,package_count=2)

    def test_exact_install_command_replaces_lock_generation(self):
        calls=[]
        hook=FrozenNpmPrepareHook(lambda *a:calls.append(a),'npm',self.front,self.lock_raw)
        self.assertIsNone(hook(['npm','install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org'],self.front))
        self.assertEqual((self.front/'package-lock.json').read_bytes(),self.lock_raw)
        self.assertEqual(hook.count,1);self.assertEqual(calls,[])

    def test_reject_second_generation(self):
        hook=FrozenNpmPrepareHook(lambda *a:None,'npm',self.front,self.lock_raw)
        args=['npm','install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org']
        hook(args,self.front)
        self.assertRaisesRegex(ValueError,'CALL_HOLD',hook,args,self.front)

    def test_reject_wrong_registry_or_cwd(self):
        hook=FrozenNpmPrepareHook(lambda *a:None,'npm',self.front,self.lock_raw)
        args=['npm','install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.invalid']
        self.assertRaisesRegex(ValueError,'CALL_HOLD',hook,args,self.front)
        args[-1]='--registry=https://registry.npmjs.org'
        self.assertRaisesRegex(ValueError,'CALL_HOLD',hook,args,self.root)

    def test_reject_overwrite_existing_lock(self):
        (self.front/'package-lock.json').write_bytes(b'wrong')
        hook=FrozenNpmPrepareHook(lambda *a:None,'npm',self.front,self.lock_raw)
        args=['npm','install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org']
        self.assertRaisesRegex(ValueError,'OVERWRITE_HOLD',hook,args,self.front)

    def test_other_commands_delegated(self):
        calls=[]
        hook=FrozenNpmPrepareHook(lambda *a:calls.append(a),'npm',self.front,self.lock_raw)
        args=['python','-m','pip','--help']
        hook(args,self.front)
        self.assertEqual(len(calls),1);self.assertEqual(hook.count,0)

    def test_fail_closed_prepare_cleanups_review_marker(self):
        class Dummy:
            def __init__(s): s.run=lambda *a:None
            def frontend(s,root):return root/'product/ai-company-os-frontend'
            def npm(s):return 'npm'
            def prepare(s,repo,stage):
                (stage/'locks').mkdir(parents=True)
                (stage/'locks/REVIEW.json').write_text('false approval')
                raise ValueError('simulated pip DNS failure')
        w=Dummy();initial=w.run
        import w8_frozen_npm as mod
        old=[mod.LOCK_BLOB,mod.LOCK_SHA256,mod.LOCK_BYTES,mod.PACKAGE_BLOB,mod.PACKAGE_COUNT]
        try:
            mod.LOCK_BLOB=sha(self.lock_raw);mod.LOCK_SHA256=hashlib.sha256(self.lock_raw).hexdigest();mod.LOCK_BYTES=len(self.lock_raw);mod.PACKAGE_BLOB=sha(self.pkg_raw);mod.PACKAGE_COUNT=1
            install_into_w8(w)
            self.assertRaisesRegex(ValueError,'simulated pip',w.prepare,self.root,self.root/'stage')
            self.assertIs(w.run,initial)
            self.assertFalse((self.root/'stage/locks/REVIEW.json').exists())
        finally:
            mod.LOCK_BLOB,mod.LOCK_SHA256,mod.LOCK_BYTES,mod.PACKAGE_BLOB,mod.PACKAGE_COUNT=old


if __name__=='__main__':unittest.main()
