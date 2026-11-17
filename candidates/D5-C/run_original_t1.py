"""Run only original 0212/0214 T1 regression, not the D5-C probe or PG.
Requires a reviewed isolated environment and exact base backend + DDL bytes.
Never installs, launches a server, or accesses external services.
"""
from hashlib import sha1, sha256
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import subprocess
import sys
import tempfile

MANIFEST_BLOB='981a13fc226184dc3a911ae0d94e0042285ff302'
EXTRA_PINS={
    'database/0192/candidate_event_outbox_fence.sql':'6e4780bf9f267c0926b40d582d5afdbd6faa543c',
    'database/0193/candidate_run_head.sql':'180924e97ee1f31fa27332941a41e37fdf73017e',
    'database/0194/candidate_transition_roles.sql':'7b5d374bb7973b283e4fcfa0d796ed6128ef9d27',
}
TEST_PINS={
    'product/ai-company-os-backend/tests/test_transition_mapping_0194.py':'a4a3827ec4267ce275efe52fe5488e1868502c3f',
    'product/ai-company-os-backend/tests/test_intent_authority_t1_0212.py':'9296347d9253d74902ed1c6a89e273d8e516f2b5',
    'product/ai-company-os-backend/tests/test_authority_fullchain_0214.py':'4918027e828e8e72273ee4d6a508cac3aa6e9b59',
}


def read_exact(root, relative):
    path=root/relative
    if not path.is_relative_to(root) or path.resolve()!=path or not path.is_file():
        raise ValueError('SOURCE_MISSING_HOLD: '+relative)
    return path.read_bytes()


def blob(raw):
    return sha1(f'blob {len(raw)}\0'.encode('ascii')+raw).hexdigest()


def main():
    root=Path(__file__).resolve().parents[2]
    try:
        raw=read_exact(root,'product/SOURCE_MANIFEST.json')
        if blob(raw)!=MANIFEST_BLOB: raise ValueError('MANIFEST_DRIFT_HOLD')
        entries={k:v for k,v in json.loads(raw)['files'].items() if k.startswith('ai-company-os-backend/')}
        if len(entries)!=237: raise ValueError('BACKEND_INVENTORY_HOLD')
        if version('cryptography')!='46.0.4': raise ValueError('CRYPTOGRAPHY_PIN_HOLD')
        with tempfile.TemporaryDirectory() as tmp:
            stage=Path(tmp)
            def copy(relative,data):
                p=stage/relative; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
            for k,v in entries.items():
                rel='product/'+k; data=read_exact(root,rel)
                if len(data)!=v['bytes'] or sha256(data).hexdigest()!=v['sha256']:
                    raise ValueError('SOURCE_DRIFT_HOLD: '+rel)
                if rel in TEST_PINS and blob(data)!=TEST_PINS[rel]: raise ValueError('TEST_PIN_HOLD: '+rel)
                copy(rel,data)
            if not set(TEST_PINS).issubset({'product/'+k for k in entries}): raise ValueError('TEST_INVENTORY_HOLD')
            for rel,expected in EXTRA_PINS.items():
                data=read_exact(root,rel)
                if blob(data)!=expected: raise ValueError('DDL_PIN_HOLD: '+rel)
                copy(rel,data)
            print('PIN_MATCH: 237 backend manifest entries + 3 original DDL; 3 explicit test pins',flush=True)
            base=stage/'product/ai-company-os-backend'
            code=('import sys,unittest; sys.path[:0]=sys.argv[1:]; '
                  's=unittest.TestLoader().loadTestsFromNames(["test_intent_authority_t1_0212","test_authority_fullchain_0214"]); '
                  'assert s.countTestCases()==17; r=unittest.TextTestRunner(verbosity=2).run(s); '
                  'sys.exit(not r.wasSuccessful() or bool(r.skipped))')
            return subprocess.run([sys.executable,'-I','-B','-c',code,str(base),str(base/'tests')],cwd=stage,check=False).returncode
    except (ValueError,OSError,KeyError,TypeError,PackageNotFoundError) as exc:
        print('T1_REGRESSION_BLOCKED:',exc); return 2

if __name__=='__main__':
    sys.exit(main())
