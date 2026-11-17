import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import getpass
import launch_disposable as m

class AuthTests(unittest.TestCase):
    def test_password(self):
        with patch.object(m.getpass,'getpass',return_value='fixture-secret'):
            self.assertEqual(m.read_admin_password(),'fixture-secret')
    def test_empty_password(self):
        with patch.object(m.getpass,'getpass',return_value=''):
            with self.assertRaisesRegex(m.Hold,'ADMIN_PASSWORD_REQUIRED'):
                m.read_admin_password()
    def test_no_echo_fallback(self):
        import warnings
        def unsafe(*args):
            warnings.warn('no terminal',getpass.GetPassWarning)
            return 'secret'
        with patch.object(m.getpass,'getpass',side_effect=unsafe):
            with self.assertRaises(getpass.GetPassWarning): m.read_admin_password()
    def test_environment_copy(self):
        env={'OTHER':'keep'}
        self.assertEqual(m.admin_env(env,'fixture-secret'),{'OTHER':'keep','PGPASSWORD':'fixture-secret','PGCLIENTENCODING':'UTF8'})
        self.assertEqual(env,{'OTHER':'keep'})
    def test_empty_environment(self):
        with self.assertRaisesRegex(m.Hold,'ADMIN_PASSWORD_REQUIRED'): m.admin_env({},'')
    def test_recovery_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); stage=root/'org'; stage.mkdir(); report=root/'r.json'
            (stage/'PG_VERSION').write_text('17\n')
            m.validate_recovery(stage,report)
            report.touch()
            with self.assertRaisesRegex(m.Hold,'RECOVERY_REPORT_EXISTS'): m.validate_recovery(stage,report)
    def test_recovery_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); stage=root/'org'; stage.mkdir(); (stage/'PG_VERSION').write_text('16\n')
            with self.assertRaisesRegex(m.Hold,'RECOVERY_PG17_REQUIRED'): m.validate_recovery(stage,root/'r.json')
    def test_recovery_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            with self.assertRaisesRegex(m.Hold,'RECOVERY_STAGE_REQUIRED'): m.validate_recovery(root/'org',root/'r.json')
    def test_modes_exclusive(self):
        with self.assertRaises(SystemExit) as e:
            m.main(['--pg-bin','x','--stage','y','--report','z','--stop-verified-stage','--execute-disposable'])
        self.assertEqual(e.exception.code,2)

if __name__ == '__main__': unittest.main()
