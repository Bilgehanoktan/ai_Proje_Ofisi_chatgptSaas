"""Synthetic isolated R2 certifi 2026.11.20 bridge tests; NOT formal W8 C07."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

APP = Path(__file__).with_name('w8_unified_u3_c50_r2_dev.py')
spec = importlib.util.spec_from_file_location('w8_u3_c50_dev',APP)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
SOURCE_ROOT = APP.parent / 'core0207_crypto50_r2'


class FakeW:
    MANIFEST_BLOB = m.ORIGINAL_MANIFEST
    def __init__(self, mode='pass'):
        self.mode=mode
        self.subprocesses=[]
        self.run=self.base_run
        self.verify_aux=self.base_aux
        self.test=self.base_test
        self.smoke=self.base_smoke
    def checked_path(self,root,rel):
        return root / rel
    def base_aux(self,root):
        return {'preexisting.pin':'abcdef'}
    def python(self,stage):
        return stage/'.venv/Scripts/python.exe'
    def reviewed(self, stage, approval):
        assert approval==m.APPROVED_REVIEW_SHA256
    def installed(self,stage,approval):
        assert approval==m.APPROVED_REVIEW_SHA256
    def base_run(self, args, cwd, env=None):
        self.subprocesses.append(list(map(str,args)))
        if len(args)>2 and str(args[2]).endswith('run_core0207_c50_r2.py'):
            output=Path(args[-1])
            if self.mode=='missing_report':return
            payload={'status':'PASS','passed':29,'source_files_verified':55,
                'contract_pin':m.SOURCE_BLOBS[m.VERSIONED_CONTRACT],
                'stage_review_sha256':m.APPROVED_REVIEW_SHA256,
                'immutable_stage_guards_preserved':True,
                'W8_C07':'HOLD','suite_classification':'VERSIONED_LOCAL_D0_CANDIDATE_NOT_W8_C07',
                'dependency_versions':{'cryptography':'50.0.2'}}
            if self.mode=='bad_report':payload['passed']=28
            output.write_text(json.dumps(payload))
    def base_test(self, stage, approval):
        # Mimic the *original* P10J24 nested hook after source history materialization.
        with tempfile.TemporaryDirectory(prefix='aicos-p10j24-history-') as tmp:
            path=Path(tmp)
            orig_run=self.run
            def p24_hook(args,cwd,env=None):
                if len(args)>1 and str(args[1]) == str(stage/m.ORIGINAL_P24):
                    # The original P10J24 changes index 3 from stage to historic temp.
                    changed=list(args)
                    changed[3]=path
                    return orig_run(changed,cwd,env)
                return orig_run(args,cwd,env)
            self.run=p24_hook
            try:
                self.run([str(self.python(stage)),str(stage/m.ORIGINAL_P24),'--source',str(stage),'--report',str(stage/'core29-p10f.json')],stage,{})
            finally:
                self.run=orig_run
            if self.mode=='duplicate':
                self.run([str(self.python(stage)),str(stage/m.ORIGINAL_P24),'--source',str(path),'--report',str(stage/'core29-p10f.json')],stage,{})
        (stage/'BUILD_TEST_OK').write_text(approval,encoding='utf-8')
        return 'FULL_W8_INHERITED_TESTS_SUCCEEDED_MOCK'
    def base_smoke(self,*args,**kwargs):
        return 'NO_SMOKE'


def make_fixture(tmp, missing_aux=None):
    stage=Path(tmp)/'root'/'stage'
    stage.mkdir(parents=True)
    for name in ('CONTRACT.json', 'run_core0207_c50_r2.py'):
        src = SOURCE_ROOT / name
        target = stage / 'tests/integration/core0207_crypto50_r2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(src.read_bytes())
    if missing_aux:
        (stage/missing_aux).unlink()
    return stage


class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.stage=make_fixture(self.t.name)
    def tearDown(self):self.t.cleanup()
    def wrapped(self,mode='pass'):
        w=FakeW(mode)
        return m.extend(w)
    def test_exact_new_auxiliary_pins(self):
        w=self.wrapped()
        pins=w.verify_aux(self.stage)
        self.assertEqual(pins[m.VERSIONED_RUNNER],m.SOURCE_BLOBS[m.VERSIONED_RUNNER])
        self.assertEqual(pins[m.VERSIONED_CONTRACT],m.SOURCE_BLOBS[m.VERSIONED_CONTRACT])
    def test_success_development_only_with_no_acceptance_markers(self):
        w=self.wrapped()
        result=w.test(self.stage,m.APPROVED_REVIEW_SHA256)
        self.assertIn('SUCCEEDED_MOCK',result)
        for x in m.MARKERS:self.assertFalse((self.stage/x).exists())
        self.assertFalse((self.stage/'core29-p10f.json').exists())
        info=json.loads((self.stage.parent/m.DEV_SUMMARY_NAME).read_text())
        self.assertIn('NOT_C07_ACCEPTANCE',info['classification'])
        self.assertEqual(info['W8_C07'],'HOLD_PENDING_OWNER_SECURITY_REVIEW')
        self.assertEqual(len(w.subprocesses),1)
        self.assertIn('--runner-root',w.subprocesses[0])
        root_index=w.subprocesses[0].index('--runner-root')
        self.assertEqual(w.subprocesses[0][root_index+1],str(APP.resolve().parent))
        self.assertEqual(w.run,w.base_run)
    def test_original_smoke_is_rejected(self):
        w=self.wrapped()
        with self.assertRaisesRegex(ValueError,'C08_FORBIDDEN'):
            w.smoke(self.stage,m.APPROVED_REVIEW_SHA256,None)
    def test_stale_markers_rejected(self):
        w=self.wrapped()
        (self.stage/'BUILD_TEST_OK').write_text('stale')
        with self.assertRaisesRegex(ValueError,'NONFRESH_STAGE_MARKER_HOLD'):
            w.test(self.stage,m.APPROVED_REVIEW_SHA256)
    def test_wrong_review_fingerprint_rejected(self):
        w=self.wrapped()
        with self.assertRaisesRegex(ValueError,'C06_REVIEW_APPROVAL_HOLD'):
            w.test(self.stage,'0'*64)
    def test_missing_runner_rejected(self):
        (self.stage/m.VERSIONED_RUNNER).unlink()
        w=self.wrapped()
        with self.assertRaisesRegex(ValueError,'SOURCE_PIN_HOLD'):
            w.test(self.stage,m.APPROVED_REVIEW_SHA256)
    def test_bad_report_failclosed_and_no_marker(self):
        w=self.wrapped('bad_report')
        with self.assertRaisesRegex(ValueError,'REPORT_CONTENT_HOLD'):
            w.test(self.stage,m.APPROVED_REVIEW_SHA256)
        self.assertFalse((self.stage/'BUILD_TEST_OK').exists())
        self.assertFalse((self.stage.parent/m.DEV_SUMMARY_NAME).exists())
        self.assertEqual(w.run,w.base_run)
    def test_missing_report_failclosed(self):
        w=self.wrapped('missing_report')
        with self.assertRaisesRegex(ValueError,'REPORT_MISSING_HOLD'):
            w.test(self.stage,m.APPROVED_REVIEW_SHA256)
        self.assertFalse((self.stage/'BUILD_TEST_OK').exists())
    def test_duplicate_original_runner_call_rejected(self):
        w=self.wrapped('duplicate')
        with self.assertRaisesRegex(ValueError,'DUPLICATE_OR_LEGACY_REPORT_HOLD'):
            w.test(self.stage,m.APPROVED_REVIEW_SHA256)
        self.assertFalse((self.stage/'BUILD_TEST_OK').exists())
    def test_cannot_reuse_report(self):
        (self.stage.parent/m.DEV_REPORT_NAME).write_text('old')
        w=self.wrapped()
        with self.assertRaisesRegex(ValueError,'DEV_REPORT_EXISTS_HOLD'):
            w.test(self.stage,m.APPROVED_REVIEW_SHA256)
    def test_legacy_script_never_called(self):
        w=self.wrapped()
        w.test(self.stage,m.APPROVED_REVIEW_SHA256)
        self.assertFalse(any('run_core_0207.py' in ' '.join(x) for x in w.subprocesses))


    def test_certifi_2026_11_20_new_review_pin(self):
        self.assertEqual(m.APPROVED_REVIEW_SHA256,
            'a5d5751047206186fad92098341c1f351648a8b012adc24df7dd83869a388009')
        self.assertNotEqual(m.APPROVED_REVIEW_SHA256,
            '341e179afda3e344ac32b3f4643860e44c7dd350cfb66ac59ac5edc98c79a1b3')
    def test_r2_preserves_security_gates(self):
        w=self.wrapped()
        with self.assertRaisesRegex(ValueError,'C08_FORBIDDEN'):
            w.smoke(self.stage,m.APPROVED_REVIEW_SHA256,None)
        self.assertEqual(m.SOURCE_BLOBS[m.VERSIONED_RUNNER],
                         '83e2111d4e155b8fd7487bfbde2301aefad80e42')
        self.assertEqual(m.SOURCE_BLOBS[m.VERSIONED_CONTRACT],
                         'e48c5855d70860cbc35442e1898780839c79b214')


if __name__=='__main__':unittest.main(verbosity=2)
