"""Rebind the exact original W8 reviewed pipeline to UX-PREMIUM-07-A0B; D0 only."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

MANIFEST = 'c61c2006d3c01877ef002664e585c7c5289c1676'
PARENT_PINS = {
    'w8_p10g.py': 'f2fa61c515f9b4eb5b964dccde88f58b8daff73b',
    'w8_p10f.py': '155a2179eb71bd554aa34dff36147be4658473e0',
    'w8_unified.py': '162a2387e5cdea6828a0cbbf0dab247bc4678551',
}
NATIVE_PATH = 'tests/integration/native_ux_a0b.py'
NATIVE_BLOB = 'becb59ee24df2a76c4aa31428abf3365b35172ed'
LAST_SMOKE = 'tests/integration/browser_task_budget_0188.py'


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()


def checked_pin(root, relative, expected):
    root = root.resolve()
    p = root / relative
    if p.resolve() != p.absolute() or not p.resolve().is_relative_to(root) or not p.is_file() or blob(p.read_bytes()) != expected:
        raise ValueError('UX_A0B_PIN_HOLD: '+relative)
    return p


def load_candidate():
    here = Path(__file__).resolve().parent
    for name, expected in PARENT_PINS.items():
        checked_pin(here, name, expected)
    spec = importlib.util.spec_from_file_location('ux_a0b_parent',here/'w8_p10g.py')
    if spec is None or spec.loader is None:
        raise ValueError('UX_A0B_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = MANIFEST
    w = parent.load_candidate()
    if w.MANIFEST_BLOB != MANIFEST:
        raise ValueError('UX_A0B_MANIFEST_REBIND_HOLD')
    return extend_candidate(w)


def extend_candidate(w):
    verify_aux, test, smoke = w.verify_aux, w.test, w.smoke

    def verify_aux_candidate(root):
        pins = verify_aux(root)
        checked_pin(root, NATIVE_PATH, NATIVE_BLOB)
        return {**pins, NATIVE_PATH: NATIVE_BLOB}

    def test_candidate(stage, approval):
        w.installed(stage,approval)
        for name in ('BUILD_TEST_OK','SMOKE_OK','NATIVE_SMOKE_OK'):
            (stage/name).unlink(missing_ok=True)
        f = w.frontend(stage)
        out = stage/'compiled-ux-a0b'
        out.mkdir(exist_ok=False)
        env = w.env_local()
        w.run([w.node(), f/'node_modules/typescript/bin/tsc', '--strict', '--target','ES2022','--module','commonjs','--outDir',out,'office/engine/premiumModel.ts','office/engine/premiumRouting.ts','office/engine/premiumTraffic.ts'],f,env)
        for name, module in [('model','premiumModel'),('traffic','premiumTraffic'),('traffic-boundary','premiumTraffic')]:
            w.run([w.node(),f/f'tests/premium-{name}.test.cjs',out/f'{module}.js'],f,env)
        return test(stage,approval)

    def smoke_candidate(stage, approval, chromium, frontend_port=17300, backend_port=17301):
        w.installed(stage,approval)
        (stage/'NATIVE_SMOKE_OK').unlink(missing_ok=True)
        run = w.run
        native_runs = 0
        # Extend the existing smoke while its reviewed loopback servers and DB hash guard are active.
        def run_with_native(args,cwd,env=None):
            nonlocal native_runs
            result = run(args,cwd,env)
            if len(args)>1 and str(args[1])==str(stage/LAST_SMOKE):
                if native_runs:
                    raise ValueError('UX_A0B_DUPLICATE_NATIVE_HOLD')
                checked_pin(stage,NATIVE_PATH,NATIVE_BLOB)
                run([w.python(stage),stage/NATIVE_PATH,'--frontend',f'http://127.0.0.1:{frontend_port}','--backend',f'http://127.0.0.1:{backend_port}','--chromium',chromium,'--output',stage/'native-ux-a0b'],stage,w.env_local())
                native_runs += 1
            return result
        w.run = run_with_native
        try:
            result = smoke(stage,approval,chromium,frontend_port,backend_port)
            if native_runs != 1 or (stage/'SMOKE_OK').read_text(encoding='utf-8') != approval:
                raise ValueError('UX_A0B_NATIVE_SMOKE_HOLD')
            w.reviewed(stage,approval)
            (stage/'NATIVE_SMOKE_OK').write_text(approval,encoding='utf-8')
            return result
        except Exception:
            (stage/'SMOKE_OK').unlink(missing_ok=True)
            (stage/'NATIVE_SMOKE_OK').unlink(missing_ok=True)
            raise
        finally:
            w.run = run

    w.verify_aux = verify_aux_candidate
    w.test = test_candidate
    w.smoke = smoke_candidate
    return w


if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:',exc,file=sys.stderr)
        sys.exit(1)
