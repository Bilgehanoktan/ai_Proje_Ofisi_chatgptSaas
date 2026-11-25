"""W1-0198-P05 isolated D0 build runner. No CI, main, provider calls or PROD."""
import argparse
import email
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile

MANIFEST_BLOB = '6bce9a2424c251cd001fa8bd4780a3c0395c5ce2'
HARNESS = {
    'run_combined_helpers.cjs': '5d830e090ad87e36c7b340cf9213b91d7682b136',
    'office-workbench-merge.test.cjs': 'c19cb85bd9f418c69ba47eb177b5151db20d43b7',
    'browser_0187_w1.py': 'b829ad9b2fa12f7910e014ec87e9ee2a59d17370',
    'browser_task_budget_0188.py': '4511877f03ffae35d4baef7267c6d7e8ea6bf583',
    'browser_lifecycle_p02.py': 'd7e8760b3f366d410459b33dc16f44b1144fe231',
    'browser_lifecycle_prefix_p03.py': 'c41ea2455ce1bd6792fa829be0377344fd30e9da',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def checked_path(root, name):
    p = root / name
    if p.resolve() != p.absolute() or not p.resolve().is_relative_to(root.resolve()):
        raise ValueError('unsafe path: ' + name)
    return p

DATABASE_FIXTURES = {
    'database/0192/candidate_event_outbox_fence.sql': '6e4780bf9f267c0926b40d582d5afdbd6faa543c',
    'database/0193/candidate_run_head.sql': '180924e97ee1f31fa27332941a41e37fdf73017e',
    'database/0194/candidate_transition_roles.sql': '7b5d374bb7973b283e4fcfa0d796ed6128ef9d27',
    'database/0195/candidate_admission_budget.sql': 'd5dc6abc045da14ef42e88b4e85e50e9062a1b27',
    'database/0196L/candidate_lease_settlement.sql': 'e4c9a84ff705c39486579c393b1f3aaef9e34da9',
}

def verify_aux(root):
    pins = {**{'tests/integration/' + name: h for name, h in HARNESS.items()}, **DATABASE_FIXTURES, 'progress/W1_0198_MILESTONES.json': '1c35eae82c96dea1607b2f3b7c63702f458bee18'}
    for name, h in pins.items():
        p = checked_path(root, name)
        if not p.is_file() or blob(p) != h:
            raise ValueError('auxiliary source missing or changed: ' + name)
    mirror = checked_path(root, 'product/ai-company-os-frontend/features/progress/w1PlanProgress.json')
    if not mirror.is_file() or blob(mirror) != pins['progress/W1_0198_MILESTONES.json']:
        raise ValueError('W1 milestone mirror mismatch')
    return pins

def verify(repo, pin=MANIFEST_BLOB, clean=False):
    product = repo / 'product'
    m = product / 'SOURCE_MANIFEST.json'
    if not m.is_file() or blob(m) != pin:
        raise ValueError('missing or wrong SOURCE_MANIFEST.json; use exact W1-0198-P05 archive')
    files = json.loads(m.read_text(encoding='utf-8'))['files']
    for name, info in files.items():
        p = checked_path(product, name)
        if not p.is_file() or p.stat().st_size != info['bytes'] or sha(p) != info['sha256']:
            raise ValueError('missing or changed source: ' + name)
    if clean:
        actual = {p.relative_to(product).as_posix() for p in product.rglob('*') if p.is_file()}
        if actual != set(files) | {'SOURCE_MANIFEST.json'}:
            raise ValueError('source checkout contains extra files; extract a clean archive')
    f, b = product / 'ai-company-os-frontend', product / 'ai-company-os-backend'
    pairs = 0
    for d1, d2 in [(f/'contracts/generated', b/'contracts/source'), (f/'fixtures', b/'fixtures')]:
        a, c = {p.name: sha(p) for p in d1.glob('*.json')}, {p.name: sha(p) for p in d2.glob('*.json')}
        if a != c:
            raise ValueError('schema/fixture parity mismatch')
        pairs += len(a)
    return files, pairs

def env_local():
    allowed = {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','HOME','USERPROFILE','LOCALAPPDATA','APPDATA','LANG','LC_ALL','SYSTEMDRIVE','HOMEDRIVE','HOMEPATH'}
    env = {k:v for k,v in os.environ.items() if k.upper() in allowed}
    env.update(NEXT_TELEMETRY_DISABLED='1', PYTHONDONTWRITEBYTECODE='1', NO_PROXY='127.0.0.1,localhost', no_proxy='127.0.0.1,localhost')
    return env

def run(args, cwd, env=None):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str,args)), cwd=cwd, env=env, check=True)

def npm():
    p = shutil.which('npm')
    if not p: raise ValueError('npm not installed')
    return p

def frontend(stage): return stage/'product/ai-company-os-frontend'
def backend(stage): return stage/'product/ai-company-os-backend'
def python(stage): return stage/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python')
def node():
    p=shutil.which('node')
    if not p: raise ValueError('Node.js not installed')
    return p

def lock_inventory(stage):
    locks=stage/'locks'; wheels=locks/'wheels'; lock=frontend(stage)/'package-lock.json'
    pkg=json.loads((frontend(stage)/'package.json').read_text(encoding='utf-8'))
    data=json.loads(lock.read_text(encoding='utf-8'))
    packages=data.get('packages',{})
    for key in ['dependencies','devDependencies']:
        if packages.get('',{}).get(key)!=pkg.get(key): raise ValueError('npm direct pins drift')
    for name, version in pkg.get('overrides', {}).items():
        matches = [info for path, info in packages.items() if path.endswith('node_modules/' + name)]
        if not matches or any(info.get('version') != version for info in matches):
            raise ValueError('npm override pin drift: ' + name)
    from urllib.parse import urlparse
    for name, info in packages.items():
        if name and (not info.get('integrity','').startswith(('sha512-','sha256-')) or urlparse(info.get('resolved','')).scheme!='https' or urlparse(info.get('resolved','')).hostname!='registry.npmjs.org'):
            raise ValueError('unreviewable npm dependency: '+name)
    return {'manifest_blob':MANIFEST_BLOB,'npm_lock_sha256':sha(lock),'python_lock_sha256':sha(locks/'python.lock'),'wheels':{p.name:sha(p) for p in sorted(wheels.glob('*.whl'))},'npm_packages':len(packages)-1,'platform':sys.platform,'python':sys.version.split()[0],'node':subprocess.check_output([node(),'--version'],text=True).strip()}

def prepare(repo, stage):
    files,pairs=verify(repo,clean=True)
    if stage.exists() or stage.is_relative_to(repo): raise ValueError('stage must be a new directory outside source')
    aux = verify_aux(repo)
    stage.mkdir(parents=True,exist_ok=False)
    for name in [*files,'SOURCE_MANIFEST.json']:
        dest=stage/'product'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/'product'/name,dest)
    for name in aux:
        dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/name,dest)
    verify_aux(stage)
    locks=stage/'locks';wheels=locks/'wheels';wheels.mkdir(parents=True)
    run([npm(),'install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org'],frontend(stage))
    tools=locks/'test-tools.txt';tools.write_text('playwright==1.57.0\n',encoding='utf-8')
    run([sys.executable,'-m','pip','--isolated','download','--only-binary=:all:','--index-url','https://pypi.org/simple','--dest',wheels,'-r',backend(stage)/'requirements.txt','-r',backend(stage)/'requirements-test.txt','-r',tools],stage)
    entries={}
    for p in sorted(wheels.glob('*.whl')):
        with zipfile.ZipFile(p) as z:
            names=[n for n in z.namelist() if n.endswith('.dist-info/METADATA')]
            if len(names)!=1:raise ValueError('wheel metadata mismatch')
            meta=email.message_from_bytes(z.read(names[0]))
        name=meta['Name'];version=meta['Version'];key=name.lower().replace('_','-')
        if key in entries:raise ValueError('ambiguous wheel: '+key)
        entries[key]=f'{name}=={version} --hash=sha256:{sha(p)}'
    if not entries:raise ValueError('wheelhouse empty')
    (locks/'python.lock').write_text('\n'.join(entries.values())+'\n',encoding='utf-8')
    write_json(locks/'REVIEW.json',lock_inventory(stage))
    print('REVIEW REQUIRED: inspect lock, transitive versions, provenance and wheel hashes.')
    print('Review fingerprint:',sha(locks/'REVIEW.json'))

def reviewed(stage, approval):
    verify(stage)
    verify_aux(stage)
    review=stage/'locks/REVIEW.json'
    if sha(review)!=approval or json.loads(review.read_text(encoding='utf-8'))!=lock_inventory(stage):
        raise ValueError('lock inventory or approval mismatch')

def install(stage, approval):
    reviewed(stage,approval)
    if (stage/'.venv').exists() or (frontend(stage)/'node_modules').exists(): raise ValueError('install requires unused stage')
    run([sys.executable,'-m','venv',stage/'.venv'],stage)
    run([python(stage),'-m','pip','--isolated','install','--no-index','--find-links',stage/'locks/wheels','--require-hashes','-r',stage/'locks/python.lock'],stage)
    run([npm(),'ci','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org'],frontend(stage))
    run([python(stage),'-m','pip','check'],stage,env_local())
    reviewed(stage,approval)
    (stage/'INSTALL_OK').write_text(approval,encoding='utf-8')

def installed(stage, approval):
    reviewed(stage,approval)
    if (stage/'INSTALL_OK').read_text(encoding='utf-8')!=approval: raise ValueError('install not verified')

def test(stage, approval):
    installed(stage,approval)
    marker=stage/'BUILD_TEST_OK';marker.unlink(missing_ok=True)
    (stage/'SMOKE_OK').unlink(missing_ok=True)
    f,b=frontend(stage),backend(stage); e=env_local()
    run([node(),stage/'tests/integration/run_combined_helpers.cjs'],stage,e)
    out=stage/'compiled-task-budget';out.mkdir(exist_ok=False)
    tsc=f/'node_modules/typescript/bin/tsc'
    run([node(),tsc,'--strict','--target','ES2022','--module','commonjs','--lib','ES2022,DOM','--outDir',out,'features/mvp/taskBudgetProjection.ts','app/api/demo/task-budget/route.ts'],f,e)
    run([node(),f/'tests/task-budget.test.cjs',out/'features/mvp/taskBudgetProjection.js',out/'app/api/demo/task-budget/route.js'],f,e)
    run([python(stage),'-m','unittest','discover','-s','tests','-p','test_*.py','-v'],b,e)
    run([node(),f/'node_modules/next/dist/bin/next','build'],f,e)
    run([node(),tsc,'--noEmit'],f,e)
    reviewed(stage,approval)
    marker.write_text(approval,encoding='utf-8')

def get_json(url):
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url,timeout=4) as response:
        return json.load(response)

def ready(url, proc):
    for _ in range(60):
        if proc.poll() is not None: raise ValueError('server exited: '+url)
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url,timeout=2) as r:
                if r.status==200:return
        except OSError:pass
        time.sleep(1)
    raise ValueError('local server not ready: '+url)

def validate_ports(frontend_port, backend_port):
    if any(type(p) is not int or not 1024 <= p <= 49151 for p in (frontend_port, backend_port)) or frontend_port == backend_port:
        raise ValueError('ports must be distinct integers in 1024..49151')


def check_ports(frontend_port, backend_port):
    validate_ports(frontend_port, backend_port)
    for port in (frontend_port, backend_port):
        with socket.socket() as sock:
            if os.name == 'nt':
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            try:
                sock.bind(('127.0.0.1', port))
            except OSError as exc:
                raise ValueError('local port unavailable: ' + str(port)) from exc


def smoke(stage, approval, chromium, frontend_port=17300, backend_port=17301):
    installed(stage,approval)
    if (stage/'BUILD_TEST_OK').read_text(encoding='utf-8')!=approval: raise ValueError('full build/test not passed')
    if not chromium or not chromium.is_file():raise ValueError('explicit reviewed Chrome/Chromium executable required')
    (stage/'SMOKE_OK').unlink(missing_ok=True)
    check_ports(frontend_port, backend_port)
    front_origin=f'http://127.0.0.1:{frontend_port}'
    back_origin=f'http://127.0.0.1:{backend_port}'
    b,f=backend(stage),frontend(stage); e=env_local(); pair=stage/'sample-pair';outbox=stage/'demo.review.atomic.d0.sqlite'
    lifecycle=stage/'lifecycle.d0.sqlite'; prefix=stage/'lifecycle-prefix.d0.sqlite'
    if pair.exists() or outbox.exists() or lifecycle.exists() or prefix.exists():raise ValueError('use fresh stage for smoke; preserve old sample for inspection')
    run([python(stage),'-m','app.core.development_review.paired_demo','--directory',pair,'--outcome','unknown'],b,e)
    run([python(stage),'-m','app.core.development_review.outbox_demo','create','--db',outbox],b,e)
    run([python(stage),'-c',"import sys; sys.path.insert(0,'tests'); from test_lifecycle_projection_p02 import export_fixture; export_fixture(sys.argv[1])",lifecycle],b,e)
    run([python(stage),'-c',"import sys; sys.path.insert(0,'tests'); from test_lifecycle_prefix_p03 import export_prefix_fixture; export_prefix_fixture(sys.argv[1])",prefix],b,e)
    w,a=pair/'demo.workbench.d0.sqlite',pair/'demo.admission.d0.sqlite'
    before=[sha(p) for p in (w,a,outbox,lifecycle,prefix)]
    e.update(AICOS_D0_BACKEND_PORT=str(backend_port), AICOS_D0_WORKBENCH_DB=str(w),AICOS_D0_ADMISSION_DB=str(a),AICOS_D0_REVIEW_DB=str(outbox),AICOS_D0_LIFECYCLE_DB=str(lifecycle),AICOS_D0_LIFECYCLE_PREFIX_DB=str(prefix))
    procs=[]
    try:
        procs.append(subprocess.Popen([str(python(stage)),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(backend_port)],cwd=b,env=e))
        ready(back_origin+'/demo/v1/status',procs[-1])
        procs.append(subprocess.Popen([node(),str(f/'node_modules/next/dist/bin/next'),'start','-H','127.0.0.1','-p',str(frontend_port)],cwd=f,env=e))
        ready(front_origin+'/',procs[-1])
        routes={'mvp':'mvp/diagnostics','admission':'admission/sample-projection','outbox':'outbox/review-projection','office-workbench':'office/workbench-projection','task-budget':'task-budget/sample-projection','lifecycle':'lifecycle/sample-projection','lifecycle-prefix':'lifecycle/prefix-projection'}
        for front,back in routes.items():
            x=get_json(back_origin+'/demo/v1/'+back);y=get_json(front_origin+'/api/demo/'+front)
            if x!=y:raise ValueError('loopback parity mismatch: '+front)
            if front=='lifecycle-prefix' and (x['head_version']!=3 or x['lease_freshness']!='UNKNOWN' or x['dispatch_allowed'] is not False):raise ValueError('prefix invariant mismatch')
            if front=='task-budget' and (x['budget']['phase']!='UNKNOWN_HOLD' or x['budget']['sample_reserved_minor']!=100 or x['spend_allowed'] is not False):raise ValueError('paired invariant mismatch')
        run([python(stage),stage/'tests/integration/browser_lifecycle_prefix_p03.py','--chromium',chromium,'--frontend-port',frontend_port],stage,e)
        run([python(stage),stage/'tests/integration/browser_lifecycle_p02.py','--chromium',chromium,'--frontend-port',frontend_port],stage,e)
        run([python(stage),stage/'tests/integration/browser_0187_w1.py','--chromium',chromium,'--output',stage/'screenshots','--frontend-port',frontend_port],stage,e)
        run([python(stage),stage/'tests/integration/browser_task_budget_0188.py','--chromium',chromium,'--frontend-port',frontend_port],stage,e)
        if before!=[sha(p) for p in (w,a,outbox,lifecycle,prefix)]:raise ValueError('readback changed sample DB')
        print('PASS loopback parity and 52 baseline captures; pixel review and independent acceptance remain open')
    finally:
        for p in reversed(procs):
            p.terminate()
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill();p.wait()
    reviewed(stage,approval)
    (stage/'SMOKE_OK').write_text(approval,encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['audit','prepare','install','test','smoke'])
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--stage',type=Path)
    parser.add_argument('--approve',default='')
    parser.add_argument('--chromium',type=Path)
    parser.add_argument('--frontend-port',type=int,default=17300)
    parser.add_argument('--backend-port',type=int,default=17301)
    args=parser.parse_args();repo=args.repo.resolve();stage=args.stage.resolve() if args.stage else None
    if args.command=='audit':
        files,pairs=verify(repo,clean=True);aux=verify_aux(repo);print(f'PASS {len(files)} source SHA-256 pins; {pairs} shared file pairs; {len(aux)} auxiliary Git blob pins');return
    if stage is None:parser.error('--stage required')
    if args.command=='prepare':prepare(repo,stage);return
    if len(args.approve)!=64:parser.error('--approve requires reviewed REVIEW.json SHA-256')
    if args.command=='install':install(stage,args.approve)
    elif args.command=='test':test(stage,args.approve)
    else:smoke(stage,args.approve,args.chromium.resolve() if args.chromium else None,args.frontend_port,args.backend_port)

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as exc:
        print('HOLD:',exc,file=sys.stderr);sys.exit(1)
