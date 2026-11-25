"""Read-only checkout audit; never installs or executes product code."""
import hashlib, json, sys
from pathlib import Path, PurePosixPath

def audit(root, manifest, expected_count=384):
    root=Path(root).resolve(); entries=manifest['files']; errors=[]; matched=0; seen=set()
    if len(entries)!=expected_count: errors.append('COUNT_MISMATCH')
    for name, pin in entries.items():
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name or p.as_posix()!=name or name.casefold() in seen:
            errors.append('UNSAFE_PATH:'+name); continue
        seen.add(name.casefold()); f=root.joinpath(*p.parts)
        if any(x.is_symlink() for x in [f,*[q for q in f.parents if q!=root and root in q.parents]]) or not f.is_file():
            errors.append('MISSING_OR_LINK:'+name); continue
        data=f.read_bytes()
        if len(data)!=pin['bytes'] or hashlib.sha256(data).hexdigest()!=pin['sha256']: errors.append('PIN_MISMATCH:'+name)
        else: matched+=1
    for f in root.rglob('*'):
        if f.is_symlink() or (f.is_file() and f.relative_to(root).as_posix() not in entries and f.relative_to(root).as_posix()!='SOURCE_MANIFEST.json'):
            errors.append('UNEXPECTED_PATH:'+f.relative_to(root).as_posix())
    return {'expected':expected_count,'matched':matched,'errors':errors,'status':'PASS' if not errors else 'HOLD'}

if __name__=='__main__':
    root=Path(sys.argv[1]); mf=root/'SOURCE_MANIFEST.json'
    if mf.is_symlink(): raise SystemExit('MANIFEST_LINK')
    raw=mf.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sys.argv[2]: raise SystemExit('MANIFEST_PIN_MISMATCH')
    result=audit(root,json.loads(raw)); print(json.dumps(result,indent=2)); sys.exit(result['status']!='PASS')
