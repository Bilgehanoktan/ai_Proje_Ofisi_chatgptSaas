"""P09 diagnostic: three original routers and compiled frontend handlers, no full Next/app.main."""
import argparse, hashlib, json, os, pathlib, sqlite3, subprocess, sys, tempfile
from contextlib import closing
from run_office_http_p08 import port, request, ready, stop
ROOT=pathlib.Path(__file__).resolve().parents[2]
B=ROOT/'product/ai-company-os-backend'; F=ROOT/'product/ai-company-os-frontend'
ROUTES={'office-workbench':'office/workbench-projection','admission':'admission/sample-projection','task-budget':'task-budget/sample-projection'}
NODE=r'''
const http=require('node:http'),path=require('node:path');const root=process.argv[2];
const keys=['office-workbench','admission','task-budget'];const routes=Object.fromEntries(keys.map(k=>['/api/demo/'+k,require(path.join(root,'app/api/demo',k,'route.js')).GET]));
http.createServer(async(req,res)=>{const get=routes[req.url];if(!get){res.writeHead(404);return res.end();}if(req.method!=='GET'){res.writeHead(405);return res.end();}try{const r=await get();res.writeHead(r.status,Object.fromEntries(r.headers));res.end(Buffer.from(await r.arrayBuffer()));}catch(e){res.writeHead(500);res.end();}}).listen(Number(process.argv[3]),'127.0.0.1');
'''
BACKEND=r'''
from fastapi import FastAPI
from app.api.office_workbench_projection import router as w
from app.api.admission_projection import router as a
from app.api.task_budget_projection import router as t
import uvicorn,sys
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
for router in (w,a,t):app.include_router(router)
uvicorn.run(app,host='127.0.0.1',port=int(sys.argv[1]),log_level='warning')
'''
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(lock):
    for p,expected in lock.items():
        f=ROOT/p
        if f.resolve()!=f or not f.is_file():raise ValueError('SOURCE_PATH_HOLD '+p)
        data=f.read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual!=expected:raise ValueError('SOURCE_BLOB_HOLD '+p)
def main():
    p=argparse.ArgumentParser();p.add_argument('--type-roots',required=True);p.add_argument('--report',required=True,type=pathlib.Path);p.add_argument('--lock',required=True,type=pathlib.Path);p.add_argument('--probe-before',action='store_true');a=p.parse_args()
    if not __debug__:raise RuntimeError('ASSERTIONS_DISABLED')
    lock=json.loads(a.lock.read_text());verify(lock);sys.path.insert(0,str(B))
    from app.core.development_review.sandbox_store import Workbench
    from app.core.development_review.admission_sample import AdmissionSample, OWNER
    from app.core.development_review.task_budget_snapshot import new_pair_id
    plan=json.loads((B/'fixtures/core.preview.json').read_bytes())['plan'];cases=[]
    env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','TMPDIR','LANG','LC_ALL','HOME'}};env.update(NO_PROXY='*',no_proxy='*',PYTHONDONTWRITEBYTECODE='1')
    with tempfile.TemporaryDirectory(prefix='aicos-p09-') as d:
        temp=pathlib.Path(d);w=temp/'demo.workbench.d0.sqlite';b=temp/'demo.admission.d0.sqlite';compiled=temp/'compiled';script=temp/'proxy.cjs';script.write_text(NODE)
        ts=[str(F/'app/api/demo'/k/'route.ts') for k in ROUTES]
        subprocess.run(['tsc','--strict','--target','ES2022','--lib','ES2022,DOM','--module','commonjs','--types','node','--typeRoots',a.type_roots,'--rootDir',str(F),'--outDir',str(compiled),*ts],check=True,env=env,timeout=45)
        bp=port();fp=port((bp,));env.update(AICOS_D0_WORKBENCH_DB=str(w),AICOS_D0_ADMISSION_DB=str(b),AICOS_D0_BACKEND_PORT=str(bp))
        def build(phase='PENDING',n=0):
            for path in (w,b):path.unlink(missing_ok=True)
            pair=new_pair_id();wb=Workbench(w,plan);ab=AdmissionSample(b);wb.create(pair_id=pair);ab.create(pair_id=pair)
            if phase!='PENDING':assert ab.apply(OWNER,'ADMIT',0)=='RESERVED'
            for i,task in enumerate(('plan','draft','research','merge','qa')[:n],1):
                fence=wb.lease(task,'demo-holder',i,10);assert wb.observe(task,'demo-holder',fence,i,'demo-command-'+task)=='SAMPLE_OBSERVED'
            if phase in ('UNKNOWN_HOLD','SETTLED_SAMPLE'):assert ab.apply(OWNER,{'UNKNOWN_HOLD':'UNKNOWN','SETTLED_SAMPLE':'KNOWN_SAMPLE'}[phase],1)==phase
            return pair,wb,ab
        def get(key):
            before={str(x):digest(x) for x in (w,b) if x.exists()};x=request(bp,'/demo/v1/'+ROUTES[key]);y=request(fp,'/api/demo/'+key);assert x==y,(key,x,y);assert x[1]=='no-store';assert before=={str(x):digest(x) for x in (w,b) if x.exists()};return x
        def record(id,**kw):cases.append({'id':id,'status':'PASS',**kw})
        def hold(key,id):
            code,_,body=get(key);assert code==503,(id,body);record(id,http=code)
        def alter(path,sql):
            with closing(sqlite3.connect(path)) as db,db:db.executescript(sql)
        procs=[]
        try:
            build()
            back=subprocess.Popen([sys.executable,'-B','-c',BACKEND,str(bp)],cwd=B,env=env);procs.append(back);ready(bp,'/demo/v1/'+ROUTES['admission'],back)
            front=subprocess.Popen(['node',str(script),str(compiled),str(fp)],env=env);procs.append(front);ready(fp,'/api/demo/admission',front)
            if a.probe_before:
                for id,sql in [('budget_view','ALTER TABLE sample_budget RENAME TO old_budget; CREATE VIEW sample_budget AS SELECT * FROM old_budget;'),('unrelated_trigger','CREATE TABLE unrelated(id); CREATE TRIGGER injected AFTER INSERT ON unrelated BEGIN SELECT 1; END;'),('pair_view','ALTER TABLE sample_pair RENAME TO old_pair; CREATE VIEW sample_pair AS SELECT * FROM old_pair;')]:
                    build('RESERVED',5);alter(b,sql);key='task-budget' if id=='pair_view' else 'admission';code,_,_=get(key);cases.append({'id':id,'observed_http':code,'expected_http':503})
                build('RESERVED',5);side=pathlib.Path(str(b)+'-wal');side.touch()
                try:cases.append({'id':'wal_sidecar','observed_http':get('admission')[0],'expected_http':503})
                finally:side.unlink(missing_ok=True)
            else:
                for phase,version,reserved,observed,n in [('PENDING',0,0,0,0),('RESERVED',1,100,0,3),('UNKNOWN_HOLD',2,100,0,5),('SETTLED_SAMPLE',2,0,60,5)]:
                    pair,wb,ab=build(phase,n);values={}
                    for key in ROUTES:
                        code,_,body=get(key);assert code==200,(phase,key,body);values[key]=body;record(phase+'_'+key,http=200)
                    adm=values['admission'];office=values['office-workbench'];joined=values['task-budget'];assert (adm['phase'],adm['version'],adm['sample_reserved_minor'],adm['sample_observed_minor'],adm['sample_remaining_minor'])==(phase,version,reserved,observed,1000-reserved-observed)
                    assert joined['pair_id']==pair and joined['budget']==adm and joined['office']==office and joined['workbench_event_seq']==n
                    assert joined['research_event_seq']==(3 if n>=3 else None) and joined['causality']=='UNPROVEN' and joined['lease_binding']==joined['geometry_join']=='HOLD'
                    assert joined['consistency']=='STABLE_DOUBLE_READ_NOT_ATOMIC' and not joined['authoritative'] and not joined['spend_allowed'] and adm['actual_cost_minor'] is None
                    record(phase+'_economic_invariants',phase=phase,reserved=reserved,observed=observed,version=version)
                pair,wb,ab=build('UNKNOWN_HOLD',5);before=digest(b);assert ab.apply(OWNER,'UNKNOWN',1)=='DUPLICATE_IGNORED';assert digest(b)==before;record('unknown_idempotency')
                try:ab.apply(OWNER,'KNOWN_SAMPLE',1)
                except ValueError as e:assert str(e)=='ADMISSION_SAMPLE_IDEMPOTENCY_HOLD'
                else:raise AssertionError('unknown released')
                assert digest(b)==before;record('unknown_conflict_hold')
                for id,sql,key in [('pair_mismatch',"UPDATE sample_pair SET pair_id='ffffffffffffffffffffffffffffffff'",'task-budget'),('pair_scope',"UPDATE sample_pair SET principal='other'",'task-budget'),('audit',"DELETE FROM sample_audit WHERE command='demo-admit'",'admission'),('outbox',"DELETE FROM sample_outbox WHERE command='demo-admit'",'admission'),('event',"DELETE FROM sample_event WHERE command='demo-settle'",'admission'),('budget',"UPDATE sample_budget SET reserved=99",'admission'),('duplicate_budget','ALTER TABLE sample_budget RENAME TO old_budget; CREATE TABLE sample_budget AS SELECT * FROM old_budget; INSERT INTO sample_budget SELECT * FROM old_budget;','admission'),('budget_view','ALTER TABLE sample_budget RENAME TO old_budget; CREATE VIEW sample_budget AS SELECT * FROM old_budget;','admission'),('unrelated_trigger','CREATE TABLE unrelated(id); CREATE TRIGGER injected AFTER INSERT ON unrelated BEGIN SELECT 1; END;','admission'),('pair_view','ALTER TABLE sample_pair RENAME TO old_pair; CREATE VIEW sample_pair AS SELECT * FROM old_pair;','task-budget')]:
                    build('UNKNOWN_HOLD',5);alter(b,sql);hold(key,id)
                for suffix in ('-wal','-shm','-journal'):
                    build('RESERVED',5);side=pathlib.Path(str(b)+suffix);side.touch()
                    try:hold('admission','sidecar'+suffix);hold('task-budget','pair_sidecar'+suffix)
                    finally:side.unlink(missing_ok=True)
                build('RESERVED',5)
                from app.core.development_review.paired_read_guard import guarded_read, ADMISSION_TABLES, PAIR_TABLES
                before=(digest(w),digest(b))
                for path,suffix,tables,sqls in [(b,'.admission.d0.sqlite',ADMISSION_TABLES,('SELECT * FROM sample_pair','DELETE FROM sample_budget','PRAGMA query_only=OFF','SELECT random()')),(w,'.workbench.d0.sqlite',PAIR_TABLES,('SELECT * FROM sample_event','DELETE FROM sample_pair'))]:
                    with guarded_read(path,suffix,tables) as db:
                        for sql in sqls:
                            try:db.execute(sql).fetchall()
                            except sqlite3.DatabaseError:pass
                            else:raise AssertionError('authorizer allowed '+sql)
                assert before==(digest(w),digest(b));record('guard_authorizer',denied_operations=6)
                build('RESERVED',5);b.unlink();hold('admission','missing_admission');hold('task-budget','missing_pair');assert not b.exists()
                build('RESERVED',5);before=(digest(w),digest(b))
                for key in ROUTES:assert request(bp,'/demo/v1/'+ROUTES[key],'POST')[0]==405 and request(fp,'/api/demo/'+key,'POST')[0]==405
                assert before==(digest(w),digest(b));record('post_all_rejected',frontend_guard='test wrapper only')
                stop(back)
                for key in ROUTES:assert request(fp,'/api/demo/'+key)[0]==503
                record('backend_unavailable_all')
        finally:
            for proc in reversed(procs):stop(proc)
    verify(lock);result={'revision':'W1-0198-P09','scope':'three original FastAPI routers, compiled Next GET handlers via Node wrapper, original D0 writers, not full product','probe_before':a.probe_before,'pins':lock,'cases':cases,'passed':sum(x.get('status')=='PASS' for x in cases),'full_product_parity':'NOT_RUN','independent_acceptance':'HOLD'}
    with a.report.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print('RESULT',len(cases),result['passed'],[(x['id'],x.get('observed_http')) for x in cases if 'observed_http' in x])
if __name__=='__main__':main()
