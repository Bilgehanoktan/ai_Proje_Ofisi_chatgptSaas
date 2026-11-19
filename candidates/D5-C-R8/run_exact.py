"""D5-C-R8 isolated exact-source selected regression; stdlib only, no PG."""
from pathlib import Path
from hashlib import sha1
import json
import subprocess
import sys
import tempfile

SUITES = {
    'test_protected_org_t1_d5c_r8': 10,
    'test_iam_org_d5g5': 12,
    'test_iam_identity_d5g4': 14,
    'test_postgres_strict_expiry_d5c_r6': 12,
    'test_postgres_preclaim_d5c_r7': 5,
}

def main():
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    pins = json.loads((here/'SOURCE_PINS.json').read_text(encoding='utf-8'))
    if len(pins) != 37:
        raise ValueError('PIN_INVENTORY_HOLD')
    with tempfile.TemporaryDirectory(prefix='d5c-r8-') as tmp:
        stage = Path(tmp).resolve()
        for rel, expected in pins.items():
            p = root/rel
            if not p.is_relative_to(root) or p.resolve() != p or not p.is_file():
                raise ValueError('PATH_HOLD '+rel)
            raw = p.read_bytes()
            if sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != expected:
                raise ValueError('PIN_HOLD '+rel)
            out = stage/rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(raw)
        print(f'EXACT_SOURCE_PINS: {len(pins)}/{len(pins)}', flush=True)
        backend = stage/'product/ai-company-os-backend'
        org = stage/'candidates/ORG-05R3'
        code = """import json, sys, unittest, sqlite3
sys.path[:0] = sys.argv[1:4]
print('Python', sys.version.split()[0], 'SQLite', sqlite3.sqlite_version, flush=True)
expected = json.loads(sys.argv[4])
loader = unittest.TestLoader()
suite = unittest.TestSuite()
for name, count in expected.items():
    group = loader.loadTestsFromName(name)
    if loader.errors or group.countTestCases() != count:
        raise SystemExit('COLLECTION_HOLD '+name+' '+str(loader.errors))
    print('COLLECTED', name, count, flush=True)
    suite.addTests(group)
r = unittest.TextTestRunner(verbosity=2).run(suite)
print('RESULT', json.dumps(dict(executed=r.testsRun, failures=len(r.failures), errors=len(r.errors), skipped=len(r.skipped))), flush=True)
sys.exit(0 if r.wasSuccessful() and not r.skipped and not r.expectedFailures and r.testsRun == sum(expected.values()) else 1)
"""
        return subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code,
                               str(backend), str(backend/'tests'), str(org),
                               json.dumps(SUITES)], cwd=stage, check=False).returncode

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError) as e:
        print('BLOCKED:', e)
        sys.exit(2)
