import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
import warnings
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
import mi05_verified_local_checkout as m

ROOT = 'ai_Proje_Ofisi_chatgptSaas-SYNTHETIC/'


def blob(data):
    return m.object_sha('blob', data)


def make_zip(path, entries):
    with ZipFile(path, 'w', ZIP_DEFLATED) as z:
        for name, data in entries.items():
            z.writestr(ROOT + name, data)


class TreeTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)

    def test_git_tree_matches_independent_git(self):
        if not shutil.which('git'):
            self.skipTest('git not installed')
        files = {'b.txt': b'bb\n', 'x/a.txt': b'aa\n', 'x/y.txt': b'yy', 'z.txt': b'zzz', 'T\u00fcrk\u00e7e.txt': '\u0131'.encode()}
        repo = self.root / 'gitroot'
        repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(repo)], check=True, capture_output=True)
        for n, v in files.items():
            p = repo / n
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(v)
        subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True, capture_output=True)
        git = subprocess.run(['git', '-C', str(repo), 'write-tree'], check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(m.tree_sha(files), git)

    def test_archive_verified_with_exact_tree_and_count(self):
        files = {'a.txt': b'a', 'dir/x.txt': b'one'}
        z = self.root / 'x.zip'
        make_zip(z, files)
        result, sha = m.read_archive(z, expected_tree=m.tree_sha(files), expected_count=2, expected_bytes=4)
        self.assertEqual(result, files)
        self.assertEqual(sha, m.tree_sha(files))

    def test_archive_rejects_wrong_tree(self):
        z = self.root / 'x.zip'
        make_zip(z, {'a.txt': b'a'})
        with self.assertRaisesRegex(m.TransferHold, 'GIT_TREE_PIN_MISMATCH'):
            m.read_archive(z, expected_tree='0' * 40, expected_count=1, expected_bytes=1)

    def test_archive_rejects_traversal(self):
        z = self.root / 'x.zip'
        make_zip(z, {'../outside.txt': b'no'})
        with self.assertRaisesRegex(m.TransferHold, 'UNSAFE_ARCHIVE_PATH'):
            m.read_archive(z, expected_count=1, expected_bytes=2)

    def test_archive_rejects_symlink(self):
        z = self.root / 'x.zip'
        with ZipFile(z, 'w') as f:
            item = ZipInfo(ROOT + 'link.txt')
            item.create_system = 3
            item.external_attr = (stat.S_IFLNK | 0o777) << 16
            f.writestr(item, b'destination')
        with self.assertRaisesRegex(m.TransferHold, 'UNEXPECTED_ZIP_MODE'):
            m.read_archive(z, expected_count=1, expected_bytes=11)

    def test_archive_rejects_duplicate(self):
        z = self.root / 'x.zip'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with ZipFile(z, 'w') as f:
                f.writestr(ROOT + 'duplicate.txt', b'a')
                f.writestr(ROOT + 'duplicate.txt', b'a')
        with self.assertRaisesRegex(m.TransferHold, 'DUPLICATE_ZIP_MEMBER'):
            m.read_archive(z, expected_count=2, expected_bytes=2)

    def test_archive_rejects_root_scope(self):
        z = self.root / 'x.zip'
        with ZipFile(z, 'w') as f:
            f.writestr('unrelated-archive/readme', b'hello')
        with self.assertRaisesRegex(m.TransferHold, 'UNEXPECTED_ARCHIVE_ROOT'):
            m.read_archive(z, expected_count=1, expected_bytes=5)

    def test_archive_rejects_oversize_file(self):
        z = self.root / 'x.zip'
        with ZipFile(z, 'w') as f:
            f.writestr(ROOT + 'huge', b'0' * 64)
        with patch.object(m, 'MAX_FILE_BYTES', 32):
            with self.assertRaisesRegex(m.TransferHold, 'ZIP_MEMBER_OVERSIZE'):
                m.read_archive(z, expected_count=1, expected_bytes=64)

    def test_existing_target_hold(self):
        x = self.root / 'target'
        x.mkdir()
        with self.assertRaisesRegex(m.TransferHold, 'DESTINATION_ALREADY_EXISTS'):
            m.run(x, minimum_free=0)

    def test_disk_threshold_hold(self):
        with self.assertRaisesRegex(m.TransferHold, 'INSUFFICIENT_DISK_SPACE'):
            m.run(self.root / 'unused', minimum_free=10**18)


STUB = b'''import json
from pathlib import Path
PIN_BLOBS = {}
AUX_BLOBS = {'model': {}, 'core': {}}
def model_rows(raw): return json.loads(raw)['rows']
def core_rows(raw): return json.loads(raw)['rows']
def normalize(rows): return {r['path']: r for r in rows}
class ExactCache:
    def __init__(self,root,offline=True): self.root=Path(root)
    def read(self,blob): return (self.root/blob).read_bytes()
def recover(cache,stage,modes):
    (stage/'model').mkdir(parents=True)
    (stage/'core').mkdir(parents=True)
    return {'status':'RECOVERED_NOT_TESTED', 'modes': list(modes)}
'''


class IntegrationTests(unittest.TestCase):
    setUp = TreeTests.setUp
    def fixture(self):
        files = {m.HELPER_PATH: STUB, m.MANIFEST_PATH: b'{}\n'}
        model, core = [], []
        for i in range(114):
            name = f'{m.BACKEND_PREFIX}sample_{i:03d}.py'
            data = f'model-{i}\n'.encode()
            files[name] = data
            model.append({'path': name, 'blob': blob(data), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest() if i % 3 else None})
        for i in range(55):
            if i < 26:
                name = model[i]['path']
                if i < 2:
                    data = f'historical-{i}\n'.encode()
                    files[m.HIST_PREFIX + name[len(m.BACKEND_PREFIX):]] = data
                else:
                    data = files[name]
            else:
                name = f'history/standalone_{i:03d}.py'
                data = f'historical-{i}\n'.encode()
                files[name] = data
            core.append({'path': name, 'blob': blob(data), 'bytes': len(data), 'sha256': None})
        files[m.MODEL_PIN_PATH] = (json.dumps({'rows': model}) + '\n').encode()
        files[m.CORE_PIN_PATH] = (json.dumps({'rows': core}) + '\n').encode()
        z = self.root / 'fixture.zip'
        make_zip(z, files)
        return files, z

    def mocks(self, files):
        return [patch.object(m, 'HELPER_BLOB', blob(files[m.HELPER_PATH])),
                patch.object(m, 'MODEL_PIN_BLOB', blob(files[m.MODEL_PIN_PATH])),
                patch.object(m, 'CORE_PIN_BLOB', blob(files[m.CORE_PIN_PATH])),
                patch.object(m, 'MANIFEST_BLOB', blob(files[m.MANIFEST_PATH])),
                patch.object(m, 'EXPECTED_GIT_TREE', m.tree_sha(files)),
                patch.object(m, 'EXPECTED_FILES', len(files)),
                patch.object(m, 'EXPECTED_UNCOMPRESSED', sum(len(x) for x in files.values()))]

    def test_full_offline_stage_with_separate_history(self):
        files, z = self.fixture()
        with self.subTest('Fixture count'):
            self.assertEqual(len(files), 149)
        patchers = self.mocks(files)
        for p in patchers:
            p.start()
            self.addCleanup(p.stop)
        out = self.root / 'completed'
        result = m.run(out, archive=z, minimum_free=0)
        self.assertEqual(result['checkout_files_verified'], len(files))
        self.assertEqual(result['model_rows'], 114)
        self.assertEqual(result['core_rows'], 55)
        self.assertEqual(result['overlapping_paths'], 26)
        self.assertEqual(len(result['differing_paths']), 2)
        self.assertEqual(len(result['historical_overlay_used']), 2)
        self.assertEqual(result['status'], 'SOURCE_RECOVERED_TESTS_NOT_RUN')
        self.assertTrue((out / 'TRANSFER_REPORT.json').is_file())
        self.assertTrue((out / 'pinned_regression_stage/model').is_dir())
        self.assertTrue((out / 'pinned_regression_stage/core').is_dir())
        self.assertEqual((out / 'full_checkout' / m.MODEL_PIN_PATH).read_bytes(), files[m.MODEL_PIN_PATH])

    def test_tampered_pinned_archive_fails_closed(self):
        files, z = self.fixture()
        for p in self.mocks(files):
            p.start()
            self.addCleanup(p.stop)
        files[m.BACKEND_PREFIX+'sample_011.py'] = b'TAMPERED\n'
        make_zip(z, files)
        target = self.root / 'fail'
        with self.assertRaisesRegex(m.TransferHold, 'GIT_TREE_PIN_MISMATCH'):
            m.run(target, archive=z, minimum_free=0)
        self.assertFalse(target.exists())
        self.assertTrue((self.root / 'fail.partial/TRANSFER_HOLD.json').is_file())


if __name__ == '__main__':
    unittest.main(verbosity=2)
