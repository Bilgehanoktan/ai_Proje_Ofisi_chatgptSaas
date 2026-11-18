"""Verify pinned D5-G4 imported closure and run only new isolated review tests."""
from pathlib import Path
from hashlib import sha1
import json
import subprocess
import sys
import tempfile


def main():
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    pins = json.loads((here/'SOURCE_PINS.json').read_text())
    if len(pins) != 18:
        raise ValueError('PIN_INVENTORY_HOLD')
    with tempfile.TemporaryDirectory(prefix='d5g4-review-') as temp:
        stage = Path(temp).resolve()
        for relative,expected in pins.items():
            path = root/relative
            if not path.is_relative_to(root) or path.resolve()!=path or not path.is_file():
                raise ValueError('SOURCE_PATH_HOLD '+relative)
            raw = path.read_bytes()
            if sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()!=expected:
                raise ValueError('SOURCE_PIN_HOLD '+relative)
            target=stage/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
        print(f'EXACT_SOURCE_PINS: {len(pins)}/{len(pins)}',flush=True)
        backend=stage/'product/ai-company-os-backend'
        code='import sys,unittest,sqlite3; print("Python",sys.version.split()[0],"SQLite",sqlite3.sqlite_version,flush=True); sys.path[:0]=sys.argv[1:]; s=unittest.TestLoader().loadTestsFromName("test_iam_identity_d5g4"); assert s.countTestCases()==14; r=unittest.TextTestRunner(verbosity=2).run(s); sys.exit(not r.wasSuccessful() or bool(r.skipped))'
        return subprocess.run([sys.executable,'-I','-S','-B','-c',code,str(backend),str(backend/'tests')],cwd=stage,check=False).returncode


if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError) as e: print('BLOCKED:',e); sys.exit(2)
