"""P10J-12: exact Agent/Office presentation candidate, retaining inherited W8 gates."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = '26c724dd847f392f38c7abea549e8acfe60cbe48'
CANDIDATE_MANIFEST = '0c7a84225766444c1b2bf00c799c0d539dd47c61'
OLD_BROWSER = 'fab1cb848f6fe5f1aa0f3afbe52e80accb39b9a6'
NEW_BROWSER = '757ee7326165624b8f01bec14e0b43f5c8573497'

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j11.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J11_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j12_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J12_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    if w.HARNESS.get('browser_0187_w1.py') != OLD_BROWSER:
        raise ValueError('P10J12_BROWSER_PARENT_HOLD')
    w.HARNESS['browser_0187_w1.py'] = NEW_BROWSER
    test = w.test
    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):
            (stage/marker).unlink(missing_ok=True)
        f = w.frontend(stage)
        env = w.env_local()
        out = stage/'compiled-p10j12-studio'
        out.mkdir(exist_ok=False)
        w.run([w.node(),f/'node_modules/typescript/bin/tsc','--strict','--target','ES2022','--module','commonjs','--outDir',out,'features/evidence/studioContext.ts'],f,env)
        env.update(P10D_MODEL=str(out))
        w.run([w.node(),'--test','tests/ui-p10j12-studio.test.cjs'],f,env)
        return test(stage, approval)
    w.test = test_candidate
    return w

if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
