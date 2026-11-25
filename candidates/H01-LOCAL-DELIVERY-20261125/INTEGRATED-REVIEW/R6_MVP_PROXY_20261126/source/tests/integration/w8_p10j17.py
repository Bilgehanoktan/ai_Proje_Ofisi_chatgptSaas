"""P10J17: existing W8 gates plus CEO presentation regression."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = '761bdaa3dc7d4ec22d7e6e32c47bad33e03f5d02'
CANDIDATE_MANIFEST = 'd314b5cef9b40db2c48a4034248debd4fd7bfba1'
OLD_BROWSER = '4a329632e87200cc45b38e402a942971560ce530'
NEW_BROWSER = '2dc45a405400c856983e47c8efd20b39231a0390'

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j16.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J16_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j17_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J17_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    if w.HARNESS.get('browser_0187_w1.py') != OLD_BROWSER:
        raise ValueError('P10J17_BROWSER_PARENT_HOLD')
    w.HARNESS['browser_0187_w1.py'] = NEW_BROWSER
    inherited = w.test
    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):
            (stage/marker).unlink(missing_ok=True)
        f = w.frontend(stage)
        w.run([w.node(),'--test','tests/ui-p10j17-ceo.test.cjs'],f,w.env_local())
        return inherited(stage, approval)
    w.test = test_candidate
    return w

if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
