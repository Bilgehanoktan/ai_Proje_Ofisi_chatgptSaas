"""Offline launcher controls; does not start PostgreSQL or Windows."""
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import run_windows as r

class LaunchPreflight(unittest.TestCase):
    def test_r4_exact_blobs(self):
        for name in ('run_pg_expiry.py','postgres_session.original.py'):
            self.assertEqual(r.blob(r.HERE/name),r.PINS[name])

    def test_d1_drift_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'helper.py'; p.write_text('raise RuntimeError("must not run")')
            with self.assertRaisesRegex(ValueError,'SOURCE_PIN_HOLD_run_d1'):
                r.load_inputs(p)

    def test_prior_ports_rejected(self):
        for port in (5432,55432,55434,55435,55436,True):
            with self.subTest(port=port),self.assertRaisesRegex(ValueError,'PORT_ALLOCATION_HOLD'):
                r.check_port(port)

    def test_port_collision_rejected(self):
        with socket.socket() as s:
            s.bind(('127.0.0.1',0)); s.listen()
            with patch.object(r,'PORT',s.getsockname()[1]),self.assertRaises(OSError):
                r.check_port(r.PORT)

    def test_fresh_stage_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); src=root/'input'; src.mkdir()
            r.check_roots(src,root/'fresh')
            (root/'existing').mkdir()
            with self.assertRaisesRegex(ValueError,'FRESH_STAGE_HOLD'):
                r.check_roots(src,root/'existing')

    def test_input_overlap_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)
            with self.assertRaisesRegex(ValueError,'STAGE_OVERLAP_HOLD'):
                r.check_roots(src,src/'fresh')

if __name__=='__main__': unittest.main(verbosity=2)
