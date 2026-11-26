"""P10J20: pinned UI chain plus inspector and exact A4R2 native diagnostics."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = 'b5be090aa83800318ba14e3f2eaaf482c1fce15d'
CANDIDATE_MANIFEST = '9672f2e26f0635448f56cc02d338641bbe3ed5a5'
OLD_BROWSER = 'baac24da1edba991a240a0c41258f0f9a35d95fa'
NEW_BROWSER = '99df17ec2a0be012ad2f3c463510c64fbd69c062'
NATIVE = 'native_ux_a4r2.py'
NATIVE_BLOB = 'd82d09d0ea39e213ae4db78e8181d2c9c90d06f7'
LAST_SMOKE = 'tests/integration/browser_task_budget_0188.py'
MARKERS = ('SMOKE_OK','HYBRID_NATIVE_OK')


def clear(stage,names):
    for name in names:
        (stage/name).unlink(missing_ok=True)


def extend_candidate(w):
    if w.MANIFEST_BLOB != CANDIDATE_MANIFEST or w.HARNESS.get('browser_0187_w1.py') != OLD_BROWSER or NATIVE in w.HARNESS:
        raise ValueError('P10J20_REBIND_HOLD')
    w.HARNESS['browser_0187_w1.py'] = NEW_BROWSER
    w.HARNESS[NATIVE] = NATIVE_BLOB
    inherited_test,inherited_smoke = w.test,w.smoke

    def test_candidate(stage,approval):
        w.installed(stage,approval)
        clear(stage,('BUILD_TEST_OK',*MARKERS))
        try:
            f=w.frontend(stage)
            w.run([w.node(),'--test','tests/ui-p10j20-inspector.test.cjs'],f,w.env_local())
            return inherited_test(stage,approval)
        except Exception:
            clear(stage,('BUILD_TEST_OK',*MARKERS))
            raise

    def smoke_candidate(stage,approval,chromium,frontend_port=17300,backend_port=17301):
        w.installed(stage,approval)
        clear(stage,MARKERS)
        run=w.run
        runs=0
        def hook(args,cwd,env=None):
            nonlocal runs
            result=run(args,cwd,env)
            if len(args)>1 and str(args[1])==str(stage/LAST_SMOKE):
                if runs:
                    raise ValueError('P10J20_DUPLICATE_NATIVE_HOLD')
                w.verify_aux(stage)
                run([w.python(stage),stage/'tests/integration'/NATIVE,'--frontend',f'http://127.0.0.1:{frontend_port}','--backend',f'http://127.0.0.1:{backend_port}','--chromium',chromium,'--output',stage/'native-ux-a4r2'],stage,w.env_local())
                runs+=1
            return result
        w.run=hook
        try:
            result=inherited_smoke(stage,approval,chromium,frontend_port,backend_port)
            if runs!=1 or (stage/'SMOKE_OK').read_text(encoding='utf-8')!=approval:
                raise ValueError('P10J20_NATIVE_SMOKE_HOLD')
            w.reviewed(stage,approval)
            (stage/'HYBRID_NATIVE_OK').write_text(approval,encoding='utf-8')
            return result
        except Exception:
            clear(stage,MARKERS)
            raise
        finally:
            w.run=run
    w.test,w.smoke=test_candidate,smoke_candidate
    return w


def load_candidate():
    p=Path(__file__).resolve().with_name('w8_p10j19.py')
    raw=p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()!=PARENT_BLOB:
        raise ValueError('P10J19_PARENT_PIN_HOLD')
    spec=importlib.util.spec_from_file_location('p10j20_parent',p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J20_LOADER_HOLD')
    parent=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST=CANDIDATE_MANIFEST
    return extend_candidate(parent.load_candidate())


if __name__=='__main__':
    try:
        load_candidate().main()
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as exc:
        print('HOLD:',exc,file=sys.stderr)
        sys.exit(1)
