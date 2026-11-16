"""P10J-08: portable module names and scoped Windows temp; preserve W8 review gates."""
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager

PARENT_BLOB = '761801aabad805dd254b720e6bcd5cf1c1daf910'
CANDIDATE_MANIFEST = '2a555e7e511fe80078b233324f3442d79cd590c6'

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

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j05.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J05_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j08_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J08_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    verify, test, smoke = w.verify, w.test, w.smoke
    def verify_portable(repo, pin=CANDIDATE_MANIFEST, clean=False):
        files, pairs = verify(repo, pin=pin, clean=clean)
        portable_modules(repo, files)
        return files, pairs
    def test_candidate(stage, approval):
        w.installed(stage, approval)
        with windows_temp(stage, w):
            return test(stage, approval)
    def smoke_candidate(stage, approval, chromium, frontend_port=17300, backend_port=17301):
        w.installed(stage, approval)
        with windows_temp(stage, w):
            return smoke(stage, approval, chromium, frontend_port, backend_port)
    w.verify, w.test, w.smoke = verify_portable, test_candidate, smoke_candidate
    return w

if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
