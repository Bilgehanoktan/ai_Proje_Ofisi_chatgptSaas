"""P10J-10 exact mobile-navigation candidate; preserve the P10J-08 review chain."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = '5b992e332c245ea332a1e00d16172bb1ef81f1ba'
CANDIDATE_MANIFEST = '2888802a725b269bb34edd60ff838f0eaa85381f'
OLD_BROWSER = 'b829ad9b2fa12f7910e014ec87e9ee2a59d17370'
NEW_BROWSER = '8463d4104c2b7085dc325db87542288ea5fb35a4'

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j08.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J08_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j10_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J10_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    # Update only the exact browser harness pin; retain all other checks.
    if w.HARNESS.get('browser_0187_w1.py') != OLD_BROWSER:
        raise ValueError('P10J10_BROWSER_PARENT_HOLD')
    w.HARNESS['browser_0187_w1.py'] = NEW_BROWSER
    return w

if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
