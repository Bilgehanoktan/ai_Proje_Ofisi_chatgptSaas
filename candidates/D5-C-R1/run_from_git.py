"""D5-C-R1: local Git object recovery for the unchanged D5-C T1 runner.
No checkout, network, package installation, server, CI or product mutation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import subprocess
import sys
import tempfile

BASE = '9b66592ff67638e0a1504d327c6cf95ef4d7ac21'
MANIFEST = 'product/SOURCE_MANIFEST.json'
MANIFEST_PIN = '981a13fc226184dc3a911ae0d94e0042285ff302'
RUNNER = 'candidates/D5-C/run_original_t1.py'
RUNNER_PIN = '14f0a4dd0bde11c5e40b4f8e5e6bf17cbaf4b392'
PREFIX = 'ai-company-os-backend/'
DDL = {
    'database/0192/candidate_event_outbox_fence.sql': '6e4780bf9f267c0926b40d582d5afdbd6faa543c',
    'database/0193/candidate_run_head.sql': '180924e97ee1f31fa27332941a41e37fdf73017e',
    'database/0194/candidate_transition_roles.sql': '7b5d374bb7973b283e4fcfa0d796ed6128ef9d27',
}
TESTS = {
    'product/'+PREFIX+'tests/test_transition_mapping_0194.py': 'a4a3827ec4267ce275efe52fe5488e1868502c3f',
    'product/'+PREFIX+'tests/test_intent_authority_t1_0212.py': '9296347d9253d74902ed1c6a89e273d8e516f2b5',
    'product/'+PREFIX+'tests/test_authority_fullchain_0214.py': '4918027e828e8e72273ee4d6a508cac3aa6e9b59',
}


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()


def git(repo, *args):
    # Disable inherited Git repository overrides and lazy promisor-object fetches.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.check_output(['git', '-C', str(repo), '-c', 'protocol.allow=never',
                                    *args], env=env, stderr=subprocess.PIPE, timeout=30)


def safe_path(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name or '\0' in name:
        raise ValueError('PATH_HOLD')
    p = PurePosixPath(name)
    if p.is_absolute() or p.as_posix() != name or any(x in ('', '.', '..') for x in p.parts):
        raise ValueError('PATH_HOLD')
    return p


def read_tree(repo, commit):
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('COMMIT_FORMAT_HOLD')
    if git(repo, 'rev-parse', '--verify', commit+'^{commit}').decode().strip() != commit:
        raise ValueError('COMMIT_HOLD')
    entries = {}
    for row in git(repo, 'ls-tree', '-r', '-z', commit).split(b'\0'):
        if row:
            meta, name = row.split(b'\t', 1)
            mode, kind, digest = meta.decode('ascii').split()
            entries[name.decode('utf-8')] = (mode, kind, digest)
    return entries


def recover(repo, stage, *, commit=BASE, manifest_pin=MANIFEST_PIN, runner_pin=RUNNER_PIN,
            prefix=PREFIX, expected=237, ddl=DDL, tests=TESTS):
    """Fixture-injectable helper; CLI always uses immutable D5-C constants."""
    if stage.is_symlink() or not stage.is_dir() or any(stage.iterdir()):
        raise ValueError('STAGE_NOT_EMPTY_HOLD')
    tree = read_tree(repo, commit)
    def read(path, pin=None):
        safe_path(path)
        mode, kind, digest = tree.get(path, (None, None, None))
        if mode != '100644' or kind != 'blob' or not re.fullmatch(r'[0-9a-f]{40}', digest or ''):
            raise ValueError('TREE_ENTRY_HOLD: '+path)
        if pin is not None and digest != pin:
            raise ValueError('PIN_HOLD: '+path)
        raw = git(repo, 'cat-file', 'blob', digest)
        if blob(raw) != digest:
            raise ValueError('BLOB_HOLD: '+path)
        return raw
    def write(path, raw):
        p = stage.joinpath(*safe_path(path).parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(raw)
    raw = read(MANIFEST, manifest_pin)
    entries = {k: v for k, v in json.loads(raw)['files'].items() if k.startswith(prefix)}
    wanted = {'product/'+k for k in entries}
    actual = {k for k in tree if k.startswith('product/'+prefix)}
    if len(entries) != expected or wanted != actual or not set(tests) <= wanted:
        raise ValueError('BACKEND_INVENTORY_HOLD')
    names = wanted | set(ddl) | {MANIFEST, RUNNER}
    if len(names) != expected + len(ddl) + 2 or len({p.casefold() for p in names}) != len(names):
        raise ValueError('PATH_COLLISION_HOLD')
    for name in names:
        safe_path(name)
    write(MANIFEST, raw)
    for key, meta in sorted(entries.items()):
        path = 'product/'+key
        raw = read(path, tests.get(path))
        if len(raw) != meta['bytes'] or hashlib.sha256(raw).hexdigest() != meta['sha256']:
            raise ValueError('MANIFEST_DRIFT_HOLD: '+path)
        write(path, raw)
    for path, pin in sorted(ddl.items()):
        write(path, read(path, pin))
    write(RUNNER, read(RUNNER, runner_pin))
    return {'backend': len(entries), 'ddl': len(ddl), 'explicit_test_pins': len(tests),
            'files': len(names)}


def outcome(returncode, raw):
    log = raw.decode('utf-8', errors='replace')
    if returncode == 2 and 'T1_REGRESSION_BLOCKED:' in log:
        return 'BLOCKED'
    if (returncode == 0 and re.search(r'^Ran 17 tests? in [^\n]+$', log, re.M)
            and log.rstrip().endswith('\nOK') and 'PIN_MATCH: 237 backend manifest entries + 3 original DDL; 3 explicit test pins' in log):
        return 'PASS_LOCAL_SQLITE_ONLY'
    return 'FAIL_OR_INCOMPLETE'


def run(repo, output):
    # New evidence directory only, outside the input repository.
    if output.is_relative_to(repo):
        raise ValueError('EVIDENCE_INSIDE_REPO_HOLD')
    output.mkdir(parents=True, exist_ok=False)
    report = {'revision': '0230-D5-C-R1', 'commit': BASE, 'status': 'BLOCKED',
              'original_t1': 'NOT_RUN', 'python': sys.version.split()[0],
              'sqlite': sqlite3.sqlite_version, 'product_changes': 0,
              'gate_promotions': 0, 'scope': 'synthetic SQLite only; no PG/IAM/independent acceptance'}
    try:
        with tempfile.TemporaryDirectory(prefix='d5c-r1-') as tmp:
            stage = Path(tmp)
            report['recovery'] = recover(repo, stage)
            command = [sys.executable, '-I', '-B', str(stage/RUNNER)]
            p = subprocess.run(command, cwd=stage, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=180, check=False)
            (output/'original_t1.log').write_bytes(p.stdout)
            report['log_sha256'] = hashlib.sha256(p.stdout).hexdigest()
            report['returncode'] = p.returncode
            report['status'] = outcome(p.returncode, p.stdout)
            report['original_t1'] = ('17_PASS' if report['status'] == 'PASS_LOCAL_SQLITE_ONLY'
                                     else 'NOT_RUN' if report['status'] == 'BLOCKED' else 'UNVERIFIED')
            return 0 if report['status'] == 'PASS_LOCAL_SQLITE_ONLY' else 2 if report['status'] == 'BLOCKED' else 1
    except subprocess.TimeoutExpired as exc:
        raw = exc.output or b''
        (output/'timeout_partial.log').write_bytes(raw)
        report.update(status='BLOCKED_TIMEOUT', original_t1='UNVERIFIED',
                      log_sha256=hashlib.sha256(raw).hexdigest())
        return 2
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        report['blocker'] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        return 2
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path, help='local repo already containing exact D5-C commit')
    parser.add_argument('--evidence', required=True, type=Path, help='new directory outside repo')
    args = parser.parse_args()
    sys.exit(run(args.repo.resolve(), args.evidence.resolve()))
