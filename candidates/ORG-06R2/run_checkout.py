"""Local-only ORG-06R2 exact archive verifier and SQLite test launcher."""
import argparse
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile
import tempfile

BASE = '17be56406408d572ebc66cf6fe7c1b6d83f18d76'
EXPECTED = 1739


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def materialize(repo, commit, root, expected):
    if git(repo, 'rev-parse', commit+'^{commit}').decode().strip() != commit:
        raise ValueError('COMMIT_HOLD')
    entries = {}
    for row in git(repo, 'ls-tree', '-r', '-z', commit).split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        mode, kind, digest = meta.decode().split()
        if mode != '100644' or kind != 'blob':
            raise ValueError('TREE_MODE_HOLD')
        entries[name.decode()] = digest
    if len(entries) != expected:
        raise ValueError('TREE_COUNT_HOLD')
    with tarfile.open(fileobj=io.BytesIO(git(repo, 'archive', '--format=tar', commit)), mode='r:') as archive:
        archive.extractall(root, filter='data')
    actual = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
    if actual.keys() != entries.keys() or any(blob(p.read_bytes()) != entries[k] for k,p in actual.items()):
        raise ValueError('ARCHIVE_BLOB_HOLD')
    return len(entries)


def run(repo, output):
    output.mkdir(parents=True, exist_ok=False)
    report = {'commit': BASE, 'status': 'BLOCKED', 'original': 'NOT_RUN', 'additional': 'NOT_RUN',
              'python': sys.version.split()[0], 'sqlite': sqlite3.sqlite_version,
              'scope': 'local synthetic SQLite only; no CI/PG/real IAM or acceptance'}
    try:
        with tempfile.TemporaryDirectory(prefix='org06r2-') as tmp:
            root = Path(tmp)
            report['verified_blobs'] = materialize(repo, BASE, root, EXPECTED)
            report['cryptography'] = importlib.metadata.version('cryptography')
            if report['cryptography'] != '46.0.4':
                raise ValueError('CRYPTOGRAPHY_PIN_HOLD')
            original = root/'candidates/ORG-06/test_org_core_checkout.py'
            # Additional test is staged outside the historical checkout.
            extra = Path(__file__).with_name('test_operation_notice.py').resolve()
            report['additional_sha256'] = hashlib.sha256(extra.read_bytes()).hexdigest()
            for key, script, count, args in (
                ('original', original, 11, []), ('additional', extra, 1, [str(root)])):
                command = [sys.executable, '-E', '-s', '-B', str(script), *args]
                p = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   timeout=120, check=False)
                (output/(key+'.log')).write_bytes(p.stdout)
                log = p.stdout.decode('utf-8', errors='replace')
                passed = p.returncode == 0 and f'Ran {count} test' in log and '\nOK\n' in log
                report[key] = 'PASS' if passed else 'FAIL'
                report[key+'_returncode'] = p.returncode
                if not passed:
                    report['status'] = 'FAIL'
                    return 1
            report['status'] = 'PASS_LOCAL_SQLITE_ONLY'
            return 0
    except (OSError, ValueError, subprocess.SubprocessError, importlib.metadata.PackageNotFoundError, tarfile.TarError) as exc:
        report['blocker'] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        return 2
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True, help='local Git repository with exact ORG-06 commit')
    p.add_argument('--evidence', type=Path, required=True, help='new evidence directory outside checkout')
    a = p.parse_args()
    sys.exit(run(a.repo.resolve(), a.evidence.resolve()))
