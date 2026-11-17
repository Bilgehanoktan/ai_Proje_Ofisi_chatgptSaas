"""Read-only review manifest overlay; never writes to product or enables routes."""
import argparse
import hashlib
import json
from pathlib import Path

BASE = '8a3b05aadd32b214f3f8988fc9c793f853fbe3d0'
BASE_MANIFEST = '07f1fc919daa6dd3d7ffad7b67c3e9eebcd5d276'
PREFIX = 'product/ai-company-os-frontend/'


def git_blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def row(raw):
    return {'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


def review_delta(candidate):
    scope_raw=(candidate/'PRODUCT_SCOPE.json').read_bytes()
    if git_blob(scope_raw)!='4af76dd5c38b266f0aacf5b84443e00ac9e714df':
        raise ValueError('SCOPE_PIN_HOLD')
    scope = json.loads(scope_raw)
    if scope['base'] != BASE or scope['status'] != 'REVIEW_ONLY_NOT_APPLIED':
        raise ValueError('BASE_HOLD')
    before, after, changes = {}, {}, {}
    for full, expected in scope['base_pins'].items():
        if not full.startswith(PREFIX): raise ValueError('PATH_HOLD')
        raw=(candidate/'base'/Path(full).name).read_bytes()
        if git_blob(raw)!=expected: raise ValueError('BASE_PIN_HOLD')
        before[full.removeprefix('product/')]=row(raw)
    for full, spec in scope['proposed'].items():
        if not full.startswith(PREFIX): raise ValueError('PATH_HOLD')
        rel=full.removeprefix(PREFIX)
        if '..' in Path(rel).parts or Path(rel).is_absolute(): raise ValueError('PATH_HOLD')
        raw=(candidate/'staged'/rel).read_bytes()
        if git_blob(raw)!=spec['git_blob']: raise ValueError('STAGED_PIN_HOLD')
        path=full.removeprefix('product/')
        after[path]=row(raw)
        old=before.get(path)
        kind='added' if old is None else 'unchanged' if old==after[path] else 'modified'
        if kind!=spec['status']: raise ValueError('STATUS_HOLD')
        if kind!='unchanged': changes[path]={'before':old,'after':after[path]}
    if (len(before),len(after),len(changes))!=(4,8,7) or not before.keys()<=after.keys():
        raise ValueError('INVENTORY_HOLD')
    if sum(v['before'] is None for v in changes.values())!=4:
        raise ValueError('INVENTORY_HOLD')
    return {'base_commit':BASE,'base_manifest_git_blob':BASE_MANIFEST,
            'status':'REVIEW_ONLY_NOT_APPLIED','base_rows':before,'changes':changes}


def overlay(base, delta):
    """Pure manifest transformation. Input bytes must be pinned by caller."""
    if delta['base_commit']!=BASE or delta['base_manifest_git_blob']!=BASE_MANIFEST or delta['status']!='REVIEW_ONLY_NOT_APPLIED':
        raise ValueError('DELTA_HOLD')
    original=base['files']
    if len(original)!=504: raise ValueError('MANIFEST_COUNT_HOLD')
    for path,expected in delta['base_rows'].items():
        if original.get(path)!=expected: raise ValueError('MANIFEST_ROW_HOLD')
    entries=dict(original)
    for path,change in delta['changes'].items():
        old=change['before']
        if (old is None and path in entries) or (old is not None and entries.get(path)!=old):
            raise ValueError('MANIFEST_COLLISION_HOLD')
        entries[path]=change['after']
    if len(entries)!=508: raise ValueError('MANIFEST_RESULT_HOLD')
    return {**base,'doc_revision':'ORG-07C-R2-REVIEW','status':'D0_REVIEW_ONLY_NOT_APPLIED',
            'parent_candidate_sha256':None,'parent_git_commit':BASE,'source_git_commit':None,
            'parent_source_manifest_blob':BASE_MANIFEST,'additional_parent_git_commit':None,
            'additional_parent_source_manifest_blob':None,
            'source_git_commit_note':'Review-only seven-path overlay. No complete byte audit, backend registration, IAM, runtime acceptance or product promotion.',
            'files':dict(sorted(entries.items()))}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True,help='new review output outside product')
    p.add_argument('--manifest',type=Path,help='exact original Unified U3A manifest, optional')
    a=p.parse_args(); delta=review_delta(a.candidate)
    if a.manifest:
        raw=a.manifest.read_bytes()
        if git_blob(raw)!=BASE_MANIFEST: raise ValueError('MANIFEST_PIN_HOLD')
        result=overlay(json.loads(raw),delta)
    else: result=delta
    if 'product' in a.output.resolve().parts: raise ValueError('PRODUCT_WRITE_HOLD')
    with a.output.open('x',encoding='utf-8') as f: f.write(json.dumps(result,indent=2,ensure_ascii=False)+'\n')


if __name__=='__main__': main()
