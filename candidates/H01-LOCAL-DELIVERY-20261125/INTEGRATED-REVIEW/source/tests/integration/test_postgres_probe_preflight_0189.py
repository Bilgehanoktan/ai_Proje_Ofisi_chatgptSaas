"""Preflight tests only; these never run PostgreSQL."""
import importlib.util
from pathlib import Path
import tempfile
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('pg_probe', ROOT/'scripts/run_postgres_0189.py')
pg = importlib.util.module_from_spec(spec); spec.loader.exec_module(pg)


class PostgreSQLProbePreflight(TestCase):
    def test_pinned_ddl_and_outer_rollback(self):
        ddl=pg.DDL.read_bytes(); probe=pg.PROBE.read_bytes(); combined=pg.compose(ddl,probe)
        self.assertEqual(combined,ddl[:-len(b'ROLLBACK;\n')]+probe)
        self.assertTrue(combined.endswith(b'ROLLBACK;\n'))
        self.assertEqual(combined.count(b'\nBEGIN;\n'),1)
        self.assertNotIn(b'\nCOMMIT;',combined)

    def test_modified_ddl_refused(self):
        with self.assertRaisesRegex(ValueError,'PG_DDL_PIN_HOLD'):
            pg.compose(pg.DDL.read_bytes()+b' ',pg.PROBE.read_bytes())

    def test_missing_rollback_refused(self):
        with self.assertRaisesRegex(ValueError,'PG_PROBE_ROLLBACK_HOLD'):
            pg.compose(pg.DDL.read_bytes(),b'SELECT 1;\n')

    def test_no_binaries_refused(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(FileNotFoundError,'PG_BINARY_MISSING: initdb'):
            pg.binaries(Path(d))
