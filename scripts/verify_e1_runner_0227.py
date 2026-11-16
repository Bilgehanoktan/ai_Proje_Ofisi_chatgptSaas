"""Runner mechanics tests only; no AIOS product test or Windows acceptance."""
import importlib.util, json, os, pathlib, subprocess, sys, tempfile, unittest
p=pathlib.Path(__file__).with_name('run_e1_0227.py')
s=importlib.util.spec_from_file_location('e1',p); e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name)
    def result(self, body, expected=1):
        (self.root/'tests').mkdir();(self.root/'tests'/'demo.py').write_text('import unittest\nclass Tests(unittest.TestCase):\n'+body)
        log=self.root/'log.txt';code=e.run_logged([sys.executable,'-B','-c',e.TEST_DRIVER,'demo',expected],self.root,os.environ.copy(),log)
        return log,code
    def test_exact_success(self):
        log,code=self.result('    def test_one(self): self.assertEqual(1,1)\n')
        self.assertEqual(e.parse_result(log,'demo',1,code)['ran'],1)
    def test_wrong_count_rejected(self):
        log,code=self.result('    def test_one(self): pass\n',2)
        with self.assertRaises(ValueError):e.parse_result(log,'demo',2,code)
    def test_skip_rejected(self):
        log,code=self.result('    @unittest.skip("test")\n    def test_one(self): pass\n')
        with self.assertRaises(ValueError):e.parse_result(log,'demo',1,code)
    def test_failure_rejected(self):
        log,code=self.result('    def test_one(self): self.fail("test")\n')
        with self.assertRaises(ValueError):e.parse_result(log,'demo',1,code)
    def test_missing_marker_rejected(self):
        log=self.root/'log';log.write_text('OK\n')
        with self.assertRaises(ValueError):e.parse_result(log,'demo',1,0)
    def test_duplicate_marker_rejected(self):
        log,code=self.result('    def test_one(self): pass\n');log.write_bytes(log.read_bytes()*2)
        with self.assertRaises(ValueError):e.parse_result(log,'demo',1,code)
    def test_stage_extra_rejected(self):
        f=self.root/e.F;f.mkdir(parents=True);(f/'package-lock.json').touch();d=self.root/'database';d.mkdir();(d/'a.sql').touch()
        e.check_stage_clean(self.root,{}, {'database/a.sql':'ignored'});(d/'extra.sql').touch()
        with self.assertRaises(ValueError):e.check_stage_clean(self.root,{}, {'database/a.sql':'ignored'})
    def test_fresh_stage_only(self):
        src=self.root/'src';a0=self.root/'a0';src.mkdir();a0.mkdir();stage=self.root/'stage'
        e.fresh_dir(stage,src,a0)
        with self.assertRaises(ValueError):e.fresh_dir(stage,src,a0)
        with self.assertRaises(ValueError):e.fresh_dir(src/'nested',src,a0)
    def test_python_inventory(self):
        lock=self.root/'python.lock';log=self.root/'pip.json';rows=[{'name':f'package-{i}','version':'1.0'} for i in range(28)]
        lock.write_text(''.join(f"{r['name']}=={r['version']} --hash=sha256:"+'0'*64+'\n' for r in rows))
        log.write_text(json.dumps(rows+[{'name':'pip','version':'25.0'}]));e.check_python_inventory(lock,log)
        rows[0]['version']='2.0';log.write_text(json.dumps(rows))
        with self.assertRaises(ValueError):e.check_python_inventory(lock,log)
    def test_blob_mismatch_rejected(self):
        p=self.root/'file';p.write_bytes(b'abc');e.check_files(self.root,{'file':e.blob(p)})
        with self.assertRaises(ValueError):e.check_files(self.root,{'file':'0'*40})
if __name__=='__main__':unittest.main(verbosity=2)
