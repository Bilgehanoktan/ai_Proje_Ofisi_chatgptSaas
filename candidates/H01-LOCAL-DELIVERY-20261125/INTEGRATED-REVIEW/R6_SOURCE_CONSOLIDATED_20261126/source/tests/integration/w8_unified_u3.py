"""U3A: source-bound W8 acceptance adapter, retains P10J24 historical isolation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

MANIFEST = '359e084b4a8aceb9120fda6a3be3e298646b4f1f'
P24 = '0728ba08494bb8d67c7cec42fe27dd8606bdc7f3'
P23 = '7a386554e51caed2db89ae94afc8215277f76c3c'
U2 = 'tests/integration/run_unified_u2_session.py'
BROWSER = 'tests/integration/browser_unified_u3.py'
LAST_SMOKE = 'tests/integration/browser_task_budget_0188.py'
EXTRA = {
    U2: 'c27eb541d4ad4c26f879dd5a45e98f20dd81de2f',
    BROWSER: '2a3f2b8e286c5d79847a6b00cdb6d046d0429773',
    'tests/integration/w8_frozen_npm.py': '257ba8f110508ff30ad03212111cfe8e2299d801',
    'tests/integration/locks/mi01-frozen-npm/package-lock.json': '4cd33f437df85d7e74c7946a0999f76adf2e31fe',
    'database/0192/candidate_event_outbox_fence.sql': '6e4780bf9f267c0926b40d582d5afdbd6faa543c',
    'database/0193/candidate_run_head.sql': '180924e97ee1f31fa27332941a41e37fdf73017e',
    'database/0194/candidate_transition_roles.sql': '7b5d374bb7973b283e4fcfa0d796ed6128ef9d27',
    'database/0195/candidate_admission_budget.sql': 'd5dc6abc045da14ef42e88b4e85e50e9062a1b27',
    'database/0196L/candidate_lease_settlement.sql': 'e4c9a84ff705c39486579c393b1f3aaef9e34da9',
    'database/0203T/terminal_command_anchors.sql': '0b5f9725f4020e4f41ec1a0090efa9cddc8a050f',
    'database/0204C/company_event_order.sql': 'edb2ef263204b89f88f172000ecb031428a027e4',
    'database/migrations/0183_D0_PHYSICAL_CANDIDATE.sql': '8e6b4a4e886459be74ae575becd5917c5f070fab',
}
MARKERS = ('BUILD_TEST_OK', 'SMOKE_OK', 'HYBRID_NATIVE_OK')


def blob(path):
    raw = path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()


def load_exact(path, pin):
    if path.is_symlink() or blob(path) != pin:
        raise ValueError('U3_RUNNER_PIN_HOLD: '+path.name)
    spec = importlib.util.spec_from_file_location('u3_'+path.stem, path)
    if spec is None or spec.loader is None:
        raise ValueError('U3_LOADER_HOLD')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clear(stage, names=MARKERS):
    for name in names:
        (stage/name).unlink(missing_ok=True)


def extend(w):
    if w.MANIFEST_BLOB != MANIFEST:
        raise ValueError('U3_MANIFEST_HOLD')
    inherited_aux, inherited_test, inherited_smoke = w.verify_aux, w.test, w.smoke

    def aux(root):
        pins = inherited_aux(root)
        for name, expected in EXTRA.items():
            if name in pins and pins[name] != expected:
                raise ValueError('U3_AUX_COLLISION_HOLD: '+name)
            path = w.checked_path(root, name)
            if not path.is_file() or blob(path) != expected:
                raise ValueError('U3_AUX_PIN_HOLD: '+name)
        return {**pins, **EXTRA}

    def test(stage, approval):
        w.installed(stage, approval)
        clear(stage)
        try:
            f = w.frontend(stage)
            env = w.env_local()
            tsc = f/'node_modules/typescript/bin/tsc'
            office = stage/'compiled-u3-office'
            session = stage/'compiled-u3-session'
            office.mkdir(exist_ok=False)
            session.mkdir(exist_ok=False)
            w.run([w.node(),tsc,'--strict','--target','ES2020','--module','commonjs','--outDir',office,'office/engine/unifiedOfficePreview.ts'], f, env)
            w.run([w.node(),'--test','tests/unified-office-preview.test.cjs'], f, {**env,'U1_BUILD':str(office)})
            w.run([w.node(),'--test','tests/premium-floor-render.test.cjs'], f, {**env,'A5R3_BUILD':str(office)})
            w.run([w.node(),'tests/premium-floor-traffic.test.cjs',office/'premiumFloorTraffic.js',office/'premiumHybridLayout.js',office/'premiumActorIdentity.js'], f, env)
            w.run([w.node(),'--test','tests/premium-dynamic-floors.test.cjs'], f, {**env,'A5_MODEL':str(office/'premiumDynamicFloors.js')})
            w.run([w.node(),tsc,'--strict','--target','ES2022','--lib','ESNext,DOM','--module','commonjs','--rootDir','.','--outDir',session,'features/data/sharedReplaySession.ts','features/mvp/studioContext.ts','app/api/demo/shared-snapshot/route.ts'], f, env)
            w.run([w.python(stage),'-B',stage/U2,'--build',session], stage, {**env,'AICOS_NODE':str(w.node())})
            result = inherited_test(stage, approval)
            if (stage/'BUILD_TEST_OK').read_text(encoding='utf-8') != approval:
                raise ValueError('U3_BUILD_REQUIRED_HOLD')
            w.reviewed(stage, approval)
            return result
        except Exception:
            clear(stage)
            raise

    def smoke(stage, approval, chromium, frontend_port=17300, backend_port=17301):
        w.installed(stage, approval)
        clear(stage, ('SMOKE_OK','HYBRID_NATIVE_OK'))
        run, calls = w.run, 0
        def hook(args, cwd, env=None):
            nonlocal calls
            result = run(args, cwd, env)
            if len(args)>1 and str(args[1]) == str(stage/LAST_SMOKE):
                if calls or Path(cwd) != stage:
                    raise ValueError('U3_BROWSER_CALL_HOLD')
                w.verify_aux(stage)
                output = stage/'unified-u3-browser'
                run([w.python(stage),stage/BROWSER,'--frontend-port',str(frontend_port),'--chromium',chromium,'--output',output],stage,w.env_local())
                report = json.loads((output/'U3_BROWSER_REPORT.json').read_text(encoding='utf-8'))
                if report != {'status':'PASS','shared_reads':3,'actual_browser':True,'same_document':True,'screenshots':5,'join':'HOLD'} or len(list(output.glob('*.png'))) != 5:
                    raise ValueError('U3_BROWSER_REPORT_HOLD')
                calls += 1
            return result
        w.run = hook
        try:
            result = inherited_smoke(stage,approval,chromium,frontend_port,backend_port)
            if calls != 1 or any((stage/name).read_text(encoding='utf-8') != approval for name in ('SMOKE_OK','HYBRID_NATIVE_OK')):
                raise ValueError('U3_BROWSER_REQUIRED_HOLD')
            w.reviewed(stage, approval)
            return result
        except Exception:
            clear(stage, ('SMOKE_OK','HYBRID_NATIVE_OK'))
            raise
        finally:
            w.run = run
    w.verify_aux, w.test, w.smoke = aux, test, smoke
    helper = load_exact(Path(__file__).resolve().parent/'w8_frozen_npm.py', '257ba8f110508ff30ad03212111cfe8e2299d801')
    return helper.install_into_w8(w)


def load_candidate():
    root = Path(__file__).resolve().parent
    p24 = load_exact(root/'w8_p10j24.py', P24)
    p23 = load_exact(root/'w8_p10j23.py', P23)
    p23.CANDIDATE_MANIFEST = MANIFEST
    p24.CANDIDATE_MANIFEST = MANIFEST
    # Preserve exact 0207 regression source outside the updated product transport.
    p24.HISTORICAL = {**p24.HISTORICAL, p24.PREFIX+'app/core/transaction/postgres_session.py': '8e65e4575a77b11c38c2d2e62ec91fc89d75e23c'}
    return extend(p24.extend_candidate(p23.load_candidate()))


if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
