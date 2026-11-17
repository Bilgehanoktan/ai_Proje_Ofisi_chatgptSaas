"""D4-R3 Windows isolated bootstrap; source-pinned D1/D3 mechanics, no production or default execution."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys

R1='79f815188d7aa6135b8b1cfb86f83179bd83aa0d'
HELPER='d20bbb6740901e2abf02d445b20cfa34f4b93d50'
LOCK='576dc61d00895bf3ba624b881b49785c1617b1e476bd4b7dec3ea05217c9b4ac'
D1_REVIEW='ce09749cc9507961cec8120c712cc599556fc83d6ecf1f0da2eae4546a4dd407'
D1_FINAL='5e50f13bf80cf221c981fe535bcd3bcbfeb02e3adc0dc65363e6996064545177'
ADMIN='aicos_d4_admin'
DB='aicos_d4_0229'
PORT=55434
CLUSTER='aicos_d4_0229_disposable'
ACK='0229_D4_R3_DISPOSABLE_LOCAL_ONLY'
SEEDS=tuple('aicos_d4_seed_'+k for k in 'abcd')
RUNTIME=('aicos_d4_run_a',)
ROLES=SEEDS+RUNTIME
BASE=Path('C:/AIOS')

class Hold(Exception): pass

def need(ok,label):
    if not ok: raise Hold(label)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def blob(p):
    b=p.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def file(p):
    need(p.is_file() and p.resolve()==p.absolute(),'FILE_OR_LINK_HOLD');return p

def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')

def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def git(root,*args): return subprocess.check_output(['git','-C',str(root),*args]).decode().strip()

def fixture_check(repo,commit):
    need(re.fullmatch(r'[0-9a-f]{40}',commit) and git(repo,'rev-parse','HEAD')==commit,'FIXTURE_HEAD_HOLD')
    need(not git(repo,'status','--porcelain','--untracked-files=all'),'FIXTURE_DIRTY_HOLD')
    need(not git(repo,'ls-files','--others','--ignored','--exclude-standard'),'IGNORED_SOURCE_HOLD')
    need(subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',R1,commit]).returncode==0,'FIXTURE_ANCESTOR_HOLD')
    folder=repo/'candidates/D4-R3'
    runner=file(folder/'run_d4_r3.py')
    need(Path(__file__).resolve()==runner.resolve() and blob(runner)==git(repo,'rev-parse',commit+':candidates/D4-R3/run_d4_r3.py'),'RUNNER_PIN_HOLD')
    mp=file(folder/'INPUT_PINS.json')
    need(blob(mp)=='41fec19c4ca1cdda2db3a474dc3fd22b24b93529','INPUT_PIN_MANIFEST_HOLD')
    m=json.loads(mp.read_text(encoding='utf-8'))
    need(m['parent']==R1 and git(repo,'rev-parse',commit+':product')==m['product_tree'],'PRODUCT_TREE_HOLD')
    for x in m['files']:
        p=file(repo/x['path'])
        need(blob(p)==x['blob'] and p.stat().st_size==x['bytes'],'INPUT_FILE_PIN_HOLD')
    for n in ('company_pg.py','RUN_PLAN.json'):
        p=file(folder/n);need(blob(p)==git(repo,'rev-parse',commit+':candidates/D4-R3/'+n),'CANDIDATE_PIN_HOLD')
    # Re-read all original product source bytes; git tree alone does not validate checkout.
    count=0
    for row in subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','-z',commit,'--','product']).split(b'\0'):
        if not row: continue
        meta,name=row.split(b'\t',1);mode,kind,pin=meta.decode().split()
        need(kind=='blob' and mode in ('100644','100755') and blob(file(repo/name.decode()))==pin,'PRODUCT_CHECKOUT_HOLD')
        count+=1
    need(count>0,'PRODUCT_EMPTY_HOLD')
    hp=file(repo/'scripts/run_d1_0227_authfix.py');need(blob(hp)==HELPER,'HELPER_PIN_HOLD')
    return folder,load(hp,'d1_verified_helper')

def fixed_paths(repo,root,scenario):
    need(repo.resolve()==repo.absolute() and root.resolve()==root.absolute(),'ROOT_LINK_HOLD')
    need(repo==BASE/'core-0229-d4-r3-source' and root==BASE/('core-0229-d4-r3-'+scenario.replace('_','-')),'ISOLATION_PATH_HOLD')
    need(not root.exists(),'FRESH_STAGE_HOLD')

def input_check(h,e1,d1):
    for p,d in [(d1/'pg.lock',LOCK),(d1/'D1_REVIEW.json',D1_REVIEW),(d1/'evidence/D1_FINAL.json',D1_FINAL),(e1/'locks/REVIEW_0227.json',h.E1_REVIEW),(e1/'locks/python.lock',h.E1_LOCK),(d1/'postgresql-17.12.zip',h.SERVER_HASH)]:
        need(sha(file(p))==d,'ACCEPTED_INPUT_HASH_HOLD')
    rev=json.loads((e1/'locks/REVIEW_0227.json').read_text(encoding='utf-8'))
    wheels=rev['inventory']['wheels'];need(len(wheels)==28,'E1_WHEEL_COUNT_HOLD')
    for n,d in wheels.items(): need(Path(n).name==n and sha(file(e1/'locks/wheels'/n))==d,'E1_WHEEL_HOLD')
    need({p.name for p in (d1/'wheels').iterdir()}==set(h.WHEELS),'D1_WHEEL_SET_HOLD')
    for n,(_,_,d) in h.WHEELS.items(): need(sha(file(d1/'wheels'/n))==d,'D1_WHEEL_HOLD')
    pins={}
    for line in (d1/'pg.lock').read_text(encoding='utf-8').splitlines():
        m=re.fullmatch(r'([^=\s]+)==([^\s]+) --hash=sha256:[0-9a-f]{64}',line)
        need(m is not None and h.norm(m[1]) not in pins,'LOCK_FORMAT_HOLD');pins[h.norm(m[1])]=m[2]
    need(len(pins)==31,'LOCK_COUNT_HOLD');return pins

def bootstrap_statements(text):
    # The pinned R2 roles file starts with one procedural guard, then simple DDL.
    body='\n'.join(l for l in text.splitlines() if not l.lstrip().startswith('--'))
    head,marker,tail=body.partition('END $guard$;')
    need(bool(marker) and head.strip().startswith('DO $guard$ BEGIN'),'ROLE_GUARD_HOLD')
    statements=[x.strip() for x in tail.split(';') if x.strip()]
    need(len(statements)==13 and [x.split()[0:2] for x in statements]==[['CREATE','ROLE']]*10+[['CREATE','DATABASE'],['REVOKE','CONNECT,TEMPORARY'],['GRANT','CONNECT']],'ROLE_SQL_SHAPE_HOLD')
    return [head+marker,*statements]

def safe_error(exc):
    result={'type':type(exc).__name__}
    if isinstance(exc,Hold) or type(exc).__name__=='Hold': result['reason']=str(exc)
    state=getattr(exc,'sqlstate',None)
    if isinstance(state,str) and re.fullmatch('[A-Z0-9]{5}',state):result['sqlstate']=state
    return result

def child(repo,root,commit,scenario):
    need(os.environ.pop('AICOS_D4_CHILD_ACK',None)==ACK,'CHILD_ACK_HOLD')
    need(repo==BASE/'core-0229-d4-r3-source' and root==BASE/('core-0229-d4-r3-'+scenario.replace('_','-')) and root.resolve()==root.absolute(),'CHILD_PATH_HOLD')
    folder,h=fixture_check(repo,commit);r2=repo/'candidates/D4-R2'
    review=json.loads(file(root/'evidence/D4_REVIEW.json').read_text(encoding='utf-8'))
    need(review['fixture_commit']==commit and review['runner_blob']==blob(file(Path(__file__).absolute())) and review['cluster']==CLUSTER and review['port']==PORT and review['scenario']==scenario,'CHILD_REVIEW_HOLD')
    need(file(root/'data/PG_VERSION').read_text().strip()=='17','CHILD_DATA_HOLD')
    import psycopg
    from psycopg import sql
    report={'status':'HOLD','classification':'D0_COMPANY_T1_FIXTURE_ONLY','fixture_commit':commit,'scenario':scenario,'checks':[],'bootstrap':[],'canonical_mapping':'HOLD','independent_acceptance':'HOLD'}
    stage='credentials'
    try:
        creds=json.load(sys.stdin)
        need(set(creds)=={ADMIN,*ROLES} and all(re.fullmatch('[A-Za-z0-9_-]{40,60}',v) for v in creds.values()),'SECRET_PIPE_HOLD')
        need(psycopg.__version__=='3.3.9' and psycopg.pq.__impl__=='binary','DRIVER_HOLD')
        common={'host':'127.0.0.1','hostaddr':'127.0.0.1','port':str(PORT),'sslmode':'disable','connect_timeout':3,'passfile':os.devnull}
        def connect(role,db=DB):
            c=psycopg.connect(**common,user=role,dbname=db,password=creds[role],autocommit=True)
            try:
                row=c.execute("SELECT current_database(),session_user,current_user,host(inet_server_addr()),inet_server_port(),current_setting('cluster_name'),current_setting('server_version_num'),current_setting('listen_addresses')").fetchone()
                need(row==(db,role,role,'127.0.0.1',PORT,CLUSTER,'170012','127.0.0.1'),'SERVER_PROFILE_HOLD')
                if role!=ADMIN:
                    flags=c.execute("SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication,rolinherit FROM pg_roles WHERE rolname=session_user").fetchone()
                    need(flags==(False,)*6,'ROLE_FLAGS_HOLD')
                    need(c.execute("SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=session_user)").fetchone()==(0,),'ROLE_MEMBERSHIP_HOLD')
                if role in RUNTIME:
                    need(c.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'aicos_d4_seed_%' AND rolcanlogin").fetchone()==(0,),'SEED_LOGIN_HOLD')
                return c
            except BaseException:c.close();raise
        def mark(x):report['checks'].append(x)
        def boot(x):report['bootstrap'].append(x)
        stage='roles_and_database'
        with connect(ADMIN,'postgres') as c:
            need(Path(c.execute('SHOW data_directory').fetchone()[0]).resolve()==(root/'data').resolve(),'DATA_DIRECTORY_HOLD')
            need(c.execute("SELECT current_setting('password_encryption')").fetchone()==('scram-sha-256',),'SCRAM_HOLD')
            rules=c.execute('SELECT DISTINCT auth_method,error FROM pg_hba_file_rules').fetchall()
            need(bool(rules) and all(x==('scram-sha-256',None) for x in rules),'HBA_HOLD')
            for stmt in bootstrap_statements((r2/'00_roles.sql').read_text(encoding='utf-8')):c.execute(stmt)
            c.execute('REVOKE CONNECT,TEMPORARY ON DATABASE postgres,template1,template0 FROM PUBLIC')
            for role in ROLES:
                v=c.pgconn.encrypt_password(creds[role].encode('ascii'),role.encode('ascii'),b'scram-sha-256').decode('ascii')
                need(v.startswith('SCRAM-SHA-256$'),'VERIFIER_HOLD')
                c.execute(sql.SQL('ALTER ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role),sql.Literal(v)))
                del v
            boot(stage)
        stage='schema_and_policies'
        with connect(ADMIN) as c:
            for name in ('01_schema.sql','02_policies.sql'):c.execute((r2/name).read_text(encoding='utf-8'),prepare=False)
            boot(stage)
        stage='coherent_seed'
        backend=repo/'product/ai-company-os-backend'
        sys.path.insert(0,str(backend));sys.path.insert(0,str(backend/'tests'))
        module=load(folder/'company_pg.py','d4_company_verified')
        fixture=module.CompanyFixture(lambda:connect(RUNTIME[0]),root/'references.sqlite')
        with connect(SEEDS[0]) as c:fixture.seed(c)
        for k,role in zip('bcd',SEEDS[1:]):
            with connect(role) as c:c.execute((r2/('seed_'+k+'.sql')).read_text(encoding='utf-8'),prepare=False)
        with connect(ADMIN) as c:
            for role in SEEDS:c.execute(sql.SQL('ALTER ROLE {} NOLOGIN PASSWORD NULL').format(sql.Identifier(role)))
            need(c.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'aicos_d4_seed_%' AND rolcanlogin").fetchone()==(0,),'SEED_DISABLE_HOLD')
            c.execute((r2/'03_owner_probe.sql').read_text(encoding='utf-8'),prepare=False)
            rows=c.execute("SELECT relname,relrowsecurity,relforcerowsecurity,pg_get_userbyid(relowner) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='t1_candidate' AND relkind='r'").fetchall()
            need(len(rows)==16 and all(r[1:]==(True,True,'aicos_d4_owner') for r in rows),'RLS_INVENTORY_HOLD')
            boot(stage)
        stage='company_scenario'
        result=fixture.run(mark) if scenario=='race' else fixture.run_lost_ack(mark)
        expected=json.loads((folder/'RUN_PLAN.json').read_text(encoding='utf-8'))['scenarios'][scenario]
        need(report['checks']==expected and result['retry_allowed'] is False,'SCENARIO_CHECK_INVENTORY_HOLD')
        report['result']=result
        with connect(ADMIN) as c:
            for role in RUNTIME:c.execute(sql.SQL('ALTER ROLE {} NOLOGIN PASSWORD NULL').format(sql.Identifier(role)))
        report['status']='D4_R3_SCENARIO_PROBES_PASS';boot(stage)
    except Exception as exc:report['failure']={'stage':stage,**safe_error(exc)}
    finally:write(root/'evidence/D4_PROBE.json',report)
    return 0 if report['status']=='D4_R3_SCENARIO_PROBES_PASS' else 1

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--commit',required=True);p.add_argument('--child',action='store_true');p.add_argument('--scenario',choices=('race','lost_ack'),required=True);a=p.parse_args()
    need(sys.platform=='win32' and sys.version.split()[0]=='3.14.3','WINDOWS_PYTHON_HOLD')
    repo=a.repo.absolute();root=BASE/('core-0229-d4-r3-'+a.scenario.replace('_','-'));e1=BASE/'core-0227-e1';d1=BASE/'core-0227-pg-retry2';source=BASE/'core-0227-clean'
    if a.child:return child(repo,root,a.commit,a.scenario)
    fixed_paths(repo,root,a.scenario);folder,h=fixture_check(repo,a.commit);h.source_check(source);pins=input_check(h,e1,d1)
    review={'fixture_commit':a.commit,'fixture_manifest_blob':blob(folder/'INPUT_PINS.json'),'scenario':a.scenario,'runner_blob':blob(file(Path(__file__).absolute())),'accepted_lock_sha256':LOCK,'accepted_d1_review_sha256':D1_REVIEW,'source_commit':h.SOURCE,'product_manifest':h.MANIFEST,'port':PORT,'cluster':CLUSTER,'database':DB,'credential_mode':'all ephemeral; no password in evidence','scope':'D4-R3 fresh Company T1 fixture only; previous clusters untouched'}
    print(json.dumps(review,indent=2));need(input('Approve isolated D4-R3 scenario only? EVET/HAYIR: ')=='EVET','APPROVAL_HOLD')
    with socket.socket() as s:s.bind(('127.0.0.1',PORT))
    root.mkdir();(root/'tmp').mkdir();logs=root/'evidence';logs.mkdir();write(logs/'D4_REVIEW.json',review)
    final={'status':'HOLD','server_stopped':False,'source_preserved':False,'fixture_preserved':False,'accepted_inputs_preserved':False,'canonical_mapping':'HOLD','independent_acceptance':'HOLD'};ctl=None;e=None;stage='venv'
    try:
        e=h.env_local(root);h.run([sys.executable,'-m','venv',root/'.venv'],root,e,logs/'01_venv.log');py=root/'.venv/Scripts/python.exe'
        h.run([py,'-m','pip','--isolated','install','--no-index','--find-links',e1/'locks/wheels','--find-links',d1/'wheels','--require-hashes','-r',d1/'pg.lock'],root,e,logs/'02_pip_install.log')
        h.run([py,'-m','pip','check'],root,e,logs/'03_pip_check.log');h.run([py,'-m','pip','list','--format=json'],root,e,logs/'04_pip_list.json')
        actual={h.norm(x['name']):x['version'] for x in json.loads((logs/'04_pip_list.json').read_text(encoding='utf-8'))};need(all(actual.get(n)==v for n,v in pins.items()) and set(actual)-set(pins)<={'pip'},'INSTALLED_PINS_HOLD')
        stage='server_extract';bindir=h.extract_archive(d1/'postgresql-17.12.zip',root/'server');e=h.env_local(root,bindir);ctl=bindir/'pg_ctl.exe'
        need(re.search(r'\b17\.12\b',subprocess.check_output([str(bindir/'postgres.exe'),'--version'],env=e,text=True)),'SERVER_VERSION_HOLD')
        stage='initdb';creds={r:secrets.token_urlsafe(32) for r in (ADMIN,*ROLES)};h.ADMIN=ADMIN;h.protected_initdb(root,bindir,e,creds[ADMIN])
        with (root/'data/postgresql.conf').open('a',encoding='ascii') as f:f.write("\nlisten_addresses = '127.0.0.1'\nport = 55434\ncluster_name = 'aicos_d4_0229_disposable'\nssl = off\npassword_encryption = 'scram-sha-256'\nlog_statement = 'none'\nlog_min_error_statement = panic\n")
        stage='start';h.run([ctl,'-D',root/'data','-l',root/'server-private.log','-w','start'],root,e)
        stage='probes';rc=subprocess.run([str(py),'-I','-B',str(Path(__file__).absolute()),'--repo',str(repo),'--commit',a.commit,'--child','--scenario',a.scenario],cwd=root,env=dict(e,AICOS_D4_CHILD_ACK=ACK),input=json.dumps(creds).encode('ascii'),check=False,timeout=300).returncode;del creds
        need(rc==0,'PROBE_CHILD_HOLD');final['status']='D4_R3_SCENARIO_PASS_RAW_REVIEW_REQUIRED'
    except Exception as exc:final['failure']={'stage':stage,**safe_error(exc)}
    finally:
        try:
            if ctl and (root/'data/PG_VERSION').is_file():
                rc=subprocess.run([str(ctl),'-D',str(root/'data'),'status'],cwd=root,env=e,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
                if rc==0:h.run([ctl,'-D',root/'data','-m','fast','-w','stop'],root,e)
                rc=subprocess.run([str(ctl),'-D',str(root/'data'),'status'],cwd=root,env=e,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode;need(rc==3,'STOP_HOLD')
            final['server_stopped']=True
            h.source_check(source);final['source_preserved']=True;fixture_check(repo,a.commit);final['fixture_preserved']=True;input_check(h,e1,d1);final['accepted_inputs_preserved']=True
            need(not list((root/'tmp').glob('initdb-*.pw')),'TEMP_SECRET_HOLD')
        except Exception as exc:final['status']='HOLD';final['postcheck_failure']=safe_error(exc)
        final['logs']={p.name:sha(p) for p in logs.iterdir() if p.is_file()};write(logs/'D4_FINAL.json',final)
    print(json.dumps(final,indent=2));return 0 if final['status']=='D3_LOCAL_PASS_RAW_REVIEW_REQUIRED' else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Exception,KeyboardInterrupt) as exc:print('HOLD',json.dumps(safe_error(exc)));raise SystemExit(1)
