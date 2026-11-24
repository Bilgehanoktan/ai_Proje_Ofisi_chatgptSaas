"""P10J19: inherited W8 plus Project roadmap and exact A4 model checks."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = '0159c24f93cfe209193d828f04df0576a1a6b4e4'
CANDIDATE_MANIFEST = '6caabe5948967e1532a117e99780e7fb90b1b968'
OLD_BROWSER = '9d4a741e9c8b4e643e494b0c19f0d789d6967a17'
NEW_BROWSER = 'baac24da1edba991a240a0c41258f0f9a35d95fa'

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j18.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J18_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j19_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J19_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    if w.HARNESS.get('browser_0187_w1.py') != OLD_BROWSER:
        raise ValueError('P10J19_BROWSER_PARENT_HOLD')
    w.HARNESS['browser_0187_w1.py'] = NEW_BROWSER
    inherited = w.test
    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):
            (stage/marker).unlink(missing_ok=True)
        f = w.frontend(stage)
        env = w.env_local()
        w.run([w.node(),'--test','tests/ui-p10j19-roadmap.test.cjs'],f,env)
        out = stage/'compiled-p10j19-a4'
        out.mkdir(exist_ok=False)
        tsc = f/'node_modules/typescript/bin/tsc'
        w.run([w.node(),tsc,'--strict','--target','ES2022','--module','commonjs','--outDir',out,'office/engine/premiumHybridRender.ts','office/engine/premiumModel.ts'],f,env)
        w.run([w.node(),f/'tests/premium-hybrid-render.test.cjs',out/'premiumHybridRender.js',out/'premiumActorIdentity.js'],f,env)
        return inherited(stage, approval)
    w.test = test_candidate
    return w

if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
