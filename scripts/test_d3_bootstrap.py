import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import os
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run_d3_0228 as r
PROBE=HERE.parent/'tests/fixtures/0228-d3/d3_probe.py'
p=r.load(PROBE,'pinned_probe_for_test')

class BootstrapTests(unittest.TestCase):
    def test_exact_probe_inventory(self):
        ids=r.expected_ids(p)
        self.assertEqual(len(ids),230)
        self.assertEqual(len(set(ids)),230)
        self.assertIn('same_scope_nowait_contention',ids)
        self.assertIn('b_sample_settlements_cross_insert',ids)
    def test_role_statements(self):
        s='-- note; ignored\n'+';\n'.join(['CREATE ROLE '+x for x in ('owner','a','b','u')]+['CREATE DATABASE x','REVOKE CONNECT,TEMPORARY ON DATABASE x FROM PUBLIC','GRANT CONNECT ON DATABASE x TO a'])+';'
        self.assertEqual(len(r.bootstrap_statements(s)),7)
    def test_role_sql_extra_statement_denied(self):
        with self.assertRaises(r.Hold):r.bootstrap_statements('CREATE ROLE x; DROP DATABASE x;')
    def test_fresh_path(self):
        with tempfile.TemporaryDirectory() as d,patch.object(r,'BASE',Path(d)):
            r.fixed_paths(Path(d)/'core-0228-d3-source',Path(d)/'core-0228-d3')
    def test_existing_stage_denied(self):
        with tempfile.TemporaryDirectory() as d,patch.object(r,'BASE',Path(d)):
            root=Path(d)/'core-0228-d3';root.mkdir()
            with self.assertRaisesRegex(r.Hold,'FRESH_STAGE_HOLD'):r.fixed_paths(Path(d)/'core-0228-d3-source',root)
    def test_accepted_stage_denied(self):
        with tempfile.TemporaryDirectory() as d,patch.object(r,'BASE',Path(d)):
            with self.assertRaisesRegex(r.Hold,'ISOLATION_PATH_HOLD'):r.fixed_paths(Path(d)/'core-0228-d3-source',Path(d)/'core-0227-pg-retry2')
    def test_wrong_source_path_denied(self):
        with tempfile.TemporaryDirectory() as d,patch.object(r,'BASE',Path(d)):
            with self.assertRaisesRegex(r.Hold,'ISOLATION_PATH_HOLD'):r.fixed_paths(Path(d)/'core-0227-clean',Path(d)/'core-0228-d3')
    def test_root_symlink_denied(self):
        with tempfile.TemporaryDirectory() as d,patch.object(r,'BASE',Path(d)):
            target=Path(d)/'other';target.mkdir();root=Path(d)/'core-0228-d3';root.symlink_to(target,target_is_directory=True)
            with self.assertRaisesRegex(r.Hold,'ROOT_LINK_HOLD'):r.fixed_paths(Path(d)/'core-0228-d3-source',root)
    def test_child_without_ack_denied(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(r.Hold,'CHILD_ACK_HOLD'):r.child(Path('x'),Path('y'),'x')
    def test_child_wrong_path_denied(self):
        with patch.dict(os.environ,{'AICOS_D3_CHILD_ACK':r.ACK},clear=True):
            with self.assertRaisesRegex(r.Hold,'CHILD_PATH_HOLD'):r.child(Path('x'),Path('y'),'x')
    def test_safe_error(self):
        class PrivateError(Exception):sqlstate='42501'
        self.assertEqual(r.safe_error(PrivateError('private password')),{'type':'PrivateError','sqlstate':'42501'})
    def test_report_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'r.json';r.write(path,{'ok':True})
            with self.assertRaises(FileExistsError):r.write(path,{'ok':False})
    def test_input_hash_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'pg.lock').write_text('tamper')
            class H:E1_REVIEW='x';E1_LOCK='x';SERVER_HASH='x'
            with self.assertRaisesRegex(r.Hold,'ACCEPTED_INPUT_HASH_HOLD'):r.input_check(H,root,root)

if __name__=='__main__':unittest.main(verbosity=2)
