"""EXT-07 offline acceptance preflight; no product mutation, execution or grant."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

BASE = 'ba20cd64eba0f09390818c294ae8894fab9a3acf'
FRONT = 'product/ai-company-os-frontend/'
BACK = 'product/ai-company-os-backend/'
C5 = 'candidates/W5-EXT-05/'
DATA = FRONT + 'features/capabilities/ext06/skillData.json'


def safe_file(root, name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or p.as_posix() != name or '\\' in name:
        raise ValueError('UNSAFE_PATH: ' + name)
    path = root.joinpath(*p.parts)
    if any(part.is_symlink() for part in (path, *path.parents) if part != root and root in part.parents):
        raise ValueError('SYMLINK: ' + name)
    if not path.is_file():
        raise ValueError('MISSING: ' + name)
    return path


def read(root, name):
    return safe_file(root, name).read_bytes()


def load(root, name):
    return json.loads(read(root, name))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()


def verify(root):
    root = Path(root).resolve()
    errors = []
    counts = dict(product=0, core=0, catalog=0, projection=0)
    def check(label, condition):
        if not condition:
            errors.append(label)
    # Only exact committed EXT-06 inputs; EXT-07 metadata may live outside checkout.
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
    check('BASE_MISMATCH', git('rev-parse', 'HEAD') == BASE)
    check('DIRTY_CHECKOUT', not git('status', '--porcelain', '--untracked-files=all'))
    if errors:
        return {'status':'HOLD', 'errors':errors, 'counts':counts, 'independent_acceptance':'HOLD', 'execution_allowed':False}
    manifest = load(root, 'product/SOURCE_MANIFEST.json')['files']
    tracked = set(git('ls-files', 'product').splitlines())
    check('PRODUCT_INVENTORY', tracked == {'product/SOURCE_MANIFEST.json', *('product/'+p for p in manifest)})
    for p, expected in manifest.items():
        raw = read(root, 'product/'+p)
        ok = len(raw) == expected['bytes'] and sha(raw) == expected['sha256']
        check('PRODUCT_HASH:'+p, ok)
        counts['product'] += int(ok)
    for p, expected in load(root, C5+'CORE_PINS.json').items():
        raw = read(root, BACK+p)
        ok = len(raw)==expected['bytes'] and sha(raw)==expected['sha256'] and blob(raw)==expected['git_blob']
        check('CORE_PIN:'+p, ok)
        counts['core'] += int(ok)
    lock = load(root,C5+'CATALOG_LOCK.json')
    proj = load(root,C5+'CATALOG_PROJECTION.json')
    ui = load(root, DATA)
    check('LOCK_PIN', blob(read(root,C5+'CATALOG_LOCK.json')) == ui['lock_blob'])
    check('PROJECTION_PIN', blob(read(root,C5+'CATALOG_PROJECTION.json')) == ui['projection_blob'])
    check('CATALOG_SCOPE', [e['skill_id'] for e in lock['entries']] == ['superpowers','ui-ux-pro-max','watch'])
    check('PROJECTION_SCOPE', [e['skill_id'] for e in proj['skills']] == [e['skill_id'] for e in lock['entries']] == [e['skill_id'] for e in ui['skills']])
    for e, p, s in zip(lock['entries'],proj['skills'],ui['skills'],strict=True):
        raw=read(root,e['source_path'])
        ok=sha(raw)==e['artifact_sha256'] and blob(raw)==e['artifact_git_blob'] and all(s[k]==v for k,v in e.items() if k!='artifact_file')
        for name in ('manifest','input.schema','output.schema'):
            key=name.replace('.','_')+'_sha256'
            ok &= sha(read(root,C5+'catalog/'+e['skill_id']+'/'+name+'.json')) == e[key]
        check('CATALOG_PIN:'+e['skill_id'],ok)
        counts['catalog']+=int(ok)
        ok=all(s.get(k)==v for k,v in p.items()) and s['enabled'] is False and s['installed'] is False and not s['effective_tools'] and s['status']=='QUARANTINED' and s['g7_ref'] is None and s['g8_ref'] is None
        ok &= all(r['decision']=='HOLD' and r['grant_created'] is False and r['dispatch_allowed'] is False and r['independent_verified'] is False and not r['effective_tools'] for r in s['reviews'])
        check('UI_PROJECTION:'+e['skill_id'],ok)
        counts['projection']+=int(ok)
    check('UI_AUTHORITY', ui['authority']=='NONE' and ui['independent_acceptance']=='HOLD' and all(ui[k] is None for k in ('actual_installed_count','actual_active_count','actual_assignments')) and ui['active_count']==ui['installed_count']==0)
    return {'status':'HOLD' if errors else 'SOURCE_PREFLIGHT_PASS', 'errors':errors, 'counts':counts, 'independent_acceptance':'HOLD', 'execution_allowed':False, 'build':'NOT_RUN', 'browser':'NOT_RUN'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    args=parser.parse_args()
    try:
        result=verify(args.root)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result={'status':'HOLD','errors':[str(exc)],'independent_acceptance':'HOLD','execution_allowed':False}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='SOURCE_PREFLIGHT_PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
