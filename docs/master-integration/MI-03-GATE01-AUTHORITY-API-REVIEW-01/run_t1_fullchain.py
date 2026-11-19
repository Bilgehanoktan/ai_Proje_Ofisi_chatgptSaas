"""GATE01 remaining ten original Memory/T1 tests on exact common+G6A overlay.
Separate from original G2 runner. Disposable D0 only; never a protected route.
Usage: python -I -B run_t1_fullchain.py EXACT_COMMON_ROOT EXACT_G6A_ROOT
"""
from pathlib import Path
from hashlib import sha1, sha256
from importlib.metadata import version
import json, sqlite3, subprocess, sys, tempfile
COMMON_MANIFEST='03af243e8683f92c5d9c0b24e90b70d2bd6af29f'
PREFIX='product/ai-company-os-backend/'
OWNER={
    PREFIX+'app/core/transaction/intent_authority.py':'88fd68c563db7e620c5b06c1a9c6b68d304ae071',
    PREFIX+'app/core/iam_session.py':'f3c37428acd475e09c228bce47d534d6584cd944',
}
DDL={
    'database/0192/candidate_event_outbox_fence.sql':'6e4780bf9f267c0926b40d582d5afdbd6faa543c',
    'database/0193/candidate_run_head.sql':'180924e97ee1f31fa27332941a41e37fdf73017e',
    'database/0194/candidate_transition_roles.sql':'7b5d374bb7973b283e4fcfa0d796ed6128ef9d27',
}
REQUIRED={
    PREFIX+'app/core/transaction/intent_authority.py':'fa47acd32adb309896f762ec50e47bf26641adbb',
    PREFIX+'app/core/transaction/postgres_session.py':'6c0995712bd368f72c239cb19cd3e85aa781c1b9',
    PREFIX+'app/core/agent_runtime/joint_context.py':'e6bb84ab19a730a7913ae4a7f545f480897e1dcd',
    PREFIX+'app/core/agent_runtime/memory_witness.py':'d783f00f6b7521ce0d979b977b45a8e44410eb8e',
    PREFIX+'app/engines/memory_engine/snapshot_store.py':'bc8cd58a5e58a9043d5bf188af11521b1641b9c7',
    PREFIX+'tests/test_transition_mapping_0194.py':'a4a3827ec4267ce275efe52fe5488e1868502c3f',
    PREFIX+'tests/test_authority_fullchain_0214.py':'4918027e828e8e72273ee4d6a508cac3aa6e9b59',
}
def blob(b): return sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def require(ok, reason):
    if not ok: raise ValueError(reason)
def read(root, rel):
    p=root/rel
    require(p.is_relative_to(root) and p.resolve()==p and p.is_file(),'SOURCE_PATH_HOLD '+rel)
    return p.read_bytes()
def main():
    require(len(sys.argv)==3,'EXACT_COMMON_AND_G6A_ROOTS_REQUIRED')
    common, owner=map(lambda p:Path(p).resolve(),sys.argv[1:])
    require(common!=owner,'SEPARATE_ROOTS_REQUIRED')
    raw=read(common,'product/SOURCE_MANIFEST.json')
    require(blob(raw)==COMMON_MANIFEST,'COMMON_MANIFEST_HOLD')
    require((sys.version.split()[0],sqlite3.sqlite_version,version('cryptography'))==('3.13.5','3.46.1','46.0.4'),'ENVIRONMENT_HOLD')
    files={k:v for k,v in json.loads(raw)['files'].items() if k.startswith('ai-company-os-backend/')}
    require(len(files)==265,'COMMON_BACKEND_INVENTORY_HOLD')
    require(PREFIX+'app/core/iam_session.py' not in {'product/'+k for k in files},'COMMON_IAM_UNEXPECTED_HOLD')
    stage_files={}
    for k,v in files.items():
        rel='product/'+k; b=read(common,rel)
        require(len(b)==v['bytes'] and sha256(b).hexdigest()==v['sha256'],'COMMON_SHA_HOLD '+rel)
        if rel in REQUIRED: require(blob(b)==REQUIRED[rel],'REQUIRED_PIN_HOLD '+rel)
        stage_files[rel]=b
    require(set(REQUIRED)<=stage_files.keys(),'REQUIRED_SOURCE_MISSING_HOLD')
    for rel,h in OWNER.items():
        b=read(owner,rel);require(blob(b)==h,'OWNER_PIN_HOLD '+rel);stage_files[rel]=b
    for rel,h in DDL.items():
        b=read(common,rel);require(blob(b)==h,'DDL_PIN_HOLD '+rel);stage_files[rel]=b
    print('COMMON_BACKEND=265/265 OWNER=2/2 DDL=3/3',flush=True)
    with tempfile.TemporaryDirectory(prefix='mi04-fullchain-') as tmp:
        root=Path(tmp)
        for rel,b in stage_files.items():
            p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        backend=root/PREFIX
        child="""import sys,unittest,json
sys.path[:0]=sys.argv[1:]
s=unittest.defaultTestLoader.loadTestsFromName('test_authority_fullchain_0214')
if s.countTestCases()!=10: sys.exit(2)
r=unittest.TextTestRunner(verbosity=2).run(s)
c=[r.testsRun,len(r.failures),len(r.errors),len(r.skipped),len(r.expectedFailures),len(r.unexpectedSuccesses)]
print('COUNTS='+json.dumps(c),flush=True)
sys.exit(0 if r.wasSuccessful() and c==[10,0,0,0,0,0] else 1)
"""
        result=subprocess.run([sys.executable,'-I','-B','-c',child,str(backend),str(backend/'tests')],cwd=root)
        for rel,b in stage_files.items(): require((root/rel).read_bytes()==b,'STAGE_DRIFT_HOLD '+rel)
        print('PRODUCT_ACCEPTANCE=HOLD; full restore residual is not security PASS',flush=True)
        return result.returncode
if __name__=='__main__':
    try: sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError) as e:
        print('PREFLIGHT_BLOCKED '+str(e),flush=True);sys.exit(2)
