"""P10J15 exact validation candidate; inherited W8 gates remain mandatory."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = '02da55f178dd3c4ea1f31dce8d91ae9c1ca36906'
CANDIDATE_MANIFEST = 'e0dfff291acf9fab0893569bbc8be855a12d58d3'
OLD_BROWSER = '757ee7326165624b8f01bec14e0b43f5c8573497'
NEW_BROWSER = 'b4685f647ddfa97854fc09ab003c90f5064cd24d'

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j14.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J14_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j15_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J15_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    if w.HARNESS.get('browser_0187_w1.py') != OLD_BROWSER:
        raise ValueError('P10J15_BROWSER_PARENT_HOLD')
    w.HARNESS['browser_0187_w1.py'] = NEW_BROWSER
    test = w.test
    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):
            (stage/marker).unlink(missing_ok=True)
        f = w.frontend(stage)
        env = w.env_local()
        out = stage/'compiled-p10j15-presentation'
        out.mkdir(exist_ok=False)
        tsc = f/'node_modules/typescript/bin/tsc'
        w.run([w.node(),tsc,'--strict','--target','ES2022','--module','commonjs','--lib','ES2022,DOM','--outDir',out,'features/mvp/historicalPresentation.ts'],f,env)
        env.update(AICOS_UI_BUILD=str(out))
        w.run([w.node(),'--test','tests/historical-presentation-0215.test.cjs'],f,env)
        return test(stage, approval)
    w.test = test_candidate
    return w

if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
