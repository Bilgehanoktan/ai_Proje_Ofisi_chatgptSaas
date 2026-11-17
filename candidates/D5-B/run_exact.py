"""Verify full imported source closure and run in a clean temporary source tree."""
from hashlib import sha1
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    pins = json.loads((Path(__file__).parent/'SOURCE_PINS.json').read_text())
    with tempfile.TemporaryDirectory() as stage:
        stage = Path(stage)
        for relative, expected in pins.items():
            path = root / relative
            if not path.is_file() or path.resolve() != path or not path.is_relative_to(root):
                print('SOURCE_MISSING_HOLD:', relative)
                return 2
            raw = path.read_bytes()
            if sha1(f'blob {len(raw)}\0'.encode('ascii')+raw).hexdigest() != expected:
                print('SOURCE_DRIFT_HOLD:', relative)
                return 2
            dest = stage / relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(raw)
        print(f'PIN_MATCH: {len(pins)}/{len(pins)}',flush=True)
        paths = [str(stage / x) for x in ('candidates/D5-B','candidates/D5-INTENT','candidates/D4-R4','product/ai-company-os-backend')]
        code = ('import sys,unittest; sys.path[:0]=sys.argv[1:]; '
                's=unittest.TestSuite([unittest.TestLoader().discover(sys.argv[1],pattern="test_identity_fence_review.py"),'
                'unittest.TestLoader().discover(sys.argv[2],pattern="test_intent_identity.py")]); '
                'r=unittest.TextTestRunner(verbosity=2).run(s); sys.exit(not r.wasSuccessful())')
        return subprocess.run([sys.executable,'-I','-S','-B','-c',code,*paths],cwd=stage,check=False).returncode


if __name__=='__main__':
    sys.exit(main())
