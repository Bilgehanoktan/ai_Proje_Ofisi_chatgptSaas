"""A0C portability and acceptance guard tests; no real Windows/build/browser run."""
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import w8_ux_a0c as a


class ExactChain(unittest.TestCase):
    def test_actual_parent_chain(self):
        w = a.load_candidate()
        self.assertEqual(w.MANIFEST_BLOB, a.MANIFEST)
        self.assertEqual(w.verify.__defaults__[0], a.MANIFEST)

    def test_wrong_manifest_rejected(self):
        w = a.load_candidate()
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, 'P10F_MANIFEST_PIN_HOLD'):
            w.verify(Path(tmp), pin='0'*40, clean=True)

    def test_incomplete_checkout_rejected(self):
        w = a.load_candidate()
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, 'missing or wrong SOURCE_MANIFEST'):
            w.verify(Path(tmp), clean=True)

    def test_missing_review_no_markers(self):
        w = a.load_candidate()
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            for run in (lambda: w.test(stage, '0'*64), lambda: w.smoke(stage, '0'*64, Path('chrome'))):
                with self.assertRaises(ValueError):
                    run()
            for name in ('BUILD_TEST_OK','SMOKE_OK','NATIVE_SMOKE_OK'):
                self.assertFalse((stage/name).exists())


class PortableModules(unittest.TestCase):
    def check(self, files, error=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, value in files.items():
                p = root/'product'/name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(value, encoding='utf-8')
            if error:
                with self.assertRaisesRegex(ValueError, error):
                    a.portable_modules(root, files)
            else:
                a.portable_modules(root, files)

    def test_collision(self):
        self.check({'x/HistoricalEvidence.tsx':'', 'x/historicalEvidence.ts':''}, 'PORTABLE_MODULE_COLLISION')

    def test_stale_import(self):
        self.check({'x/EvidenceDetails.tsx':"import X from './HistoricalEvidence';"}, 'STALE_COMPONENT_IMPORT')

    def test_corrected_import(self):
        self.check({'x/HistoricalEvidencePanel.tsx':"import {x} from './historicalEvidence';", 'x/historicalEvidence.ts':'', 'x/EvidenceDetails.tsx':"import X from './HistoricalEvidencePanel';"})

    @unittest.skipIf(os.name == 'nt', 'non-Windows branch only')
    def test_non_windows_temp_no_mutation(self):
        before = {k:os.environ.get(k) for k in ('TEMP','TMP','TMPDIR')}
        with a.windows_temp(Path('.'), None):
            self.assertEqual(before, {k:os.environ.get(k) for k in before})
        self.assertEqual(before, {k:os.environ.get(k) for k in before})


class GuardDoubles(unittest.TestCase):
    def exercise(self, mode, smoke=False):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            names = ('SMOKE_OK','NATIVE_SMOKE_OK') if smoke else ('BUILD_TEST_OK','SMOKE_OK','NATIVE_SMOKE_OK')
            for name in names:
                (stage/name).write_text('old')
            @contextmanager
            def temp_guard(stage, w):
                if mode == 'entry':
                    raise ValueError('entry failed')
                yield
                if mode == 'exit':
                    raise ValueError('exit failed')
            def product(*args):
                for name in names:
                    self.assertFalse((stage/name).exists())
                    (stage/name).write_text('new')
                if mode == 'body':
                    raise ValueError('body failed')
            w = SimpleNamespace(verify=lambda *a,**k:({},0),test=product,smoke=product,installed=lambda *a:None)
            a.extend_candidate(w)
            call = lambda: w.smoke(stage,'x',Path('chrome')) if smoke else w.test(stage,'x')
            with patch.object(a,'windows_temp',temp_guard):
                if mode == 'success':
                    call()
                    for name in names:self.assertEqual((stage/name).read_text(),'new')
                else:
                    with self.assertRaises(ValueError):call()
                    for name in names:self.assertFalse((stage/name).exists())

    def test_success(self):self.exercise('success')
    def test_temp_entry_failure(self):self.exercise('entry')
    def test_body_failure(self):self.exercise('body')
    def test_temp_cleanup_failure(self):self.exercise('exit', smoke=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
