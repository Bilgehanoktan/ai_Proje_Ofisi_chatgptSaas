"""Supplemental isolated mechanics, not full historical or product acceptance."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import w8_unified_u3 as u3
import w8_p10j24 as p24

HERE = Path(__file__).resolve().parent
REL = 'app/core/transaction/postgres_session.py'
OLD = '8e65e4575a77b11c38c2d2e62ec91fc89d75e23c'
CURRENT = '6c0995712bd368f72c239cb19cd3e85aa781c1b9'


class CommonHistoryTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.stage = self.root/'stage'
        self.dest = self.root/'dest'
        self.stage.mkdir(); self.dest.mkdir()
        self.name = p24.PREFIX+REL
        self.overlay = p24.HISTORY+REL
        self.current = self.stage/self.name
        self.old = self.stage/self.overlay
        self.current.parent.mkdir(parents=True)
        self.old.parent.mkdir(parents=True)
        self.old_bytes = (HERE/'historical_postgres_session.py').read_bytes()
        self.current_bytes = (HERE/'current_postgres_session.py').read_bytes()
        self.assertEqual(p24.blob(self.old_bytes),OLD)
        self.assertEqual(p24.blob(self.current_bytes),CURRENT)
        self.current.write_bytes(self.current_bytes)
        self.old.write_bytes(self.old_bytes)
        self.row = {'path':self.name,'git_blob':OLD,'bytes':len(self.old_bytes),'sha256':hashlib.sha256(self.old_bytes).hexdigest()}

    def test_new_binding_preserves_existing_history_before_extend(self):
        original = dict(p24.HISTORICAL)
        self.assertEqual(len(original),3)
        parent = SimpleNamespace(CANDIDATE_MANIFEST='previous')
        def load_parent():
            self.assertEqual(parent.CANDIDATE_MANIFEST,u3.MANIFEST)
            self.assertEqual(p24.CANDIDATE_MANIFEST,u3.MANIFEST)
            self.assertEqual(p24.HISTORICAL,{**original,self.name:OLD})
            return SimpleNamespace(MANIFEST_BLOB=u3.MANIFEST,verify_aux=lambda root:{},test=lambda *_:None,smoke=lambda *_:None)
        parent.load_candidate = load_parent
        with patch.object(p24,'HISTORICAL',original),patch.object(p24,'CANDIDATE_MANIFEST','previous'),patch.object(u3,'load_exact',side_effect=[p24,parent]) as loader:
            result = u3.load_candidate()
            self.assertEqual(result.MANIFEST_BLOB,u3.MANIFEST)
            self.assertEqual([(x.args[0].name,x.args[1]) for x in loader.call_args_list],[('w8_p10j24.py',u3.P24),('w8_p10j23.py',u3.P23)])
            # The real P24 auxiliary validator requires the historical files, not current transport.
            with self.assertRaisesRegex(ValueError,'P10J24_HISTORICAL_AUX_HOLD'):
                result.verify_aux(self.stage)
        self.assertEqual(p24.HISTORICAL,original)

    def test_materialize_exact_old_only_and_preserve_current(self):
        p24.materialize_locked(self.stage,self.dest,[self.row],{self.name:self.overlay})
        self.assertEqual((self.dest/self.name).read_bytes(),self.old_bytes)
        self.assertEqual(self.current.read_bytes(),self.current_bytes)
        self.assertEqual(self.old.read_bytes(),self.old_bytes)

    def test_current_transport_does_not_satisfy_historical_pin(self):
        with self.assertRaisesRegex(ValueError,'P10J24_SOURCE_PIN_HOLD'):
            p24.materialize_locked(self.stage,self.dest,[self.row],{})
        self.assertFalse((self.dest/self.name).exists())
        self.assertEqual(self.current.read_bytes(),self.current_bytes)

    def test_missing_or_changed_overlay_fails_without_current_fallback(self):
        self.old.unlink()
        with self.assertRaisesRegex(ValueError,'P10J24_SOURCE_MISSING'):
            p24.materialize_locked(self.stage,self.dest,[self.row],{self.name:self.overlay})
        self.old.write_bytes(self.current_bytes)
        with self.assertRaisesRegex(ValueError,'P10J24_SOURCE_PIN_HOLD'):
            p24.materialize_locked(self.stage,self.dest,[self.row],{self.name:self.overlay})
        self.assertFalse((self.dest/self.name).exists())
        self.assertEqual(self.current.read_bytes(),self.current_bytes)


if __name__ == '__main__':
    unittest.main()
