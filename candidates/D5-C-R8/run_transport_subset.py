"""Exact R8 transport subset; not the full 53-case runner, no PostgreSQL."""
from pathlib import Path
from hashlib import sha1
import json
import subprocess
import sys
import tempfile

SOURCE_COMMIT = '459c3eb16302375cd352140a0d6023fb1554d566'
BACKEND = 'product/ai-company-os-backend'
PINS = {
    'app/__init__.py': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
    'app/core/__init__.py': '9d457472970b7f581687ba142d1bf99ba91c7388',
    'app/core/agent_runtime/__init__.py': '5b19819cd7070302e874ecee80170a3921ce8fb0',
    'app/core/agent_runtime/lifecycle.py': '4c4ecbba9b2b1ec56dd8f73378b56b50f6578b49',
    'app/core/agent_runtime/transition_command.py': '5680fa428be81645a43d7442ec161c0c10384986',
    'app/core/transaction/__init__.py': '5b19819cd7070302e874ecee80170a3921ce8fb0',
    'app/core/transaction/port.py': '12f40659e916d5722d60c41c27f3116d746545f0',
    'app/core/transaction/postgres_session.py': '6c0995712bd368f72c239cb19cd3e85aa781c1b9',
    'app/core/transaction/review.py': '79b2b442f51bb5ea7706a33a5f9f1e7aed258cd4',
    'tests/test_postgres_preclaim_d5c_r7.py': 'c7a03aaadd1660e723b21c789dfa0744ac3721cb',
    'tests/test_postgres_strict_expiry_d5c_r6.py': 'cde0ed2b841c6b48500a464979096aad55a635b1',
}
SUITES = {'test_postgres_strict_expiry_d5c_r6': 12, 'test_postgres_preclaim_d5c_r7': 5}


def main():
    root = Path(__file__).resolve().parents[2]
    backend = root / BACKEND
    with tempfile.TemporaryDirectory(prefix='d5c-r8-transport-') as tmp:
        stage = Path(tmp).resolve()
        for rel, expected in PINS.items():
            p = backend / rel
            if not p.is_relative_to(root) or p.resolve() != p or not p.is_file():
                raise ValueError('PATH_HOLD ' + rel)
            raw = p.read_bytes()
            if sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest() != expected:
                raise ValueError('PIN_HOLD ' + rel)
            out = stage / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(raw)
        print('EXACT_R8_SUBSET_SOURCE_PINS: 11/11', flush=True)
        code = """import json, sys, unittest, sqlite3
sys.path[:0] = sys.argv[1:3]
print('Python', sys.version.split()[0], 'SQLite', sqlite3.sqlite_version, flush=True)
expected = json.loads(sys.argv[3])
loader = unittest.TestLoader()
suite = unittest.TestSuite()
for name, count in expected.items():
    group = loader.loadTestsFromName(name)
    if loader.errors or group.countTestCases() != count:
        raise SystemExit('COLLECTION_HOLD ' + name + ' ' + str(loader.errors))
    print('COLLECTED', name, count, flush=True)
    suite.addTests(group)
r = unittest.TextTestRunner(verbosity=2).run(suite)
print('RESULT', json.dumps(dict(executed=r.testsRun, failures=len(r.failures), errors=len(r.errors), skipped=len(r.skipped))), flush=True)
sys.exit(0 if r.wasSuccessful() and not r.skipped and not r.expectedFailures and not r.unexpectedSuccesses and r.testsRun == sum(expected.values()) else 1)
"""
        return subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code,
                               str(stage), str(stage / 'tests'), json.dumps(SUITES)],
                              cwd=stage, check=False).returncode


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError) as e:
        print('BLOCKED:', e)
        sys.exit(2)
