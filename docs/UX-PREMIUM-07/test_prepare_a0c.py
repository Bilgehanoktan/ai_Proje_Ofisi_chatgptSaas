"""Real local Git fixtures for bootstrap only; not product or Windows acceptance."""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from prepare_a0c import prepare, git_blob, RUNNER

RUNNER_FIXTURE = '''import pathlib,sys
if sys.argv[1] == 'audit':
    assert pathlib.Path('product/SOURCE_MANIFEST.json').read_text() == 'fixture\\n'
elif sys.argv[1] == 'prepare':
    p=pathlib.Path(sys.argv[3]); (p/'locks').mkdir(parents=True)
    (p/'locks/REVIEW.json').write_bytes(b'review-fixture')
else:
    raise AssertionError('unexpected phase')
'''


class Bootstrap(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root/'repo'
        self.repo.mkdir()
        self.git('init', '--quiet', '--template=')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'core.autocrlf', 'false')
        self.write('product/SOURCE_MANIFEST.json', 'fixture\n')
        self.write(RUNNER, RUNNER_FIXTURE)
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.commit = self.git('rev-parse', 'HEAD')
        self.pins = {p:git_blob(self.repo/p) for p in ('product/SOURCE_MANIFEST.json', RUNNER)}
        self.workspace = self.root/'workspace'

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()

    def write(self, name, value):
        p = self.repo/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(value, encoding='utf-8', newline='\n')

    def advance(self, name, value):
        self.write(name, value)
        self.git('add', '.')
        self.git('commit', '-qm', 'next fixture')
        return self.git('rev-parse', 'HEAD')

    def invoke(self, **kw):
        opts = dict(repo=self.repo.as_uri(), commit=self.commit, pins=self.pins)
        opts.update(kw)
        return prepare(self.workspace, **opts)

    def test_exact_commit_and_review_only(self):
        self.advance('product/SOURCE_MANIFEST.json', 'later\n')
        result = self.invoke()
        self.assertEqual(result, hashlib.sha256(b'review-fixture').hexdigest())
        src, stage = self.workspace/'src', self.workspace/'stage'
        self.assertEqual(subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip(), self.commit)
        self.assertEqual(subprocess.check_output(['git','-C',str(src),'config','--local','core.autocrlf'],text=True).strip(), 'false')
        self.assertTrue((stage/'locks/REVIEW.json').is_file())
        for marker in ('INSTALL_OK','BUILD_TEST_OK','SMOKE_OK','NATIVE_SMOKE_OK'):
            self.assertFalse((stage/marker).exists())

    def test_audit_only(self):
        self.assertIsNone(self.invoke(audit_only=True))
        self.assertFalse((self.workspace/'stage').exists())

    def test_preserve_existing_workspace(self):
        self.workspace.mkdir(); sentinel=self.workspace/'keep'; sentinel.write_text('keep')
        with self.assertRaisesRegex(ValueError, 'WORKSPACE_ALREADY_EXISTS'):
            self.invoke()
        self.assertEqual(sentinel.read_text(), 'keep')

    def test_wrong_source_pin(self):
        with self.assertRaisesRegex(ValueError, 'SOURCE_PIN_HOLD'):
            self.invoke(pins={**self.pins, 'product/SOURCE_MANIFEST.json':'0'*40})
        self.assertFalse((self.workspace/'stage').exists())

    def test_missing_commit(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke(commit='0'*40)
        self.assertFalse((self.workspace/'stage').exists())

    def test_audit_failure_stops_prepare(self):
        commit=self.advance(RUNNER, 'raise SystemExit(5)\n')
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke(commit=commit, pins={**self.pins,RUNNER:git_blob(self.repo/RUNNER)})
        self.assertFalse((self.workspace/'stage').exists())

    def test_prepare_without_review_is_hold(self):
        commit=self.advance(RUNNER, 'pass\n')
        with self.assertRaisesRegex(ValueError, 'REVIEW_MISSING_HOLD'):
            self.invoke(commit=commit,pins={**self.pins,RUNNER:git_blob(self.repo/RUNNER)})
        self.assertFalse((self.workspace/'stage/INSTALL_OK').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
