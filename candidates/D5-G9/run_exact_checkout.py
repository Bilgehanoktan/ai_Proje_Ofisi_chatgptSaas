"""Stage exact G8 backend and G7 original seven cases; no install or live access."""
from pathlib import Path, PurePosixPath
from hashlib import sha1, sha256
from importlib.metadata import version
import argparse
import json
import subprocess
import sys
import tempfile

BASE = '247813150153e4ad1f1c9eb574b9b991095a7c5c'
MANIFEST = '0555852afa38b7317a53a63db26a79cf151488b9'
PINS = 'candidates/D5-G7/SOURCE_PINS.json'
PIN_BLOB = 'cef9ce82a497522d2e4a9347b77453879e4790f3'
FIXTURE = 'candidates/D5-G7/test_checkout.py'
FIXTURE_BLOB = '6bd86d7972c8bca511b5702117be3542431e7493'
NAMES = sorted(('test_exact_existing_readers_no_write', 'test_persisted_member_tamper',
                'test_forged_role_reference', 'test_wrong_expected_version',
                'test_current_org_head_drift', 'test_revoked_iam', 'test_wrong_latest_member'))
CHILD = '''import runpy,sys,unittest,sqlite3,json
from importlib.metadata import version
ns=runpy.run_path(sys.argv[1]); cls=ns['ActualReadbackTests']
expected=json.loads(sys.argv[2]); loader=unittest.TestLoader()
if loader.getTestCaseNames(cls)!=expected: raise RuntimeError('COLLECTION_HOLD')
suite=loader.loadTestsFromTestCase(cls)
print('ENV',sys.version.split()[0],sqlite3.sqlite_version,version('cryptography'),flush=True)
result=unittest.TextTestRunner(verbosity=2).run(suite)
print('RESULT_JSON='+json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),expected_failures=len(result.expectedFailures),unexpected_successes=len(result.unexpectedSuccesses))),flush=True)
sys.exit(0 if result.wasSuccessful() and result.testsRun==7 and not result.skipped and not result.expectedFailures else 1)
'''


def require(ok, label):
    if not ok:
        raise ValueError(label)


def blob(raw):
    return sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()


def read(root, rel):
    p = PurePosixPath(rel)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in rel and ':' not in rel,
            'PATH_HOLD '+rel)
    target = root / rel
    require(target.resolve() == target and target.is_file(), 'SOURCE_MISSING_OR_LINK_HOLD '+rel)
    return target.read_bytes()


def stage_exact(root, stage):
    raw = read(root, 'product/SOURCE_MANIFEST.json')
    require(blob(raw) == MANIFEST, 'MANIFEST_HOLD')
    files = json.loads(raw)['files']
    entries = {'product/'+k:v for k,v in files.items() if k.startswith('ai-company-os-backend/')}
    require(len(files) == 403 and len(entries) == 248, 'MANIFEST_COUNT_HOLD')
    pin_raw = read(root, PINS)
    require(blob(pin_raw) == PIN_BLOB, 'PIN_MANIFEST_HOLD')
    pins = json.loads(pin_raw)
    require(len(pins) == 56 and pins.get(FIXTURE) == FIXTURE_BLOB, 'PIN_COUNT_HOLD')
    def put(rel, data):
        dest = stage / rel
        require(dest.is_relative_to(stage) and dest.resolve() == dest, 'STAGE_PATH_HOLD')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as f:
            f.write(data)
    for rel, entry in entries.items():
        data = read(root, rel)
        require(len(data) == entry['bytes'] and sha256(data).hexdigest() == entry['sha256'], 'SOURCE_SHA_HOLD '+rel)
        if rel in pins:
            require(blob(data) == pins[rel], 'SOURCE_PIN_HOLD '+rel)
        put(rel, data)
    for rel, expected in pins.items():
        if rel in entries:
            continue
        data = read(root, rel)
        require(blob(data) == expected, 'SOURCE_PIN_HOLD '+rel)
        put(rel, data)
    put(PINS, pin_raw)
    put('product/SOURCE_MANIFEST.json', raw)
    return {'backend_verified':len(entries), 'selected_pins_verified':len(pins),
            'external_pins_verified':len(set(pins)-set(entries)), 'manifest_blob':blob(raw)}


def result_ok(code, log):
    rows = [line[12:] for line in log.decode('utf-8', errors='replace').splitlines() if line.startswith('RESULT_JSON=')]
    expected = dict(tests=7, failures=0, errors=0, skips=0, expected_failures=0, unexpected_successes=0)
    return code == 0 and len(rows) == 1 and json.loads(rows[0]) == expected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, help='Exact G8 or G9 extracted repository root')
    parser.add_argument('--out', required=True, help='New evidence directory outside repository')
    args = parser.parse_args(argv)
    root, out = Path(args.root).resolve(), Path(args.out).resolve()
    require(not out.is_relative_to(root), 'EVIDENCE_PATH_HOLD')
    out.mkdir(parents=True, exist_ok=False)
    report = {'base_commit':BASE, 'status':'BLOCKED', 'tests':'NOT_RUN', 'exit_code':2,
              'activation':'HOLD', 'scope':'isolated synthetic SQLite; no grant or independent acceptance'}
    try:
        require(version('cryptography') == '46.0.4', 'CRYPTOGRAPHY_HOLD')
        with tempfile.TemporaryDirectory(prefix='d5g9-exact-') as tmp:
            stage = Path(tmp).resolve()
            report['verified'] = stage_exact(root, stage)
            result = subprocess.run([sys.executable,'-I','-B','-c',CHILD,str(stage/FIXTURE),json.dumps(NAMES)],
                                    cwd=stage,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False,timeout=120)
            (out/'checkout.log').write_bytes(result.stdout)
            report['log_sha256'] = sha256(result.stdout).hexdigest()
            report['child_exit_code'] = result.returncode
            report['tests'] = 'REVIEW_RAW_LOG'
            report['status'] = 'FAIL_OR_INCOMPLETE'
            report['exit_code'] = 1
            if result_ok(result.returncode,result.stdout):
                report.update(status='PASS_SELECTED_D0_READBACK',tests='7/7 PASS',exit_code=0)
    except subprocess.TimeoutExpired as exc:
        if exc.stdout:
            (out/'checkout.log').write_bytes(exc.stdout)
            report['log_sha256'] = sha256(exc.stdout).hexdigest()
        report.update(status='TIMEOUT_HOLD',tests='REVIEW_RAW_LOG',exit_code=1)
    except Exception as exc:
        report['blocker'] = type(exc).__name__+': '+str(exc)
    finally:
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        (out/'exit_code.txt').write_text(str(report['exit_code'])+'\n',encoding='ascii')
        print(json.dumps(report,indent=2))
    return report['exit_code']


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError) as exc:
        print('BLOCKED:',exc)
        sys.exit(2)
