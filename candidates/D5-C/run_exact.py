"""Run selected exact-source tests, in an isolated temporary source tree."""
from hashlib import sha1
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    pins=json.loads((Path(__file__).parent/'SOURCE_PINS.json').read_text())
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)
        for relative, expected in pins.items():
            p=root/relative
            if not p.is_file() or p.resolve()!=p or not p.is_relative_to(root):
                print('SOURCE_MISSING_HOLD:',relative); return 2
            raw=p.read_bytes()
            if sha1(f'blob {len(raw)}\0'.encode('ascii')+raw).hexdigest()!=expected:
                print('SOURCE_DRIFT_HOLD:',relative); return 2
            target=stage/relative; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
        print(f'PIN_MATCH: {len(pins)}/{len(pins)}',flush=True)
        paths=[str(stage/x) for x in ('candidates/D5-C','candidates/D5-B','candidates/D5-INTENT','candidates/D4-R4','product/ai-company-os-backend','product/ai-company-os-backend/tests')]
        code=('import sys,unittest; sys.path[:0]=sys.argv[1:]; '
              's=unittest.TestSuite([unittest.TestLoader().discover(sys.argv[1],pattern="test_fence_insertion.py"),'
              'unittest.TestLoader().discover(sys.argv[2],pattern="test_identity_fence_review.py"),'
              'unittest.TestLoader().discover(sys.argv[3],pattern="test_intent_identity.py"),'
              'unittest.TestLoader().loadTestsFromName("test_intent_authority_0211")]); '
              'r=unittest.TextTestRunner(verbosity=2).run(s); sys.exit(not r.wasSuccessful())')
        return subprocess.run([sys.executable,'-I','-S','-B','-c',code,*paths],cwd=stage,check=False).returncode

if __name__=='__main__':
    sys.exit(main())
