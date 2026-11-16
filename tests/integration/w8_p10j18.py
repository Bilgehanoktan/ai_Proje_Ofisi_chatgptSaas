"""P10J18: existing W8 plus Agent profile and exact premium A3 regression."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = 'a1afc60ca42e301394ded0e2a8d8564602cc6096'
CANDIDATE_MANIFEST = 'a234ce2017432b88d1cabad37872d3f8444850ee'
OLD_BROWSER = '2dc45a405400c856983e47c8efd20b39231a0390'
NEW_BROWSER = '9d4a741e9c8b4e643e494b0c19f0d789d6967a17'

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j17.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J17_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j18_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J18_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    if w.HARNESS.get('browser_0187_w1.py') != OLD_BROWSER:
        raise ValueError('P10J18_BROWSER_PARENT_HOLD')
    w.HARNESS['browser_0187_w1.py'] = NEW_BROWSER
    inherited = w.test
    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):
            (stage/marker).unlink(missing_ok=True)
        f = w.frontend(stage)
        env = w.env_local()
        w.run([w.node(),'--test','tests/ui-p10j18-agent-profile.test.cjs'],f,env)
        out = stage/'compiled-p10j18-a3'
        out.mkdir(exist_ok=False)
        tsc = f/'node_modules/typescript/bin/tsc'
        w.run([w.node(),tsc,'--strict','--target','ES2022','--module','commonjs','--outDir',out,'office/engine/premiumIdentityTraffic.ts','office/engine/premiumModel.ts'],f,env)
        w.run([w.node(),f/'tests/premium-identity-traffic.test.cjs',out/'premiumIdentityTraffic.js',out/'premiumActorIdentity.js',out/'premiumHybridLayout.js'],f,env)
        return inherited(stage, approval)
    w.test = test_candidate
    return w

if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
