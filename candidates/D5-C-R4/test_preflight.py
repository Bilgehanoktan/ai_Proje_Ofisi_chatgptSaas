import tempfile
import unittest
from pathlib import Path
import run_pg_expiry as r

class Preflight(unittest.TestCase):
    def test_original_source(self):
        t = r.load_transport(Path(r.__file__).with_name('postgres_session.original.py'))
        self.assertTrue(callable(t.postgres_transaction))
    def test_source_drift(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'transport.py'; p.write_text('changed')
            with self.assertRaisesRegex(ValueError,'SOURCE_PIN_HOLD'):
                r.load_transport(p)
    def test_reserved_ports(self):
        for p in (5432,55432,55434,55435,55436,0,65536,True):
            with self.subTest(port=p), self.assertRaises(ValueError):
                r.validate_target(p,'d5c_r4_db','d5c_r4_role')
    def test_wrong_db_or_role(self):
        for db,role in [('postgres','d5c_r4_role'),('d5c_r4_db','postgres'),('d5c_r4_db;drop','d5c_r4_role')]:
            with self.subTest(db=db,role=role), self.assertRaises(ValueError):
                r.validate_target(55555,db,role)
    def test_valid_shape_only(self):
        r.validate_target(55555,'d5c_r4_db','d5c_r4_role')
    def test_deferred_sql_shape(self):
        self.assertIn('DEFERRABLE INITIALLY DEFERRED',r.SETUP[-1])
        self.assertIn('pg_catalog.clock_timestamp()',r.SETUP[-2])
        self.assertIn('P0001',r.SETUP[-2])

if __name__ == '__main__': unittest.main(verbosity=2)
