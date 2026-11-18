"""Read-only ORG10 archive-to-inventory comparison. No install/extract/DB start."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

MANIFEST_SHA = '50870555adc6334556feefdd8323d42241229099e1cb3ccea5707de779cf6ef4'
PINS = {
    'postgresql-17.12.zip': 'a2cd8a774389347b70be7748ac4a37ef43cb6ee539c5fc3e85ae264b15e4a04c',
    'psycopg-3.3.9-py3-none-any.whl': 'd2d7d04a1ce6dab4f5b27316bea3b52585cafa2f2d631e5b09dd69823f5c26f6',
    'psycopg_binary-3.3.9-cp314-cp314-win_amd64.whl': '109c5df5b0e5117e01a42d3b56a2f4ccd5431bd54d25efdfc89df095ac9f9605',
}
PG_ALIAS = 'postgresql-17.12-1-windows-x64-binaries.zip'
AREAS = {'bin','lib','share'}


def sha_file(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def unique(pairs):
    d = {}
    for k,v in pairs:
        if k in d: raise ValueError('DUPLICATE_JSON_KEY')
        d[k]=v
    return d


def archive_map(path, expected, kind):
    if sha_file(path) != expected: raise ValueError('ARCHIVE_PIN_MISMATCH')
    rows={}; seen=set()
    with ZipFile(path) as z:
        for info in z.infolist():
            if info.is_dir(): continue
            name=info.filename
            p=PurePosixPath(name)
            if p.is_absolute() or '\\' in name or any(x in ('','.', '..') for x in name.split('/')) or ':' in name:
                raise ValueError('UNSAFE_ARCHIVE_PATH')
            parts=p.parts
            if kind=='pg':
                if parts[0]=='pgsql': parts=parts[1:]
                if not parts or parts[0] not in AREAS: continue
            else:
                if any(x.endswith('.data') for x in parts): raise ValueError('WHEEL_DATA_LAYOUT_UNSUPPORTED')
                parts=('Lib','site-packages',*parts)
            key='/'.join(parts)
            if key.casefold() in seen: raise ValueError('DUPLICATE_ARCHIVE_PATH')
            seen.add(key.casefold())
            with z.open(info) as f: rows[key]=hashlib.file_digest(f,'sha256').hexdigest()
    if sha_file(path)!=expected: raise ValueError('ARCHIVE_CHANGED_DURING_READ')
    return rows


def compare(observed, reference, wheel=False):
    # RECORD is rewritten by pip. INSTALLER and REQUESTED are local metadata.
    generated=lambda k: wheel and '.dist-info/' in k and k.rsplit('/',1)[1] in {'RECORD','INSTALLER','REQUESTED'}
    local=sorted(k for k in observed if generated(k))
    o={k:v for k,v in observed.items() if not generated(k)}
    r={k:v for k,v in reference.items() if not generated(k)}
    missing=sorted(r.keys()-o.keys()); extra=sorted(o.keys()-r.keys())
    mismatch=sorted(k for k in o.keys()&r.keys() if o[k]!=r[k])
    return {'status':'MATCH' if not (missing or extra or mismatch) else 'HOLD',
            'matched':len(o.keys()&r.keys())-len(mismatch),'expected':len(r),
            'missing':missing,'extra':extra,'mismatch':mismatch,'local_metadata_not_publisher_matched':local}


def find_file(roots, names, digest):
    found=[]
    for root in roots:
        if not root.is_dir(): continue
        for name in names:
            for p in (root/name,root/'wheels'/name):
                if p.is_file(): found.append(p)
        # Search immediate subdirectories only; no traversal of live DB files.
        for sub in root.iterdir():
            if sub.is_dir() and sub.name.lower().startswith(('core-0227','aios_0227','ai_company_os_0227')):
                for name in names:
                    for p in (sub/name,sub/'wheels'/name):
                        if p.is_file(): found.append(p)
    for p in dict.fromkeys(found):
        if sha_file(p)==digest: return p
    raise ValueError('ARCHIVE_MISSING_OR_PIN_MISMATCH: '+names[0])


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--search',type=Path,action='append',required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    if a.report.exists(): raise SystemExit('HOLD: REPORT_EXISTS')
    if sha_file(a.manifest)!=MANIFEST_SHA: raise SystemExit('HOLD: MANIFEST_HASH')
    j=json.loads(a.manifest.read_bytes(),object_pairs_hook=unique)
    report={'classification':'LOCAL_ARCHIVE_COMPARISON_NOT_INDEPENDENT_ATTESTATION','manifest_sha256':MANIFEST_SHA,'results':{},'python_base_provenance':'HOLD','port_owner_approval':'HOLD','pg_execution':'NOT_RUN'}
    cases=[('postgresql',next(iter(PINS)),j['pg_files'],False),('psycopg',list(PINS)[1],j['drivers']['psycopg']['files'],True),('psycopg-binary',list(PINS)[2],j['drivers']['psycopg-binary']['files'],True)]
    for label,name,observed,wheel in cases:
        try:
            names=(name,) if wheel else (name,PG_ALIAS)
            path=find_file(a.search,names,PINS[name])
            result=compare(observed,archive_map(path,PINS[name],'wheel' if wheel else 'pg'),wheel)
            result['archive_sha256']=PINS[name]
        except (OSError,ValueError,RuntimeError) as exc:
            result={'status':'HOLD','reason':str(exc) if isinstance(exc,ValueError) else type(exc).__name__}
        report['results'][label]=result
    report['archive_comparison']='MATCH' if all(x['status']=='MATCH' for x in report['results'].values()) else 'HOLD'
    with a.report.open('x',encoding='utf-8',newline='\n') as f: json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(report,indent=2));return 0 if report['archive_comparison']=='MATCH' else 2

if __name__=='__main__': raise SystemExit(main())
