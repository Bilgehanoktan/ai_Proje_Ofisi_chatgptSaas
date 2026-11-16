"""A0C: reuse P10J-08 Windows portability helpers; preserve reviewed A0B W8."""
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager

PARENT_BLOB = '9267828684fbf905d3132d114f3566f191780793'
MANIFEST = 'f5b011cc9f72e85a7d1c371705e11e6dacfc9c42'


def portable_modules(root, files):
    seen = {}
    for name in files:
        p = Path(name)
        if p.suffix not in ('.ts', '.tsx', '.js', '.jsx'):
            continue
        key = p.with_suffix('').as_posix().casefold()
        if key in seen:
            raise ValueError('PORTABLE_MODULE_COLLISION: ' + seen[key] + ' / ' + name)
        seen[key] = name
        if p.suffix in ('.ts', '.tsx'):
            source = (root / 'product' / p).read_text(encoding='utf-8')
            if re.search(r"""['"][^'"\n]*/(?:HistoricalEvidence|DependencyNeighborhood)['"]""", source):
                raise ValueError('STALE_COMPONENT_IMPORT: ' + name)


@contextmanager
def windows_temp(stage, w):
    if os.name != 'nt':
        yield
        return
    original = {k: os.environ.get(k) for k in ('TEMP', 'TMP', 'TMPDIR')}
    with tempfile.TemporaryDirectory(prefix='aicos-w8-', dir=stage.parent.resolve(strict=True)) as tmp:
        root = Path(tmp).resolve(strict=True)
        try:
            os.environ.update({k: str(root) for k in original})
            w.run([w.python(stage), '-B', '-c',
                   'import sys,tempfile;from pathlib import Path; '
                   'assert Path(tempfile.gettempdir()).resolve(strict=True)==Path(sys.argv[1]), "TEMP_LOCATION_HOLD"',
                   root], stage, w.env_local())
            yield
        finally:
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def extend_candidate(w):
    verify, test, smoke = w.verify, w.test, w.smoke

    def verify_portable(repo, pin=MANIFEST, clean=False):
        files, pairs = verify(repo, pin=pin, clean=clean)
        portable_modules(repo, files)
        return files, pairs

    def guarded(stage, approval, markers, call):
        w.installed(stage, approval)
        for name in markers:
            (stage/name).unlink(missing_ok=True)
        try:
            with windows_temp(stage, w):
                return call()
        except Exception:
            for name in markers:
                (stage/name).unlink(missing_ok=True)
            raise

    def test_candidate(stage, approval):
        return guarded(stage, approval, ('BUILD_TEST_OK','SMOKE_OK','NATIVE_SMOKE_OK'),
                       lambda: test(stage, approval))

    def smoke_candidate(stage, approval, chromium, frontend_port=17300, backend_port=17301):
        return guarded(stage, approval, ('SMOKE_OK','NATIVE_SMOKE_OK'),
                       lambda: smoke(stage, approval, chromium, frontend_port, backend_port))

    w.verify, w.test, w.smoke = verify_portable, test_candidate, smoke_candidate
    return w


def load_candidate():
    p = Path(__file__).resolve().with_name('w8_ux_a0b.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('UX_A0B_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('ux_a0c_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('UX_A0C_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.MANIFEST = MANIFEST
    w = parent.load_candidate()
    if w.MANIFEST_BLOB != MANIFEST:
        raise ValueError('UX_A0C_MANIFEST_REBIND_HOLD')
    return extend_candidate(w)


if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
