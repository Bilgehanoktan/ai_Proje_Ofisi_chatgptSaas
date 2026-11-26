"""Run the exact 0207 candidate core slice in a disposable directory, no CI."""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

LOCK_BLOB = '223f6fbd28cf4c428c07eb60dda4a36f644fa58c'
HELPER_BLOB = 'befb9f429791a01b2fe37009e40f994a5924b2ff'
MODULES = {'test_retained_snapshot_0201': 5, 'test_terminal_anchor_lifecycle_0203': 7,
           'test_lifecycle_projection_p02': 8, 'test_lifecycle_prefix_p03': 9}


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--check-only', action='store_true')
    p.add_argument('--diagnostic-unpinned', action='store_true',
                   help='Explicit synthetic diagnostic only, not lock/build acceptance')
    args = p.parse_args()
    if args.report.exists() or args.report.is_symlink():
        p.error('report must not exist')
    home = Path(__file__).resolve().parent
    result = {'revision': '0207', 'status': 'HOLD', 'passed': None, 'scope': 'D0 only'}
    try:
        raw = (home/'core_0207_source_lock.json').read_bytes()
        if blob(raw) != LOCK_BLOB:
            raise ValueError('LOCK_BLOB_MISMATCH')
        lock = json.loads(raw)
        helper = home/'run_lifecycle_p05.py'
        if blob(helper.read_bytes()) != HELPER_BLOB:
            raise ValueError('HELPER_BLOB_MISMATCH')
        if len(lock['files']) != 55 or {x['module']: x['count'] for x in lock['tests']} != MODULES:
            raise ValueError('LOCK_SCOPE_MISMATCH')
        if sys.version_info < (3, 10) or sqlite3.sqlite_version_info < (3, 37):
            raise ValueError('PYTHON_OR_SQLITE_VERSION_HOLD')
        spec = importlib.util.spec_from_file_location('historical_p05_helper', helper)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory(prefix='aicos-0207-') as tmp:
            stage = Path(tmp)
            mod.materialize(args.source, stage, lock)
            result.update(source_commit=lock['source_commit'], verified_files=55)
            if args.check_only:
                result['status'] = 'SOURCE_MATCH_TESTS_NOT_RUN'
            else:
                actual = {}
                for name in lock['direct_dependency_pins']:
                    try:
                        actual[name] = importlib.metadata.version(name)
                    except importlib.metadata.PackageNotFoundError:
                        actual[name] = None
                result['dependency_versions'] = actual
                if actual != lock['direct_dependency_pins'] and not args.diagnostic_unpinned:
                    raise ValueError('DIRECT_DEPENDENCY_PIN_MISMATCH')
                result['environment'] = 'DIRECT_PINS_MATCH_TRANSITIVE_REVIEW_SEPARATE' if actual == lock['direct_dependency_pins'] else 'DIAGNOSTIC_UNPINNED'
                result.update(mod.run_cases(stage, MODULES))
                for info in lock['files']:
                    mod.check_bytes((stage/info['path']).read_bytes(), info)
    except (OSError, ValueError, KeyError, TypeError, ImportError, subprocess.SubprocessError) as exc:
        result.update(status='HOLD', passed=None, reason=str(exc))
    with args.report.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    return 0 if result['status'] in ('PASS', 'SOURCE_MATCH_TESTS_NOT_RUN') else 1


if __name__ == '__main__':
    sys.exit(main())
