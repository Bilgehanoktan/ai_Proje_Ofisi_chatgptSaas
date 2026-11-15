"""Offline runner preflight tests, not product acceptance."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import w8_local as w

class Preflight(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.prod=self.root/'product';self.prod.mkdir()
        self.files={}
        for name in ('ai-company-os-frontend/fixtures/test.json','ai-company-os-backend/fixtures/test.json'):
            p=self.prod/name;p.parent.mkdir(parents=True);p.write_bytes(b'{}\n');self.files[name]={'bytes':3,'sha256':hashlib.sha256(b'{}\n').hexdigest()}
        self.m=self.prod/'SOURCE_MANIFEST.json';self.refresh()
    def refresh(self):
        self.m.write_text(json.dumps({'files':self.files}),encoding='utf-8');self.pin=w.blob(self.m)
    def test_clean_exact_checkout(self):self.assertEqual(w.verify(self.root,self.pin,clean=True)[1],1)
    def test_wrong_manifest_pin(self):
        with self.assertRaisesRegex(ValueError,'wrong SOURCE'):w.verify(self.root,'a'*40)
    def test_same_size_tamper(self):
        (self.prod/next(iter(self.files))).write_bytes(b'[]\n')
        with self.assertRaisesRegex(ValueError,'changed source'):w.verify(self.root,self.pin)
    def test_missing_file(self):
        (self.prod/next(iter(self.files))).unlink()
        with self.assertRaisesRegex(ValueError,'changed source'):w.verify(self.root,self.pin)
    def test_extra_file(self):
        (self.prod/'extra').write_text('x')
        with self.assertRaisesRegex(ValueError,'extra files'):w.verify(self.root,self.pin,clean=True)
    def test_parity_mismatch_even_with_matching_manifest(self):
        name=next(iter(self.files));p=self.prod/name;p.write_bytes(b'[]\n');self.files[name]['sha256']=w.sha(p);self.refresh()
        with self.assertRaisesRegex(ValueError,'parity mismatch'):w.verify(self.root,self.pin)
    def test_path_traversal(self):
        self.files['../outside']={'bytes':0,'sha256':'x'};self.refresh()
        with self.assertRaisesRegex(ValueError,'unsafe path'):w.verify(self.root,self.pin)
    def test_override_pin_drift_stops_review(self):
        f=w.frontend(self.root);f.mkdir(parents=True,exist_ok=True)
        (f/'package.json').write_text(json.dumps({'overrides':{'postcss':'8.5.32'}}))
        for packages in [{'':{}},{'':{},'node_modules/postcss':{'version':'8.4.31'}},{'':{},'node_modules/postcss':{'version':'8.5.32'},'node_modules/next/node_modules/postcss':{'version':'8.4.31'}}]:
            (f/'package-lock.json').write_text(json.dumps({'packages':packages}))
            with self.assertRaisesRegex(ValueError,'override pin drift'):w.lock_inventory(self.root)
    def test_review_tamper_stops_before_install(self):
        lock=self.root/'locks';lock.mkdir();(lock/'REVIEW.json').write_text('{}')
        with patch.object(w,'verify'),patch.object(w,'run') as run:
            with self.assertRaisesRegex(ValueError,'approval mismatch'):w.install(self.root,'0'*64)
            run.assert_not_called()

    def test_port_validation(self):
        for pair in [(80,17301),(17300,17300),(17300,49152),(True,17301),('17300',17301)]:
            with self.assertRaises(ValueError):w.validate_ports(*pair)
        w.validate_ports(17300,17301)
    def test_occupied_port_holds(self):
        import socket
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));sock.listen()
            port=sock.getsockname()[1]
            if not 1024 <= port <= 49151:self.skipTest('ephemeral port outside allowed range')
            with self.assertRaisesRegex(ValueError,'unavailable'):
                w.check_ports(port,17301 if port!=17301 else 17300)

if __name__=='__main__':unittest.main()
