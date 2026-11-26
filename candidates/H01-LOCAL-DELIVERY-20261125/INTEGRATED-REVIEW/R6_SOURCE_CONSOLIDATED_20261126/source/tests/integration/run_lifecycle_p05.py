"""Recover and execute only the pinned P02/P03 D0 lifecycle cases (no CI/PG/providers)."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import stat
import subprocess
import sys
import tempfile
import zipfile

LOCK_BLOB = '44ba5836b086b576c45d50ace2e64152f41c9adc'
SOURCE = '4ead00903f34e0226f0ca6475c89aaeacb9de364'
BACKEND = 'product/ai-company-os-backend'
MODULES = {'test_lifecycle_projection_p02': 8, 'test_lifecycle_prefix_p03': 9}


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def load_lock(path):
    data = Path(path).read_bytes()
    if blob(data) != LOCK_BLOB:
        raise ValueError('LOCK_BLOB_MISMATCH')
    lock = json.loads(data)
    if (lock['source_commit'] != SOURCE or len(lock['files']) != 44
            or {x['module']: x['count'] for x in lock['tests']} != MODULES):
        raise ValueError('LOCK_SCOPE_MISMATCH')
    return lock


def safe_name(name):
    p = PurePosixPath(name)
    if (p.is_absolute() or '\\' in name or ':' in name or name != p.as_posix()
            or any(x in ('.', '..') for x in p.parts) or not p.parts):
        raise ValueError('UNSAFE_SOURCE_PATH')
    return p


def check_bytes(data, info):
    if len(data) != info['bytes'] or blob(data) != info['git_blob']:
        raise ValueError('SOURCE_BLOB_MISMATCH: ' + info['path'])
    if info['sha256'] and hashlib.sha256(data).hexdigest() != info['sha256']:
        raise ValueError('SOURCE_SHA256_MISMATCH: ' + info['path'])


def materialize(source, stage, lock):
    """Copy only exact pinned regular files; never extract arbitrary ZIP members."""
    source, stage = Path(source).resolve(), Path(stage).resolve()
    if not stage.is_dir() or any(stage.iterdir()):
        raise ValueError('STAGE_NOT_EMPTY')
    entries = lock['files']
    names = [str(safe_name(info['path'])) for info in entries]
    if len(set(names)) != len(names):
        raise ValueError('DUPLICATE_LOCK_PATH')
    if source.is_dir():
        def read(info):
            p = source / info['path']
            if p.resolve() != p or not p.is_file() or p.stat().st_size != info['bytes']:
                raise ValueError('SOURCE_FILE_MISSING_OR_UNSAFE: ' + info['path'])
            return p.read_bytes()
        _copy(entries, stage, read)
    else:
        with zipfile.ZipFile(source) as z:
            members = {}
            wanted = set(names)
            for item in z.infolist():
                if item.is_dir():
                    continue
                name = item.filename
                # Accept exact root paths or GitHub's single archive root directory.
                rest = name.split('/', 1)[-1]
                match = name if name in wanted else rest if rest in wanted else None
                if match is None:
                    continue
                safe_name(name)
                mode = (item.external_attr >> 16) & 0o170000
                if match in members or mode not in (0, stat.S_IFREG):
                    raise ValueError('DUPLICATE_OR_NONREGULAR_ZIP_MEMBER: ' + match)
                members[match] = item
            def read(info):
                item = members.get(info['path'])
                if item is None or item.file_size != info['bytes']:
                    raise ValueError('ZIP_MEMBER_MISSING_OR_SIZE_MISMATCH: ' + info['path'])
                return z.read(item)
            _copy(entries, stage, read)


def _copy(entries, stage, read):
    for info in entries:
        data = read(info)
        check_bytes(data, info)
        path = stage / info['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(data)


CHILD = r'''
import json, sys, unittest, sqlite3
from pathlib import Path
root = Path.cwd()
sys.path[:0] = [str(root), str(root/'tests')]
import fastapi
modules = json.loads(sys.argv[1])
class Results(unittest.TestResult):
    def __init__(self):
        super().__init__(); self.cases = {}
    def addSuccess(self, test):
        super().addSuccess(test); self.cases[test.id()] = 'PASS'
    def addFailure(self, test, err):
        super().addFailure(test, err); self.cases[test.id()] = 'FAIL'
    def addError(self, test, err):
        super().addError(test, err); self.cases[test.id()] = 'ERROR'
    def addSkip(self, test, reason):
        super().addSkip(test, reason); self.cases[test.id()] = 'SKIP'
    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None: self.cases[test.id()] = 'FAIL_SUBTEST'
loader = unittest.TestLoader()
results = {}
for name, expected in modules.items():
    suite = loader.loadTestsFromName(name)
    r = Results()
    suite.run(r)
    results[name] = {'expected': expected, 'ran': r.testsRun, 'cases': r.cases,
      'failures': r.failures and [str(x[0]) for x in r.failures] or [],
      'errors': r.errors and [str(x[0]) for x in r.errors] or [],
      'skipped': len(r.skipped), 'successful': r.wasSuccessful()}
print(json.dumps({'modules':results, 'python':sys.version.split()[0], 'sqlite':sqlite3.sqlite_version, 'fastapi':fastapi.__version__}))
'''


def run_cases(stage, modules):
    backend = Path(stage) / BACKEND
    allowed = {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','TMPDIR','LANG','LC_ALL'}
    env = {k:v for k,v in os.environ.items() if k.upper() in allowed}
    env.update(NO_PROXY='*', no_proxy='*')
    p = subprocess.run([sys.executable, '-I', '-B', '-c', CHILD, json.dumps(modules)],
                       cwd=backend, env=env, capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        raise ValueError('TEST_PROCESS_FAILED: ' + p.stderr[-1500:])
    result = json.loads(p.stdout)
    if set(result['modules']) != set(modules):
        raise ValueError('TEST_MODULE_SET_MISMATCH')
    for name, expected in modules.items():
        row = result['modules'][name]
        row['accepted'] = (row['expected'] == expected == row['ran'] == len(row['cases'])
                           and row['successful'] and row['skipped'] == 0
                           and all(k.startswith(name+'.') and v == 'PASS' for k,v in row['cases'].items()))
    result['passed'] = sum(v == 'PASS' for row in result['modules'].values() for v in row['cases'].values())
    result['status'] = 'PASS' if all(row['accepted'] for row in result['modules'].values()) else 'FAIL'
    return result


def execute(source, lock):
    if sys.version_info < (3,10) or sqlite3.sqlite_version_info < (3,37):
        raise ValueError('PYTHON_OR_SQLITE_VERSION_HOLD')
    with tempfile.TemporaryDirectory(prefix='aicos-p05-') as temp:
        stage = Path(temp)
        materialize(source, stage, lock)
        result = run_cases(stage, MODULES)
        for info in lock['files']:
            check_bytes((stage/info['path']).read_bytes(), info)
        return {'source_commit':SOURCE, 'verified_files':len(lock['files']),
                'scope':'D0 SQLite fixture and direct API handler only', **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Pinned archive or checkout')
    parser.add_argument('--lock', type=Path, default=Path(__file__).with_name('lifecycle_p05_source_lock.json'))
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists() or args.report.is_symlink():
        parser.error('report must not exist')
    try:
        result = execute(args.source, load_lock(args.lock))
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
        result = {'source_commit':SOURCE,'status':'HOLD','reason':str(exc),'passed':None}
    with args.report.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
