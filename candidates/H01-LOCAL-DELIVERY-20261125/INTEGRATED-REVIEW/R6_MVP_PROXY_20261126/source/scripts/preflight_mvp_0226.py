"""0226 read-only acceptance input inventory; never grants or closes a gate.
Use a clean source tree before installation and a separate runtime copy.
No network, installation, DB connection, product import, build or test execution.
"""
from pathlib import Path, PurePosixPath
from importlib import metadata
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from verify_product import verify, git_blob

MANIFEST = '981a13fc226184dc3a911ae0d94e0042285ff302'
CORE_LOCK = '223f6fbd28cf4c428c07eb60dda4a36f644fa58c'
BACKEND = 'product/ai-company-os-backend/'
FRONTEND = 'product/ai-company-os-frontend/'
SPECS = {
    BACKEND+'requirements.txt': 'e1e7b627b7f83b54687170391406cbf996a85dfb02fed06591b301c01a78799a',
    BACKEND+'requirements-test.txt': 'ba0bd6f14734ee8ea5631476bfff673b07b96b0b22c4e493a7c92bc0dae8a0e4',
    BACKEND+'requirements-history-signatures.txt': 'a2b52ebff7bc0ae138ca5cc06dc483826e5ec245fb506c76d01411a9beccd020',
    FRONTEND+'package.json': 'e00528a32e54e21b7547ad08762a44dede75366af0f0781140f42b35f102c0f0',
}

def read_safe(root, name):
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or ':' in name or '\\' in name or p.as_posix()!=name:
        raise ValueError('UNSAFE_PATH')
    target=root
    for part in p.parts:
        target=target/part
        if target.is_symlink() or getattr(target,'is_junction',lambda:False)():
            raise ValueError('LINK_HOLD')
    if not target.is_file(): raise FileNotFoundError(name)
    with target.open('rb') as f: raw=f.read(16*1024*1024+1)
    if len(raw)>16*1024*1024: raise ValueError('SIZE_HOLD')
    return raw

def python_version(name):
    try: return metadata.version(name)
    except metadata.PackageNotFoundError: return None

def version_row(name, expected, actual):
    return {'name':name,'expected':expected,'observed':actual,
            'status':'MATCH' if actual==expected else 'MISSING' if actual is None else 'MISMATCH'}

def lock_status(root,name):
    try: return {'status':'PRESENT_UNREVIEWED','sha256':hashlib.sha256(read_safe(root,name)).hexdigest()}
    except FileNotFoundError: return {'status':'ABSENT'}
    except (OSError,ValueError): return {'status':'HOLD'}

def inspect(root, runtime, historical=None, pg_bindir=None):
    report={'revision':'0226','decision':'HOLD','gate_promotion':False,'product_execution':'NOT_RUN',
            'manifest_blob':MANIFEST,'python':sys.version.split()[0], 'source_integrity':'HOLD',
            'direct_spec_pins':{},'python_direct':[],'node_direct':[],'overrides':{},
            'historical_core':{'status':'NOT_SUPPLIED'},'lock_review':'NOT_EVALUATED'}
    try:
        checked=verify(root,MANIFEST)
        if checked['verified_files']!=392: raise ValueError('SOURCE_COUNT_HOLD')
        report['source_integrity']='MATCH';report['verified_files']=checked['verified_files']
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        report['source_reason']=type(exc).__name__
    for name,pin in SPECS.items():
        try:
            raw=read_safe(root,name)
            if hashlib.sha256(raw).hexdigest()!=pin: raise ValueError('SPEC_PIN_HOLD')
            report['direct_spec_pins'][name]='MATCH'
            if name.endswith('package.json'):
                obj=json.loads(raw)
                for group in ('dependencies','devDependencies'):
                    for key,expected in obj[group].items():
                        try:
                            actual=json.loads(read_safe(runtime,FRONTEND+'node_modules/'+key+'/package.json'))
                            observed=actual['version'] if actual.get('name')==key else None
                        except (OSError,ValueError,KeyError,TypeError): observed=None
                        report['node_direct'].append(version_row(key,expected,observed))
                report['overrides']=obj.get('overrides',{})
            else:
                for line in raw.decode('utf-8').splitlines():
                    if not line.strip() or line.startswith('#'): continue
                    m=re.fullmatch(r'([A-Za-z0-9_.-]+)==([0-9]+\.[0-9]+\.[0-9]+)',line)
                    if m is None: raise ValueError('DIRECT_PIN_FORMAT_HOLD')
                    key,expected=m.groups();report['python_direct'].append(version_row(key,expected,python_version(key)))
        except (OSError,ValueError,KeyError,TypeError): report['direct_spec_pins'][name]='HOLD'
    report['locks']={'python':lock_status(runtime,BACKEND+'requirements.lock.txt'),
                     'node':lock_status(runtime,FRONTEND+'package-lock.json')}
    names=('postgres','initdb','pg_ctl','psql')
    report['postgres_binaries']={name:bool((pg_bindir/(name+('.exe' if os.name=='nt' else ''))).is_file()) if pg_bindir else bool(shutil.which(name)) for name in names}
    report['psycopg']=python_version('psycopg')
    report['node_on_path']=bool(shutil.which('node'));report['npm_on_path']=bool(shutil.which('npm'))
    report['chromium_on_path']=bool(shutil.which('chromium') or shutil.which('chrome'))
    if historical is not None:
        try:
            raw=read_safe(root,'tests/integration/core_0207_source_lock.json')
            if git_blob(raw)!=CORE_LOCK: raise ValueError('CORE_LOCK_HOLD')
            lock=json.loads(raw); files=lock['files']
            if len(files)!=55: raise ValueError('CORE_COUNT_HOLD')
            mismatches=[]
            for row in files:
                try:
                    body=read_safe(historical,row['path'])
                    if len(body)!=row['bytes'] or git_blob(body)!=row['git_blob'] or (row['sha256'] is not None and hashlib.sha256(body).hexdigest()!=row['sha256']): raise ValueError('CORE_FILE_HOLD')
                except (OSError,ValueError): mismatches.append(row['path'])
            report['historical_core']={'status':'SOURCE_MATCH' if not mismatches else 'HOLD','verified':55-len(mismatches),'total':55,'mismatches':mismatches,
                'direct_dependencies':[version_row(k,v,python_version(k)) for k,v in lock['direct_dependency_pins'].items()]}
        except (OSError,ValueError,KeyError,TypeError): report['historical_core']={'status':'LOCK_UNAVAILABLE_OR_INVALID'}
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True,type=Path);p.add_argument('--runtime-root',type=Path);p.add_argument('--historical-root',type=Path);p.add_argument('--pg-bindir',type=Path);p.add_argument('--report',required=True,type=Path)
    a=p.parse_args();root=a.root.resolve(strict=True);runtime=(a.runtime_root or root).resolve(strict=True)
    result=inspect(root,runtime,a.historical_root.resolve(strict=True) if a.historical_root else None,a.pg_bindir)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
    return 0 if result['source_integrity']=='MATCH' and all(x=='MATCH' for x in result['direct_spec_pins'].values()) else 1

if __name__=='__main__': raise SystemExit(main())
