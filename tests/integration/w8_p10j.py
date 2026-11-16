"""P10J candidate adapter; P10I adapter absent in parent tree. Preserve W8 review gates."""
import hashlib
import importlib.util
from pathlib import Path
import sys
P10H_BLOB='b9dc676f2e5477e5c58e839c5f66d582c191d608'
CANDIDATE_MANIFEST='35724e95238201da97a9f98b390d879704f68771'
EXTRA={
 'tests/integration/audit_source_archive.py':'9a8a55b67360a8d55b4e647b29f745d4e8b6b378',
 'tests/integration/test_audit_source_archive.py':'d361a22ee65f44fdbca8a81fffdb51b8f390e028',
}
def load_candidate():
    p=Path(__file__).resolve().with_name('w8_p10h.py')
    raw=p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()!=P10H_BLOB:
        raise ValueError('P10H_ADAPTER_PIN_HOLD')
    spec=importlib.util.spec_from_file_location('p10j_parent_adapter',p)
    if spec is None or spec.loader is None:raise ValueError('P10J_LOADER_HOLD')
    parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST=CANDIDATE_MANIFEST
    w=parent.load_candidate();test=w.test;verify_aux=w.verify_aux
    def verify_aux_candidate(root):
        pins=verify_aux(root)
        for name,expected in EXTRA.items():
            f=w.checked_path(root,name)
            if not f.is_file() or w.blob(f)!=expected:raise ValueError('P10J_AUX_HOLD: '+name)
        return {**pins,**EXTRA}
    w.verify_aux=verify_aux_candidate
    def test_candidate(stage,approval):
        w.installed(stage,approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):(stage/marker).unlink(missing_ok=True)
        f=w.frontend(stage);env=w.env_local();out=stage/'compiled-p10j-model';out.mkdir(exist_ok=False)
        w.run([w.node(),f/'node_modules/typescript/bin/tsc','--strict','--target','ES2022','--module','commonjs','--lib','ES2022,DOM','--resolveJsonModule','--esModuleInterop','--rootDir','.','--outDir',out,'features/project-management/dependencyNeighborhood.ts','features/data/projectionRead.ts','features/workflow/draftOverview.ts'],f,env)
        env.update(P10D_MODEL=str(out))
        w.run([w.node(),'--test','tests/ui-p10i-model.test.cjs','tests/ui-p10j-model.test.cjs'],f,env)
        w.run([w.python(stage),'-m','unittest','discover','-s',stage/'tests/integration','-p','test_audit_source_archive.py','-v'],stage,w.env_local())
        return test(stage,approval)
    w.test=test_candidate
    return w
if __name__=='__main__':
    try:load_candidate().main()
    except (OSError,ValueError,KeyError) as exc:
        print('HOLD:',exc,file=sys.stderr);sys.exit(1)
