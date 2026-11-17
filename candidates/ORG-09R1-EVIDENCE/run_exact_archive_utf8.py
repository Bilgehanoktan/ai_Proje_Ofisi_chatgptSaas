"""ORG-09: verify an immutable GitHub ZIP, run original 12+8 SQLite scenarios.
No git checkout, PostgreSQL, network, product startup or permission changes.
"""
import argparse
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

CURRENT = '663b7b1a60d8444c9b972f3fa30e8a4ecc83b352'
CURRENT_TREE = '0987d2dbd90178202eba6a2eb6dc2e5dbe9483d4'
HISTORICAL = '17be56406408d572ebc66cf6fe7c1b6d83f18d76'
HISTORICAL_TREE = 'ff7b149d066387060173afa3c78f26b74a72b731'
ROOT_NAME = 'ai_Proje_Ofisi_chatgptSaas-' + CURRENT
CURRENT_COUNT, HISTORICAL_COUNT = 1770, 1739
CURRENT_BYTES = 20505213
EXCLUDED = ('candidates/ORG-06R2/', 'candidates/ORG-07A/', 'candidates/ORG-08-READBACK/')
DEPENDENCIES = {'cryptography':'46.0.4','jsonschema':'4.26.0','fastapi':'0.128.2','starlette':'0.50.0','httpx':'0.28.1'}
STUDIO_OWNER = '601cba1ef3108a381adb6bf8dd8a67e763eb744d'
PG_EVIDENCE = 'ba6c72a2508e3eab579c33f48e52008d1d601897'
SUITES = (
    ('runtime_original', 'historical', 'candidates/ORG-06/test_org_core_checkout.py', (
        'test_queued_readback','test_admitted_readback','test_wrong_seat','test_research_seat',
        'test_stale_head','test_wrong_history','test_wrong_member','test_wrong_environment',
        'test_gate_not_run','test_org_notice_tamper','test_no_db_changes')),
    ('runtime_notice', 'historical', 'candidates/ORG-06R2/test_operation_notice.py', ('test_operation_notice_tamper',)),
    ('office_readback', 'current', 'candidates/ORG-08-READBACK/test_preview_checkout.py', (
        'test_existing_studio_transport_matches_internal_review','test_project_office_preview',
        'test_office_stale_pin','test_role_mismatch','test_membership_mismatch','test_stale_head',
        'test_operation_history','test_no_mutation')),
)

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


def verify_archive(archive):
    require(archive.is_file() and archive.stat().st_size <= 50_000_000, 'ARCHIVE_FILE_HOLD')
    with archive.open('rb') as f:
        raw=f.read(50_000_001)
    files=read_archive(raw)
    require(git_tree(files)==CURRENT_TREE,'CURRENT_TREE_HOLD')
    historical={p:raw for p,raw in files.items() if not p.startswith(EXCLUDED)}
    require(len(historical)==HISTORICAL_COUNT and git_tree(historical)==HISTORICAL_TREE,'HISTORICAL_TREE_HOLD')
    return files,historical,sha256(raw)


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


def versions():
    require(sys.version_info >= (3,12),'PYTHON_3_12_REQUIRED')
    actual={k:importlib.metadata.version(k) for k in DEPENDENCIES}
    require(actual==DEPENDENCIES,'DEPENDENCY_PIN_HOLD')
    return actual


def exact_pass(raw, returncode, expected):
    lines=raw.decode('utf-8',errors='replace').replace('\r\n','\n').splitlines()
    actual=[m.group(1) for line in lines if (m:=re.fullmatch(r'(test_\w+) \(.+\) \.\.\. ok',line))]
    summary=[line for line in lines if re.fullmatch(r'Ran \d+ tests? in .+s',line)]
    return (returncode==0 and len(actual)==len(expected) and set(actual)==set(expected)
            and len(summary)==1 and re.match(rf'Ran {len(expected)} tests? in ',summary[0]) is not None
            and [line for line in lines if line=='OK']==['OK'] and lines[-1:] == ['OK'])


def clean_env():
    return {k:v for k,v in os.environ.items() if not k.upper().startswith(('PG','PYTHON'))}


def run_suite(name, tree, script, expected, current, historical, output):
    root=historical if tree=='historical' else current
    # The extra R2 scenario is not in the historical tree. Reuse its exact current bytes.
    source=(current if name=='runtime_notice' else root)/script
    args=[str(historical)] if name=='runtime_notice' else []
    cmd=[sys.executable,'-E','-s','-B','-X','utf8',str(source),*args]
    start=time.monotonic()
    try:
        p=subprocess.run(cmd,cwd=root,env=clean_env(),stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180,check=False)
        raw=p.stdout; code=p.returncode; status='PASS' if exact_pass(raw,code,expected) else 'FAIL_OR_INCOMPLETE'
    except subprocess.TimeoutExpired as exc:
        raw=(exc.stdout or b'')+b'\nORG09_TEST_TIMEOUT\n'; code=None; status='TIMEOUT'
    log=output/(name+'.log')
    with log.open('xb') as f: f.write(raw)
    return {'id':name,'status':status,'expected':len(expected),'expected_ids':list(expected),
            'returncode':code,'log':log.name,'log_sha256':sha256(raw),'elapsed_ms':round((time.monotonic()-start)*1000)}


def run(archive, output, work_parent, execute):
    require(output.is_absolute() and output.parent.is_dir() and not os.path.lexists(output),'FRESH_EVIDENCE_REQUIRED')
    require(work_parent.is_absolute() and work_parent.is_dir(),'WORK_PARENT_REQUIRED')
    output.mkdir(exist_ok=False)
    report={'profile':'ORG09_SYNTHETIC_SQLITE_ONLY','archive_commit':CURRENT,'archive_tree':CURRENT_TREE,
            'historical_commit':HISTORICAL,'historical_tree':HISTORICAL_TREE,'status':'BLOCKED',
            'python':sys.version.split()[0],'sqlite':sqlite3.sqlite_version,'passed_here':0,'suites':[],
            'studio_owner_evidence':{'commit':STUDIO_OWNER,'original_pass':6,'additional_pass':6,'rerun':False},
            'pg_evidence':{'commit':PG_EVIDENCE,'rerun':False,'custody':'UNATTESTED'},
            'product_acceptance':'HOLD','independent_security':'HOLD','real_iam':'HOLD','office_placement':'HOLD',
            'child_text_encoding_policy':'EXPLICIT_X_UTF8'}
    try:
        files,old,archive_digest=verify_archive(archive)
        report['archive_sha256']=archive_digest
        report['verified_current_blobs']=len(files); report['verified_historical_blobs']=len(old)
        print(f'EXACT_ARCHIVE_PASS {len(files)}; HISTORICAL_TREE_PASS {len(old)}',flush=True)
        if not execute:
            report['status']='SOURCE_PREFLIGHT_ONLY'; return 0
        report['dependencies']=versions()
        with tempfile.TemporaryDirectory(prefix='org09-',dir=work_parent) as tmp:
            current=Path(tmp)/'current'; historical=Path(tmp)/'historical'
            materialize(files,current,CURRENT_TREE); materialize(old,historical,HISTORICAL_TREE)
            for name,tree,script,expected in SUITES:
                result=run_suite(name,tree,script,expected,current,historical,output)
                report['suites'].append(result)
                if result['status']=='PASS': report['passed_here']+=len(expected)
                print(f'{name}: {result["status"]}',flush=True)
                if result['status']!='PASS': report['status']='FAIL_OR_INCOMPLETE'; return 1
            verify_materialized(files,current,CURRENT_TREE); verify_materialized(old,historical,HISTORICAL_TREE)
            report['post_run_source_integrity']='PASS'
        report['status']='PASS_LOCAL_SQLITE_ONLY'
        return 0
    except (Hold,OSError,zipfile.BadZipFile,RuntimeError,importlib.metadata.PackageNotFoundError,subprocess.SubprocessError) as exc:
        report['blocker']=str(exc) if isinstance(exc,Hold) else type(exc).__name__
        print('HOLD: '+report['blocker'],file=sys.stderr)
        return 2
    finally:
        with (output/'report.json').open('x',encoding='utf-8') as f:
            json.dump(report,f,indent=2,sort_keys=True); f.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--work-parent',type=Path,required=True)
    p.add_argument('--execute-local',action='store_true')
    a=p.parse_args()
    try:
        return run(a.archive.resolve(),a.evidence.resolve(),a.work_parent.resolve(),a.execute_local)
    except Hold as exc:
        print('HOLD: '+str(exc),file=sys.stderr); return 2

if __name__=='__main__': sys.exit(main())
