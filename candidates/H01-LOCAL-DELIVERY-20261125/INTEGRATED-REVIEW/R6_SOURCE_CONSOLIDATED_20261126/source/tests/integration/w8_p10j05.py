"""P10J-05 extension to the recovered W8 chain; preserve review and installation gates."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = '328464e636baff4488830e054db6f52690505056'
CANDIDATE_MANIFEST = '106bc3353d545cf4145093c766b8b9d18caecc5d'

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j.py')
    if p.is_symlink():
        raise ValueError('P10J_PARENT_PIN_HOLD')
    raw = p.read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()!=PARENT_BLOB:
        raise ValueError('P10J_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j05_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J05_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    test = w.test
    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):
            (stage/marker).unlink(missing_ok=True)
        f=w.frontend(stage); env=w.env_local(); out=stage/'compiled-p10j05-model'
        out.mkdir(exist_ok=False)
        w.run([w.node(),f/'node_modules/typescript/bin/tsc','--strict','--target','ES2022','--module','commonjs','--lib','ES2022,DOM','--rootDir','.','--outDir',out,'features/graph/graphPresentation.ts'],f,env)
        env.update(P10D_MODEL=str(out))
        w.run([w.node(),'--test','tests/ui-p10j05-model.test.cjs'],f,env)
        return test(stage,approval)
    w.test=test_candidate
    return w
if __name__=='__main__':
    try:
        load_candidate().main()
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as exc:
        print('HOLD:',exc,file=sys.stderr);sys.exit(1)
