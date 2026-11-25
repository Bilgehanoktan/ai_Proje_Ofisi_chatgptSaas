"""Read-only full candidate preflight; no install, launch, migration, CI or authority change."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path, PurePosixPath
import sqlite3
import sys

EXCLUDED = {'node_modules','.next','__pycache__','.pytest_cache','.venv'}
CORE_LOCK_BLOB = '223f6fbd28cf4c428c07eb60dda4a36f644fa58c'
CORE_COUNT = 55

def blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()

def checked(root,name):
    p=PurePosixPath(name)
    if p.is_absolute() or not p.parts or any(x in ('..','.') for x in p.parts) or '\\' in name:
        raise ValueError('UNSAFE_SOURCE_PATH')
    path=root.joinpath(*p.parts)
    if any(x.is_symlink() for x in (path,*path.parents) if x==root or root in x.parents):
        raise ValueError('SOURCE_SYMLINK_HOLD')
    return path

def inventory(product):
    if not product.is_dir() or product.is_symlink():raise ValueError('PRODUCT_MISSING')
    m=json.loads(checked(product,'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))['files']
    actual=set()
    for path in product.rglob('*'):
        rel=path.relative_to(product)
        if any(part in EXCLUDED for part in rel.parts):continue
        if path.is_symlink():raise ValueError('SOURCE_SYMLINK_HOLD: '+rel.as_posix())
        if path.is_file() and rel.as_posix()!='SOURCE_MANIFEST.json':actual.add(rel.as_posix())
    missing=sorted(set(m)-actual);extra=sorted(actual-set(m));bad=[]
    for name in sorted(set(m)&actual):
        data=checked(product,name).read_bytes();pin=m[name]
        if len(data)!=pin['bytes'] or hashlib.sha256(data).hexdigest()!=pin['sha256']:bad.append(name)
    return {'expected':len(m),'exact':len(m)-len(missing)-len(bad),'missing':missing,'extra':extra,'mismatch':bad,'pass':not(missing or extra or bad)}

def core_lock(root):
    raw=checked(root,'tests/integration/core_0207_source_lock.json').read_bytes()
    if blob(raw)!=CORE_LOCK_BLOB:raise ValueError('CORE_LOCK_BLOB_MISMATCH')
    lock=json.loads(raw)
    if len(lock['files'])!=CORE_COUNT:raise ValueError('CORE_LOCK_COUNT')
    failures=[]
    for f in lock['files']:
        p=checked(root,f['path'])
        if not p.is_file() or blob(p.read_bytes())!=f['git_blob'] or p.stat().st_size!=f['bytes']:failures.append(f['path'])
    versions={}
    for name in lock['direct_dependency_pins']:
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:versions[name]=None
    return {'expected':CORE_COUNT,'exact':CORE_COUNT-len(failures),'failed':failures,'direct_pins':lock['direct_dependency_pins'],'installed':versions,'direct_match':versions==lock['direct_dependency_pins']}

def npm_status(front):
    pkg=json.loads(checked(front,'package.json').read_text(encoding='utf-8'))
    pins={**pkg['dependencies'],**pkg['devDependencies']};installed={}
    for name in pins:
        path=front/'node_modules'/name/'package.json'
        try:installed[name]=json.loads(path.read_text(encoding='utf-8'))['version']
        except (OSError,ValueError,KeyError):installed[name]=None
    lock=front/'package-lock.json'
    return {'direct_pins':pins,'installed':installed,'direct_match':installed==pins,'npm_lock_present':lock.is_file() and not lock.is_symlink(),'npm_lock_sha256':hashlib.sha256(lock.read_bytes()).hexdigest() if lock.is_file() and not lock.is_symlink() else None,'transitive_review':'REQUIRED_SEPARATE'}

def inspect(root):
    result={'scope':'D0 read-only preflight; no build/test execution','python':sys.version.split()[0],'sqlite':sqlite3.sqlite_version,'checks':{}}
    for name,fn in [('source',lambda:inventory(root/'product')),('core',lambda:core_lock(root)),('npm',lambda:npm_status(root/'product/ai-company-os-frontend'))]:
        try:result['checks'][name]=fn()
        except (OSError,ValueError,TypeError,KeyError) as e:result['checks'][name]={'error':str(e)}
    c=result['checks'];result['status']='READY_FOR_REVIEW_NOT_ACCEPTED' if c['source'].get('pass') and c['core'].get('exact')==CORE_COUNT and c['core'].get('direct_match') and c['npm'].get('direct_match') and c['npm'].get('npm_lock_present') else 'HOLD'
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    root=a.source.resolve();report=a.report.resolve()
    if report==root or root in report.parents:p.error('report must be outside source checkout')
    result=inspect(root)
    with report.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(result['status']);return 0 if result['status']=='READY_FOR_REVIEW_NOT_ACCEPTED' else 1

if __name__=='__main__':sys.exit(main())
