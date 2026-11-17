import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import run_isolated_pg as m

class Launcher(unittest.TestCase):
    def test_env(self):
        with patch.dict(os.environ,{'PGHOST':'remote','pgpassword':'secret','PYTHONPATH':'bad','NORMAL':'ok'},clear=True):
            self.assertEqual(m.safe_env(),{'NORMAL':'ok','PGCLIENTENCODING':'UTF8'})
    def test_port_reserved(self):
        for p in (5432,55433,0,True,65536):
            with self.subTest(p=p),self.assertRaises(m.Hold): m.validate_port(p)
    def test_wrong_cluster(self):
        with self.assertRaises(m.Hold): m.verify_location('core\t170012\torg_r5_admin\t/tmp/x',Path('/tmp/x'))
    def test_wrong_version(self):
        with self.assertRaises(m.Hold): m.verify_location(m.CLUSTER+'\t160012\torg_r5_admin\t/tmp/x',Path('/tmp/x'))
    def test_wrong_admin(self):
        with self.assertRaises(m.Hold): m.verify_location(m.CLUSTER+'\t170012\tother\t/tmp/x',Path('/tmp/x'))
    def test_wrong_data(self):
        with self.assertRaises(m.Hold): m.verify_location(m.CLUSTER+'\t170012\torg_r5_admin\t/tmp/core',Path('/tmp/x'))
    def test_correct_data(self): m.verify_location(m.CLUSTER+'\t170012\torg_r5_admin\t/tmp/x\n',Path('/tmp/x'))
    def test_multiple_query_rows(self):
        with self.assertRaises(m.Hold): m.verify_location('x\ny',Path('/tmp/x'))
    def test_admin_rejected_before_child(self):
        with patch.object(m,'non_admin',return_value=False),patch.object(m,'child') as c:
            with self.assertRaisesRegex(m.Hold,'NON_ADMIN'): m.launch(Path('.'),Path('.'),Path('.'),55435)
            c.assert_not_called()
    def test_reviewer_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'review.py'; p.write_text('tamper')
            with self.assertRaisesRegex(m.Hold,'R5R2_REVIEW_HASH'): m.verify_reviewer(p)
    def test_reviewer_missing(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(m.Hold,'R5R2_REVIEW_MISSING'): m.verify_reviewer(Path(d)/'missing')
    def test_wrong_driver(self):
        with patch.object(m,'child',return_value='3.3.8\n'),self.assertRaises(m.Hold): m.verify_driver()
    def test_pg17(self):
        with patch.object(m,'child',return_value='psql (PostgreSQL) 17.8\n'): m.verify_version('psql')
    def test_pg16(self):
        with patch.object(m,'child',return_value='psql (PostgreSQL) 16.8\n'),self.assertRaises(m.Hold): m.verify_version('psql')
    def test_child_nonzero(self):
        with patch.object(m.subprocess,'run',return_value=type('Result',(),{'returncode':7})()),self.assertRaisesRegex(m.Hold,'CHILD_EXIT_7'): m.child(['x'])
    def scenario(self,fail=None):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); candidates=root/'candidates'; candidates.mkdir(); r2=candidates/'ORG-05R5R2'; r2.mkdir(); (r2/'review_pg_evidence.py').touch()
            stage_parent=root/'stages'; stage_parent.mkdir(); calls=[]
            def fake_child(args,**kw):
                calls.append(args)
                if fail and any(fail in str(x) for x in args): raise m.Hold('INJECTED')
                if '-c' in args and 'current_setting' in args[-1]:
                    d=next(stage_parent.iterdir())/'data'
                    return f'{m.CLUSTER}\t170012\t{m.ADMIN}\t{d}\n'
            with patch.object(m,'non_admin',return_value=True),patch.object(m,'verify_reviewer'),patch.object(m,'verify_driver'),patch.object(m,'verify_version'),patch.object(m,'validate_port'),patch.object(m,'executable',side_effect=lambda _,name:name),patch.object(m,'child',side_effect=fake_child),patch('builtins.print'):
                if fail:
                    with self.assertRaises(m.Hold): m.launch(candidates,root,stage_parent,55435)
                else:
                    report=m.launch(candidates,root,stage_parent,55435); self.assertEqual(report.name,'ORG_R5_PG_RESULT.json')
            return calls,list(stage_parent.iterdir())
    def test_sequence(self):
        calls,stages=self.scenario(); self.assertEqual(len(stages),1)
        self.assertEqual(len(calls),9); self.assertIn('initdb',calls[1]); self.assertIn('start',calls[2]); self.assertIn('-c',calls[3]); self.assertTrue(calls[4][-1].endswith('bootstrap_roles.sql')); self.assertTrue(calls[5][-1].endswith('PG_SCHEMA_R4.sql')); self.assertIn('--execute-disposable',calls[6]); self.assertIn('--report',calls[7]); self.assertIn('stop',calls[8]); self.assertNotIn('5432',str(calls))
    def test_preflight_failure_no_stage(self):
        calls,stages=self.scenario('review_pg_evidence.py'); self.assertEqual(len(calls),1); self.assertEqual(stages,[])
    def test_init_failure_preserves_stage(self):
        calls,stages=self.scenario('initdb'); self.assertEqual(len(stages),1); self.assertEqual(len(calls),2)
    def test_bootstrap_failure_no_schema_or_retry(self):
        calls,stages=self.scenario('bootstrap_roles.sql'); self.assertEqual(len(stages),1); self.assertEqual(len(calls),5)
    def test_runner_failure_no_review_or_stop(self):
        calls,stages=self.scenario('run_pg_acceptance.py'); self.assertEqual(len(stages),1); self.assertEqual(len(calls),7)

if __name__=='__main__': unittest.main(verbosity=2)
