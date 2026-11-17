"""ORG-10R1: exact archive, reviewed runtime fingerprint and isolated PG17 fixture. No production authority."""
import argparse, ast, hashlib, importlib.metadata as metadata, io, json, os, re, stat, subprocess, sys, tempfile, zipfile, socket, getpass, warnings
from pathlib import Path

COMMIT = '5c7eb6b148e6e96247682653ff70dccc4a7ba823'
TREE = '3b25cc7e7a30acdacc27df433e08443322946aa6'
ROOT_NAME = 'ai_Proje_Ofisi_chatgptSaas-' + COMMIT
CURRENT_COUNT = 1798
CURRENT_BYTES = 20653746
PORT = 55436
CLUSTER = DATABASE = 'aicos_org10_disposable'
ADMIN = 'org10_admin'
CANDIDATE = 'candidates/ORG-10-COMMON-SCOPE'
DRIVER = '3.3.9'
VERSION_NUM = 170012

class Hold(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise Hold(reason)


def object_hash(kind, data):
    return hashlib.sha1(kind.encode('ascii') + b' ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def safe_components(path):
    require(type(path) is str and path and len(path) <= 240 and path.isascii(), 'ARCHIVE_PATH_HOLD')
    parts = path.split('/')
    for p in parts:
        require(p not in ('', '.', '..') and re.fullmatch(r'[\x20-\x7e]+',p) is not None
                and not any(c in p for c in '<>:"\\|?*') and not p.endswith(('.', ' '))
                and not re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)',p,re.I), 'ARCHIVE_PATH_HOLD')
    return parts


def git_tree(files):
    """Git tree serialization for the pinned all-100644, regular-blob trees."""
    root = {}
    for path, raw in files.items():
        parts = safe_components(path)
        node = root
        for p in parts[:-1]:
            child = node.setdefault(p,{})
            require(type(child) is dict, 'TREE_COLLISION_HOLD')
            node = child
        require(parts[-1] not in node, 'TREE_COLLISION_HOLD')
        node[parts[-1]] = bytes.fromhex(object_hash('blob', raw))
    def serialize(node):
        rows=[]
        for name, value in node.items():
            directory = type(value) is dict
            key = name.encode('ascii')
            rows.append((key + (b'/' if directory else b''),
                         (b'40000' if directory else b'100644')+b' '+key+b'\0'+
                         (bytes.fromhex(serialize(value)) if directory else value)))
        return object_hash('tree', b''.join(v for _,v in sorted(rows)))
    return serialize(root)


def read_archive(archive_bytes, root_name=ROOT_NAME, expected_count=CURRENT_COUNT, expected_bytes=CURRENT_BYTES):
    """Read bounded ZIP, reject unsafe paths and compare names before any write."""
    require(type(archive_bytes) is bytes and len(archive_bytes) <= 50_000_000, 'ARCHIVE_FILE_HOLD')
    files={}; dirs=set(); seen={}; total=0; root_seen=False
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
        entries=z.infolist()
        require(len(entries)<=expected_count+1000,'ARCHIVE_ENTRY_LIMIT')
        for info in entries:
            name=info.filename
            require(name==info.orig_filename and not (info.flag_bits & 1),'ARCHIVE_ENTRY_HOLD')
            mode=(info.external_attr>>16)&0xffff
            require(stat.S_IFMT(mode) in (0,stat.S_IFDIR if info.is_dir() else stat.S_IFREG),'ARCHIVE_MODE_HOLD')
            if name==root_name+'/':
                require(info.is_dir() and not root_seen,'ARCHIVE_ROOT_HOLD'); root_seen=True
                continue
            require(name.startswith(root_name+'/'),'ARCHIVE_ROOT_HOLD')
            relative=name[len(root_name)+1:]
            if info.is_dir(): relative=relative[:-1]
            parts=safe_components(relative)
            for i in range(1,len(parts)+1):
                prefix='/'.join(parts[:i]); folded=prefix.lower()
                require(seen.setdefault(folded,prefix)==prefix,'ARCHIVE_CASE_COLLISION')
            if info.is_dir():
                require(relative not in dirs and relative not in files,'ARCHIVE_DUPLICATE'); dirs.add(relative); continue
            require(relative not in files and relative not in dirs,'ARCHIVE_DUPLICATE')
            total+=info.file_size
            require(len(files)<expected_count and total<=expected_bytes,'ARCHIVE_SIZE_HOLD')
            raw=z.read(info); require(len(raw)==info.file_size,'ARCHIVE_SIZE_HOLD')
            files[relative]=raw
    require(len(files)==expected_count and total==expected_bytes,'ARCHIVE_INVENTORY_HOLD')
    parents={p for name in files for p in ('/'.join(name.split('/')[:i]) for i in range(1,len(name.split('/'))))}
    require(not (parents & files.keys()) and dirs<=parents,'ARCHIVE_DIRECTORY_HOLD')
    return files


def materialize(files, root, expected):
    root.mkdir(exist_ok=False)
    for path,raw in files.items():
        target=root.joinpath(*safe_components(path)); target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f: f.write(raw)
    verify_materialized(files,root,expected)


def verify_materialized(files, root, expected):
    paths=list(root.rglob('*'))
    require(not any(p.is_symlink() for p in paths),'MATERIALIZED_SYMLINK_HOLD')
    actual={p.relative_to(root).as_posix():p.read_bytes() for p in paths if p.is_file()}
    require(actual.keys()==files.keys() and git_tree(actual)==expected,'MATERIALIZED_TREE_HOLD')


def read_exact(archive):
    require(archive.is_file() and archive.stat().st_size <= 50_000_000, 'ARCHIVE_FILE_HOLD')
    raw = archive.read_bytes()
    files = read_archive(raw)
    require(git_tree(files) == TREE, 'ARCHIVE_TREE_HOLD')
    return files, sha256(raw)


def canonical_json(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)+'\n').encode('utf-8')


def new_file(path, raw):
    with path.open('xb') as f:
        f.write(raw)


def regular(path):
    return path.is_file() and not path.is_symlink() and path.resolve() == path


def fingerprint(pg_bin, archive_sha):
    """Read-only inventory. Do not execute binaries or import drivers here."""
    require(pg_bin.is_absolute() and pg_bin.is_dir() and pg_bin.resolve()==pg_bin and pg_bin.name.lower()=='bin','PG_BIN_PATH')
    root=pg_bin.parent
    suffix='.exe' if os.name=='nt' else ''
    require(all(regular(pg_bin/(n+suffix)) for n in ('postgres','initdb','pg_ctl','psql')),'PG_BIN_MISSING')
    rows={}
    for area in ('bin','lib','share'):
        directory=root/area
        require(directory.is_dir() and directory.resolve()==directory,'PG_DISTRIBUTION_DIR')
        for p in sorted(directory.rglob('*')):
            require(not p.is_symlink() and p.resolve()==p,'PG_DISTRIBUTION_LINK')
            if p.is_file(): rows[p.relative_to(root).as_posix()] = sha256(p.read_bytes())
    require(len(rows)>4,'PG_DISTRIBUTION_INCOMPLETE')
    require(sys.prefix != sys.base_prefix,'ISOLATED_VENV_REQUIRED')
    venv=Path(sys.prefix).resolve(); packages={}
    for name in ('psycopg','psycopg-binary'):
        d=metadata.distribution(name)
        require(d.version==DRIVER and d.files is not None,'DRIVER_PIN')
        record={}
        for item in d.files:
            if str(item).endswith('.pyc'): continue
            raw_path=Path(d.locate_file(item))
            p=raw_path.resolve()
            require(not raw_path.is_symlink() and p.is_relative_to(venv) and regular(p),'DRIVER_FILE_HOLD')
            key=p.relative_to(venv).as_posix()
            require(key not in record,'DRIVER_DUPLICATE')
            record[key]=sha256(p.read_bytes())
        require(record,'DRIVER_EMPTY')
        packages[name]={'version':d.version,'files':record}
    return {'profile':'ORG10_RUNTIME_REVIEW_ONLY','archive_commit':COMMIT,'archive_tree':TREE,
            'archive_sha256':archive_sha,'pg_files':rows,'drivers':packages,
            'python_version':sys.version.split()[0], 'python_executable_sha256':sha256(Path(sys.executable).read_bytes())}


def clean_env():
    return {k:v for k,v in os.environ.items() if not k.upper().startswith(('PG','PYTHON'))}


def check_port():
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
        if os.name=='nt': sock.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        try: sock.bind(('127.0.0.1',PORT))
        except OSError as e: raise Hold('PORT_55436_UNAVAILABLE') from e


def fresh(path):
    require(path.is_absolute() and path.parent.is_dir() and path.parent.resolve()==path.parent and not os.path.lexists(path),'FRESH_ABSOLUTE_PATH_REQUIRED')


def validate_paths(stage,evidence,manifest):
    for p in (stage,evidence):
        fresh(p)
        require(str(p).isascii(),'ASCII_STAGE_EVIDENCE_REQUIRED')
    require(stage!=evidence and stage not in evidence.parents and evidence not in stage.parents,'PATH_OVERLAP')
    require(manifest not in (stage,evidence) and stage not in manifest.parents and evidence not in manifest.parents,'MANIFEST_OVERLAP')


def non_admin():
    if os.name=='nt':
        import ctypes
        require(not ctypes.windll.shell32.IsUserAnAdmin(),'NON_ADMIN_REQUIRED')
    else: require(os.geteuid()!=0,'NON_ADMIN_REQUIRED')


def parse_version(raw):
    require(re.fullmatch(r'[^\r\n]+ \(PostgreSQL\) 17\.12(?: [^\r\n]+)?',raw.strip()) is not None,'PG17_12_REQUIRED')
    return VERSION_NUM


def identity(output, stage, database):
    fields=output.strip().split('|')
    require(len(fields)==10,'IDENTITY_SHAPE')
    require(fields[:3]==[CLUSTER,str(PORT),str(VERSION_NUM)] and Path(fields[3]).resolve()==stage,'IDENTITY_CLUSTER_STAGE')
    require(fields[4:]==[ADMIN,ADMIN,'127.0.0.1','127.0.0.1',database,'UTF8'],'IDENTITY_ADMIN_DATABASE')
    pid=(stage/'postmaster.pid').read_text(encoding='utf-8').splitlines()
    require(len(pid)>=4 and pid[0].isdigit() and int(pid[0])>0 and Path(pid[1]).resolve()==stage and pid[3]==str(PORT),'PID_FILE_IDENTITY')


def digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None


def strict_json(raw):
    def pairs(items):
        d={}
        for k,v in items:
            require(k not in d,'JSON_DUPLICATE_KEY'); d[k]=v
        return d
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda _: (_ for _ in ()).throw(Hold('JSON_CONSTANT')))


def source_r3_pins(candidate):
    tree=ast.parse((candidate/'run_pg_acceptance.py').read_text(encoding='utf-8'))
    pins=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='R3_PINS' for t in n.targets))
    require(type(pins) is dict and len(pins)==7 and all(re.fullmatch(r'[a-z_]+\.py',n) and digest(h) for n,h in pins.items()),'R3_PIN_MAP')
    for n,h in pins.items():
        require(sha256((candidate.parent/'ORG-05R3'/n).read_bytes())==h,'R3_SOURCE_HOLD')
    return pins


def exact_json(a,b):
    return canonical_json(a)==canonical_json(b)


def review_report(raw, matrix, pins):
    """Strict structural review only; never execution attestation or authority."""
    require(len(raw)<=65536,'REPORT_SIZE')
    r=strict_json(raw)
    require(type(r) is dict and set(r)=={'profile','source_pins','schema_sha256','driver','checks','status'},'REPORT_FIELDS')
    require(r['profile']=='ORG10_COMMON_SCOPE_DISPOSABLE_ONLY' and r['driver']==DRIVER and r['status']=='PASS_DISPOSABLE_FIXTURE_ONLY','REPORT_STATUS')
    require(r['source_pins']==pins and r['schema_sha256']=='3a520ee1277c903eb6be4e704ce2c6d8ff749356f1d2537c7883887d14246a1a','REPORT_SOURCE_PINS')
    ids=[x['id'] for x in matrix['checks']]
    checks=r['checks']; require(type(checks) is list and len(checks)==len(ids)==31,'REPORT_COUNT')
    for c,n in zip(checks,ids):
        require(type(c) is dict and set(c)=={'id','status','detail','elapsed_ms'} and c['id']==n and c['status']=='PASS' and type(c['elapsed_ms']) is int and c['elapsed_ms']>=0,'REPORT_CHECK')
    d=[x['detail'] for x in checks]
    require(exact_json(d[0],{'tables':12,'policies':25,'cluster':CLUSTER}),'REPORT_INVENTORY')
    require(type(d[1]) is dict and set(d[1])=={'revision','loser'} and digest(d[1]['revision']) and d[1]['loser'] in [['hold','STALE_HEAD'],['sqlstate','23505']],'REPORT_GENESIS')
    require(all(digest(d[i]) for i in (2,3,19)),'REPORT_DIGEST')
    require(exact_json(d[4],{'sqlstate':'23514','counts':[0,0]}) and exact_json(d[5],{'same_scope':'55P03','other_scope':'PASS'}),'REPORT_ROLLBACK_LOCK')
    require(type(d[6]) is dict and set(d[6])=={'count','head','loser'} and type(d[6]['count']) is int and d[6]['count']==1 and digest(d[6]['head']) and d[6]['loser']==['hold','HISTORY_CAS'],'REPORT_CAS')
    require(type(d[8]) is dict and set(d[8])=={'count','head'} and type(d[8]['count']) is int and d[8]['count']==2 and digest(d[8]['head']),'REPORT_HISTORY')
    expected={7:'HISTORY_CAS',9:None,10:None,11:'42501',12:'42501',13:'42501',14:'23503',15:'42501',16:'42501',17:{'reader':'42501','unmapped':'42501'},18:'TASK_REFERENCE',20:'STALE_ORG',21:None,22:'STALE_HEAD',23:None,24:'HEAD_MISMATCH',25:None,26:'42501',27:'42501',28:'42501',29:{'tables':12,'reader_matches':True,'other_scope_hidden':True},30:{'tables':12,'roles':4,'checks':360}}
    require(all(exact_json(d[i],v) for i,v in expected.items()),'REPORT_DETAIL')
    return {'status':'COMPLETE_REPORT_UNATTESTED','passed':31,'report_sha256':sha256(raw),'custody':'UNATTESTED','real_iam':'HOLD','common_core_join':'HOLD','independent_security':'HOLD','product':'HOLD'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True); parser.add_argument('--pg-bin',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--stage',type=Path); parser.add_argument('--evidence',type=Path)
    parser.add_argument('--reviewed-fingerprint'); parser.add_argument('--execute-disposable',action='store_true')
    args=parser.parse_args(argv); started=False; report=None
    try:
        require(sys.version_info>=(3,12),'PYTHON_VERSION')
        files,archive_sha=read_exact(args.archive)
        inventory=fingerprint(args.pg_bin,archive_sha); manifest=canonical_json(inventory); fp=sha256(manifest)
        print(f'EXACT_ARCHIVE_PASS {len(files)}; RUNTIME_FINGERPRINT {fp}',flush=True)
        check_port()
        if not args.execute_disposable:
            require(args.reviewed_fingerprint is None and args.stage is None and args.evidence is None,'PREFLIGHT_ONLY_ARGUMENTS')
            fresh(args.manifest); new_file(args.manifest,manifest)
            print('PREFLIGHT_ONLY; independent runtime review and port owner approval required; PG NOT_RUN',flush=True); return 0
        require(args.stage is not None and args.evidence is not None and digest(args.reviewed_fingerprint),'EXECUTION_ARGUMENTS')
        require(regular(args.manifest) and args.manifest.read_bytes()==manifest and args.reviewed_fingerprint==fp,'REVIEWED_FINGERPRINT_MISMATCH')
        non_admin(); require(sys.stdin.isatty(),'INTERACTIVE_TERMINAL_REQUIRED')
        validate_paths(args.stage,args.evidence,args.manifest); stage=args.stage; evidence=args.evidence
        env=clean_env(); suffix='.exe' if os.name=='nt' else ''
        bins={n:args.pg_bin/(n+suffix) for n in ('initdb','pg_ctl','psql','postgres')}
        def run(cmd,capture=False,password=None):
            child=env if password is None else {**env,'PGPASSWORD':password,'PGCLIENTENCODING':'UTF8','PGCONNECT_TIMEOUT':'5'}
            return subprocess.run([str(x) for x in cmd],check=True,env=child,stdout=subprocess.PIPE if capture else None,encoding='utf-8' if capture else None).stdout
        for binary in bins.values(): parse_version(run([binary,'--version'],True))
        run([sys.executable,'-E','-s','-B','-X','utf8','-c',"import psycopg; assert psycopg.__version__=='3.3.9' and psycopg.pq.__impl__=='binary'"])
        check_port(); validate_paths(stage,evidence,args.manifest); evidence.mkdir(exist_ok=False)
        report={'status':'FAIL_OR_INCOMPLETE','source_commit':COMMIT,'source_tree':TREE,'archive_sha256':archive_sha,'runtime_fingerprint':fp,'events':[],'product':'HOLD','independent_security':'HOLD','real_iam':'HOLD','core_join':'HOLD'}
        def event(name):
            report['events'].append(name); print(name,flush=True)
        with tempfile.TemporaryDirectory(prefix='org10-source-',dir=stage.parent) as tmp:
            root=Path(tmp)/'source'; materialize(files,root,TREE); candidate=root/CANDIDATE
            py=[sys.executable,'-E','-s','-B','-X','utf8']
            run(py+[candidate/'derive_common.py','--source-root',root,'--verify',candidate]); pins=source_r3_pins(candidate); event('SOURCE_DERIVATION_AND_R3_PASS')
            # No source files executed before exact tree and reviewed fingerprint checks.
            check_port()
            run([bins['initdb'],'-D',stage,'--username='+ADMIN,'--auth=scram-sha-256','--locale-provider=libc','--locale=C','--encoding=UTF8','--pwprompt']); event('INITDB_PASS')
            run([bins['pg_ctl'],'-D',stage,'-l',stage/'server.log','-o',f'-p {PORT} -h 127.0.0.1 -c cluster_name={CLUSTER}','-w','-t','60','start']); started=True; event('SERVER_STARTED')
            with warnings.catch_warnings():
                warnings.simplefilter('error',getpass.GetPassWarning); password=getpass.getpass('ORG10 admin password: ')
            require(bool(password),'ADMIN_PASSWORD_REQUIRED')
            base=[bins['psql'],'-X','-w','-v','ON_ERROR_STOP=1','-h','127.0.0.1','-p',str(PORT),'-U',ADMIN]
            sql="SELECT current_setting('cluster_name'),current_setting('port'),current_setting('server_version_num'),current_setting('data_directory'),current_user,session_user,host(inet_server_addr()),host(inet_client_addr()),current_database(),current_setting('server_encoding');"
            def authenticate(db):
                run([bins['pg_ctl'],'-D',stage,'status']); identity(run(base+['-d',db,'-A','-t','-c',sql],True,password),stage,db)
            try:
                authenticate('postgres'); event('ADMIN_IDENTITY_PASS')
                run(base+['-d','postgres','-f',candidate/'bootstrap_roles.sql'],password=password); event('BOOTSTRAP_PASS')
                authenticate(DATABASE)
                run(base+['-d',DATABASE,'-f',candidate/'PG_SCHEMA_ORG10.sql'],password=password); event('SCHEMA_PASS')
                authenticate(DATABASE)
                raw_report=evidence/'pg_report.json'
                run(py+[candidate/'run_pg_acceptance.py','--execute-disposable','--port',str(PORT),'--report',raw_report]); event('RUNNER_EXIT_ZERO')
                review=review_report(raw_report.read_bytes(),strict_json((candidate/'PG_ACCEPTANCE_MATRIX.json').read_bytes()),pins)
                report['review']=review; event('REPORT_MATCH_UNATTESTED')
                # PG17 MAINTAIN is not included in the original 360 ACL probes.
                # Keep this additional read-only diagnostic separate from PG01–31.
                authenticate(DATABASE)
                acl_sql="SELECT count(*), count(*) FILTER (WHERE pg_catalog.has_table_privilege(r.rolname,c.oid,'MAINTAIN')) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace CROSS JOIN pg_catalog.pg_roles r WHERE n.nspname='aicos_org10_fixture' AND c.relkind='r' AND r.rolname IN ('aicos_org10_writer_a','aicos_org10_writer_b','aicos_org10_reader_a','aicos_org10_unmapped');"
                require(run(base+['-d',DATABASE,'-A','-t','-c',acl_sql],True,password).strip()=='48|0','PG17_MAINTAIN_ACL_HOLD')
                report['supplemental_maintain_acl']={'checks':48,'granted':0}; event('MAINTAIN_ACL_48_PASS')
                verify_materialized(files,root,TREE); require(fingerprint(args.pg_bin,archive_sha)==inventory,'POST_RUNTIME_FINGERPRINT_DRIFT'); event('POST_SOURCE_RUNTIME_PASS')
                authenticate(DATABASE)
                run([bins['pg_ctl'],'-D',stage,'-w','-t','60','stop','-m','fast']); started=False; check_port(); event('SERVER_STOPPED')
                report['status']='COMPLETE_REPORT_UNATTESTED'
            finally:
                del password
        return 0
    except (Hold,OSError,ValueError,KeyError,TypeError,StopIteration,subprocess.SubprocessError,metadata.PackageNotFoundError,zipfile.BadZipFile,EOFError,KeyboardInterrupt,getpass.GetPassWarning) as exc:
        print('HOLD: '+(str(exc) if isinstance(exc,Hold) else type(exc).__name__),file=sys.stderr)
        if started or (args.stage is not None and os.path.lexists(args.stage)):
            print('Preserve stage and evidence. No automatic retry/delete. Stop only after positive stage identity review.',file=sys.stderr)
        return 2
    finally:
        if report is not None: new_file(args.evidence/'launch_report.json',canonical_json(report))

if __name__=='__main__': raise SystemExit(main())
