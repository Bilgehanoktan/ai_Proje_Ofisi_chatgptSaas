"""P10J24: separate exact historical 0207 regression from current product tests."""
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile

PARENT_BLOB = '7a386554e51caed2db89ae94afc8215277f76c3c'
CANDIDATE_MANIFEST = '614c1d4c7d0b48540927daca9aadf34e7b7b8008'
LOCK_BLOB = '223f6fbd28cf4c428c07eb60dda4a36f644fa58c'
LOCK = 'tests/integration/core_0207_source_lock.json'
RUNNER = 'tests/integration/run_core_0207.py'
PREFIX = 'product/ai-company-os-backend/'
HISTORY = 'tests/integration/historical_0207/'
HISTORICAL = {
    PREFIX+'app/api/lifecycle_prefix_projection.py': 'b465e37d2959b1c29dd0e14980f286de86c1c906',
    PREFIX+'app/core/agent_runtime/scheduler_review.py': '719ce306304bca7b294483c1a8f7c74c64dd0b73',
    PREFIX+'app/core/transaction/postgres_admission_mapping.py': '0a3ce60662254b8f1e5bb27c9dd6c2ae2656d254',
}
MARKERS = ('BUILD_TEST_OK', 'SMOKE_OK', 'HYBRID_NATIVE_OK')


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()


def safe_path(root, name):
    p = PurePosixPath(name)
    if not p.parts or p.is_absolute() or name != p.as_posix() or '\\' in name or ':' in name or '..' in p.parts:
        raise ValueError('P10J24_UNSAFE_PATH')
    path = root / name
    if path.resolve() != path.absolute() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('P10J24_UNSAFE_PATH')
    return path


def read_exact(root, name, expected):
    p = safe_path(root, name)
    if not p.is_file():
        raise ValueError('P10J24_SOURCE_MISSING: '+name)
    raw = p.read_bytes()
    if len(raw) != expected['bytes'] or blob(raw) != expected['git_blob'] or (expected['sha256'] is not None and hashlib.sha256(raw).hexdigest() != expected['sha256']):
        raise ValueError('P10J24_SOURCE_PIN_HOLD: '+name)
    return raw


def materialize_locked(stage, dest, entries, replacements):
    """Copy pinned bytes only, with replacements outside the product tree."""
    if not dest.is_dir() or dest.is_symlink() or any(dest.iterdir()) or dest.resolve().is_relative_to(stage.resolve()):
        raise ValueError('P10J24_DESTINATION_HOLD')
    names = [row['path'] for row in entries]
    if len(set(names)) != len(names) or not set(replacements).issubset(names):
        raise ValueError('P10J24_LOCK_SCOPE_HOLD')
    for row in entries:
        name = row['path']
        raw = read_exact(stage, replacements.get(name, name), row)
        out = safe_path(dest, name)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('xb') as f:
            f.write(raw)


def materialize_history(stage, dest):
    raw = safe_path(stage, LOCK).read_bytes()
    if blob(raw) != LOCK_BLOB:
        raise ValueError('P10J24_LOCK_PIN_HOLD')
    lock = json.loads(raw)
    entries = lock['files']
    if lock['source_commit'] != '614aa63efbd0a95d0fa5fe47390df043d773370f' or len(entries) != 55:
        raise ValueError('P10J24_LOCK_SCOPE_HOLD')
    observed = {row['path']:row['git_blob'] for row in entries}
    if any(observed.get(name) != expected for name, expected in HISTORICAL.items()):
        raise ValueError('P10J24_HISTORY_PIN_HOLD')
    materialize_locked(stage, dest, entries, {p:HISTORY+p[len(PREFIX):] for p in HISTORICAL})


def extend_candidate(w):
    if w.MANIFEST_BLOB != CANDIDATE_MANIFEST:
        raise ValueError('P10J24_MANIFEST_HOLD')
    verify_aux, inherited = w.verify_aux, w.test
    extra = {HISTORY+p[len(PREFIX):]:h for p,h in HISTORICAL.items()}

    def verify_aux_candidate(root):
        pins = verify_aux(root)
        if set(pins)&set(extra):
            raise ValueError('P10J24_AUX_COLLISION_HOLD')
        for name, expected in extra.items():
            p = safe_path(root, name)
            if not p.is_file() or blob(p.read_bytes()) != expected:
                raise ValueError('P10J24_HISTORICAL_AUX_HOLD: '+name)
        return {**pins, **extra}

    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for name in MARKERS:
            (stage/name).unlink(missing_ok=True)
        run = w.run
        runs = 0
        expected = [str(w.python(stage)), str(stage/RUNNER), '--source', str(stage), '--report', str(stage/'core29-p10f.json')]

        def hook(args, cwd, env=None):
            nonlocal runs
            actual = list(map(str, args))
            if len(actual)>1 and actual[1] == str(stage/RUNNER):
                if runs or actual != expected or Path(cwd) != stage:
                    raise ValueError('P10J24_CORE29_CALL_HOLD')
                w.verify_aux(stage)
                with tempfile.TemporaryDirectory(prefix='aicos-p10j24-history-') as tmp:
                    dest = Path(tmp).resolve()
                    materialize_history(stage, dest)
                    changed = list(args)
                    changed[3] = dest
                    result = run(changed, cwd, env)
                runs += 1
                return result
            return run(args, cwd, env)

        w.run = hook
        try:
            result = inherited(stage, approval)
            if runs != 1 or (stage/'BUILD_TEST_OK').read_text(encoding='utf-8') != approval:
                raise ValueError('P10J24_CORE29_REQUIRED_HOLD')
            w.reviewed(stage, approval)
            return result
        except Exception:
            for name in MARKERS:
                (stage/name).unlink(missing_ok=True)
            raise
        finally:
            w.run = run
    w.verify_aux, w.test = verify_aux_candidate, test_candidate
    return w


def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j23.py')
    if p.is_symlink() or blob(p.read_bytes()) != PARENT_BLOB:
        raise ValueError('P10J23_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j24_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J24_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    return extend_candidate(parent.load_candidate())


if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
