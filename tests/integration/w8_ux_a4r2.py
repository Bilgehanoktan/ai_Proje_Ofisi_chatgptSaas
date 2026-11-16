"""A4R2 rebinds reviewed A0C W8 without replacing earlier acceptance gates."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

MANIFEST = '397f87b7d9a9227ee435b1501347c6460fc73c5e'
PARENT_BLOB = '52ac6add8b0bc338527e9e12c7848c9056d8f836'
NATIVE_PATH = 'tests/integration/native_ux_a4r2.py'
NATIVE_BLOB = 'd82d09d0ea39e213ae4db78e8181d2c9c90d06f7'
LAST_SMOKE = 'tests/integration/browser_task_budget_0188.py'
MARKERS = ('SMOKE_OK','NATIVE_SMOKE_OK','HYBRID_NATIVE_OK')


def checked_pin(root, relative, expected):
    p = root.resolve()/relative
    if p.resolve() != p.absolute() or not p.resolve().is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError('A4R2_PATH_HOLD: '+relative)
    raw = p.read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != expected:
        raise ValueError('A4R2_PIN_HOLD: '+relative)
    return p


def clear(stage, names):
    for name in names:
        (stage/name).unlink(missing_ok=True)


def extend_candidate(w):
    verify_aux, test, smoke = w.verify_aux, w.test, w.smoke

    def verify_aux_candidate(root):
        pins = verify_aux(root)
        checked_pin(root,NATIVE_PATH,NATIVE_BLOB)
        return {**pins,NATIVE_PATH:NATIVE_BLOB}

    def test_candidate(stage,approval):
        w.installed(stage,approval)
        clear(stage,('BUILD_TEST_OK',*MARKERS))
        try:
            f = w.frontend(stage)
            out = stage/'compiled-ux-a4r2'
            out.mkdir(exist_ok=False)
            env = w.env_local()
            w.run([w.node(),f/'node_modules/typescript/bin/tsc','--strict','--target','ES2022','--module','commonjs','--outDir',out,'office/engine/premiumHybridRender.ts','office/engine/premiumModel.ts'],f,env)
            for name, modules in [('hybrid-render',['premiumHybridRender','premiumActorIdentity']),('identity-traffic',['premiumIdentityTraffic','premiumActorIdentity','premiumHybridLayout']),('actor-identity',['premiumActorIdentity','premiumHybridLayout']),('hybrid-layout',['premiumHybridLayout'])]:
                w.run([w.node(),f/f'tests/premium-{name}.test.cjs',*[out/f'{m}.js' for m in modules]],f,env)
            return test(stage,approval)
        except Exception:
            clear(stage,('BUILD_TEST_OK',*MARKERS))
            raise

    def smoke_candidate(stage,approval,chromium,frontend_port=17300,backend_port=17301):
        w.installed(stage,approval)
        clear(stage,MARKERS)
        run = w.run
        runs = 0
        def hook(args,cwd,env=None):
            nonlocal runs
            result = run(args,cwd,env)
            if len(args)>1 and str(args[1])==str(stage/LAST_SMOKE):
                if runs:
                    raise ValueError('A4R2_DUPLICATE_NATIVE_HOLD')
                checked_pin(stage,NATIVE_PATH,NATIVE_BLOB)
                run([w.python(stage),stage/NATIVE_PATH,'--frontend',f'http://127.0.0.1:{frontend_port}','--backend',f'http://127.0.0.1:{backend_port}','--chromium',chromium,'--output',stage/'native-ux-a4r2'],stage,w.env_local())
                runs += 1
            return result
        w.run = hook
        try:
            result = smoke(stage,approval,chromium,frontend_port,backend_port)
            if runs != 1 or any((stage/n).read_text(encoding='utf-8')!=approval for n in MARKERS[:2]):
                raise ValueError('A4R2_NATIVE_SMOKE_HOLD')
            w.reviewed(stage,approval)
            (stage/'HYBRID_NATIVE_OK').write_text(approval,encoding='utf-8')
            return result
        except Exception:
            clear(stage,MARKERS)
            raise
        finally:
            w.run = run

    w.verify_aux,w.test,w.smoke = verify_aux_candidate,test_candidate,smoke_candidate
    return w


def load_candidate():
    here = Path(__file__).resolve().parent
    p = checked_pin(here,'w8_ux_a0c.py',PARENT_BLOB)
    spec = importlib.util.spec_from_file_location('ux_a4r2_parent',p)
    if spec is None or spec.loader is None:
        raise ValueError('A4R2_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.MANIFEST = MANIFEST
    w = parent.load_candidate()
    if w.MANIFEST_BLOB != MANIFEST:
        raise ValueError('A4R2_MANIFEST_REBIND_HOLD')
    return extend_candidate(w)


if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as exc:
        print('HOLD:',exc,file=sys.stderr)
        sys.exit(1)
