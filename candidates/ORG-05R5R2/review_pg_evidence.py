"""Offline ORG-05R5 evidence gate. Never executes SQL or promotes product acceptance."""
import argparse
import hashlib
import json
import re
from pathlib import Path

PARENT = 'a49c20d8e0e9d1e69400a710385a5434b43f577c'
MANIFEST = 'd271153aa3d3b1dfd947f076f3809cccd9cb305d817af0d45c15e10dd9b689c6'
SCHEMA = 'f5ebb556ccc9b37a0f2bd0e05f36c7cf85a5bd54de9c1d0244845f146f7b3731'
DRIVER = '3.3.9'
R3_PINS = {
    'durable_ops.py': 'c68f07b1f802983ba87f3486ce51d330e7e4b3a59c4fc98ff7f80de3a5d6bdb1',
    'integration_guard.py': '3fba6f345356725be61f8d7aa5460a95f0a376705fc8dfefe37d3c7686c55042',
    'office_bridge.py': 'e8a2eb953313bc2342fa9c0264358ab6eda16eb6a40b0a36036d2a04991615a3',
    'operations.py': 'ac57a06a9f0c6a9b6a9886f04456962582f8aa080478a95654a2e1032c66e82b',
    'org_model.py': 'a864d7bd6f1ca1fe17095c953529dc739f95ad2073e121bdb90014d1a16ea46e',
    'persistence.py': 'beffb280340c1c3da13f13248d5049d6d51d87ad05e5448a3373168919ecfd34',
    'staffing.py': '51131102e6c601c2efaf6ec18e430b87dd221edec9650d9c8391a3bcff131d32',
}
IDS = tuple('PG%02d_%s' % (i, name) for i, name in enumerate('FRESH_AND_RLS_INVENTORY GENESIS_RACE OTHER_SCOPE_GENESIS TEAM ATOMIC_ROLLBACK LOCK_ISOLATION HANDOFF_CAS_RACE STALE_HISTORY DELEGATION REOPEN_HISTORY CROSS_SCOPE_READ FOREIGN_TENANT FOREIGN_COMPANY FOREIGN_ENV CROSS_SCOPE_FK IMMUTABLE_UPDATE IMMUTABLE_DELETE READER_UNMAPPED_DENIED REFERENCE_MISMATCH REVISION_SUCCESSOR STALE_REVISION ARCHIVED_HISTORY STALE_HEAD READER_CURRENT READER_STALE_HEAD FINAL_COUNTS'.split(), 1))
R5_FILES = frozenset('ACCEPTANCE_MATRIX.json ARCHITECTURE_DELTA.md CATALOG.json HANDOVER.md RUNBOOK.md TEST_EVIDENCE.json bootstrap_roles.sql pg_operations.py pg_transaction.py run_pg_acceptance.py test_pg_protocol.py test_protocol.log'.split())

class ReviewHold(ValueError):
    pass

def require(ok, code):
    if not ok:
        raise ReviewHold(code)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def pinned_file(path, expected):
    require(path.is_file() and not path.is_symlink(), 'SOURCE_MISSING')
    require(sha(path.read_bytes()) == expected, 'SOURCE_HASH_MISMATCH')

def verify_sources(candidates):
    """Check 12 R5, 7 R3, 1 R4 files against independently embedded pins."""
    r5 = candidates / 'ORG-05R5'
    manifest = r5 / 'SHA256SUMS'
    pinned_file(manifest, MANIFEST)
    seen = set()
    for line in manifest.read_text(encoding='utf-8').splitlines():
        m = re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9_.-]+)', line)
        require(m is not None, 'MANIFEST_FORMAT')
        digest, name = m.groups()
        require(name in R5_FILES and name not in seen, 'MANIFEST_PATH')
        pinned_file(r5 / name, digest)
        seen.add(name)
    require(seen == R5_FILES, 'MANIFEST_INVENTORY')
    for name, digest in R3_PINS.items():
        pinned_file(candidates / 'ORG-05R3' / name, digest)
    pinned_file(candidates / 'ORG-05R4' / 'PG_SCHEMA_R4.sql', SCHEMA)
    return 20

def unique_object(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, 'DUPLICATE_JSON_KEY')
        result[k] = v
    return result

def no_constant(value):
    raise ReviewHold('NONFINITE_JSON')

def valid_hex(x):
    return type(x) is str and re.fullmatch('[0-9a-f]{64}', x) is not None

def check_detail(i, detail):
    """Critical independently checkable details emitted by the pinned R5 runner."""
    if i == 1:
        require(detail == {'tables': 12, 'policies': 25, 'cluster': 'aicos_org_r5_disposable'}, 'PG01_DETAIL')
    elif i == 2:
        require(type(detail) is dict and set(detail) == {'revision','loser'} and valid_hex(detail['revision']) and detail['loser'] in [['hold','STALE_HEAD'],['sqlstate','23505']], 'PG02_DETAIL')
    elif i == 5:
        require(detail == {'sqlstate':'23514','counts':[0,0]}, 'PG05_DETAIL')
    elif i == 6:
        require(detail == {'same_scope':'55P03','other_scope':'PASS'}, 'PG06_DETAIL')
    elif i == 7:
        require(type(detail) is dict and set(detail) == {'count','head','loser'} and type(detail['count']) is int and detail['count']==1 and valid_hex(detail['head']) and detail['loser']==['hold','HISTORY_CAS'], 'PG07_DETAIL')
    elif i == 9:
        require(type(detail) is dict and set(detail)=={'count','head'} and type(detail['count']) is int and detail['count']==2 and valid_hex(detail['head']), 'PG09_DETAIL')
    elif i in (3,4,20):
        require(valid_hex(detail), 'DIGEST_DETAIL')
    elif i in (8,12,13,14,15,16,17,19,21,23,25):
        expected = {8:'HISTORY_CAS',12:'42501',13:'42501',14:'42501',15:'23503',16:'42501',17:'42501',19:'TASK_REFERENCE',21:'STALE_ORG',23:'STALE_HEAD',25:'HEAD_MISMATCH'}
        require(detail==expected[i], 'DENIAL_DETAIL')
    elif i == 18:
        require(detail=={'reader':'42501','unmapped':'42501'}, 'PG18_DETAIL')
    else:
        require(detail is None, 'UNEXPECTED_DETAIL')

def inspect_report(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 65536, 'REPORT_SIZE')
    try:
        report = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object, parse_constant=no_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewHold('REPORT_JSON') from exc
    require(type(report) is dict and set(report)=={'profile','source_pins','schema_sha256','driver','checks','status'}, 'REPORT_SHAPE')
    require(report['profile']=='ORG-05R5_DISPOSABLE_ONLY' and report['source_pins']==R3_PINS and report['schema_sha256']==SCHEMA and report['driver']==DRIVER, 'REPORT_PINS')
    rows = report['checks']
    require(type(rows) is list and len(rows)<=len(IDS), 'CHECK_COUNT')
    for i, row in enumerate(rows,1):
        require(type(row) is dict and row.get('id')==IDS[i-1], 'CHECK_ORDER')
        if row.get('status')=='PASS':
            require(set(row)=={'id','status','detail','elapsed_ms'} and type(row['elapsed_ms']) is int and row['elapsed_ms']>=0, 'CHECK_SHAPE')
            check_detail(i,row['detail'])
        else:
            require(row.get('status')=='FAIL' and i==len(rows) and set(row)=={'id','status','error_type','sqlstate'} and type(row['error_type']) is str and (row['sqlstate'] is None or (type(row['sqlstate']) is str and re.fullmatch('[A-Z0-9]{5}', row['sqlstate']))), 'CHECK_FAILURE_SHAPE')
    complete = len(rows)==len(IDS) and all(r['status']=='PASS' for r in rows)
    require(report['status']==('PASS_DISPOSABLE_FIXTURE_ONLY' if complete else 'FAIL_OR_INCOMPLETE'), 'STATUS_CONTRADICTION')
    return {'parent':PARENT,'report_sha256':sha(raw),'reported_checks':len(rows),'reported_pass':sum(r['status']=='PASS' for r in rows),'review':'COMPLETE_REPORT_UNATTESTED' if complete else 'INCOMPLETE_REPORT_HOLD','actual_pg_acceptance':'HOLD','product_acceptance':'HOLD'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidates',type=Path,required=True)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    try:
        count=verify_sources(args.candidates)
        result=inspect_report(args.report.read_bytes()) if args.report else {'review':'SOURCE_PREFLIGHT_ONLY','actual_pg_acceptance':'NOT_RUN','product_acceptance':'HOLD'}
        print(json.dumps({'source_files_verified':count,**result},sort_keys=True))
        return 0 if not args.report or result['review']=='COMPLETE_REPORT_UNATTESTED' else 2
    except (ReviewHold,OSError) as exc:
        print(json.dumps({'review':'HOLD','reason':str(exc) if isinstance(exc,ReviewHold) else 'FILE_IO','actual_pg_acceptance':'HOLD','product_acceptance':'HOLD'},sort_keys=True))
        return 2

if __name__=='__main__':
    raise SystemExit(main())
