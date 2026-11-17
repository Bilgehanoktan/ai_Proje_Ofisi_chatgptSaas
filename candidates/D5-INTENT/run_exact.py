"""Fail closed before the exact-source D5 unit run; no database or external effects."""
from hashlib import sha1
from pathlib import Path
import subprocess
import sys

PINS = {
    'product/ai-company-os-backend/app/core/agent_runtime/lifecycle.py': '4c4ecbba9b2b1ec56dd8f73378b56b50f6578b49',
    'product/ai-company-os-backend/app/core/transaction/review.py': '79b2b442f51bb5ea7706a33a5f9f1e7aed258cd4',
    'product/ai-company-os-backend/app/core/event_store/company_coordination.py': 'fb068ef9bececca21e6b0562b12ac41aa3d4fcc5',
    'candidates/D4-R4/identity_binding.py': 'e1e977880324664bb359eee3286223a796878f44',
    'candidates/D5-INTENT/intent_identity.py': 'fbdc75920bbcc698fb726190d52aa2e37e06a818',
    'candidates/D5-INTENT/test_intent_identity.py': '7bc6edca2f26e1970b5b63484ea8dd1d11758028',
}


def main():
    root = Path(__file__).resolve().parents[2]
    for relative, expected in PINS.items():
        path = root / relative
        if not path.is_file() or path.is_symlink():
            print('SOURCE_MISSING_HOLD:', relative)
            return 2
        raw = path.read_bytes()
        actual = sha1(f'blob {len(raw)}\0'.encode('ascii') + raw).hexdigest()
        if actual != expected:
            print('SOURCE_DRIFT_HOLD:', relative)
            return 2
    print(f'PIN_MATCH: {len(PINS)}/{len(PINS)}', flush=True)
    paths = [str(root / x) for x in ('candidates/D5-INTENT', 'candidates/D4-R4', 'product/ai-company-os-backend')]
    code = 'import sys,unittest; sys.path[:0]=sys.argv[1:]; r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(sys.argv[1],pattern="test_intent_identity.py")); sys.exit(not r.wasSuccessful())'
    return subprocess.run([sys.executable, '-I', '-B', '-c', code, *paths], cwd=root, check=False).returncode


if __name__ == '__main__':
    sys.exit(main())
