"""D5-G: run original T1 tests on three exact W5-MEM-03 source blobs.
Not full MEM-03 checkout, not product installation or a new authority.
Usage: python -B run_cross_regression.py EXACT_D5_C_EXTRACTED_ROOT
"""
from pathlib import Path
import hashlib,json,shutil,sys,tempfile,subprocess
from importlib.metadata import version

HERE=Path(__file__).resolve().parent
MANIFEST='981a13fc226184dc3a911ae0d94e0042285ff302'
OVERLAY={
 'ai-company-os-backend/app/core/agent_runtime/joint_context.py':('e6bb84ab19a730a7913ae4a7f545f480897e1dcd','d003cb73a1b36a9db28339fb6e9ab705de095c0c6019524f8da168135d7a289c'),
 'ai-company-os-backend/app/core/agent_runtime/memory_witness.py':('d783f00f6b7521ce0d979b977b45a8e44410eb8e','81fa16a2bf8f78943b52763a36c961344965371d216b375e79ab40220bd875e0'),
 'ai-company-os-backend/app/engines/memory_engine/snapshot_store.py':('bc8cd58a5e58a9043d5bf188af11521b1641b9c7','2fba57be279f54e94dc3cd8689297d96493d7d0c34c2b0cf0380e1a54c2db2f0')}
DDL={'database/0192/candidate_event_outbox_fence.sql':'6e4780bf9f267c0926b40d582d5afdbd6faa543c','database/0193/candidate_run_head.sql':'180924e97ee1f31fa27332941a41e37fdf73017e','database/0194/candidate_transition_roles.sql':'7b5d374bb7973b283e4fcfa0d796ed6128ef9d27'}
TESTS={'product/ai-company-os-backend/tests/test_transition_mapping_0194.py':'a4a3827ec4267ce275efe52fe5488e1868502c3f','product/ai-company-os-backend/tests/test_intent_authority_t1_0212.py':'9296347d9253d74902ed1c6a89e273d8e516f2b5','product/ai-company-os-backend/tests/test_authority_fullchain_0214.py':'4918027e828e8e72273ee4d6a508cac3aa6e9b59'}
def require(ok,label):
    if not ok: raise ValueError(label)
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def read(root,relative):
    p=root/relative
    require(p.is_relative_to(root) and p.resolve()==p and p.is_file(),'SOURCE_PATH_HOLD '+relative)
    return p.read_bytes()
def main():
    require(len(sys.argv)==2,'Supply exact extracted D5-C root')
    root=Path(sys.argv[1]).resolve(); raw=read(root,'product/SOURCE_MANIFEST.json')
    require(blob(raw)==MANIFEST,'MANIFEST_HOLD'); require(version('cryptography')=='46.0.4','CRYPTOGRAPHY_HOLD')
    entries={k:v for k,v in json.loads(raw)['files'].items() if k.startswith('ai-company-os-backend/')}
    require(len(entries)==237 and set(OVERLAY)<=set(entries),'INVENTORY_HOLD')
    with tempfile.TemporaryDirectory(prefix='d5g-cross-') as d:
        stage=Path(d)
        def write(relative,data):
            p=stage/relative; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
        for k,v in entries.items():
            rel='product/'+k; data=read(root,rel)
            require(len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['sha256'],'BASE_SHA_HOLD '+rel)
            if rel in TESTS: require(blob(data)==TESTS[rel],'TEST_PIN_HOLD '+rel)
            if k in OVERLAY:
                data=read(HERE,'overlay/'+Path(k).name)
                require((blob(data),hashlib.sha256(data).hexdigest())==OVERLAY[k],'OVERLAY_PIN_HOLD '+k)
            write(rel,data)
        for rel,h in DDL.items():
            data=read(root,rel);require(blob(data)==h,'DDL_PIN_HOLD '+rel);write(rel,data)
        print('CROSS_SCOPE: 234 exact original backend entries + 3 exact MEM03 source blobs; 3 DDL and 3 test pins; NOT full MEM03 checkout',flush=True)
        b=stage/'product/ai-company-os-backend'
        code='import sys,unittest,sqlite3; from importlib.metadata import version; print("Python",sys.version.split()[0],"SQLite",sqlite3.sqlite_version,"cryptography",version("cryptography"),flush=True); sys.path[:0]=sys.argv[1:]; s=unittest.TestLoader().loadTestsFromNames(["test_intent_authority_t1_0212","test_authority_fullchain_0214"]); assert s.countTestCases()==17; r=unittest.TextTestRunner(verbosity=2).run(s);sys.exit(not r.wasSuccessful() or bool(r.skipped))'
        return subprocess.run([sys.executable,'-I','-B','-c',code,str(b),str(b/'tests')],cwd=stage,check=False).returncode
if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError) as e: print('CROSS_REGRESSION_BLOCKED:',e);sys.exit(2)
