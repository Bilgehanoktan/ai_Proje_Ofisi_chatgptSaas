"""Selected exact-source MI-03 replay; no installation, database or execution grants."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PINS = json.loads((HERE / 'SOURCE_PINS.json').read_text(encoding='utf-8'))
SUITES = {'test_identity_binding': 22, 'test_intent_identity': 19}
CODE = '''import importlib, json, pathlib, sys, unittest
root=pathlib.Path(sys.argv[1]); mode=sys.argv[2]
backend=root/'product/ai-company-os-backend'
paths=[root/'candidates/D4-R4',root/'candidates/D5-INTENT',backend]
sys.path[:0]=[str(p) for p in paths]
if mode=='product':
    from app.core.transaction import identity_binding, intent_identity
    assert identity_binding.__file__ == str(backend/'app/core/transaction/identity_binding.py')
    assert intent_identity.__file__ == str(backend/'app/core/transaction/intent_identity.py')
    assert intent_identity.Request is identity_binding.Request
    assert intent_identity.Review is identity_binding.Review
    # Unmodified original test modules use historical short import names.
    # Only the harness maps these names to the product module instances.
    sys.modules['identity_binding']=identity_binding
    sys.modules['intent_identity']=intent_identity
else:
    import identity_binding, intent_identity
    assert identity_binding.__file__ == str(paths[0]/'identity_binding.py')
    assert intent_identity.__file__ == str(paths[1]/'intent_identity.py')
print('MODE', mode, 'PYTHON', sys.version.split()[0], flush=True)
loader=unittest.TestLoader(); suite=unittest.TestSuite(); expected=json.loads(sys.argv[3])
for name,count in expected.items():
    mod=importlib.import_module(name)
    group=loader.loadTestsFromModule(mod)
    if loader.errors or group.countTestCases()!=count:
        raise SystemExit('COLLECTION_HOLD '+name)
    print('COLLECTED',name,count,flush=True); suite.addTests(group)
r=unittest.TextTestRunner(verbosity=2).run(suite)
print('RESULT', json.dumps(dict(executed=r.testsRun, failures=len(r.failures), errors=len(r.errors), skipped=len(r.skipped), expected_failures=len(r.expectedFailures), unexpected_successes=len(r.unexpectedSuccesses))),flush=True)
sys.exit(0 if r.wasSuccessful() and not r.skipped and not r.expectedFailures and not r.unexpectedSuccesses and r.testsRun==sum(expected.values()) else 1)
'''


def main():
    if len(PINS)!=15:
        raise ValueError('PIN_INVENTORY_HOLD')
    with tempfile.TemporaryDirectory(prefix='mi03-r2-') as tmp:
        stage=Path(tmp).resolve()
        for rel, expected in PINS.items():
            path=ROOT/rel
            if not path.is_relative_to(ROOT) or path.resolve()!=path or not path.is_file():
                raise ValueError('PATH_HOLD '+rel)
            raw=path.read_bytes()
            if hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()!=expected:
                raise ValueError('PIN_HOLD '+rel)
            out=stage/rel; out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(raw)
        print('EXACT_SOURCE_PINS:',len(PINS),flush=True)
        for mode in ('original','product'):
            result=subprocess.run([sys.executable,'-I','-S','-B','-c',CODE,str(stage),mode,json.dumps(SUITES)],cwd=stage,check=False)
            if result.returncode!=0: return 1
    return 0


if __name__=='__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('BLOCKED:',exc)
        sys.exit(2)
