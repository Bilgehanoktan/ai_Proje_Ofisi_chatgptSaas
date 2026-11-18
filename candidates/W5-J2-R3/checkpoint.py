"""J2-R3 local checkpoint. No PostgreSQL connection, migration, test runner or authority.
Original R2 plan is an inventory, not executable tests. A local preflight cannot promote J2.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

PLAN_SHA = 'aa354b3149b563fd1968653590947f98f03fbdc44dc48ab9b008e28ed2b32823'
PLAN_IDS = tuple(f'J2-PG-{i:02}' for i in range(1,23))
BLOCKERS = ('R03_OWNER_DECISION_NOT_SUPPLIED','INVOCATION_OPERATION_NOT_SUPPORTED',
            'LEGACY_TERMINAL_RELEASE_INCOMPATIBLE','RUN_SCOPED_CLAIM_AND_JOURNAL',
            'D5_PROTECTED_READER_DIAGNOSTIC_ONLY','OWNER_PG_TEST_IMPLEMENTATION_NOT_SUPPLIED',
            'APPROVED_DISPOSABLE_PG_ENDPOINT_NOT_SUPPLIED','INDEPENDENT_ACCEPTANCE_NOT_SUPPLIED')


def _unique_pairs(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise ValueError('DUPLICATE_JSON_KEY_HOLD')
        result[k]=v
    return result


def verify_plan(raw):
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=PLAN_SHA:
        raise ValueError('PG_PLAN_PIN_HOLD')
    p=json.loads(raw,object_pairs_hook=_unique_pairs)
    cases=p['cases']
    if p['status']!='NOT_RUN' or tuple(c['id'] for c in cases)!=PLAN_IDS or any(c['status']!='NOT_RUN' for c in cases):
        raise ValueError('PG_PLAN_INVENTORY_HOLD')
    return cases


def verify_parent_manifests(root):
    total=0
    for rev,count,pin in [('R1',9,'4620e3f6ec33041d4bce192d92a4a99b7036683c9ae4de94978de56bf327ee25'),
                          ('R2',10,'7d374aa372f44a343732895a7baed1bd4d04d7dc80d60ab09501c1bb831b7b0b')]:
        p=Path(root)/('W5-J2-'+rev)
        raw_manifest=(p/'SOURCE_MANIFEST.json').read_bytes()
        if hashlib.sha256(raw_manifest).hexdigest()!=pin: raise ValueError('PARENT_MANIFEST_PIN_HOLD')
        manifest=json.loads(raw_manifest,object_pairs_hook=_unique_pairs)
        if len(manifest)!=count: raise ValueError('PARENT_MANIFEST_COUNT_HOLD')
        for name, expected in manifest.items():
            if Path(name).name!=name or name in ('.','..') or (p/name).is_symlink(): raise ValueError('PARENT_PATH_HOLD')
            raw=(p/name).read_bytes()
            if len(raw)!=expected['bytes'] or hashlib.sha256(raw).hexdigest()!=expected['sha256']:
                raise ValueError('PARENT_SOURCE_PIN_HOLD')
            total+=1
    return total


def local_checkpoint(root):
    cases=verify_plan((Path(root)/'W5-J2-R2'/'PG_ACCEPTANCE_PLAN.json').read_bytes())
    count=verify_parent_manifests(root)
    tools={name:shutil.which(name) is not None for name in ('psql','postgres','docker','podman')}
    drivers={name:importlib.util.find_spec(name) is not None for name in ('psycopg','psycopg2')}
    return {'decision':'HOLD','status':'BLOCKED','parent_manifest_verified':count,
            'pg_inventory_count':len(cases),'pg_executed':0,'pg_passed':0,
            'pg_cases':[{**c,'status':'NOT_RUN'} for c in cases],
            'tools':tools,'drivers':drivers,'approved_endpoint_supplied':False,
            'owner_approval_supplied':False,'blockers':list(BLOCKERS),
            'provider_call_allowed':False,'spend_allowed':False,'retry_allowed':False,
            'settlement_allowed':False,'commit_allowed':False,'independent_accepted':False}

if __name__=='__main__':
    try:
        print(json.dumps(local_checkpoint(Path(__file__).resolve().parent.parent),indent=2))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'BLOCKED','decision':'HOLD','error_type':type(exc).__name__}))
    raise SystemExit(2)
