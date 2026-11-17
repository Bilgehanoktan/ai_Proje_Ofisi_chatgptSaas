"""Tests the archive verifier against a disposable Git fixture, NOT the product."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from run_checkout import git, materialize


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)/'repo'; self.repo.mkdir()
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.name', 'D0 Fixture')
        git(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        (self.repo/'a.txt').write_bytes(b'original\n')
        git(self.repo, 'add', 'a.txt'); git(self.repo, 'commit', '-qm', 'fixture')
        self.commit = git(self.repo, 'rev-parse', 'HEAD').decode().strip()
        self.root = Path(self.tmp.name)/'archive'; self.root.mkdir()

    def test_exact_commit_not_dirty_worktree(self):
        (self.repo/'a.txt').write_bytes(b'dirty\n')
        self.assertEqual(materialize(self.repo, self.commit, self.root, 1), 1)
        self.assertEqual((self.root/'a.txt').read_bytes(), b'original\n')

    def test_wrong_count(self):
        with self.assertRaisesRegex(ValueError, 'TREE_COUNT_HOLD'):
            materialize(self.repo, self.commit, self.root, 2)

    def test_missing_commit(self):
        with self.assertRaises(subprocess.CalledProcessError):
            materialize(self.repo, '0'*40, self.root, 1)

    def test_archive_blob_tamper(self):
        real = git
        def altered(repo, *args):
            data = real(repo, *args)
            return data.replace(b'original\n', b'tampered\n') if args[0] == 'archive' else data
        with patch('run_checkout.git', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'ARCHIVE_BLOB_HOLD'):
                materialize(self.repo, self.commit, self.root, 1)


if __name__ == '__main__': unittest.main(verbosity=2)
