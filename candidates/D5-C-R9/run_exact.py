"""D5-C-R9: execute existing G6A claim and full-chain suites, no PG.
Only exact source bytes enter a new temporary stage. No network or installs.
"""
import argparse
from hashlib import sha1, sha256
from importlib.metadata import version, PackageNotFoundError
import json
from pathlib import Path, PurePosixPath
import sqlite3
import subprocess
import sys
import tempfile

SOURCE_COMMIT = '6bab62305d2ea15f8608f7835270ae027ce01e83'
PREFIX = 'product/ai-company-os-backend/'
MANIFEST = 'product/SOURCE_MANIFEST.json'
MANIFEST_PIN = '3b92a30f84e7262b4396fd75e7581c303b5d507c'
AUTHORITY_PINS = {PREFIX + k: v for k, v in {
    'app/__init__.py': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
    'app/core/__init__.py': '9d457472970b7f581687ba142d1bf99ba91c7388',
    'app/core/transaction/__init__.py': '5b19819cd7070302e874ecee80170a3921ce8fb0',
    'app/core/transaction/intent_authority.py': '88fd68c563db7e620c5b06c1a9c6b68d304ae071',
    'tests/test_intent_authority_0211.py': '0179b7f3b10d2dac1db07ffef68dae3d230244fd',
}.items()}
CRITICAL = AUTHORITY_PINS | {PREFIX + k: v for k, v in {
    'app/core/transaction/postgres_session.py': '6c0995712bd368f72c239cb19cd3e85aa781c1b9',
    'app/core/transaction/fenced_transition.py': 'b43a8d1129138b917c499ad1091ac61940af1846',
    'app/core/transaction/port.py': 'b0dde358be781b48e06b8901acc63ef31b013db0',
    'tests/test_authority_preclaim_fullchain_d5g6a.py': '822d27c55b6626a07cd9a56b4dbd53d9eb52292d',
    'tests/test_authority_fullchain_0214.py': '4918027e828e8e72273ee4d6a508cac3aa6e9b59',
    'tests/test_intent_authority_t1_0212.py': '9296347d9253d74902ed1c6a89e273d8e516f2b5',
    'tests/test_transition_mapping_0194.py': 'a4a3827ec4267ce275efe52fe5488e1868502c3f',
}.items()}
DDL = {
    'database/0192/candidate_event_outbox_fence.sql': '6e4780bf9f267c0926b40d582d5afdbd6faa543c',
    'database/0193/candidate_run_head.sql': '180924e97ee1f31fa27332941a41e37fdf73017e',
    'database/0194/candidate_transition_roles.sql': '7b5d374bb7973b283e4fcfa0d796ed6128ef9d27',
}
SUITES = {
    'authority': {'test_intent_authority_0211': 10},
    'fullchain': {'test_authority_preclaim_fullchain_d5g6a': 2,
                  'test_intent_authority_t1_0212': 7,
                  'test_authority_fullchain_0214': 10},
}


def blob(raw):
    return sha1(f'blob {len(raw)}\0'.encode('ascii') + raw).hexdigest()


def read_exact(root, name, pin=None):
    if not isinstance(name, str) or '\\' in name or ':' in name or '\0' in name:
        raise ValueError('PATH_HOLD')
    rel = PurePosixPath(name)
    if rel.is_absolute() or rel.as_posix() != name or any(x in ('', '.', '..') for x in rel.parts):
        raise ValueError('PATH_HOLD')
    p = root.joinpath(*rel.parts)
    if not p.is_relative_to(root) or p.resolve() != p or not p.is_file():
        raise ValueError('SOURCE_MISSING_HOLD: '+name)
    raw = p.read_bytes()
    if pin is not None and blob(raw) != pin:
        raise ValueError('PIN_HOLD: '+name)
    return raw


def stage_sources(root, stage, scope):
    def copy(name, raw):
        p = stage / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(raw)
    if scope == 'authority':
        for name, pin in AUTHORITY_PINS.items():
            copy(name, read_exact(root, name, pin))
        return '5 exact Git blob pins'
    raw = read_exact(root, MANIFEST, MANIFEST_PIN)
    manifest = json.loads(raw)['files']
    entries = {'product/'+k: v for k, v in manifest.items()
               if k.startswith('ai-company-os-backend/')}
    if (len(manifest) != 403 or len(entries) != 248 or not set(CRITICAL) <= entries.keys()
            or len({k.casefold() for k in entries}) != len(entries)):
        raise ValueError('BACKEND_INVENTORY_HOLD')
    if version('cryptography') != '46.0.4':
        raise ValueError('CRYPTOGRAPHY_PIN_HOLD')
    for name, meta in sorted(entries.items()):
        data = read_exact(root, name, CRITICAL.get(name))
        if len(data) != meta['bytes'] or sha256(data).hexdigest() != meta['sha256']:
            raise ValueError('MANIFEST_DRIFT_HOLD: '+name)
        copy(name, data)
    for name, pin in DDL.items():
        copy(name, read_exact(root, name, pin))
    return '248 exact backend manifest bytes + 3 DDL + 12 critical Git pins'


def main(root, scope):
    try:
        root = root.resolve(strict=True)
        with tempfile.TemporaryDirectory(prefix='d5c-r9-') as temp:
            stage = Path(temp).resolve()
            print('SOURCE_COMMIT:', SOURCE_COMMIT, flush=True)
            print('SCOPE:', scope, flush=True)
            print('PIN_MATCH:', stage_sources(root, stage, scope), flush=True)
            backend = stage / PREFIX
            code = """import json,sys,unittest,sqlite3
sys.path[:0] = sys.argv[1:3]
expected = json.loads(sys.argv[3])
loader = unittest.TestLoader()
suite = unittest.TestSuite()
print('Python',sys.version.split()[0],'SQLite',sqlite3.sqlite_version,flush=True)
for name,count in expected.items():
    group = loader.loadTestsFromName(name)
    if loader.errors or group.countTestCases()!=count:
        raise SystemExit('COLLECTION_HOLD '+name+' '+str(loader.errors))
    print('COLLECTED',name,count,flush=True)
    suite.addTests(group)
r = unittest.TextTestRunner(verbosity=2).run(suite)
print('RESULT',json.dumps(dict(executed=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped))),flush=True)
sys.exit(0 if r.wasSuccessful() and not r.skipped and not r.expectedFailures and not r.unexpectedSuccesses and r.testsRun==sum(expected.values()) else 1)
"""
            flags = ['-I', '-B'] + (['-S'] if scope == 'authority' else [])
            return subprocess.run([sys.executable, *flags, '-c', code, str(backend),
                                   str(backend/'tests'), json.dumps(SUITES[scope])],
                                  cwd=stage, timeout=180, check=False).returncode
    except (OSError, ValueError, KeyError, TypeError, PackageNotFoundError, subprocess.TimeoutExpired) as e:
        print('R9_REGRESSION_BLOCKED:', type(e).__name__, str(e), flush=True)
        return 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--scope', choices=tuple(SUITES), default='fullchain')
    args = parser.parse_args()
    sys.exit(main(args.root, args.scope))
