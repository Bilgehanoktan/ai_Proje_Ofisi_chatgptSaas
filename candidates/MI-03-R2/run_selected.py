"""MI-03 selected product import closure, unchanged original tests. No DB or runtime."""
from hashlib import sha1, sha256
from pathlib import Path
import importlib
import importlib.util
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'product/ai-company-os-backend'
PINS = {
    'app/__init__.py': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
    'app/core/__init__.py': '9d457472970b7f581687ba142d1bf99ba91c7388',
    'app/core/agent_runtime/__init__.py': '5b19819cd7070302e874ecee80170a3921ce8fb0',
    'app/core/agent_runtime/lifecycle.py': '4c4ecbba9b2b1ec56dd8f73378b56b50f6578b49',
    'app/core/event_store/__init__.py': 'c4c3c4dd20cc9a7e1e76fc80c231f223467fdd78',
    'app/core/event_store/ledger.py': 'e3f94cab61a27c7d4c89d02516887146b2026eb3',
    'app/core/event_store/company_coordination.py': 'fb068ef9bececca21e6b0562b12ac41aa3d4fcc5',
    'app/core/transaction/__init__.py': '5b19819cd7070302e874ecee80170a3921ce8fb0',
    'app/core/transaction/review.py': '79b2b442f51bb5ea7706a33a5f9f1e7aed258cd4',
    'app/core/transaction/identity_binding.py': 'e1e977880324664bb359eee3286223a796878f44',
    'app/core/transaction/intent_identity.py': '472b2a5fd935b59cec22a248853cd5b0f301a8e9',
}
TESTS = {
    'candidates/D4-R4/test_identity_binding.py': 'b98d86e46be32451479c3cbdc39ddf6ff1611c73',
    'candidates/D5-INTENT/test_intent_identity.py': '7bc6edca2f26e1970b5b63484ea8dd1d11758028',
}


def verify(path, expected):
    if path.resolve() != path or not path.is_file():
        raise RuntimeError('SOURCE_PATH_HOLD: ' + str(path))
    raw = path.read_bytes()
    if sha1(f'blob {len(raw)}\0'.encode('ascii') + raw).hexdigest() != expected:
        raise RuntimeError('SOURCE_PIN_HOLD: ' + str(path))
    compile(raw, str(path), 'exec')
    return {'blob': expected, 'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}


def main():
    verified = {str((BACKEND / p).relative_to(ROOT)): verify(BACKEND / p, h) for p, h in PINS.items()}
    verified.update({p: verify(ROOT / p, h) for p, h in TESTS.items()})
    print('MI03_EXACT_SELECTED_SOURCE_PINS:', len(verified), '/', len(verified), flush=True)
    print('PYTHON:', sys.version.split()[0], flush=True)
    print('SELECTED_FILE_HASHES:', json.dumps(verified, sort_keys=True), flush=True)
    sys.path.insert(0, str(BACKEND))
    # The unchanged original tests use historical top-level imports; alias the
    # actual product modules, never replace implementations or use test doubles.
    for name in ('identity_binding', 'intent_identity'):
        full = 'app.core.transaction.' + name
        mod = importlib.import_module(full)
        if Path(mod.__file__).resolve() != BACKEND / ('app/core/transaction/' + name + '.py'):
            raise RuntimeError('PRODUCT_IMPORT_HOLD: ' + full)
        sys.modules[name] = mod
    for name, rel in [('app.core.agent_runtime.lifecycle', 'app/core/agent_runtime/lifecycle.py'),
                      ('app.core.event_store.company_coordination', 'app/core/event_store/company_coordination.py'),
                      ('app.core.transaction.review', 'app/core/transaction/review.py')]:
        if Path(sys.modules[name].__file__).resolve() != BACKEND / rel:
            raise RuntimeError('DEPENDENCY_IMPORT_HOLD: ' + name)
    if any(name in sys.modules for name in ('app.core.iam_session', 'app.core.transaction.intent_authority',
                                           'app.core.transaction.postgres_session', 'app.core.transaction.port')):
        raise RuntimeError('AUTHORITY_IMPORT_HOLD')
    failures = 0
    for rel, expected in zip(TESTS, (22, 19)):
        name = Path(rel).stem
        spec = importlib.util.spec_from_file_location(name, ROOT / rel)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
        if suite.countTestCases() != expected:
            raise RuntimeError('TEST_COUNT_HOLD: ' + name)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        print('RESULT:', name, f'{passed}/{expected}', 'failures=', len(result.failures),
              'errors=', len(result.errors), 'skipped=', len(result.skipped), flush=True)
        failures += int(not result.wasSuccessful() or bool(result.skipped) or result.testsRun != expected)
    print('AUTHORITY_MODULES_NOT_IMPORTED: PASS', flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    sys.exit(main())
