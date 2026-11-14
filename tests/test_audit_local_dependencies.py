import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_local_dependencies import REQ, PKG, audit, parse_requirements, parse_package, read_safe

class DependencyAuditTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.req = b'# sample\nfastapi==0.115.12\n'
        self.pkg = b'{"dependencies":{"next":"15.5.9"},"devDependencies":{"typescript":"5.9.3"}}'
        self.put(REQ, self.req); self.put(PKG, self.pkg)
        self.pins = {k:(len(v),hashlib.sha256(v).hexdigest()) for k,v in ((REQ,self.req),(PKG,self.pkg))}
    def put(self, name, raw):
        p=self.root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(raw)
    def result(self, lookup=lambda n: None): return audit(self.root,self.pins,lookup)
    def test_missing(self): self.assertEqual(self.result()['python_direct'][0]['status'],'MISSING')
    def test_mismatch(self): self.assertEqual(self.result(lambda n:'0.0.0')['python_direct'][0]['status'],'MISMATCH')
    def test_match(self): self.assertEqual(self.result(lambda n:'0.115.12')['python_direct'][0]['status'],'MATCH')
    def test_node_match(self):
        self.put('product/ai-company-os-frontend/node_modules/next/package.json',b'{"name":"next","version":"15.5.9"}')
        self.assertEqual(self.result()['node_direct'][0]['status'],'MATCH')
    def test_node_mismatch(self):
        self.put('product/ai-company-os-frontend/node_modules/next/package.json',b'{"name":"next","version":"1.0.0"}')
        self.assertEqual(self.result()['node_direct'][0]['status'],'MISMATCH')
    def test_lock_unreviewed(self):
        self.put('product/ai-company-os-frontend/package-lock.json',b'{}')
        self.assertEqual(self.result()['node_lock']['status'],'PRESENT_UNREVIEWED')
        self.assertEqual(self.result()['readiness'],'HOLD')
    def test_no_implicit_authority(self): self.assertEqual(self.result()['authority'],'NOT_EVALUATED')
    def test_pin_tamper(self):
        self.put(REQ,b'fastapi==0.0.0')
        with self.assertRaisesRegex(ValueError,'SPEC_PIN_MISMATCH'): self.result()
    def test_python_unpinned(self):
        with self.assertRaisesRegex(ValueError,'PYTHON_PIN_FORMAT'): parse_requirements(b'fastapi>=1.0.0')
    def test_npm_range(self):
        with self.assertRaisesRegex(ValueError,'NPM_PIN_FORMAT'): parse_package(b'{"dependencies":{"next":"^15.5.9"}}')
    def test_duplicate_json(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_JSON_KEY'): parse_package(b'{"dependencies":{"next":"1.0.0","next":"2.0.0"}}')
    def test_unsafe_path(self):
        with self.assertRaisesRegex(ValueError,'UNSAFE_PATH'): read_safe(self.root,'../outside')
    def test_wrong_node_identity(self):
        self.put('product/ai-company-os-frontend/node_modules/next/package.json',b'{"name":"other","version":"15.5.9"}')
        with self.assertRaisesRegex(ValueError,'NPM_INSTALLED_METADATA_INVALID'): self.result()
    def test_symlink(self):
        p=self.root/REQ; p.unlink(); p.symlink_to(self.root/PKG)
        with self.assertRaisesRegex(ValueError,'LINK_OR_JUNCTION'): self.result()
if __name__=='__main__': unittest.main()
