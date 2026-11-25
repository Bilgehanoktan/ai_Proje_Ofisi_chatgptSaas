"""P10J14 pinned candidate; no W8 acceptance shortcut."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = 'f6ff5605e13ef23a731b51d7ff292f181ac6f27e'
CANDIDATE_MANIFEST = 'aecff74cb7c9084d80a90cf7f317545c5e086e4e'

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j12.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J12_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j14_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J14_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    test = w.test
    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):
            (stage/marker).unlink(missing_ok=True)
        f = w.frontend(stage)
        env = w.env_local()
        out = stage/'compiled-p10j14-governance'
        out.mkdir(exist_ok=False)
        tsc = f/'node_modules/typescript/bin/tsc'
        w.run([w.node(),tsc,'--strict','--target','ES2022','--module','commonjs','--outDir',out,'features/evidence/studioGovernance.ts'],f,env)
        env.update(P10J14_MODEL=str(out/'studioGovernance.js'))
        w.run([w.node(),'--test','tests/ui-p10j14-governance.test.cjs'],f,env)
        w.run([w.node(),'scripts/run-studio-0223.cjs'],f,{**env,'AICOS_PYTHON':str(w.python(stage)),'AICOS_TSC':str(tsc)})
        return test(stage, approval)
    w.test = test_candidate
    return w

if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
