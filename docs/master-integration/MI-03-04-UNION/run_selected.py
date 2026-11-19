"""Exact combined MI-03/04 selected regression; no DB, grants or full build."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PINS = json.loads((HERE / 'SOURCE_PINS.json').read_text(encoding='utf-8'))
CODE = '''import importlib, pathlib, sys, unittest
root=pathlib.Path(sys.argv[1]); backend=root/'product/ai-company-os-backend'
sys.path[:0]=[str(backend),str(backend/'tests'),str(root/'candidates/D4-R4'),str(root/'candidates/D5-INTENT')]
from app.core.transaction import identity_binding, intent_identity, postgres_session, port
for m in (identity_binding,intent_identity,postgres_session,port):
    assert m.__file__ == str(backend/'app/core/transaction'/ (m.__name__.split('.')[-1]+'.py'))
assert intent_identity.Request is identity_binding.Request
assert intent_identity.Review is identity_binding.Review
assert postgres_session.CommitReceipt is port.CommitReceipt
sys.modules['identity_binding']=identity_binding
sys.modules['intent_identity']=intent_identity
print('PYTHON',sys.version.split()[0],flush=True)
loader=unittest.TestLoader(); suite=unittest.TestSuite()
for name,count in [('test_identity_binding',22),('test_intent_identity',19),('test_postgres_preclaim_d5c_r7',5)]:
    group=loader.loadTestsFromModule(importlib.import_module(name))
    if loader.errors or group.countTestCases()!=count:
        raise SystemExit('COLLECTION_HOLD '+name)
    print('COLLECTED',name,count,flush=True); suite.addTests(group)
r=unittest.TextTestRunner(verbosity=1).run(suite)
print('RESULT',dict(executed=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),expected_failures=len(r.expectedFailures),unexpected_successes=len(r.unexpectedSuccesses)),flush=True)
sys.exit(0 if r.wasSuccessful() and not r.skipped and not r.expectedFailures and not r.unexpectedSuccesses and r.testsRun==46 else 1)
'''


def main():
    if len(PINS)!=16:
        raise ValueError('PIN_INVENTORY_HOLD')
    with tempfile.TemporaryDirectory(prefix='mi0304-union-') as tmp:
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
        return subprocess.run([sys.executable,'-I','-S','-B','-c',CODE,str(stage)],cwd=stage,check=False).returncode


if __name__=='__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('BLOCKED:',exc)
        sys.exit(2)
