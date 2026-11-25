"""P10J-11 exact sectioned UI candidate; preserve all inherited W8 gates."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = '3561d91fa657262eec37fb63974bef5cd6781c49'
CANDIDATE_MANIFEST = '606f6449d1bdcb4a83db9e2857644761adc1a63a'
BROWSER_PINS = {
    'browser_0187_w1.py': ('8463d4104c2b7085dc325db87542288ea5fb35a4', 'fab1cb848f6fe5f1aa0f3afbe52e80accb39b9a6'),
    'browser_lifecycle_p02.py': ('d7e8760b3f366d410459b33dc16f44b1144fe231', 'e444e60d53914e78e77418fc1ac63e1dc0b7a4de'),
    'browser_lifecycle_prefix_p03.py': ('c41ea2455ce1bd6792fa829be0377344fd30e9da', '15b6f9656f5768e942fd63810d0ca1eb438edab3'),
    'browser_task_budget_0188.py': ('4511877f03ffae35d4baef7267c6d7e8ea6bf583', '70714854ccf650862602d541420ccd7b985408d0'),
}

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j10.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J10_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j11_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J11_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    for name, (before, after) in BROWSER_PINS.items():
        if w.HARNESS.get(name) != before:
            raise ValueError('P10J11_BROWSER_PARENT_HOLD: '+name)
        w.HARNESS[name] = after
    test = w.test
    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):
            (stage/marker).unlink(missing_ok=True)
        f = w.frontend(stage)
        env = w.env_local()
        out = stage/'compiled-p10j11-sections'
        out.mkdir(exist_ok=False)
        w.run([w.node(),f/'node_modules/typescript/bin/tsc','--strict','--target','ES2022','--module','commonjs','--outDir',out,'features/ceo-dashboard/sectionModel.ts'],f,env)
        env.update(P10D_MODEL=str(out))
        w.run([w.node(),'--test','tests/ui-p10j11-sections.test.cjs'],f,env)
        return test(stage, approval)
    w.test = test_candidate
    return w

if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
