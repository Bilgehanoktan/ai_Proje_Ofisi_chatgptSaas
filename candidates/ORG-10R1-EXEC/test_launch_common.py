import hashlib, io, json, os, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
import launch_common as m

ROOT=Path(__file__).resolve().parents[1]/'ORG-10-COMMON-SCOPE'
MATRIX=json.loads((ROOT/'PG_ACCEPTANCE_MATRIX.json').read_text())
PINS={'example.py':'a'*64}

def report():
    h='a'*64
    details=[{'tables':12,'policies':25,'cluster':m.CLUSTER},{'revision':h,'loser':['sqlstate','23505']},h,h,{'sqlstate':'23514','counts':[0,0]},{'same_scope':'55P03','other_scope':'PASS'},{'count':1,'head':h,'loser':['hold','HISTORY_CAS']},'HISTORY_CAS',{'count':2,'head':h},None,None,'42501','42501','42501','23503','42501','42501',{'reader':'42501','unmapped':'42501'},'TASK_REFERENCE',h,'STALE_ORG',None,'STALE_HEAD',None,'HEAD_MISMATCH',None,'42501','42501','42501',{'tables':12,'reader_matches':True,'other_scope_hidden':True},{'tables':12,'roles':4,'checks':360}]
    return dict(profile='ORG10_COMMON_SCOPE_DISPOSABLE_ONLY',driver='3.3.9',source_pins=PINS,schema_sha256='3a520ee1277c903eb6be4e704ce2c6d8ff749356f1d2537c7883887d14246a1a',status='PASS_DISPOSABLE_FIXTURE_ONLY',checks=[dict(id=c['id'],status='PASS',detail=d,elapsed_ms=1) for c,d in zip(MATRIX['checks'],details)])

class Review(unittest.TestCase):
    def check(self,r): return m.review_report(m.canonical_json(r),MATRIX,PINS)
    def test_valid(self):
        x=self.check(report()); self.assertEqual(x['passed'],31);self.assertEqual(x['product'],'HOLD');self.assertEqual(x['custody'],'UNATTESTED')
    def test_reject_detail(self):
        for index in range(31):
            with self.subTest(index=index):
                r=report();r['checks'][index]['detail']='invalid'
                with self.assertRaises(m.Hold):self.check(r)
    def test_reject_order(self):
        r=report();r['checks'][0],r['checks'][1]=r['checks'][1],r['checks'][0]
        with self.assertRaises(m.Hold):self.check(r)
    def test_reject_missing(self):
        r=report();r['checks'].pop()
        with self.assertRaises(m.Hold):self.check(r)
    def test_reject_failure(self):
        r=report();r['checks'][3]['status']='FAIL'
        with self.assertRaises(m.Hold):self.check(r)
    def test_reject_unknown_field(self):
        r=report();r['authority']=True
        with self.assertRaises(m.Hold):self.check(r)
    def test_reject_pin(self):
        r=report();r['source_pins']={}
        with self.assertRaises(m.Hold):self.check(r)
    def test_reject_bool_count(self):
        r=report();r['checks'][6]['detail']['count']=True
        with self.assertRaises(m.Hold):self.check(r)
    def test_reject_bool_acl(self):
        r=report();r['checks'][29]['detail']['reader_matches']=1
        with self.assertRaises(m.Hold):self.check(r)
    def test_reject_duplicate_json(self):
        with self.assertRaises(m.Hold):m.strict_json(b'{"x":1,"x":2}')
    def test_reject_nan(self):
        with self.assertRaises(m.Hold):m.strict_json(b'{"x":NaN}')
    def test_reject_size(self):
        with self.assertRaises(m.Hold):m.review_report(b' '*65537,MATRIX,PINS)

class Preflight(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
    def test_tree(self):self.assertEqual(m.git_tree({'a':b'x'}),m.object_hash('tree',b'100644 a\0'+bytes.fromhex(m.object_hash('blob',b'x'))))
    def test_path_traversal(self):
        for name in ('../x','a/../../b','CON.txt','a\\b','a.','a/','/a'):
            with self.subTest(name=name),self.assertRaises(m.Hold):m.safe_components(name)
    def archive(self,entries):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            for n,v in entries:z.writestr('root/'+n,v)
        return b.getvalue()
    def test_archive(self):self.assertEqual(m.read_archive(self.archive([('a',b'x')]),'root',1,1),{'a':b'x'})
    def test_archive_case(self):
        with self.assertRaises(m.Hold):m.read_archive(self.archive([('a',b'x'),('A',b'x')]),'root',2,2)
    def test_archive_size(self):
        with self.assertRaises(m.Hold):m.read_archive(self.archive([('a',b'x')]),'root',1,2)
    def test_archive_tree_mismatch(self):
        p=self.root/'a.zip';p.write_bytes(b'x')
        with patch.object(m,'read_archive',return_value={'a':b'x'}),self.assertRaises(m.Hold):m.read_exact(p)
    def test_materialize_and_drift(self):
        p=self.root/'s'; files={'a/b':b'x'};t=m.git_tree(files);m.materialize(files,p,t);(p/'a/b').write_bytes(b'y')
        with self.assertRaises(m.Hold):m.verify_materialized(files,p,t)
    def test_existing_path(self):
        p=self.root/'a';p.touch()
        with self.assertRaises(m.Hold):m.fresh(p)
    def test_overlap(self):
        p=self.root/'a'
        with self.assertRaises(m.Hold):m.validate_paths(p,p,self.root/'manifest')
    def test_version(self):self.assertEqual(m.parse_version('postgres (PostgreSQL) 17.12'),170012)
    def test_version_other(self):
        with self.assertRaises(m.Hold):m.parse_version('postgres (PostgreSQL) 17.13')
    def test_identity(self):
        s=self.root/'stage';s.mkdir();(s/'postmaster.pid').write_text(f'42\n{s}\n0\n55436\n')
        out=f'{m.CLUSTER}|55436|170012|{s}|{m.ADMIN}|{m.ADMIN}|127.0.0.1|127.0.0.1|postgres|UTF8'
        m.identity(out,s,'postgres')
        for bad in (out.replace('55436','55435'),out.replace('|postgres|','|other|'),out.replace('127.0.0.1','192.0.2.1')):
            with self.assertRaises(m.Hold):m.identity(bad,s,'postgres')
    def test_pid_mismatch(self):
        s=self.root/'stage';s.mkdir();(s/'postmaster.pid').write_text(f'42\n{s}\n0\n55435\n')
        with self.assertRaises(m.Hold):m.identity(f'{m.CLUSTER}|55436|170012|{s}|{m.ADMIN}|{m.ADMIN}|127.0.0.1|127.0.0.1|postgres|UTF8',s,'postgres')
    def test_clean_env(self):
        with patch.dict(os.environ,{'PGPASSWORD':'x','PYTHONPATH':'x','TEST_KEEP':'y'},clear=True):self.assertEqual(m.clean_env(),{'TEST_KEEP':'y'})
    def test_preflight_no_exec(self):
        p=self.root/'manifest.json'; args=['--archive',str(self.root/'a.zip'),'--pg-bin',str(self.root/'bin'),'--manifest',str(p)]
        with patch.object(m,'read_exact',return_value=({'x':b'y'},'a'*64)),patch.object(m,'fingerprint',return_value={'synthetic':1}),patch.object(m,'check_port'),patch.object(m.subprocess,'run') as run:
            self.assertEqual(m.main(args),0);run.assert_not_called();self.assertEqual(p.read_bytes(),m.canonical_json({'synthetic':1}))
    def test_execute_review_mismatch(self):
        p=self.root/'manifest.json';p.write_bytes(m.canonical_json({'synthetic':1})); args=['--archive',str(self.root/'a.zip'),'--pg-bin',str(self.root/'bin'),'--manifest',str(p),'--stage',str(self.root/'stage'),'--evidence',str(self.root/'evidence'),'--execute-disposable','--reviewed-fingerprint','0'*64]
        with patch.object(m,'read_exact',return_value=({'x':b'y'},'a'*64)),patch.object(m,'fingerprint',return_value={'synthetic':1}),patch.object(m,'check_port'),patch.object(m.subprocess,'run') as run:
            self.assertEqual(m.main(args),2);run.assert_not_called();self.assertFalse((self.root/'stage').exists())

class MockExecution(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        self.stage=self.root/'stage';self.evidence=self.root/'evidence';self.manifest=self.root/'manifest.json';self.inventory={'fixture':True};self.manifest.write_bytes(m.canonical_json(self.inventory));self.calls=[]
    def execute(self, fail=False):
        from contextlib import ExitStack
        from types import SimpleNamespace
        args=['--archive',str(self.root/'a.zip'),'--pg-bin',str(self.root/'bin'),'--manifest',str(self.manifest),'--stage',str(self.stage),'--evidence',str(self.evidence),'--execute-disposable','--reviewed-fingerprint',m.sha256(self.manifest.read_bytes())]
        def materialize(files,root,tree):
            p=root/m.CANDIDATE;p.mkdir(parents=True);(p/'PG_ACCEPTANCE_MATRIX.json').write_bytes(m.canonical_json(MATRIX))
        def child(cmd,**kw):
            self.calls.append((cmd,kw));name=Path(cmd[0]).stem;out=None
            if '--version' in cmd:out=f'{name} (PostgreSQL) 17.12'
            elif name=='initdb':self.stage.mkdir()
            elif name=='pg_ctl' and 'start' in cmd:(self.stage/'postmaster.pid').write_text(f'42\n{self.stage}\n0\n55436\n')
            elif name=='psql' and '-c' in cmd:
                db=cmd[cmd.index('-d')+1];sql=cmd[-1]
                out='48|0' if 'MAINTAIN' in sql else f'{m.CLUSTER}|55436|170012|{self.stage}|{m.ADMIN}|{m.ADMIN}|127.0.0.1|127.0.0.1|{db}|UTF8'
            elif any(x.endswith('/run_pg_acceptance.py') for x in cmd):
                if fail:raise m.subprocess.CalledProcessError(1,cmd)
                (self.evidence/'pg_report.json').write_bytes(m.canonical_json(report()))
            return SimpleNamespace(stdout=out)
        with ExitStack() as stack:
            for key,value in [('read_exact',({'a':b'x'},'a'*64)),('fingerprint',self.inventory),('source_r3_pins',PINS)]:stack.enter_context(patch.object(m,key,return_value=value))
            for key in ('check_port','non_admin','verify_materialized'):stack.enter_context(patch.object(m,key))
            stack.enter_context(patch.object(m,'materialize',side_effect=materialize));stack.enter_context(patch.object(m.sys.stdin,'isatty',return_value=True));stack.enter_context(patch.object(m.getpass,'getpass',return_value='fixture-secret'));stack.enter_context(patch.object(m.subprocess,'run',side_effect=child))
            return m.main(args)
    def test_mock_full_order(self):
        self.assertEqual(self.execute(),0);r=json.loads((self.evidence/'launch_report.json').read_text());self.assertEqual(r['status'],'COMPLETE_REPORT_UNATTESTED');self.assertEqual(r['review']['passed'],31);self.assertEqual(r['supplemental_maintain_acl'],{'checks':48,'granted':0});self.assertEqual(r['events'][-1],'SERVER_STOPPED')
        self.assertFalse(any('fixture-secret' in x for cmd,_ in self.calls for x in cmd));self.assertTrue(all('55435' not in x for cmd,_ in self.calls for x in cmd));self.assertNotIn('fixture-secret',str(r))
        self.assertTrue(any('-X' in cmd and 'utf8' in cmd and any(x.endswith('run_pg_acceptance.py') for x in cmd) for cmd,_ in self.calls))
    def test_mock_failure_preserves_stage(self):
        self.assertEqual(self.execute(True),2);self.assertTrue(self.stage.is_dir());r=json.loads((self.evidence/'launch_report.json').read_text());self.assertEqual(r['status'],'FAIL_OR_INCOMPLETE');self.assertFalse(any('stop' in cmd for cmd,_ in self.calls));self.assertEqual(r['product'],'HOLD')

if __name__=='__main__':unittest.main(verbosity=2)
