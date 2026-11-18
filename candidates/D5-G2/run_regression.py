"""D5-G2 exact backend regression on extracted immutable GitHub checkout.
Based on the D5-G staging pattern. No install, PG, external calls or live grant.
Full run requires original checked-out files and reviewed cryptography 46.0.4.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile
from importlib.metadata import version, PackageNotFoundError

MANIFEST='15e446e4d14c95d81d1e152efa2e8cb11122b3e3'
DDL={'database/0192/candidate_event_outbox_fence.sql':'6e4780bf9f267c0926b40d582d5afdbd6faa543c','database/0193/candidate_run_head.sql':'180924e97ee1f31fa27332941a41e37fdf73017e','database/0194/candidate_transition_roles.sql':'7b5d374bb7973b283e4fcfa0d796ed6128ef9d27'}
TESTS={'product/ai-company-os-backend/tests/test_transition_mapping_0194.py':'a4a3827ec4267ce275efe52fe5488e1868502c3f','product/ai-company-os-backend/tests/test_intent_authority_t1_0212.py':'9296347d9253d74902ed1c6a89e273d8e516f2b5','product/ai-company-os-backend/tests/test_authority_fullchain_0214.py':'4918027e828e8e72273ee4d6a508cac3aa6e9b59','product/ai-company-os-backend/tests/test_iam_session_d5g1.py':'6be21cfdcaf7408d7d17b5848966bb7f6772581e','product/ai-company-os-backend/tests/test_iam_authority_d5g2.py':'16bfc7013ae77cdcf437227b9fb6ac8a9a69d08c'}
SOURCES={'product/ai-company-os-backend/app/core/iam_session.py':'f3c37428acd475e09c228bce47d534d6584cd944','product/ai-company-os-backend/app/core/transaction/intent_authority.py':'b28788f46a39c282d79d29c4abd817ed5fc9de99'}
def require(ok,label):
    if not ok: raise ValueError(label)
def blob(raw): return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def read(root,relative):
    p=root/relative
    require(p.is_relative_to(root) and p.resolve()==p and p.is_file(),'SOURCE_PATH_HOLD '+relative)
    return p.read_bytes()
def main():
    require(len(sys.argv)==2,'Supply exact extracted D5-G2 root')
    root=Path(sys.argv[1]).resolve(); raw=read(root,'product/SOURCE_MANIFEST.json')
    require(blob(raw)==MANIFEST,'MANIFEST_HOLD')
    require(version('cryptography')=='46.0.4','CRYPTOGRAPHY_HOLD')
    entries={k:v for k,v in json.loads(raw)['files'].items() if k.startswith('ai-company-os-backend/')}
    require(len(entries)==240,'INVENTORY_HOLD')
    pins=TESTS|SOURCES
    require(set(pins)<= {'product/'+k for k in entries},'PINS_MISSING_HOLD')
    with tempfile.TemporaryDirectory(prefix='d5g2-cross-') as d:
        stage=Path(d)
        def write(relative,data):
            p=stage/relative; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
        for k,v in entries.items():
            rel='product/'+k; data=read(root,rel)
            require(len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['sha256'],'BASE_SHA_HOLD '+rel)
            if rel in pins: require(blob(data)==pins[rel],'SOURCE_PIN_HOLD '+rel)
            write(rel,data)
        for rel,h in DDL.items():
            data=read(root,rel); require(blob(data)==h,'DDL_PIN_HOLD '+rel); write(rel,data)
        print('REGRESSION_SCOPE: 240 verified backend entries, 3 DDL, 7 source/test pins; no ORG, PG or live acceptance',flush=True)
        b=stage/'product/ai-company-os-backend'
        code='import sys,unittest,sqlite3; from importlib.metadata import version; print("Python",sys.version.split()[0],"SQLite",sqlite3.sqlite_version,"cryptography",version("cryptography"),flush=True); sys.path[:0]=sys.argv[1:]; s=unittest.TestLoader().loadTestsFromNames(["test_intent_authority_t1_0212","test_authority_fullchain_0214","test_iam_session_d5g1","test_iam_authority_d5g2"]); assert s.countTestCases()==50; r=unittest.TextTestRunner(verbosity=2).run(s); sys.exit(not r.wasSuccessful() or bool(r.skipped))'
        return subprocess.run([sys.executable,'-I','-B','-c',code,str(b),str(b/'tests')],cwd=stage,check=False).returncode
if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError,PackageNotFoundError) as e: print('REGRESSION_BLOCKED:',e); sys.exit(2)
