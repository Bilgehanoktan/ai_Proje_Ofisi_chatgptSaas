import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import launch_disposable as m

class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.stage = self.root / 'org'
        self.report = self.root / 'report.json'
    def test_fresh(self):
        m.validate_paths(self.stage, self.report)
    def test_existing_stage(self):
        self.stage.mkdir()
        with self.assertRaisesRegex(m.Hold, 'FRESH'):
            m.validate_paths(self.stage, self.report)
    def test_existing_report(self):
        self.report.touch()
        with self.assertRaisesRegex(m.Hold, 'FRESH'):
            m.validate_paths(self.stage, self.report)
    def test_relative(self):
        with self.assertRaisesRegex(m.Hold, 'ABSOLUTE'):
            m.validate_paths(Path('org'), self.report)
    def test_same_path(self):
        with self.assertRaisesRegex(m.Hold, 'OVERLAP'):
            m.validate_paths(self.stage, self.stage)
    def test_missing_parent(self):
        with self.assertRaisesRegex(m.Hold, 'PARENT'):
            m.validate_paths(self.stage, self.stage / 'report.json')
    def test_version(self):
        self.assertEqual(m.parse_version('psql (PostgreSQL) 17.12\n'), 170012)
    def test_wrong_version(self):
        with self.assertRaisesRegex(m.Hold, 'PG17'):
            m.parse_version('psql (PostgreSQL) 18.1')
    def identity(self):
        return '|'.join([m.CLUSTER, str(m.PORT), '170012', str(self.stage), m.ADMIN, m.ADMIN, '127.0.0.1'])
    def test_identity(self):
        m.verify_identity(self.identity(), self.stage, 170012)
    def test_d4_port_rejected(self):
        with self.assertRaisesRegex(m.Hold, 'IDENTITY_CLUSTER_PORT_VERSION'):
            m.verify_identity(self.identity().replace('55435','55434'), self.stage, 170012)
    def test_wrong_stage(self):
        with self.assertRaisesRegex(m.Hold, 'DATA_DIRECTORY'):
            m.verify_identity(self.identity(), self.root / 'other', 170012)
    def test_wrong_role(self):
        with self.assertRaisesRegex(m.Hold, 'ADMIN_LOOPBACK'):
            m.verify_identity(self.identity().replace(m.ADMIN, 'postgres'), self.stage, 170012)
    def test_pg_environment_removed(self):
        with patch.dict(os.environ, {'PGPASSWORD':'synthetic','PGHOST':'bad','OTHER':'keep'}, clear=True):
            self.assertEqual(m.env_without_pg(), {'OTHER':'keep'})
    def test_port_in_use(self):
        with patch.object(m.socket, 'socket', side_effect=OSError('busy')):
            with self.assertRaisesRegex(m.Hold, '55435'):
                m.check_port()

if __name__ == '__main__':
    unittest.main()
