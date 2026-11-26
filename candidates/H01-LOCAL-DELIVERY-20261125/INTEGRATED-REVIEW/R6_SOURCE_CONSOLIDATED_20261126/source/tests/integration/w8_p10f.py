"""P10F D0 adapter for the original reviewed W8 workflow. No independent acceptance."""
import hashlib
import importlib.util
from pathlib import Path
import sys

ORIGINAL_BLOB='162a2387e5cdea6828a0cbbf0dab247bc4678551'
CANDIDATE_MANIFEST='44844b647640694a00abc62f200af034d38ac6ff'

def blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()

def load_original():
    original=Path(__file__).resolve().with_name('w8_unified.py')
    if original.is_symlink() or blob(original.read_bytes())!=ORIGINAL_BLOB:
        raise ValueError('ORIGINAL_W8_BLOB_HOLD')
    spec=importlib.util.spec_from_file_location('p10f_original_w8',original)
    if spec is None or spec.loader is None:raise ValueError('W8_LOADER_HOLD')
    w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
    verify=w.verify;test=w.test;verify_aux=w.verify_aux;run=w.run
    # Only this process selects the new exact candidate. Original file stays unchanged.
    w.MANIFEST_BLOB=CANDIDATE_MANIFEST
    def verify_candidate(repo,pin=CANDIDATE_MANIFEST,clean=False):
        if pin!=CANDIDATE_MANIFEST:raise ValueError('P10F_MANIFEST_PIN_HOLD')
        return verify(repo,pin=CANDIDATE_MANIFEST,clean=clean)
    w.verify=verify_candidate
    # The P05 runner predates history signatures and later disposable SQL fixtures.
    extra={
        'database/0203T/terminal_command_anchors.sql':'0b5f9725f4020e4f41ec1a0090efa9cddc8a050f',
        'database/0204C/company_event_order.sql':'edb2ef263204b89f88f172000ecb031428a027e4',
        'database/migrations/0183_D0_PHYSICAL_CANDIDATE.sql':'8e6b4a4e886459be74ae575becd5917c5f070fab',
        'tests/integration/core_0207_source_lock.json':'223f6fbd28cf4c428c07eb60dda4a36f644fa58c',
        'tests/integration/run_core_0207.py':'b019a5e60cfff4183b00e99f252ffe00bc164eda',
        'tests/integration/run_lifecycle_p05.py':'befb9f429791a01b2fe37009e40f994a5924b2ff',
    }
    def verify_aux_candidate(root):
        pins=verify_aux(root)
        for name,expected in extra.items():
            p=w.checked_path(root,name)
            if not p.is_file() or w.blob(p)!=expected:raise ValueError('P10F_AUX_HOLD: '+name)
        return {**pins,**extra}
    w.verify_aux=verify_aux_candidate
    def run_candidate(args,cwd,env=None):
        args=list(args)
        # Only extend the original wheelhouse preparation, never install unreviewed wheels.
        if list(map(str,args[1:5]))==['-m','pip','--isolated','download']:
            args.extend(['-r',w.backend(Path(cwd))/'requirements-history-signatures.txt'])
        return run(args,cwd,env)
    w.run=run_candidate
    def test_candidate(stage,approval):
        w.installed(stage,approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):(stage/marker).unlink(missing_ok=True)
        f=w.frontend(stage);b=w.backend(stage);env=w.env_local()
        out=stage/'compiled-p10f-model';out.mkdir(exist_ok=False)
        tsc=f/'node_modules/typescript/bin/tsc'
        w.run([w.node(),tsc,'--strict','--target','ES2022','--module','commonjs','--lib','ES2022,DOM','--rootDir','.', '--outDir',out,'features/evidence/evidenceContext.ts','features/workflow/draftHistory.ts','office/engine/officeArtwork.ts'],f,env)
        env.update(P10D_MODEL=str(out),P10D_FIXTURE=str(b/'fixtures/core.preview.json'))
        w.run([w.node(),'--test','tests/ui-p10d-model.test.cjs','tests/ui-p10e-model.test.cjs','tests/ui-p10f-model.test.cjs'],f,env)
        w.run([w.python(stage),stage/'tests/integration/run_core_0207.py','--source',stage,'--report',stage/'core29-p10f.json'],stage,w.env_local())
        # Original full backend, frontend build and typecheck; original sets marker last.
        return test(stage,approval)
    w.test=test_candidate
    return w

if __name__=='__main__':
    try:load_original().main()
    except (OSError,ValueError,KeyError) as exc:
        print('HOLD:',exc,file=sys.stderr);sys.exit(1)
