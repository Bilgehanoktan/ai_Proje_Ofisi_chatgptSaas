"""Runner mechanics only; not Memory, Gateway or product acceptance."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import run_archive as r


class ArchiveRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'root'
        self.stage=Path(self.tmp.name)/'stage'
        self.root.mkdir(); self.stage.mkdir()
        self.a=b'original memory\n'; self.b=b'original gateway\n'
        self.pins=[dict(path='app/memory.py',ref=r.MEMORY,blob=r.git_blob(self.a)),
                   dict(path='app/gateway.py',ref=r.GATEWAY,blob=r.git_blob(self.b))]
        for path,raw in [('app/memory.py',self.a),(r.OVERLAY+'/app/gateway.py',self.b)]:
            p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)

    def test_two_sources_preserve_exact_bytes(self):
        self.assertEqual(r.stage_sources(self.root,self.stage,self.pins),2)
        self.assertEqual((self.stage/'app/memory.py').read_bytes(),self.a)
        self.assertEqual((self.stage/'app/gateway.py').read_bytes(),self.b)
        self.assertFalse((self.root/'app/gateway.py').exists())

    def test_known_git_empty_blob(self):
        self.assertEqual(r.git_blob(b''),'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')

    def test_wrong_memory_blob(self):
        (self.root/'app/memory.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'SOURCE_BLOB_MISMATCH'): r.stage_sources(self.root,self.stage,self.pins)

    def test_wrong_gateway_blob(self):
        (self.root/r.OVERLAY/'app/gateway.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'SOURCE_BLOB_MISMATCH'): r.stage_sources(self.root,self.stage,self.pins)

    def test_missing_source(self):
        (self.root/r.OVERLAY/'app/gateway.py').unlink()
        with self.assertRaises(FileNotFoundError): r.stage_sources(self.root,self.stage,self.pins)

    def test_wrong_ref(self):
        with self.assertRaisesRegex(ValueError,'UNEXPECTED_SOURCE_REF'): r.stage_sources(self.root,self.stage,[dict(self.pins[0],ref='bad')])

    def test_path_escape_and_windows_alias(self):
        for path in ('../x','/x','a\\b','C:/x','a//b','a/./b','a/../b'):
            with self.subTest(path=path), self.assertRaises(ValueError): r.checked_path(self.stage,path)

    def test_case_duplicate(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_PATH_HOLD'): r.stage_sources(self.root,self.stage,[self.pins[0],dict(self.pins[0],path='APP/MEMORY.PY')])

    def test_pin_manifest_missing(self):
        with self.assertRaises(FileNotFoundError): r.load_pins(self.root)

    def test_original_test_pin_checked_before_child(self):
        with patch.object(r,'load_pins',return_value=self.pins), patch.object(r.subprocess,'call') as child:
            with self.assertRaises(FileNotFoundError): r.main(self.root)
            child.assert_not_called()

if __name__=='__main__': unittest.main(verbosity=2)
