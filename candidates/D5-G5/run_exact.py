"""Stage exact source pins; run 12 new tests and 14 unchanged G4 tests."""
from pathlib import Path
from hashlib import sha1
import json, subprocess, sys, tempfile

def main():
    here=Path(__file__).resolve().parent
    root=here.parents[1]
    pins=json.loads((here/'SOURCE_PINS.json').read_text())
    if len(pins)!=31:
        raise ValueError('PIN_INVENTORY_HOLD')
    with tempfile.TemporaryDirectory(prefix='d5g5-review-') as tmp:
        stage=Path(tmp).resolve()
        for rel,expected in pins.items():
            p=root/rel
            if not p.is_relative_to(root) or p.resolve()!=p or not p.is_file():
                raise ValueError('PATH_HOLD '+rel)
            raw=p.read_bytes()
            if sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()!=expected:
                raise ValueError('PIN_HOLD '+rel)
            out=stage/rel
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_bytes(raw)
        print(f'EXACT_SOURCE_PINS: {len(pins)}/{len(pins)}',flush=True)
        backend=stage/'product/ai-company-os-backend'
        org=stage/'candidates/ORG-05R3'
        code='import sys,unittest,sqlite3; print("Python",sys.version.split()[0],"SQLite",sqlite3.sqlite_version,flush=True); sys.path[:0]=sys.argv[1:]; l=unittest.TestLoader(); s=l.loadTestsFromNames(["test_iam_org_d5g5","test_iam_identity_d5g4"]); assert s.countTestCases()==26; r=unittest.TextTestRunner(verbosity=2).run(s); sys.exit(not r.wasSuccessful() or bool(r.skipped))'
        return subprocess.run([sys.executable,'-I','-S','-B','-c',code,str(backend),str(backend/'tests'),str(org)],cwd=stage,check=False).returncode

if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError) as e: print('BLOCKED:',e); sys.exit(2)
