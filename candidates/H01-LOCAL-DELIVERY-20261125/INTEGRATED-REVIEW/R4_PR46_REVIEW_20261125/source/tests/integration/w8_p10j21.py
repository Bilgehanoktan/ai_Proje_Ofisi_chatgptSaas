"""P10J21: isolated capability catalog model checks, inherited W8 unchanged."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = '51ffc6c176c5bcbbec3308708bcd224d7a1f8f95'
CANDIDATE_MANIFEST = 'ce8b61352b9b56825a8ecd01238025fc07b7d2d2'
MARKERS = ('BUILD_TEST_OK', 'SMOKE_OK', 'HYBRID_NATIVE_OK')


def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j20.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J20_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j21_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J21_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    if w.MANIFEST_BLOB != CANDIDATE_MANIFEST:
        raise ValueError('P10J21_MANIFEST_HOLD')
    inherited = w.test

    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in MARKERS:
            (stage/marker).unlink(missing_ok=True)
        try:
            f = w.frontend(stage)
            env = dict(w.env_local())
            out = stage/'compiled-p10j21-capabilities'
            out.mkdir(exist_ok=False)
            tsc = f/'node_modules/typescript/bin/tsc'
            w.run([w.node(), tsc, '--strict', '--target', 'ES2022', '--module', 'commonjs', '--outDir', out, 'features/capabilities/studioCatalog.ts'], f, env)
            env['P10J21_MODEL'] = str((out/'studioCatalog.js').resolve())
            w.run([w.node(), '--test', 'tests/ui-p10j21-capabilities.test.cjs'], f, env)
            return inherited(stage, approval)
        except Exception:
            for marker in MARKERS:
                (stage/marker).unlink(missing_ok=True)
            raise
    w.test = test_candidate
    return w


if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
