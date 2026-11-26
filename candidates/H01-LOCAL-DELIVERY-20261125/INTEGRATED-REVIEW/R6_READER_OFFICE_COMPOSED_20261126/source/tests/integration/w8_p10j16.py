"""P10J16: composed D0 candidate; retain every inherited W8 gate."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT_BLOB = '0793c34d8ed64fd38e543f2677182c7880f6bfd0'
CANDIDATE_MANIFEST = '8b88d3e6ad080ab61bd91b95c9b98d28faea9b1a'
OLD_BROWSER = 'b4685f647ddfa97854fc09ab003c90f5064cd24d'
NEW_BROWSER = '4a329632e87200cc45b38e402a942971560ce530'

def load_candidate():
    p = Path(__file__).resolve().with_name('w8_p10j15.py')
    raw = p.read_bytes()
    if p.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PARENT_BLOB:
        raise ValueError('P10J15_PARENT_PIN_HOLD')
    spec = importlib.util.spec_from_file_location('p10j16_parent', p)
    if spec is None or spec.loader is None:
        raise ValueError('P10J16_LOADER_HOLD')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.CANDIDATE_MANIFEST = CANDIDATE_MANIFEST
    w = parent.load_candidate()
    if w.HARNESS.get('browser_0187_w1.py') != OLD_BROWSER:
        raise ValueError('P10J16_BROWSER_PARENT_HOLD')
    w.HARNESS['browser_0187_w1.py'] = NEW_BROWSER
    inherited = w.test
    def test_candidate(stage, approval):
        w.installed(stage, approval)
        for marker in ('BUILD_TEST_OK','SMOKE_OK'):
            (stage/marker).unlink(missing_ok=True)
        f = w.frontend(stage)
        env = w.env_local()
        out = stage/'compiled-p10j16-premium'
        out.mkdir(exist_ok=False)
        tsc = f/'node_modules/typescript/bin/tsc'
        names = ('cameraInput','premiumActorIdentity','premiumHybridLayout','premiumModel','premiumOfficeV0','premiumPresentation','premiumLift','premiumRouting','premiumTraffic')
        w.run([w.node(),tsc,'--strict','--target','ES2022','--module','commonjs','--outDir',out,*['office/engine/'+n+'.ts' for n in names]],f,env)
        def m(name):
            return out/(name+'.js')
        fixture = f/'fixtures/office.snapshot.json'
        suites = (
            ('premium-camera',m('cameraInput')),
            ('premium-actor-identity',m('premiumActorIdentity')),
            ('premium-hybrid-layout',m('premiumHybridLayout')),
            ('premium-model',m('premiumModel')),
            ('premium-office-v0',m('premiumOfficeV0'),fixture),
            ('premium-geometry',m('premiumOfficeV0'),m('premiumModel'),fixture),
            ('premium-presentation',m('premiumPresentation'),m('premiumModel'),m('premiumLift')),
            ('premium-routing',m('premiumRouting')),
            ('premium-traffic',m('premiumTraffic')),
            ('premium-traffic-boundary',m('premiumTraffic')),
        )
        for name,*args in suites:
            w.run([w.node(),f/'tests'/(name+'.test.cjs'),*args],f,env)
        w.run([w.node(),'--test','tests/ui-p10j16-office-composition.test.cjs'],f,env)
        return inherited(stage, approval)
    w.test = test_candidate
    return w

if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
