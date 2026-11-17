"""D3-R2: isolated Windows bootstrap and original D3-R1 fixture probes; no product migration."""
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

R1='f2f0c548d5de6d5cc166ac103520d4ede007e959'
MANIFEST='78b656a97302553a77b56ddaa630ad748f7746e0'
HELPER='d20bbb6740901e2abf02d445b20cfa34f4b93d50'
LOCK='576dc61d00895bf3ba624b881b49785c1617b1e476bd4b7dec3ea05217c9b4ac'
D1_REVIEW='ce09749cc9507961cec8120c712cc599556fc83d6ecf1f0da2eae4546a4dd407'
D1_FINAL='5e50f13bf80cf221c981fe535bcd3bcbfeb02e3adc0dc65363e6996064545177'
ADMIN='aicos_d3_admin'
DB='aicos_d3_0228'
PORT=55433
CLUSTER='aicos_d3_0228_disposable'
ACK='0228_D3_DISPOSABLE_LOCAL_ONLY'
ROLES=('aicos_d3_tenant_a','aicos_d3_tenant_b','aicos_d3_unmapped')
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
    need(subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',R1,commit]).returncode==0,'FIXTURE_ANCESTOR_HOLD')
    runner=file(repo/'scripts/run_d3_0228.py')
    need(Path(__file__).resolve()==runner.resolve() and blob(runner)==git(repo,'rev-parse',commit+':scripts/run_d3_0228.py'),'RUNNER_PIN_HOLD')
    folder=repo/'tests/fixtures/0228-d3';mp=file(folder/'SOURCE_MANIFEST.json')
    need(blob(mp)==MANIFEST,'FIXTURE_MANIFEST_HOLD')
    m=json.loads(mp.read_text(encoding='utf-8'));need(len(m['files'])==8,'FIXTURE_COUNT_HOLD')
    for x in m['files']:
        p=file(repo/x['path']);need(p.parent==folder and blob(p)==x['git_blob'] and p.stat().st_size==x['bytes'],'FIXTURE_PIN_HOLD')
    hp=file(repo/'scripts/run_d1_0227_authfix.py');need(blob(hp)==HELPER,'HELPER_PIN_HOLD')
    return folder,load(hp,'d1_verified_helper')

def fixed_paths(repo,root):
    need(repo.resolve()==repo.absolute() and root.resolve()==root.absolute(),'ROOT_LINK_HOLD')
    need(root==BASE/'core-0228-d3' and repo==BASE/'core-0228-d3-source','ISOLATION_PATH_HOLD')
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
    # Only the pinned 00_roles.sql; no quoted semicolons or procedural SQL.
    s='\n'.join(l for l in text.splitlines() if not l.lstrip().startswith('--'))
    statements=[x.strip() for x in s.split(';') if x.strip()]
    need(len(statements)==7 and [x.split()[0:2] for x in statements]==[['CREATE','ROLE']]*4+[['CREATE','DATABASE'],['REVOKE','CONNECT,TEMPORARY'],['GRANT','CONNECT']],'ROLE_SQL_SHAPE_HOLD')
    return statements

def expected_ids(probe):
    ids=['authenticated_runtime_and_unmapped_profiles','owner_nologin_nobypass','all_12_owned_enabled_forced','all_48_command_policies','no_fixture_definer_functions','unmapped_no_rows','unmapped_insert_denied']
    for label,other in [('a',ROLES[1]),('b',ROLES[0])]:
        for t in probe.TABLES:
            ids.extend(label+'_'+t+'_'+s for s in ['own_read','cross_read','cross_insert','scope_rebind','update_scope' if t in probe.UPDATE else 'append_only_update','delete_scope' if t=='run_leases' else 'delete_privilege','no_elevated_table_privilege','column_update_grants'])
        ids.extend(label+'_'+s for s in ['forged_context_denied','reset_preserves_authenticated_scope','set_role_'+other,'set_role_'+probe.OWNER,'session_authorization_denied','rls_off_denied','join_scope'])
    ids.extend('b_only_event_exists cross_scope_fk_missing rollback_visible_inside rollback_restores same_scope_nowait_contention other_scope_not_blocked lock_released two_connections_same_revision first_budget_cas stale_budget_cas cap_constraint other_budget_unchanged second_connection_commit snapshot_stable read_only_write_denied fresh_snapshot_visible other_budget_still_unchanged'.split())
    need(len(ids)==230 and len(set(ids))==230,'PROBE_EXPECTED_COUNT_HOLD');return ids

def safe_error(exc):
    result={'type':type(exc).__name__}
    if isinstance(exc,Hold) or type(exc).__name__=='Hold': result['reason']=str(exc)
    state=getattr(exc,'sqlstate',None)
    if isinstance(state,str) and re.fullmatch('[A-Z0-9]{5}',state):result['sqlstate']=state
    return result

def child(repo,root,commit):
    need(os.environ.pop('AICOS_D3_CHILD_ACK',None)==ACK,'CHILD_ACK_HOLD')
    need(repo==BASE/'core-0228-d3-source' and root==BASE/'core-0228-d3' and root.resolve()==root.absolute(),'CHILD_PATH_HOLD')
    folder,h=fixture_check(repo,commit);probe=load(folder/'d3_probe.py','d3_verified_probe')
    review=json.loads(file(root/'evidence/D3_REVIEW.json').read_text(encoding='utf-8'))
    need(review['fixture_commit']==commit and review['runner_blob']==blob(file(Path(__file__).absolute())) and review['cluster']==CLUSTER and review['port']==PORT,'CHILD_REVIEW_HOLD')
    need(file(root/'data/PG_VERSION').read_text().strip()=='17','CHILD_DATA_HOLD')
    import psycopg
    from psycopg import sql
    report={'status':'HOLD','classification':'DISPOSABLE_FIXTURE_ONLY','fixture_commit':commit,'checks':[],'bootstrap':[],'canonical_mapping':'HOLD','independent_acceptance':'HOLD'}
    stage='credentials'
    try:
        secrets_by_role=json.load(sys.stdin);need(set(secrets_by_role)=={ADMIN,*ROLES} and all(re.fullmatch('[A-Za-z0-9_-]{40,60}',v) for v in secrets_by_role.values()),'SECRET_PIPE_HOLD')
        need(psycopg.__version__=='3.3.9' and psycopg.pq.__impl__=='binary','DRIVER_HOLD')
        common={'host':'127.0.0.1','port':str(PORT),'sslmode':'disable','connect_timeout':'3'}
        def connect(role,db):
            c=psycopg.connect(**common,user=role,dbname=db,password=secrets_by_role[role],autocommit=True,passfile=os.devnull)
            try:
                r=c.execute("SELECT current_database(),session_user,current_user,host(inet_server_addr()),inet_server_port(),current_setting('cluster_name'),current_setting('server_version_num'),current_setting('listen_addresses')").fetchone()
                need(r==(db,role,role,'127.0.0.1',PORT,CLUSTER,'170012','127.0.0.1'),'SERVER_PROFILE_HOLD');return c
            except BaseException:c.close();raise
        def mark(s):report['bootstrap'].append(s)
        stage='roles_and_database'
        with connect(ADMIN,'postgres') as c:
            need(Path(c.execute('SHOW data_directory').fetchone()[0]).resolve()==(root/'data').resolve(),'DATA_DIRECTORY_HOLD')
            need(c.execute("SELECT current_setting('password_encryption')").fetchone()==('scram-sha-256',),'SCRAM_HOLD')
            rules=c.execute('SELECT DISTINCT auth_method,error FROM pg_hba_file_rules').fetchall()
            need(bool(rules) and all(x==('scram-sha-256',None) for x in rules),'HBA_HOLD')
            for stmt in bootstrap_statements((folder/'00_roles.sql').read_text(encoding='utf-8')):c.execute(stmt)
            c.execute('REVOKE CONNECT,TEMPORARY ON DATABASE postgres,template1,template0 FROM PUBLIC')
            for role in ROLES:
                v=c.pgconn.encrypt_password(secrets_by_role[role].encode('ascii'),role.encode('ascii'),b'scram-sha-256').decode('ascii')
                need(v.startswith('SCRAM-SHA-256$'),'VERIFIER_HOLD')
                c.execute(sql.SQL('ALTER ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role),sql.Literal(v)))
                del v
            report['server']={'version_num':170012,'cluster':CLUSTER,'host':'127.0.0.1','port':PORT,'auth':'scram-sha-256','data_directory_match':True,'driver':'3.3.9','pq_impl':'binary','libpq_version':psycopg.pq.version()}
            mark(stage)
        stage='schema_and_policies'
        with connect(ADMIN,DB) as c:
            for name in ('01_schema.sql','02_rls_policies.sql'):c.execute((folder/name).read_text(encoding='utf-8'),prepare=False)
            mark(stage)
        stage='direct_login_seeds'
        for role,name in zip(ROLES,('03_seed_a.sql','04_seed_b.sql')):
            with connect(role,DB) as c:c.execute((folder/name).read_text(encoding='utf-8'),prepare=False)
        mark(stage)
        stage='owner_force_rls'
        with connect(ADMIN,DB) as c:
            c.execute((folder/'05_owner_probe.sql').read_text(encoding='utf-8'),prepare=False)
            with c.transaction(force_rollback=True):
                c.execute('SET LOCAL ROLE aicos_d3_owner')
                need(c.execute('SELECT current_user').fetchone()==('aicos_d3_owner',),'OWNER_ROLE_HOLD')
                for t in probe.TABLES:need(c.execute('SELECT count(*) FROM '+probe.table(t)).fetchone()==(0,),'OWNER_READ_HOLD')
                state=None
                try:
                    with c.transaction(force_rollback=True):c.execute("INSERT INTO aicos_d3_fixture.run_heads VALUES ('synthetic-tenant-a','synthetic-company-a','D3_SAMPLE_ONLY','owner-plan','owner-task','owner-run','agent','principal','CREATED',0,0)")
                except psycopg.Error as exc:state=exc.sqlstate
                need(state=='42501','OWNER_INSERT_HOLD')
            report['owner']={'tables_hidden':12,'insert_denied_sqlstate':'42501','status':'PASS'};mark(stage)
        stage='runtime_probes'
        dsns={role:probe.validate_dsn(dict(common,user=role,dbname=DB,password=secrets_by_role[role]),role) for role in ROLES}
        probe.run_probe(report,dsns,psycopg)
        need([x['id'] for x in report['checks']]==expected_ids(probe) and all(x['status']=='PASS' for x in report['checks']),'PROBE_INVENTORY_HOLD')
        report['status']='D3_FIXTURE_PROBES_PASS';mark(stage)
    except Exception as exc:report['failure']={'stage':stage,**safe_error(exc)}
    finally:
        report['passed']=len(report['checks']);write(root/'evidence/D3_PROBE.json',report)
    return 0 if report['status']=='D3_FIXTURE_PROBES_PASS' else 1

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--commit',required=True);p.add_argument('--child',action='store_true');a=p.parse_args()
    need(sys.platform=='win32' and sys.version.split()[0]=='3.14.3','WINDOWS_PYTHON_HOLD')
    repo=a.repo.absolute();root=BASE/'core-0228-d3';e1=BASE/'core-0227-e1';d1=BASE/'core-0227-pg-retry2';source=BASE/'core-0227-clean'
    if a.child:return child(repo,root,a.commit)
    fixed_paths(repo,root);folder,h=fixture_check(repo,a.commit);h.source_check(source);pins=input_check(h,e1,d1)
    review={'fixture_commit':a.commit,'fixture_manifest_blob':MANIFEST,'runner_blob':blob(file(Path(__file__).absolute())),'accepted_lock_sha256':LOCK,'accepted_d1_review_sha256':D1_REVIEW,'source_commit':h.SOURCE,'product_manifest':h.MANIFEST,'port':PORT,'cluster':CLUSTER,'database':DB,'credential_mode':'all ephemeral; no password in evidence','scope':'D3 disposable fixture only; D1/D2 untouched'}
    print(json.dumps(review,indent=2));need(input('Approve isolated D3 fixture and probes only? EVET/HAYIR: ')=='EVET','APPROVAL_HOLD')
    with socket.socket() as s:s.bind(('127.0.0.1',PORT))
    root.mkdir();(root/'tmp').mkdir();logs=root/'evidence';logs.mkdir();write(logs/'D3_REVIEW.json',review)
    final={'status':'HOLD','server_stopped':False,'source_preserved':False,'fixture_preserved':False,'accepted_inputs_preserved':False,'canonical_mapping':'HOLD','independent_acceptance':'HOLD'};ctl=None;e=None;stage='venv'
    try:
        e=h.env_local(root);h.run([sys.executable,'-m','venv',root/'.venv'],root,e,logs/'01_venv.log');py=root/'.venv/Scripts/python.exe'
        h.run([py,'-m','pip','--isolated','install','--no-index','--find-links',e1/'locks/wheels','--find-links',d1/'wheels','--require-hashes','-r',d1/'pg.lock'],root,e,logs/'02_pip_install.log')
        h.run([py,'-m','pip','check'],root,e,logs/'03_pip_check.log');h.run([py,'-m','pip','list','--format=json'],root,e,logs/'04_pip_list.json')
        actual={h.norm(x['name']):x['version'] for x in json.loads((logs/'04_pip_list.json').read_text(encoding='utf-8'))};need(all(actual.get(n)==v for n,v in pins.items()) and set(actual)-set(pins)<={'pip'},'INSTALLED_PINS_HOLD')
        stage='server_extract';bindir=h.extract_archive(d1/'postgresql-17.12.zip',root/'server');e=h.env_local(root,bindir);ctl=bindir/'pg_ctl.exe'
        need(re.search(r'\b17\.12\b',subprocess.check_output([str(bindir/'postgres.exe'),'--version'],env=e,text=True)),'SERVER_VERSION_HOLD')
        stage='initdb';creds={r:secrets.token_urlsafe(32) for r in (ADMIN,*ROLES)};h.ADMIN=ADMIN;h.protected_initdb(root,bindir,e,creds[ADMIN])
        with (root/'data/postgresql.conf').open('a',encoding='ascii') as f:f.write("\nlisten_addresses = '127.0.0.1'\nport = 55433\ncluster_name = 'aicos_d3_0228_disposable'\nssl = off\npassword_encryption = 'scram-sha-256'\nlog_statement = 'none'\nlog_min_error_statement = panic\n")
        stage='start';h.run([ctl,'-D',root/'data','-l',root/'server-private.log','-w','start'],root,e)
        stage='probes';rc=subprocess.run([str(py),'-I','-B',str(Path(__file__).absolute()),'--repo',str(repo),'--commit',a.commit,'--child'],cwd=root,env=dict(e,AICOS_D3_CHILD_ACK=ACK),input=json.dumps(creds).encode('ascii'),check=False,timeout=300).returncode;del creds
        need(rc==0,'PROBE_CHILD_HOLD');final['status']='D3_LOCAL_PASS_RAW_REVIEW_REQUIRED'
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
        final['logs']={p.name:sha(p) for p in logs.iterdir() if p.is_file()};write(logs/'D3_FINAL.json',final)
    print(json.dumps(final,indent=2));return 0 if final['status']=='D3_LOCAL_PASS_RAW_REVIEW_REQUIRED' else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Exception,KeyboardInterrupt) as exc:print('HOLD',json.dumps(safe_error(exc)));raise SystemExit(1)
