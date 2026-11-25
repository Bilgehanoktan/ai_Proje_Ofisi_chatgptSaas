"""P10J23: re-pin inherited W8; standalone CSS fixture is separate evidence."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = 'e61d094aa1906592219952cc67c57345983b6a71'
CANDIDATE_MANIFEST = '614c1d4c7d0b48540927daca9aadf34e7b7b8008'


def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j22.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J22_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j23_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J23_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    if w.MANIFEST_BLOB != CANDIDATE_MANIFEST:
        raise ValueError('P10J23_MANIFEST_HOLD')
    return w


if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
