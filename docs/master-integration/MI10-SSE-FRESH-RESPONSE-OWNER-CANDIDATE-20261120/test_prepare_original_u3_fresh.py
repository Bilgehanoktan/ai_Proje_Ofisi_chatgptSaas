"""Isolated patcher validation only. A synthetic U3 fixture is not original U3 test."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import prepare_original_u3_fresh as module

SOURCE = '''def test_u3():
    browser = example
    page = browser.new_page(viewport={'width':1440,'height':900}, reduced_motion='reduce')
    def read(panel):
        with page.expect_response(lambda r: r.url == url) as response:
            panel.get_by_role('button', name='Snapshot yeniden oku').click()
        r = response.value
        assert r.status == 200 and r.headers.get('cache-control') == 'no-store'
        lines = r.text().splitlines()
        assert lines[0] == 'event: snapshot'
    return read
'''
SOURCE = 'def outer():\n' + ''.join('    '+line for line in SOURCE.splitlines(keepends=True))
JS = Path(__file__).with_name('sse_capture_init.js').read_text(encoding='utf-8')


class TestPatcher(unittest.TestCase):
    def pinned_transform(self, content=SOURCE):
        original=module.ORIGINAL_BLOB
        try:
            module.ORIGINAL_BLOB=module.git_blob(content.encode())
            return module.transform(content.encode(),JS)
        finally:
            module.ORIGINAL_BLOB=original

    def test_01_exact_pin_blocks_synthetic(self):
        with self.assertRaisesRegex(ValueError,'MI10_ORIGINAL_U3_BLOB_HOLD'):
            module.transform(SOURCE.encode(), JS)

    def test_02_git_blob_has_NUL_separator(self):
        src=b'a'
        self.assertEqual(module.git_blob(src),'2e65efe2a145dda7ee51d1741299f848e5bf752e')

    def test_03_reference_compiles(self):
        compiled=self.pinned_transform()
        self.assertIsNotNone(compile(compiled,'generated.py','exec'))

    def test_04_expected_original_assertions_preserved(self):
        compiled=self.pinned_transform()
        for line in ("assert r.status == 200 and r.headers.get('cache-control') == 'no-store'", "assert lines[0] == 'event: snapshot'"):
            self.assertIn(line,compiled)

    def test_05_capture_is_before_read_click(self):
        compiled=self.pinned_transform()
        self.assertLess(compiled.find('__mi10_before = page.evaluate('),compiled.find('with page.expect_response('))
        self.assertLess(compiled.find('with page.expect_response('),compiled.find('__mi10_expected = __mi10_before + 1'))

    def test_06_only_per_sequence_clone_is_consumed(self):
        compiled=self.pinned_transform()
        self.assertIn('window.__mi10Capture.take(seq)',compiled)
        self.assertIn('window.__mi10Capture.ready(seq)',compiled)
        self.assertNotIn('lines = r.text().splitlines()',compiled)
        self.assertIn('MI10_SSE_EXTRA_FETCH_HOLD',compiled)

    def test_07_extra_markers_are_rejected(self):
        duplicate=SOURCE+'\n'+module.BODY+'\n'
        with self.assertRaisesRegex(ValueError,'MI10_U3_PATCH_SCOPE_HOLD'):
            self.pinned_transform(duplicate)

    def test_08_missing_markers_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'MI10_U3_PATCH_SCOPE_HOLD'):
            self.pinned_transform(SOURCE.replace(module.BODY,'            lines=[]'))

    def test_09_original_file_never_modified(self):
        with tempfile.TemporaryDirectory() as dirname:
            p=Path(dirname)/'original.py';p.write_text(SOURCE)
            original=p.read_bytes()
            try:
                module.ORIGINAL_BLOB=module.git_blob(original)
                out=Path(dirname)/'adapted.py'
                with contextlib.redirect_stdout(io.StringIO()):
                    import sys
                    before=sys.argv
                    try:
                        sys.argv=['prepare_original_u3_fresh.py','--original',str(p),'--output',str(out)]
                        module.main()
                    finally:sys.argv=before
                self.assertEqual(p.read_bytes(),original)
                self.assertIn('MI10_SSE_EXTRA_FETCH_HOLD',out.read_text())
            finally:
                module.ORIGINAL_BLOB='2a3f2b8e286c5d79847a6b00cdbd046d0429773'

    def test_10_output_overwrite_rejected(self):
        with tempfile.TemporaryDirectory() as dirname:
            p=Path(dirname)/'test.py';p.write_text(SOURCE)
            output=Path(dirname)/'already.py';output.write_text('DO NOT CHANGE')
            import sys
            before=sys.argv
            try:
                sys.argv=['prepare_original_u3_fresh.py','--original',str(p),'--output',str(output)]
                with self.assertRaisesRegex(ValueError,'MI10_U3_OUTPUT_SCOPE_HOLD'):
                    module.main()
            finally:sys.argv=before
            self.assertEqual(output.read_text(),'DO NOT CHANGE')


if __name__ == '__main__':
    unittest.main(verbosity=2)
