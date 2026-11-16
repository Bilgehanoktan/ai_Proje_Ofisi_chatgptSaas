import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch
from tempfile import TemporaryDirectory

p=Path(__file__).resolve().parents[1]/'scripts/run_pg_acceptance_0215.py'
spec=importlib.util.spec_from_file_location('pg_runner',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class RunnerTests(TestCase):
    def setUp(self):
        self.info={'host':'127.0.0.1','dbname':'aicos_d0_0194_lab','user':'lab','password':'secret'}
        self.prefix='aicos_d0_0194_'
        self.result={'ran':5,'failures':[],'errors':[],'skips':[],'expected_failures':0,'unexpected_successes':0}
    def proc(self,**changes):
        r={**self.result,**changes};return SimpleNamespace(stdout=m.MARKER+json.dumps(r),returncode=0)
    def test_suite_counts(self): self.assertEqual([s[-1] for s in m.SUITES],[5,5,3])
    def test_valid_local_dsn(self): self.assertEqual(m.validate_info(self.info,self.prefix),('aicos_d0_0194_lab','lab'))
    def test_remote_and_socket_rejected(self):
        for host in ['localhost','example.com','/tmp','127.0.0.1,example.com']:
            with self.subTest(host=host),self.assertRaises(ValueError): m.validate_info({**self.info,'host':host},self.prefix)
    def test_indirect_dsn_options_rejected(self):
        for key in ('service','hostaddr','options','passfile','sslcert'):
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate_info({**self.info,key:'x'},self.prefix)
    def test_bad_db_role_port(self):
        for d in ({'dbname':'prod'},{'dbname':'aicos_d0_0196l_lab'},{'user':''},{'port':'0'},{'port':'65536'},{'sslmode':'require'},{'connect_timeout':'0'}):
            with self.subTest(d=d),self.assertRaises(ValueError):m.validate_info({**self.info,**d},self.prefix)
    def test_child_env_sanitizes(self):
        e=m.child_env({'PATH':'p','PGHOST':'remote','PGPASSWORD':'old','OPENAI_API_KEY':'secret','PYTHONPATH':'fake','AICOS_D0_PG_ACK':'bad'},'dsn','ack',Path('/repo'))
        for k in ('PGHOST','PGPASSWORD','OPENAI_API_KEY'): self.assertNotIn(k,e)
        self.assertEqual(e['AICOS_D0_PG_ACK'],'ack');self.assertEqual(e['PGPASSFILE'],os.devnull)
        self.assertEqual(e['PYTHONPATH'],os.pathsep.join(('/repo','/repo/tests')))
    def test_five_actual_successes(self):self.assertEqual(m.classify(self.proc(),5)['status'],'PASS')
    def test_skip_not_pass(self):self.assertEqual(m.classify(self.proc(skips=['skip']),5)['status'],'HOLD')
    def test_short_or_zero_run_not_pass(self):
        for n in (0,4,6):self.assertEqual(m.classify(self.proc(ran=n),5)['status'],'HOLD')
    def test_failure_error_expected_failure_not_pass(self):
        for d in ({'failures':['f']},{'errors':['e']},{'expected_failures':1},{'unexpected_successes':1}):self.assertEqual(m.classify(self.proc(**d),5)['status'],'HOLD')
    def test_nonzero_exit_not_pass(self):
        p=self.proc();p.returncode=1;self.assertEqual(m.classify(p,5)['status'],'HOLD')
    def test_duplicate_or_malformed_marker(self):
        for stdout in ('none',m.MARKER+'[]',m.MARKER+'{}',self.proc().stdout+'\n'+self.proc().stdout):
            self.assertEqual(m.classify(SimpleNamespace(stdout=stdout,returncode=0),5)['status'],'HOLD')
    def test_pin_check_rejects_missing_ddl(self):
        with TemporaryDirectory() as d,self.assertRaises(ValueError):m.check_ddl(Path(d))
    def test_preflight_cannot_run_unverified_source(self):
        with TemporaryDirectory() as d,patch.object(m.subprocess,'run') as call:
            r=m.run(Path(d),'0'*40,{'AICOS_PG_RUN_ACK':'0215_DISPOSABLE_LOCAL_ONLY'},execute=True)
            self.assertEqual(r['actual_pg'],'NOT_RUN');self.assertFalse(r['source_verified']);call.assert_not_called()

if __name__=='__main__':main()
