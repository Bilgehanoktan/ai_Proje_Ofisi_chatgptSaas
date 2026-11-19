"""MI common 02: bind original U3 W8 to exact ORG/Skill sources and original npm lock."""
import hashlib
from pathlib import Path
import subprocess
import sys
import importlib.util

MANIFEST = '03af243e8683f92c5d9c0b24e90b70d2bd6af29f'
PARENT = 'e7335eac1e4358ceef001a494f45f56ba9544fc0'
LOCK = 'docs/ORG-07C-R8-INTEGRATION/original-lock/package-lock.json'
LOCK_BLOB = '4cd33f437df85d7e74c7946a0999f76adf2e31fe'
LOCK_SHA = '036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88'
ORG = 'tests/integration/org-07c-r8'
SKILL = 'candidates/W5-EXT-06/tests/skillStudioModel.test.cjs'
EXTRA = {
    LOCK: LOCK_BLOB,
    ORG+'/tests/process.d.ts': '9fdb78617c28724b580bcf26e764d34981146cc5',
    ORG+'/tests/route.test.cjs': '4a2199dd6cc60f452b0a053f763d2d7a638b0f36',
    ORG+'/tests/owner_binding_product.test.cjs': '6f8e0046c773d330f446ab262c0fc8b4dc792bbf',
    ORG+'/tests/closed_reader.test.cjs': '6b8c418fdba4c3fd0c7c924395e27a9f89f7e19c',
    SKILL: 'f54d6dd7d1f25be9c50e5c4e9c360ff47392f153',
}
MARKERS = ('BUILD_TEST_OK', 'SMOKE_OK', 'HYBRID_NATIVE_OK')


def lock_bytes(w, root, name=LOCK):
    p = w.checked_path(root, name)
    if not p.is_file() or p.is_symlink():
        raise ValueError('MI02_LOCK_MISSING')
    raw = p.read_bytes()
    if len(raw) != 33618 or hashlib.sha256(raw).hexdigest() != LOCK_SHA or w.blob(p) != LOCK_BLOB:
        raise ValueError('MI02_LOCK_PIN_HOLD')
    return raw


def extend(w):
    if w.MANIFEST_BLOB != MANIFEST:
        raise ValueError('MI02_MANIFEST_HOLD')
    original_aux, original_prepare, original_inventory, original_test = w.verify_aux, w.prepare, w.lock_inventory, w.test

    def aux(root):
        pins = original_aux(root)
        for name, expected in EXTRA.items():
            if name in pins and pins[name] != expected:
                raise ValueError('MI02_AUX_COLLISION_HOLD: '+name)
            p = w.checked_path(root, name)
            if not p.is_file() or w.blob(p) != expected:
                raise ValueError('MI02_AUX_PIN_HOLD: '+name)
        lock_bytes(w, root)
        return {**pins, **EXTRA}

    def inventory(stage):
        lock_bytes(w, stage, 'product/ai-company-os-frontend/package-lock.json')
        result = original_inventory(stage)
        if result['npm_lock_sha256'] != LOCK_SHA:
            raise ValueError('MI02_INVENTORY_HOLD')
        return {**result, 'mi02_adapter_blob': w.blob(Path(__file__).resolve()), 'original_lock_blob': LOCK_BLOB}

    def prepare(repo, stage):
        aux(repo)
        run, calls = w.run, 0
        def hook(args, cwd, env=None):
            nonlocal calls
            actual = list(map(str, args))
            if '--package-lock-only' not in actual:
                return run(args, cwd, env)
            expected = [str(w.npm()), 'install', '--package-lock-only', '--ignore-scripts', '--no-audit', '--no-fund', '--registry=https://registry.npmjs.org']
            if calls or actual != expected or Path(cwd) != w.frontend(stage):
                raise ValueError('MI02_LOCK_PREPARE_CALL_HOLD')
            raw = lock_bytes(w, stage)
            target = w.checked_path(stage, 'product/ai-company-os-frontend/package-lock.json')
            with target.open('xb') as f:
                f.write(raw)
            lock_bytes(w, stage, 'product/ai-company-os-frontend/package-lock.json')
            calls += 1
        w.run = hook
        try:
            result = original_prepare(repo, stage)
            if calls != 1:
                raise ValueError('MI02_LOCK_COPY_REQUIRED_HOLD')
            inventory(stage)
            return result
        finally:
            w.run = run

    def test(stage, approval):
        w.installed(stage, approval)
        for name in MARKERS:
            (stage/name).unlink(missing_ok=True)
        try:
            f = w.frontend(stage)
            tsc = f/'node_modules/typescript/bin/tsc'
            env = w.env_local()
            work = stage/ORG
            out = work/'build'
            skill = stage/'compiled-mi02-skill'
            out.mkdir(exist_ok=False)
            skill.mkdir(exist_ok=False)
            w.run([w.node(),tsc,'--strict','--target','ES2022','--module','commonjs','--lib','ES2022,DOM','--rootDir',f,'--outDir',out,work/'tests/process.d.ts',f/'app/api/demo/organization/route.ts',f/'features/data/projectionRead.ts'], f, env)
            w.run([w.node(),'--test',*[work/'tests'/n for n in ('owner_binding_product.test.cjs','route.test.cjs','closed_reader.test.cjs')]], f, env)
            source = f/'features/capabilities/ext06'
            w.run([w.node(),tsc,'--strict','--target','ES2020','--module','commonjs','--esModuleInterop','--resolveJsonModule','--rootDir',source,'--outDir',skill,source/'skillStudioModel.ts'], f, env)
            w.run([w.node(),'--test',stage/SKILL], f, {**env,'EXT06_MODEL':str(skill/'skillStudioModel.js')})
            result = original_test(stage, approval)
            if (stage/'BUILD_TEST_OK').read_text(encoding='utf-8') != approval:
                raise ValueError('MI02_BUILD_REQUIRED_HOLD')
            w.reviewed(stage, approval)
            return result
        except Exception:
            for name in MARKERS:
                (stage/name).unlink(missing_ok=True)
            raise

    w.verify_aux, w.prepare, w.lock_inventory, w.test = aux, prepare, inventory, test
    return w


def load_candidate():
    path = Path(__file__).resolve().with_name('w8_unified_u3.py')
    raw = path.read_bytes()
    if path.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT:
        raise ValueError('MI02_U3_PARENT_HOLD')
    spec = importlib.util.spec_from_file_location('mi02_u3', path)
    if spec is None or spec.loader is None:
        raise ValueError('MI02_U3_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.MANIFEST = MANIFEST
    return extend(parent.load_candidate())


if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
