"""0227 D1: local disposable Windows PG, no service, no live data, no E1 mutation."""
import argparse
import email
import getpass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import socket
import secrets
import stat
import subprocess
import sys
import urllib.request
import zipfile

SOURCE='52219c7a222bae41735c9a9b9f7f7082462982b4'
MANIFEST='981a13fc226184dc3a911ae0d94e0042285ff302'
E1_REVIEW='13a39b47704ac59953b30a4723266c7d9be47b8c084998b77b61a19175b08e2b'
E1_LOCK='bedb32b1d0462180ccc25fc4487af3b61ba30c4ee0dfd946fa33a3fe6fdc5253'
SERVER_HASH='a2cd8a774389347b70be7748ac4a37ef43cb6ee539c5fc3e85ae264b15e4a04c'
WHEELS={
 'psycopg-3.3.9-py3-none-any.whl':('psycopg','3.3.9','d2d7d04a1ce6dab4f5b27316bea3b52585cafa2f2d631e5b09dd69823f5c26f6'),
 'psycopg_binary-3.3.9-cp314-cp314-win_amd64.whl':('psycopg-binary','3.3.9','109c5df5b0e5117e01a42d3b56a2f4ccd5431bd54d25efdfc89df095ac9f9605'),
 'tzdata-2026.6-py2.py3-none-any.whl':('tzdata','2026.6','0a10eec6e13ef16b627fabed9a5f2ba61a62b1c67f327305f4e7e412a70b4aec')}
PORT=55432
ADMIN='aicos_pg_admin'
ROLE='aicos_d0_runner'
DBS=('aicos_d0_0194_0227','aicos_d0_0196l_0227')

def require(ok, reason):
    if not ok: raise ValueError(reason)

def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def blob(p):
    b=p.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def safe_file(p):
    require(p.is_file() and p.resolve()==p.absolute(),'FILE_OR_LINK_HOLD')
    return p

def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')

def norm(name): return re.sub(r'[-_.]+','-',name).lower()

def env_local(root, bindir=None):
    keep={'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','HOME','USERPROFILE','LOCALAPPDATA','APPDATA','LANG','LC_ALL','SYSTEMDRIVE','HOMEDRIVE','HOMEPATH'}
    e={k:v for k,v in os.environ.items() if k.upper() in keep}
    e.update(TEMP=str(root/'tmp'),TMP=str(root/'tmp'),TMPDIR=str(root/'tmp'),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PIP_DISABLE_PIP_VERSION_CHECK='1',PGPASSFILE=os.devnull,PGSERVICEFILE=os.devnull,PGSSLMODE='disable')
    if bindir: e['PATH']=str(bindir)+os.pathsep+e.get('PATH','')
    return e

def run(args,cwd,env,log=None):
    args=list(map(str,args))
    if log:
        with log.open('xb') as f: subprocess.run(args,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    else: subprocess.run(args,cwd=cwd,env=env,check=True)

def source_check(src):
    def git(*a): return subprocess.check_output(['git','-C',str(src),*a])
    require(git('rev-parse','HEAD').decode().strip()==SOURCE,'SOURCE_COMMIT_HOLD')
    require(not git('status','--porcelain','--untracked-files=all'),'DIRTY_SOURCE_HOLD')
    v=src/'scripts/verify_product.py'
    require(blob(safe_file(v))=='dd414ebd0b65d8e9c3eec47fdeed03a00e5879e8','VERIFIER_PIN_HOLD')
    subprocess.run([sys.executable,'-B',str(v),'--root',str(src),'--manifest-blob',MANIFEST],check=True)
    count=0
    for row in git('ls-tree','-r','-z',SOURCE,'--','database').split(b'\0'):
        if not row: continue
        meta,name=row.split(b'\t',1);mode,kind,pin=meta.decode().split()
        require(kind=='blob' and blob(safe_file(src/name.decode()))==pin,'DATABASE_PIN_HOLD');count+=1
    require(count==16,'DATABASE_COUNT_HOLD')
    return count

def inputs(root,e1):
    rp=safe_file(e1/'locks/REVIEW_0227.json');lp=safe_file(e1/'locks/python.lock')
    require(sha(rp)==E1_REVIEW and sha(lp)==E1_LOCK,'E1_LOCK_HOLD')
    review=json.loads(rp.read_text(encoding='utf-8'))
    original=review['inventory']['wheels'];require(len(original)==28,'E1_WHEEL_COUNT_HOLD')
    for n,h in original.items():
        require(Path(n).name==n and sha(safe_file(e1/'locks/wheels'/n))==h,'E1_WHEEL_HASH_HOLD')
    require(sha(safe_file(root/'postgresql-17.12.zip'))==SERVER_HASH,'PG_ZIP_HASH_HOLD')
    require({p.name for p in (root/'wheels').iterdir()}==set(WHEELS),'PG_WHEEL_SET_HOLD')
    info={}
    for n,(name,version,digest) in WHEELS.items():
        p=safe_file(root/'wheels'/n);require(sha(p)==digest,'PG_WHEEL_HASH_HOLD')
        url=f'https://pypi.org/pypi/{name}/{version}/json'
        with urllib.request.urlopen(url,timeout=30) as response:
            require(response.geturl().startswith('https://pypi.org/'),'REGISTRY_REDIRECT_HOLD')
            registry=json.load(response)
        rows=[r for r in registry['urls'] if r['filename']==n]
        require(len(rows)==1 and not rows[0]['yanked'] and rows[0]['digests']['sha256']==digest,'PYPI_HASH_HOLD')
        with zipfile.ZipFile(p) as z:
            names=[x for x in z.namelist() if x.endswith('.dist-info/METADATA')]
            require(len(names)==1,'WHEEL_METADATA_HOLD');m=email.message_from_bytes(z.read(names[0]))
            require(norm(m['Name'])==name and m['Version']==version,'WHEEL_NAME_HOLD')
            info[n]={'name':name,'version':version,'sha256':digest,'registry_url':url,'requires_python':m['Requires-Python'],'requires_dist':m.get_all('Requires-Dist',[]),'license_expression':m['License-Expression'] or m['License']}
    lock=lp.read_text(encoding='utf-8').rstrip()+'\n'+''.join(f'{name}=={ver} --hash=sha256:{h}\n' for name,ver,h in WHEELS.values())
    pins={}
    for line in lock.splitlines():
        m=re.fullmatch(r'([^=\s]+)==([^\s]+) --hash=sha256:[0-9a-f]{64}',line)
        require(m is not None and norm(m[1]) not in pins,'LOCK_FORMAT_HOLD');pins[norm(m[1])]=m[2]
    require(len(pins)==31,'LOCK_COUNT_HOLD')
    return info,lock,pins

def extract_archive(archive,target):
    require(not target.exists(),'SERVER_DIR_EXISTS_HOLD')
    with zipfile.ZipFile(archive) as z:
        seen=set()
        for item in z.infolist():
            n=item.filename.rstrip('/');p=PurePosixPath(n)
            require(n and not p.is_absolute() and '\\' not in n and ':' not in n and '..' not in p.parts and p.as_posix()==n and n.casefold() not in seen and not stat.S_ISLNK(item.external_attr>>16),'ZIP_PATH_HOLD');seen.add(n.casefold())
        target.mkdir();z.extractall(target)
    matches=list(target.rglob('postgres.exe'));require(len(matches)==1,'POSTGRES_BIN_HOLD')
    bindir=matches[0].parent
    for name in ('postgres.exe','psql.exe','initdb.exe','pg_ctl.exe'):safe_file(bindir/name)
    return bindir

def valid_password(value):
    return isinstance(value,str) and 12<=len(value)<=128 and all(33<=ord(c)<=126 for c in value)

def protected_initdb(root, bindir, env, admin):
    # Create an empty file first; restrict access before writing the secret.
    pw=root/'tmp'/('initdb-'+secrets.token_hex(12)+'.pw')
    with pw.open('xb'): pass
    try:
        identity=subprocess.check_output(['whoami.exe','/user','/fo','csv','/nh'],env=env)
        matches=re.findall(rb'S-1-[0-9]+(?:-[0-9]+)+',identity)
        require(len(matches)==1,'WINDOWS_USER_SID_HOLD')
        sid=matches[0].decode('ascii')
        subprocess.run(['icacls.exe',str(pw),'/grant:r','*'+sid+':F','/inheritance:r'],env=env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        # Check the resulting DACL, not just the icacls return code.
        acl_env=dict(env,AICOS_PWFILE=str(pw),AICOS_OWNER_SID=sid)
        command="$a=Get-Acl -LiteralPath $env:AICOS_PWFILE; $r=@($a.Access); if (!$a.AreAccessRulesProtected -or $r.Count -ne 1 -or $r[0].IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value -ne $env:AICOS_OWNER_SID -or $r[0].AccessControlType -ne 'Allow' -or $r[0].IsInherited -or ($r[0].FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::FullControl) -ne [System.Security.AccessControl.FileSystemRights]::FullControl) { exit 1 }; exit 0"
        subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],env=acl_env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        pw.write_bytes(admin.encode('ascii')+b'\n')
        run([bindir/'initdb.exe','-D',root/'data','-U',ADMIN,'-A','scram-sha-256','--pwfile='+str(pw),'--encoding=UTF8','--locale=C'],root,env)
    finally:
        # No credential is retained intentionally; preserve only non-secret evidence.
        pw.unlink(missing_ok=True)

def connect_stage(root,bindir):
    import psycopg
    from psycopg import sql
    require(psycopg.__version__=='3.3.9' and psycopg.pq.__impl__=='binary','DRIVER_VERSION_HOLD')
    credentials=json.load(sys.stdin)
    require(set(credentials)=={'admin','test'} and all(valid_password(x) for x in credentials.values()),'CREDENTIAL_PIPE_HOLD')
    admin,pwd=credentials['admin'],credentials['test']
    del credentials
    common=dict(host='127.0.0.1',hostaddr='127.0.0.1',port=PORT,sslmode='disable',connect_timeout=3,passfile=os.devnull)
    result={'status':'D1_CONNECTION_PASS_PENDING_RAW_REVIEW','source_commit':SOURCE,'manifest_blob':MANIFEST,'review_sha256':sha(root/'D1_REVIEW.json'),'combined_lock_sha256':sha(root/'pg.lock'),'postgresql_archive_sha256':SERVER_HASH,'psycopg':psycopg.__version__,'pq_impl':psycopg.pq.__impl__,'libpq_version':psycopg.pq.version(),'databases':[]}
    with psycopg.connect(**common,dbname='postgres',user=ADMIN,password=admin,autocommit=True) as c:
        v,addr,port,listen,auth=c.execute("SELECT current_setting('server_version_num')::int,inet_server_addr()::text,inet_server_port(),current_setting('listen_addresses'),current_setting('password_encryption')").fetchone()
        require(v==170012 and addr in ('127.0.0.1','127.0.0.1/32') and port==PORT and listen=='127.0.0.1' and auth=='scram-sha-256','SERVER_PROFILE_HOLD')
        rules=c.execute('SELECT DISTINCT auth_method,error FROM pg_hba_file_rules').fetchall()
        require(bool(rules) and all(method=='scram-sha-256' and error is None for method,error in rules),'HBA_HOLD')
        result.update(server_version_num=v,server_address=addr,port=port,listen_addresses=listen,auth_methods=['scram-sha-256'])
        verifier=c.pgconn.encrypt_password(pwd.encode(c.info.encoding),ROLE.encode(c.info.encoding),b'scram-sha-256').decode('ascii')
        require(verifier.startswith('SCRAM-SHA-256$'),'SCRAM_VERIFIER_HOLD')
        c.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD {}').format(sql.Identifier(ROLE),sql.Literal(verifier)))
        for db in DBS:
            c.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(db),sql.Identifier(ROLE)))
    del admin,verifier
    for db in DBS:
        with psycopg.connect(**common,dbname=db,user=ROLE,password=pwd) as c:
            d,u,s,b,cd,cr,rep,can_create,empty=c.execute("SELECT current_database(),current_user,rolsuper,rolbypassrls,rolcreatedb,rolcreaterole,rolreplication,has_database_privilege(current_user,current_database(),'CREATE'),to_regnamespace('t1_candidate') IS NULL FROM pg_roles WHERE rolname=current_user").fetchone()
            require(d==db and u==ROLE and not any((s,b,cd,cr,rep)) and can_create and empty,'DISPOSABLE_ROLE_HOLD')
            c.execute('CREATE SCHEMA d1_probe');c.execute('CREATE TABLE d1_probe.probe (id int PRIMARY KEY)');c.execute('INSERT INTO d1_probe.probe VALUES (1)');require(c.execute('SELECT id FROM d1_probe.probe').fetchone()==(1,),'DB_WRITE_READ_HOLD');c.rollback()
            require(c.execute("SELECT to_regnamespace('d1_probe') IS NULL").fetchone()==(True,),'DB_ROLLBACK_HOLD')
            result['databases'].append(dict(database=d,role=u,superuser=s,bypassrls=b,createdb=cd,createrole=cr,replication=rep,can_create_schema=can_create,t1_candidate_absent=empty,write_read_rollback='PASS'))
    del pwd
    write(root/'evidence/D1_CONNECTION.json',result)
    print(json.dumps(result,indent=2));print('D1 connections PASS; PG13 not run.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--e1',type=Path);p.add_argument('--pgroot',type=Path,required=True);p.add_argument('--connect-child',type=Path);a=p.parse_args()
    require(sys.platform=='win32' and sys.version.split()[0]=='3.14.3','WINDOWS_PYTHON_PIN_HOLD')
    root=a.pgroot.resolve()
    if a.connect_child:
        connect_stage(root,a.connect_child.resolve());return
    src=a.source.resolve();e1=a.e1.resolve()
    require(root not in (src,e1) and not root.is_relative_to(src) and not root.is_relative_to(e1) and not src.is_relative_to(root) and not e1.is_relative_to(root),'ISOLATION_HOLD')
    for n in ('server','data','.venv','evidence','tmp','D1_REVIEW.json','pg.lock'):
        require(not (root/n).exists(),'FRESH_D1_STAGE_HOLD: '+n)
    source_check(src)
    info,lock,pins=inputs(root,e1)
    review={'source_commit':SOURCE,'manifest_blob':MANIFEST,'e1_review_sha256':E1_REVIEW,'e1_python_lock_sha256':E1_LOCK,'server_sha256':SERVER_HASH,'server_version':'17.12','port':PORT,'wheels':info,'combined_lock_sha256':hashlib.sha256(lock.encode()).hexdigest(),'scope':'local disposable D1 only, no PG13 or RLS','credential_mode':'generated ASCII admin; ACL-protected temporary pwfile; child stdin; no retained admin'}
    print(json.dumps(review,indent=2))
    if input('Approve isolated D1 install and connection only? EVET/HAYIR: ')!='EVET': print('HOLD: not approved');return
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',PORT))
    (root/'evidence').mkdir();(root/'tmp').mkdir();write(root/'D1_REVIEW.json',review);(root/'pg.lock').write_bytes(lock.encode())
    e=env_local(root);logs=root/'evidence'
    run([sys.executable,'-m','venv',root/'.venv'],root,e,logs/'01_venv.log')
    py=root/'.venv/Scripts/python.exe'
    run([py,'-m','pip','--isolated','install','--no-index','--find-links',e1/'locks/wheels','--find-links',root/'wheels','--require-hashes','-r',root/'pg.lock'],root,e,logs/'02_pip_install.log')
    run([py,'-m','pip','check'],root,e,logs/'03_pip_check.log')
    run([py,'-m','pip','list','--format=json'],root,e,logs/'04_pip_list.json')
    actual={norm(r['name']):r['version'] for r in json.loads((logs/'04_pip_list.json').read_text(encoding='utf-8'))}
    require(all(actual.get(n)==v for n,v in pins.items()) and set(actual)-set(pins)<={'pip'},'INSTALLED_VERSION_HOLD')
    bindir=extract_archive(root/'postgresql-17.12.zip',root/'server');e=env_local(root,bindir)
    version=subprocess.check_output([str(bindir/'postgres.exe'),'--version'],env=e,text=True).strip();require(re.search(r'\b17\.12\b',version),'POSTGRES_VERSION_HOLD');print(version)
    print('Admin password is generated for this disposable cluster; it is not displayed or saved.')
    pwd=getpass.getpass('Choose NEW test role password (12-128 printable ASCII, no spaces): ')
    require(valid_password(pwd) and pwd==getpass.getpass('Repeat test role password: '),'PASSWORD_CONFIRM_HOLD')
    admin=secrets.token_urlsafe(32)
    protected_initdb(root,bindir,e,admin)
    with (root/'data/postgresql.conf').open('a',encoding='ascii') as f:
        f.write("\nlisten_addresses = '127.0.0.1'\nport = 55432\nssl = off\npassword_encryption = 'scram-sha-256'\nlog_statement = 'none'\nlog_min_error_statement = panic\n")
    ctl=bindir/'pg_ctl.exe';started=False
    try:
        run([ctl,'-D',root/'data','-l',root/'server-private.log','-w','start'],root,e);started=True
        subprocess.run([str(py),'-B',str(Path(__file__).resolve()),'--pgroot',str(root),'--connect-child',str(bindir)],cwd=root,env=e,input=json.dumps({'admin':admin,'test':pwd}).encode('ascii'),check=True)
        del admin,pwd
    finally:
        status=subprocess.run([str(ctl),'-D',str(root/'data'),'status'],cwd=root,env=e,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
        if started or status==0: run([ctl,'-D',root/'data','-m','fast','-w','stop'],root,e)
    source_check(src)
    require(sha(e1/'locks/python.lock')==E1_LOCK and sha(e1/'locks/REVIEW_0227.json')==E1_REVIEW,'E1_POSTCHECK_HOLD')
    write(logs/'D1_FINAL.json',{'status':'PASS_LOCAL_RAW_REVIEW_REQUIRED','server_stopped':True,'source_commit':SOURCE,'manifest_blob':MANIFEST,'review_sha256':sha(root/'D1_REVIEW.json'),'logs':{p.name:sha(p) for p in logs.iterdir() if p.is_file()},'pg13':'NOT_RUN','rls':'NOT_RUN','e1_preserved':True,'admin_credential':'GENERATED_EPHEMERAL_NOT_RETAINED','test_credential':'USER_HELD_NOT_LOGGED'})
    print('D1 local PASS; server stopped. Share evidence directory, D1_REVIEW.json and pg.lock only. Never share passwords or server-private.log.')

if __name__=='__main__':
    try:main()
    except (KeyboardInterrupt,Exception) as e:
        # Do not dump database exception text/connection data/SQL verifier.
        detail=str(e) if type(e) is ValueError else 'Inspect locally; preserve stage.'
        if type(e).__name__=='OperationalError':
            msg=str(e).lower()
            if 'password authentication failed' in msg: detail='AUTHENTICATION_FAILED'
            elif 'connection refused' in msg: detail='CONNECTION_REFUSED'
        print('HOLD:',type(e).__name__,detail,file=sys.stderr);sys.exit(1)
