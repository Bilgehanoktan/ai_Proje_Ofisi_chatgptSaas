"""P08 exact D0 Office endpoint loopback diagnostic, not Next/full-product acceptance.
Requires existing Python FastAPI/Uvicorn, Node >=22, tsc and @types/node.
No downloads. Seven pinned product files for seeded diagnostic; 32 for writer mode.
"""
import argparse
from contextlib import closing
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

PARENT = '3a744286bb1dd3702f4065f4d23eddf92465a480'
B = 'product/ai-company-os-backend/'
F = 'product/ai-company-os-frontend/'
PINS = {
    B+'app/core/development_review/office_workbench.py':'d370681092a192088d67aca908eb6b0d76e5eaef',
    B+'app/api/office_workbench_projection.py':'735f1aa950285b55278cc369ae08620c972f3f66',
    B+'fixtures/core.plan.projection.json':'5a0d82d8c17c5c88f9ba5b1b11ff87e6ad79bfac',
    B+'fixtures/office.snapshot.json':'ac57b926e701196c7507a396aa868ce5e8bd5806',
    F+'features/mvp/officeWorkbenchProjection.ts':'d8d0cf4ce765651bd5490df1482a92ff0c668943',
    F+'features/mvp/localBackend.ts':'9231711d7efb18dd18b68e3322f62337a6477484',
    F+'app/api/demo/office-workbench/route.ts':'749a289984049e0cec27ed93d656023ba4da1fff',
}
WRITER_PINS = {
    B+'app/__init__.py':'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
    B+'app/core/__init__.py':'9d457472970b7f581687ba142d1bf99ba91c7388',
    B+'app/api/__init__.py':'2d899e27663a6e414765904ffd9c4624a825adde',
    B+'app/core/development_review/__init__.py':'77adaf6fcc7ccb5b1396cd4167f74416a956c05b',
    B+'app/core/orchestrator/__init__.py':'9c1e71bb5024a99ec60f934c5944584f63217692',
    B+'app/core/agent_runtime/__init__.py':'5b19819cd7070302e874ecee80170a3921ce8fb0',
    B+'app/core/task_engine/__init__.py':'5b19819cd7070302e874ecee80170a3921ce8fb0',
    B+'app/core/policy/__init__.py':'5b19819cd7070302e874ecee80170a3921ce8fb0',
    B+'app/core/transaction/__init__.py':'5b19819cd7070302e874ecee80170a3921ce8fb0',
    B+'app/engines/__init__.py':'30a8f8f99c47f5c7acae166c57006ef927f3ea73',
    B+'app/engines/model_gateway/__init__.py':'30a8f8f99c47f5c7acae166c57006ef927f3ea73',
    B+'app/core/agent_runtime/lifecycle.py':'4c4ecbba9b2b1ec56dd8f73378b56b50f6578b49',
    B+'app/core/orchestrator/engine.py':'f327ab8a69336cd1ba4d61f56035f540c66d700e',
    B+'app/core/task_engine/dag.py':'04487bda631e9133f3904451a39fc8722e985997',
    B+'app/core/policy/denial.py':'9768b34e447c08136440c891b1974fae131f3ebd',
    B+'app/core/transaction/review.py':'79b2b442f51bb5ea7706a33a5f9f1e7aed258cd4',
    B+'app/core/runtime_preview.py':'341cf800c070da5e6afcc0a5c8a75e57c2396eb9',
    B+'app/core/t1_review.py':'7a526ed4a0fb3ac6931b7c3ab50d3498a4ea068c',
    B+'app/core/development_review/sandbox_store.py':'3b2c7339a869571bb8fe4bd381c50d3f2a1a2368',
    B+'app/core/development_review/task_budget_snapshot.py':'18b40307d069622be114b77de272aaa4adaa0f85',
    B+'app/engines/model_gateway/registry.py':'c923113239c7d783fd32419b2ef51bbcf4c299bf',
    B+'app/engines/model_gateway/fallback.py':'5f8ce7c7e2afd94399fc42cc7eed7b133f6d339a',
    B+'app/engines/model_gateway/provider_contract.py':'e3a75a6d97ca6e50399c56d23f08f2325aa58c7c',
    B+'app/engines/model_gateway/sample_adapter.py':'783e9842c4712dac37b650354286f3f7c06290f0',
    B+'fixtures/core.preview.json':'1e36d523d5fb326b1bc9a4acc5197ef6b29a5dc7',
}
DDL = """CREATE TABLE meta(profile TEXT PRIMARY KEY CHECK(profile='D0_WORKBENCH_0182'), tenant TEXT NOT NULL CHECK(tenant='synthetic-tenant'), company TEXT NOT NULL CHECK(company='synthetic-company'), plan_digest TEXT NOT NULL);
CREATE TABLE sample_task(id TEXT PRIMARY KEY, role TEXT NOT NULL, deps TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('PENDING','OBSERVED')), version INTEGER NOT NULL CHECK(version>=0));
CREATE TABLE sample_lease(task_id TEXT PRIMARY KEY REFERENCES sample_task(id), holder TEXT NOT NULL, fence INTEGER NOT NULL CHECK(fence>0), issued INTEGER NOT NULL CHECK(issued>=0), expires INTEGER NOT NULL CHECK(expires>issued));
CREATE TABLE sample_event(seq INTEGER PRIMARY KEY, command_id TEXT UNIQUE NOT NULL, request_sha TEXT NOT NULL, task_id TEXT NOT NULL REFERENCES sample_task(id), fence INTEGER NOT NULL, tick INTEGER NOT NULL, output_sha TEXT NOT NULL);"""
# DDL and seeding profile from exact P07 tests/test_office_workbench.py (8d96770...).
NODE = r'''
const http=require('node:http');
const {GET}=require(process.argv[2]);
const port=Number(process.argv[3]);
http.createServer(async(req,res)=>{
 if(req.url!='/api/demo/office-workbench'){res.writeHead(404);return res.end();}
 if(req.method!=='GET'){res.writeHead(405);return res.end();}
 try{const r=await GET();res.writeHead(r.status,Object.fromEntries(r.headers));res.end(Buffer.from(await r.arrayBuffer()));}
 catch(e){res.writeHead(500);res.end();}
}).listen(port,'127.0.0.1');
'''
BACKEND = r'''
from fastapi import FastAPI
from app.api.office_workbench_projection import router
import uvicorn, sys
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
app.include_router(router)
uvicorn.run(app,host='127.0.0.1',port=int(sys.argv[1]),log_level='warning')
'''


def sha(data): return hashlib.sha256(data).hexdigest()


def verify(root, writer=False):
    result={}
    for name,expected in (PINS | WRITER_PINS if writer else PINS).items():
        path=root/name
        if path.resolve()!=path or not path.is_file(): raise ValueError('SOURCE_PATH_HOLD: '+name)
        data=path.read_bytes()
        actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual!=expected: raise ValueError('SOURCE_BLOB_HOLD: '+name)
        result[name]={'git_blob':actual,'bytes':len(data),'sha256':sha(data)}
    return result


def seed(path, count, root):
    path.unlink(missing_ok=True)
    plan=json.loads((root/B/'fixtures/core.plan.projection.json').read_bytes())
    digest=plan['digest']
    observed=('plan','draft','research','merge','qa')[:count]
    def content_digest(value):
        return sha(json.dumps(value,sort_keys=True,separators=(',', ':'),ensure_ascii=True,allow_nan=False).encode('ascii'))
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript(DDL)
        db.execute('INSERT INTO meta VALUES(?,?,?,?)',('D0_WORKBENCH_0182','synthetic-tenant','synthetic-company',digest))
        db.executemany('INSERT INTO sample_task VALUES(?,?,?,?,?)',[(t['id'],t['role'],json.dumps(t['depends_on']),'OBSERVED' if t['id'] in observed else 'PENDING',int(t['id'] in observed)) for t in plan['tasks']])
        for i,t in enumerate(observed,1):
            db.execute('INSERT INTO sample_lease VALUES(?,?,?,?,?)',(t,'demo-holder',1,i,i+10))
            db.execute('INSERT INTO sample_event VALUES(?,?,?,?,?,?,?)',(i,'demo-command-'+t,content_digest([digest,t,'demo-holder',1,i]),t,1,i,content_digest('Synthetic adapter review output; not a model response.')))


def port(excluded=()):
    for p in range(17300,17400):
        if p in excluded: continue
        with socket.socket() as s:
            try: s.bind(('127.0.0.1',p)); return p
            except OSError: pass
    raise RuntimeError('NO_LOOPBACK_PORT')


def request(p, path, method='GET'):
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req=urllib.request.Request(f'http://127.0.0.1:{p}'+path,method=method,headers={'Accept':'application/json'})
    try: response=opener.open(req,timeout=4)
    except urllib.error.HTTPError as e: response=e
    with response:
        body=response.read(8193)
        if len(body)>8192: raise ValueError('BODY_CAP')
        return response.status,response.headers.get('Cache-Control'),json.loads(body) if body else None


def ready(p, path, process):
    for _ in range(80):
        if process.poll() is not None: raise RuntimeError('SERVER_EXITED')
        try: request(p,path); return
        except (OSError,urllib.error.URLError): time.sleep(.1)
    raise RuntimeError('SERVER_NOT_READY')


def stop(p):
    if p.poll() is None:
        p.terminate()
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=5)


def run(root, type_roots, writer=False):
    if not __debug__: raise RuntimeError('ASSERTIONS_DISABLED')
    pins=verify(root, writer)
    if writer:
        sys.path.insert(0,str(root/B))
        from app.core.development_review.sandbox_store import Workbench
        from app.core.orchestrator.engine import canonical_plan
        from app.core.development_review.office_workbench import _workbench_snapshot, read_office_workbench
        plan=json.loads((root/B/'fixtures/core.preview.json').read_bytes())['plan']
        assert canonical_plan(plan)==json.loads((root/B/'fixtures/core.plan.projection.json').read_bytes())
    order=('plan','draft','research','merge','qa')
    def advance(path,n):
        wb=Workbench(path,plan)
        task=order[n-1]
        fence=wb.lease(task,'demo-holder',n,10)
        assert wb.observe(task,'demo-holder',fence,n,'demo-command-'+task)=='SAMPLE_OBSERVED'
        return wb
    def build(path,count):
        if not writer: return seed(path,count,root)
        path.unlink(missing_ok=True)
        wb=Workbench(path,plan); wb.create()
        for n in range(1,count+1): advance(path,n)
        return wb
    allowed={'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','TMPDIR','LANG','LC_ALL','HOME'}
    env={k:v for k,v in os.environ.items() if k.upper() in allowed}
    env.update(NO_PROXY='*',no_proxy='*',PYTHONDONTWRITEBYTECODE='1')
    cases=[]
    backend_path='/demo/v1/office/workbench-projection'
    frontend_path='/api/demo/office-workbench'
    def record(name, detail): cases.append({'id':name,'status':'PASS',**detail})
    with tempfile.TemporaryDirectory(prefix='aicos-p08-') as td:
        temp=Path(td); db=temp/'workbench.d0.sqlite'; compiled=temp/'compiled'
        ts=[str(root/name) for name in PINS if name.endswith('.ts')]
        subprocess.run(['tsc','--strict','--target','ES2022','--lib','ES2022,DOM','--module','commonjs','--types','node','--typeRoots',str(type_roots),'--rootDir',str(root/F),'--outDir',str(compiled),*ts],check=True,env=env,timeout=45)
        script=temp/'proxy.cjs';script.write_text(NODE)
        bp=port();fp=port((bp,));env.update(AICOS_D0_WORKBENCH_DB=str(db),AICOS_D0_BACKEND_PORT=str(bp))
        processes=[]
        try:
            build(db,0)
            with (temp/'backend.log').open('w') as blog, (temp/'frontend.log').open('w') as flog:
                back=subprocess.Popen([sys.executable,'-B','-c',BACKEND,str(bp)],cwd=root/B,env=env,stdout=blog,stderr=subprocess.STDOUT);processes.append(back)
                ready(bp,backend_path,back)
                front=subprocess.Popen(['node',str(script),str(compiled/'app/api/demo/office-workbench/route.js'),str(fp)],env=env,stdout=flog,stderr=subprocess.STDOUT);processes.append(front)
                ready(fp,frontend_path,front)
                for n in range(6):
                    if writer:
                        if n: advance(db,n)
                    else: build(db,n)
                    before=sha(db.read_bytes())
                    x=request(bp,backend_path);y=request(fp,frontend_path)
                    expected=[int(n>=1),int(n>=3),int(n>=2)+int(n>=4),int(n>=5)]
                    assert x==y and x[:2]==(200,'no-store'), (n,x,y)
                    body=x[2]; assert body['sample_event_count']==n and [r['observed'] for r in body['roles']]==expected
                    assert body['geometry_join']=='HOLD' and body['freshness']=='HISTORICAL_SAMPLE' and body['real_run_count'] is None
                    assert all(body[k] is False for k in ('dispatch_allowed','provider_called','spend_allowed','release_ready'))
                    assert sha(db.read_bytes())==before
                    record('prefix_'+str(n),{'status_code':200,'observed':expected,'db_sha256_unchanged':True})
                if writer:
                    wb=Workbench(db,plan); snap=wb.snapshot()
                    assert len(snap['events'])==5 and snap['dispatch_allowed'] is False and snap['provider_called'] is False and snap['spend_allowed'] is False
                    assert wb.observe('qa','demo-holder',1,5,'demo-command-qa')=='DUPLICATE_IGNORED'
                    assert len(wb.snapshot()['events'])==5
                    record('writer_reopen_idempotency',{'events':5,'provider_called':False,'duplicate_ignored':True})
                    guard=temp/'guard.d0.sqlite'; gw=build(guard,0)
                    def denied(name, fn, error):
                        old=sha(guard.read_bytes())
                        try: fn()
                        except ValueError as e: assert str(e)==error,(name,str(e))
                        else: raise AssertionError(name+' unexpectedly allowed')
                        assert sha(guard.read_bytes())==old
                        record(name,{'reason':error,'db_sha256_unchanged':True})
                    denied('writer_dependency_hold',lambda:gw.lease('merge','demo-holder',1,10),'SAMPLE_DEPENDENCY_HOLD')
                    denied('writer_iv_hold',lambda:gw.lease('iv','demo-holder',1,10),'SAMPLE_ROLE_HOLD')
                    fence=gw.lease('plan','demo-holder',1,10)
                    denied('writer_expired_lease',lambda:gw.observe('plan','demo-holder',fence,11,'demo-command-plan'),'SAMPLE_LEASE_STALE')
                    denied('writer_wrong_holder',lambda:gw.observe('plan','demo-other',fence,1,'demo-command-plan'),'SAMPLE_LEASE_STALE')
                for name,sql in [('scope',"UPDATE meta SET plan_digest='other'"),('event',"UPDATE sample_event SET output_sha='wrong' WHERE seq=1"),('lease',"UPDATE sample_lease SET fence=2 WHERE task_id='plan'"),('task',"UPDATE sample_task SET role='qa' WHERE id='research'")]:
                    build(db,5)
                    with closing(sqlite3.connect(db)) as con, con: con.execute(sql)
                    before=sha(db.read_bytes()); x=request(bp,backend_path);y=request(fp,frontend_path)
                    assert x==y==(503,'no-store',{'mode':'D0_OFFICE_WORKBENCH_HOLD'}),(name,x,y)
                    assert sha(db.read_bytes())==before
                    record('tamper_'+name,{'status_code':503,'db_sha256_unchanged':True})
                # P08 regressions: original P07 accepted the first three malformed profiles.
                for name,sql in [('event_view','ALTER TABLE sample_event RENAME TO event_original; CREATE VIEW sample_event AS SELECT * FROM event_original;'),
                                 ('unrelated_trigger','CREATE TABLE unrelated(id); CREATE TRIGGER injected AFTER INSERT ON unrelated BEGIN SELECT 1; END;'),
                                 ('missing_table','DROP TABLE sample_lease;')]:
                    build(db,5)
                    with closing(sqlite3.connect(db)) as con, con: con.executescript(sql)
                    before=sha(db.read_bytes());x=request(bp,backend_path);y=request(fp,frontend_path)
                    assert x==y==(503,'no-store',{'mode':'D0_OFFICE_WORKBENCH_HOLD'}),(name,x,y)
                    assert sha(db.read_bytes())==before
                    record('guard_'+name,{'status_code':503,'db_sha256_unchanged':True})
                for suffix in ('-wal','-shm','-journal'):
                    build(db,5);sidecar=Path(str(db)+suffix);sidecar.touch()
                    try:
                        before=sha(db.read_bytes());x=request(bp,backend_path);y=request(fp,frontend_path)
                        assert x==y==(503,'no-store',{'mode':'D0_OFFICE_WORKBENCH_HOLD'}),(suffix,x,y)
                        assert sha(db.read_bytes())==before and sidecar.exists()
                        record('guard_sidecar'+suffix,{'status_code':503,'db_sha256_unchanged':True})
                    finally: sidecar.unlink(missing_ok=True)
                if writer:
                    paired=temp/'paired.workbench.d0.sqlite';pw=Workbench(paired,plan)
                    pw.create(pair_id='a'*32)
                    assert read_office_workbench(paired)['sample_event_count']==0
                    assert read_office_workbench(paired)['geometry_join']=='HOLD'
                    record('guard_pair_compatible',{'status':'PASS','pair_table_allowed':True})
                    before=sha(paired.read_bytes())
                    with _workbench_snapshot(paired) as read_db:
                        for sql in ('SELECT * FROM sample_pair','DELETE FROM sample_task','PRAGMA query_only=OFF','SELECT random()'):
                            try:read_db.execute(sql).fetchall()
                            except sqlite3.DatabaseError:pass
                            else:raise AssertionError('authorizer accepted '+sql)
                    assert sha(paired.read_bytes())==before
                    record('guard_authorizer',{'rejected_operations':4,'db_sha256_unchanged':True})
                db.unlink();x=request(bp,backend_path);y=request(fp,frontend_path)
                assert x==y==(503,'no-store',{'mode':'D0_OFFICE_WORKBENCH_HOLD'}) and not db.exists()
                record('missing',{'status_code':503,'db_created':False})
                build(db,5);before=sha(db.read_bytes())
                assert request(bp,backend_path,'POST')[0]==405 and request(fp,frontend_path,'POST')[0]==405
                assert sha(db.read_bytes())==before
                record('post_rejected',{'status_code':405,'db_sha256_unchanged':True,'frontend_method_guard':'test wrapper only'})
                stop(back)
                assert request(fp,frontend_path)==(503,'no-store',{'mode':'D0_OFFICE_WORKBENCH_HOLD'})
                record('backend_unavailable',{'status_code':503})
        finally:
            for process in reversed(processes): stop(process)
    assert verify(root, writer)==pins
    return {'revision':'W1-0198-P08','parent':PARENT,'scope':'Exact existing Office router + actual compiled Next route GET/parser in Node HTTP test wrapper; '+('actual D0 Workbench writer and sequential persisted state' if writer else 'seeded D0 SQLite (not actual Workbench writer)')+'; not app.main/Next/React/PG or trusted live state','writer_mode':writer,'environment':{'python':sys.version.split()[0],'sqlite':sqlite3.sqlite_version,'node':subprocess.check_output(['node','--version'],text=True).strip(),'typescript':subprocess.check_output(['tsc','--version'],text=True).strip(),**{n:metadata.version(n) for n in ('fastapi','starlette','uvicorn')}},'pins':pins,'cases':cases,'passed':len(cases),'failed':0,'skipped':0,'status':'PASS_DIAGNOSTIC_ONLY','full_http_parity_7':'NOT_RUN','independent_acceptance':'HOLD'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--writer',action='store_true');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--type-roots',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    if a.report.exists() or a.report.is_symlink():p.error('report must not exist')
    try: result=run(a.root.resolve(),a.type_roots.resolve(),a.writer)
    except Exception as e: result={'revision':'W1-0198-P08','status':'HOLD','reason':repr(e)}
    with a.report.open('x',encoding='utf-8') as file:json.dump(result,file,indent=2);file.write('\n')
    print(json.dumps(result,indent=2));return 0 if result['status']=='PASS_DIAGNOSTIC_ONLY' else 1


if __name__=='__main__':sys.exit(main())
