"""External EXT-06 W8 adapter candidate; preserves U3A runner and historical lock review.
Run from the separately delivered candidate; no product writes, no new grants.
"""
import argparse
import hashlib
import importlib.util
import json
import struct
import zlib
from pathlib import Path
import subprocess
import sys

BASE='ba20cd64eba0f09390818c294ae8894fab9a3acf'
MANIFEST='b0ad4ae6f6caaaf37e20f99f19e551272e16956b'
U3_BLOB='391d98ba6128551a2fcb00e4e83a46faba160f2d'
LOCK_SHA='036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88'
MODEL_TEST='candidates/W5-EXT-06/tests/skillStudioModel.test.cjs'
MODEL_PIN='f54d6dd7d1f25be9c50e5c4e9c360ff47392f153'
BROWSER=Path(__file__).resolve().with_name('browser_ext07r3.py')
BROWSER_PIN='eab2719367a67e1b4ebeafe8cd243137020a9421'
MARKERS=('BUILD_TEST_OK','SMOKE_OK','HYBRID_NATIVE_OK')
CASES=['catalog-3-no-live-authority','same-role-department-intersection','search-selection-pinned-detail','selection-reset-and-parent-clear','light-theme','mobile-catalog-overflow-keyboard','no-mutation-external-request-or-pageerror']


def blob(path):
    raw=path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()


def exact(path,pin):
    if not path.is_file() or path.is_symlink() or blob(path)!=pin:
        raise ValueError('EXT07R3_SOURCE_PIN_HOLD: '+path.name)


def lock_bytes(path, expected=LOCK_SHA):
    if path is None or path.is_symlink() or not path.is_file():
        raise ValueError('EXT07R3_LOCK_MISSING')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('EXT07R3_LOCK_HASH_HOLD')
    return raw


def lock_command(w,args,cwd,stage):
    return (Path(cwd)==w.frontend(stage) and list(map(str,args)) == [str(w.npm()),'install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org'])


def clear(stage,names=MARKERS):
    for name in names:(stage/name).unlink(missing_ok=True)


def png_structure(path):
    # Structural/CRC check only, not an independent pixel or capture verifier.
    if path.is_symlink() or path.stat().st_size>100_000_000:return False
    data=path.read_bytes()
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):return False
    off=8;first=True;idat=False
    while off+12<=len(data):
        n=struct.unpack_from('>I',data,off)[0];end=off+12+n
        if end>len(data):return False
        kind=data[off+4:off+8];payload=data[off+8:off+8+n]
        if zlib.crc32(kind+payload)&0xffffffff!=struct.unpack_from('>I',data,off+8+n)[0]:return False
        if first:
            if kind!=b'IHDR' or n!=13:return False
            width,height=struct.unpack_from('>II',payload)
            if not (0<width<=32768 and 0<height<=32768):return False
            first=False
        if kind==b'IDAT':idat=True
        if kind==b'IEND':return n==0 and idat and end==len(data)
        off=end
    return False


def browser_report(output):
    data=json.loads((output/'EXT07R3_BROWSER_REPORT.json').read_text(encoding='utf-8'))
    if data!={'status':'PASS','cases':CASES,'screenshots':3,'actual_browser':True,'independent_acceptance':'HOLD'}:
        raise ValueError('EXT07R3_BROWSER_REPORT_HOLD')
    names={'01-dark-detail.png','02-light.png','03-mobile.png'}
    if {p.name for p in output.glob('*.png')}!=names or any(not png_structure(output/n) for n in names):
        raise ValueError('EXT07R3_CAPTURE_HOLD')


def extend(w,lock):
    if w.MANIFEST_BLOB!=MANIFEST:raise ValueError('EXT07R3_MANIFEST_HOLD')
    old_aux,old_prepare,old_review,old_test,old_smoke=w.verify_aux,w.prepare,w.reviewed,w.test,w.smoke
    def aux(root):
        pins=old_aux(root)
        if MODEL_TEST in pins and pins[MODEL_TEST]!=MODEL_PIN:raise ValueError('EXT07R3_AUX_COLLISION')
        exact(w.checked_path(root,MODEL_TEST),MODEL_PIN)
        return {**pins,MODEL_TEST:MODEL_PIN}
    def prepare(repo,stage):
        raw=lock_bytes(lock)
        run=w.run; calls=0
        def hook(args,cwd,env=None):
            nonlocal calls
            if lock_command(w,args,cwd,stage):
                if calls:raise ValueError('EXT07R3_DUPLICATE_LOCK')
                with (w.frontend(stage)/'package-lock.json').open('xb') as out:out.write(raw)
                calls+=1;return None
            if '--package-lock-only' in list(map(str,args)):raise ValueError('EXT07R3_UNEXPECTED_LOCK_COMMAND')
            return run(args,cwd,env)
        w.run=hook
        try:
            result=old_prepare(repo,stage)
            if calls!=1:raise ValueError('EXT07R3_LOCK_NOT_COPIED')
            lock_bytes(w.frontend(stage)/'package-lock.json')
            return result
        finally:w.run=run
    def reviewed(stage,approval):
        lock_bytes(w.frontend(stage)/'package-lock.json')
        return old_review(stage,approval)
    def test(stage,approval):
        w.installed(stage,approval);clear(stage)
        try:
            result=old_test(stage,approval)
            f=w.frontend(stage);out=stage/'compiled-ext07r3';out.mkdir(exist_ok=False)
            env=w.env_local()
            w.run([w.node(),f/'node_modules/typescript/bin/tsc','--strict','--target','ES2020','--module','commonjs','--esModuleInterop','--resolveJsonModule','--outDir',out,'features/capabilities/ext06/skillStudioModel.ts'],f,env)
            w.run([w.node(),'--test',stage/MODEL_TEST],stage,{**env,'EXT06_MODEL':str(out/'skillStudioModel.js')})
            if (stage/'BUILD_TEST_OK').read_text(encoding='utf-8')!=approval:raise ValueError('EXT07R3_BUILD_REQUIRED')
            w.reviewed(stage,approval);return result
        except Exception:clear(stage);raise
    def smoke(stage,approval,chromium,frontend_port=17300,backend_port=17301):
        w.installed(stage,approval);clear(stage,MARKERS[1:]);run=w.run;calls=0
        def hook(args,cwd,env=None):
            nonlocal calls
            result=run(args,cwd,env)
            if len(args)>1 and str(args[1])==str(stage/'tests/integration/browser_unified_u3.py'):
                if calls or Path(cwd)!=stage:raise ValueError('EXT07R3_BROWSER_CALL_HOLD')
                exact(BROWSER,BROWSER_PIN);w.verify_aux(stage)
                output=stage/'ext07r3-browser'
                run([w.python(stage),BROWSER,'--frontend-port',str(frontend_port),'--chromium',chromium,'--output',output],stage,w.env_local())
                browser_report(output);calls+=1
            return result
        w.run=hook
        try:
            result=old_smoke(stage,approval,chromium,frontend_port,backend_port)
            if calls!=1 or any((stage/n).read_text(encoding='utf-8')!=approval for n in MARKERS[1:]):raise ValueError('EXT07R3_BROWSER_REQUIRED')
            w.reviewed(stage,approval);return result
        except Exception:clear(stage,MARKERS[1:]);raise
        finally:w.run=run
    w.verify_aux,w.prepare,w.reviewed,w.test,w.smoke=aux,prepare,reviewed,test,smoke
    return w


def load(repo,lock):
    # Validate exact pinned checkout before importing any repository runner.
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    dirty=subprocess.check_output(['git','-C',str(repo),'status','--porcelain','--untracked-files=all'],text=True)
    if head!=BASE or dirty:raise ValueError('EXT07R3_CHECKOUT_HOLD')
    exact(repo/'product/SOURCE_MANIFEST.json',MANIFEST)
    path=repo/'tests/integration/w8_unified_u3.py';exact(path,U3_BLOB)
    spec=importlib.util.spec_from_file_location('ext07r3_u3',path)
    if spec is None or spec.loader is None:raise ValueError('EXT07R3_LOADER_HOLD')
    u3=importlib.util.module_from_spec(spec);spec.loader.exec_module(u3)
    if u3.MANIFEST!='07f1fc919daa6dd3d7ffad7b67c3e9eebcd5d276':raise ValueError('EXT07R3_PARENT_MANIFEST_HOLD')
    u3.MANIFEST=MANIFEST
    return extend(u3.load_candidate(),lock)


if __name__=='__main__':
    p=argparse.ArgumentParser(add_help=False);p.add_argument('--repo',required=True,type=Path);p.add_argument('--npm-lock',type=Path)
    a,rest=p.parse_known_args()
    try:
        repo=a.repo.resolve();w=load(repo,a.npm_lock)
        sys.argv=[sys.argv[0],*rest,'--repo',str(repo)];w.main()
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as exc:
        print('HOLD:',exc,file=sys.stderr);sys.exit(1)
