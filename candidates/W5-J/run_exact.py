"""W5-J isolated source regression; no installs, DB server, provider or product launch."""
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PARENT = '07eae266cfcdb6de8a4b65cca5b07101ecef2fcb'
MANIFEST = 'candidates/W5-I/SOURCE_MANIFEST.json'
MANIFEST_BLOB = '20396906516bb5479b4a4c762ac60cb58418e533'
GROUPS = (('W5-A-F', 'tests/w5', 90), ('W5-G', 'candidates/W5-G', 16),
          ('W5-H', 'candidates/W5-H', 28), ('W5-I', 'candidates/W5-I', 36))


def git_blob(data):
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def read_pin(path, sha):
    p = ROOT / path
    if (not isinstance(path, str) or not path or Path(path).is_absolute()
            or '..' in Path(path).parts or p.resolve() != p or not p.is_file()):
        raise ValueError('SOURCE_PATH_HOLD: ' + path)
    data = p.read_bytes()
    if git_blob(data) != sha:
        raise ValueError('SOURCE_GIT_BLOB_HOLD: ' + path)
    return data


def verify_sources():
    spec = json.loads((HERE / 'SOURCE_PINS.json').read_bytes())
    if (spec['parent'] != PARENT or spec['inherited_manifest'] != MANIFEST
            or spec['additional'].get(MANIFEST) != MANIFEST_BLOB):
        raise ValueError('PARENT_PIN_HOLD')
    inherited = json.loads(read_pin(MANIFEST, MANIFEST_BLOB))
    if len(inherited) != 69 or len(spec['additional']) != 25:
        raise ValueError('SOURCE_INVENTORY_HOLD')
    result = {}
    for path, pin in inherited.items():
        data = read_pin(path, pin['git_blob'])
        if hashlib.sha256(data).hexdigest() != pin['sha256']:
            raise ValueError('SOURCE_SHA256_HOLD: ' + path)
        result[path] = data
    for path, sha in spec['additional'].items():
        if path in result:
            raise ValueError('SOURCE_DUPLICATE_HOLD: ' + path)
        result[path] = read_pin(path, sha)
    return result


def run():
    sources = verify_sources()
    versions = (sys.version.split()[0], sqlite3.sqlite_version, md.version('cryptography'))
    print('PARENT', PARENT, '\nSOURCE_PINS', len(sources), '\nENV', *versions, flush=True)
    if versions != ('3.13.5', '3.46.1', '46.0.4'):
        raise RuntimeError('REFERENCE_ENVIRONMENT_HOLD: review versions before a new run')
    code = """import sys,unittest
from pathlib import Path
root=Path.cwd()
sys.path[:0]=[str(root/p) for p in ('product/ai-company-os-backend','tests/w5','candidates/W5-H','candidates/W5-I')]
suite=unittest.defaultTestLoader.discover(sys.argv[1],pattern='test_*.py')
r=unittest.TextTestRunner(verbosity=2).run(suite)
expected=int(sys.argv[2]); print('W5J_COUNTS',r.testsRun,len(r.failures),len(r.errors),len(r.skipped),len(r.expectedFailures),len(r.unexpectedSuccesses),flush=True)
sys.exit(0 if r.wasSuccessful() and r.testsRun==expected and not (r.skipped or r.expectedFailures or r.unexpectedSuccesses) else 1)
"""
    with tempfile.TemporaryDirectory(prefix='w5j-exact-') as temp:
        for path, data in sources.items():
            p = Path(temp) / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        total = 0
        for label, directory, expected in GROUPS:
            print('BEGIN', label, flush=True)
            result = subprocess.run([sys.executable, '-I', '-B', '-c', code, directory, str(expected)],
                                    cwd=temp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            print(result.stdout, end='', flush=True)
            if result.returncode or f'W5J_COUNTS {expected} 0 0 0 0 0' not in result.stdout.splitlines():
                raise RuntimeError('REGRESSION_HOLD: ' + label)
            total += expected
            print('END', label, expected, 'PASS', flush=True)
        print('TOTAL', total, 'PASS; PRODUCT_HOLD', flush=True)


if __name__ == '__main__':
    run()
