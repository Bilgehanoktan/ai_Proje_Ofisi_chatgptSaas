"""P10G candidate adapter. Preserve W8 review and lock gates; no acceptance shortcut."""
import hashlib
import importlib.util
from pathlib import Path
import sys

P10F_BLOB = '155a2179eb71bd554aa34dff36147be4658473e0'
CANDIDATE_MANIFEST = '150cda5f380d889240ca05b51a50ce8baf6e01c0'


def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10f.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != P10F_BLOB:
        raise ValueError('P10F_ADAPTER_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10g_parent_adapter', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10G_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_original()
    test = w.test

    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in ('BUILD_TEST_OK', 'SMOKE_OK'):
            (stage/marker).unlink(missing_ok=True)
        f = w.frontend(stage)
        env = w.env_local()
        out = stage/'compiled-p10g-model'
        out.mkdir(exist_ok=False)
        w.run([w.node(), f/'node_modules/typescript/bin/tsc', '--strict', '--target', 'ES2022', '--module', 'commonjs', '--lib', 'ES2022,DOM', '--rootDir', '.', '--outDir', out, 'features/workflow/readbackCatalog.ts'], f, env)
        env.update(P10D_MODEL=str(out))
        w.run([w.node(), '--test', 'tests/ui-p10g-model.test.cjs'], f, env)
        return test(stage, approval)

    w.test = test_candidate
    return w


if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
