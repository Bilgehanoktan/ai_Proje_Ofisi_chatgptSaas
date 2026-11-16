"""0213 offline fixed-source preflight. No network, DB install, or auto-test.
Usage: python scripts/diagnostic_preflight_0213.py --bundle-root ... [--run-diagnostic]
Result is NOT pinned-dependency or independent acceptance.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

EXPECTED = {'fastapi': '0.163.0', 'starlette': '1.10.0', 'cryptography': '46.0.4', 'uvicorn': '0.34.2'}
TESTS = ('test_retained_snapshot_0201', 'test_terminal_anchor_lifecycle_0203',
         'test_lifecycle_prefix_p03', 'test_lifecycle_projection_p02',
         'test_intent_authority_0211', 'test_intent_authority_t1_0212',
         'test_company_terminal_0212', 'test_company_multiproject_0213')


def verify(root):
    root = Path(root).resolve(strict=True)
    lock = json.loads((root / 'CORE_RECOVERY_0212.json').read_text(encoding='utf-8'))
    files = root / 'CORE_55'
    if not isinstance(lock, list) or len(lock) != 55:
        raise ValueError('CORE_LOCK_COUNT_HOLD')
    failures = []
    for f in lock:
        p = files / f['path']
        if not p.is_file() or p.is_symlink() or p.resolve() != p:
            failures.append([f['path'], 'MISSING_OR_PATH_HOLD'])
            continue
        body = p.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()
        digest = hashlib.sha256(body).hexdigest()
        if (len(body), digest, blob) != (f['bytes'], f['sha256'], f['git_blob']):
            failures.append([f['path'], 'SOURCE_HASH_HOLD'])
    installed = {}
    for name, required in EXPECTED.items():
        try:
            value = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            value = None
        installed[name] = {'locked': required, 'installed': value, 'matches': value == required}
    result = {'schema': '0213.d0.preflight.v1', 'source_verified':len(lock)-len(failures),
              'source_total':55, 'source_failures':failures, 'dependencies':installed,
              'locked_dependency_match':all(v['matches'] for v in installed.values()),
              'test_status':'NOT_RUN', 'acceptance':'HOLD'}
    return files / 'product' / 'ai-company-os-backend', result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle-root', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--run-diagnostic', action='store_true')
    args = parser.parse_args()
    backend, result = verify(args.bundle_root)
    if args.run_diagnostic and result['source_verified'] == 55:
        cmd = [sys.executable, '-B', '-m', 'unittest', *TESTS, '-q']
        import os
        env = dict(os.environ, PYTHONPATH='.:tests')
        proc = subprocess.run(cmd, cwd=backend, env=env, capture_output=True, text=True,
                              timeout=90, check=False)
        result['test_status'] = 'DIAGNOSTIC_PASS' if proc.returncode == 0 else 'DIAGNOSTIC_FAIL'
        result['test_return_code'] = proc.returncode
        result['test_output_sha256'] = hashlib.sha256((proc.stdout+proc.stderr).encode()).hexdigest()
        result['test_tail'] = (proc.stdout+proc.stderr)[-2500:]
        # NEVER mark pinned acceptance for this runner; lock review is separate.
    Path(args.report).write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('dependencies','test_tail')}, ensure_ascii=False))
    return int(result['source_verified'] != 55 or result['test_status'] == 'DIAGNOSTIC_FAIL')


if __name__ == '__main__':
    raise SystemExit(main())
