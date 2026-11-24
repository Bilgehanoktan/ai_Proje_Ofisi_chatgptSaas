"""Run the original 13 D0 PostgreSQL cases, only on explicit disposable local DBs.
No install, DB creation, CI, remote access, or RLS/production acceptance.
Requires a clean authenticated checkout and separately supplied two DSNs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

DDL_PINS = {
    'database/0192/candidate_event_outbox_fence.sql': '6e4780bf9f267c0926b40d582d5afdbd6faa543c',
    'database/0193/candidate_run_head.sql': '180924e97ee1f31fa27332941a41e37fdf73017e',
    'database/0194/candidate_transition_roles.sql': '7b5d374bb7973b283e4fcfa0d796ed6128ef9d27',
    'database/0195/candidate_admission_budget.sql': 'd5dc6abc045da14ef42e88b4e85e50e9062a1b27',
    'database/0196L/candidate_lease_settlement.sql': 'e4c9a84ff705c39486579c393b1f3aaef9e34da9',
}
SUITES = (
    ('0194', 'AICOS_PG_0194_DSN', '0194_DISPOSABLE_LOCAL_ONLY', 'aicos_d0_0194_', 'test_pg_transition_mapping_0194', 5),
    ('0196L', 'AICOS_PG_0196L_DSN', '0196L_DISPOSABLE_LOCAL_ONLY', 'aicos_d0_0196l_', 'test_pg_lifecycle_mapping_0196', 5),
    ('0200S', 'AICOS_PG_0196L_DSN', '0196L_DISPOSABLE_LOCAL_ONLY', 'aicos_d0_0196l_', 'test_pg_snapshot_0200', 3),
)
MARKER = 'AICOS_PG_RESULT='
CHILD = r'''
import json, sys, unittest
suite=unittest.defaultTestLoader.loadTestsFromName(sys.argv[1])
result=unittest.TextTestRunner(verbosity=0).run(suite)
print('AICOS_PG_RESULT='+json.dumps({'ran':result.testsRun,'failures':[t.id() for t,_ in result.failures], 'errors':[t.id() for t,_ in result.errors], 'skips':[t.id() for t,_ in result.skipped], 'expected_failures':len(result.expectedFailures), 'unexpected_successes':len(result.unexpectedSuccesses)}))
sys.exit(0 if result.wasSuccessful() else 1)
'''


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()


def check_ddl(root):
    for name, pin in DDL_PINS.items():
        p = root / name
        if p.resolve() != p or not p.is_file() or blob(p.read_bytes()) != pin:
            raise ValueError('DDL_PIN_HOLD: '+name)


def validate_info(info, prefix):
    # Strict allowlist: libpq can otherwise source service/hostaddr/options externally.
    if not isinstance(info, dict) or set(info) - {'host','port','dbname','user','password','sslmode','connect_timeout'}:
        raise ValueError('PG_DSN_OPTIONS_HOLD')
    if info.get('host') not in ('127.0.0.1','::1') or not re.fullmatch(re.escape(prefix)+r'[a-z0-9_]{1,32}', info.get('dbname','')):
        raise ValueError('PG_LOCAL_DISPOSABLE_NAME_HOLD')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,62}',info.get('user','')):
        raise ValueError('PG_EXPLICIT_ROLE_HOLD')
    port = info.get('port','5432')
    if not isinstance(port,str) or not port.isdecimal() or not 1<=int(port)<=65535:
        raise ValueError('PG_PORT_HOLD')
    if info.get('sslmode','disable') != 'disable' or info.get('connect_timeout','3') not in ('1','2','3','4','5'):
        raise ValueError('PG_DSN_PROFILE_HOLD')
    return info['dbname'], info['user']


def child_env(source, dsn, ack, backend):
    # Don't forward caller PG*, Python path, API keys, or any other credentials.
    keep={'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','TMPDIR','LANG','LC_ALL','LC_CTYPE','LD_LIBRARY_PATH','DYLD_LIBRARY_PATH'}
    env={k:v for k,v in source.items() if k.upper() in keep}
    # Explicitly turn off automatic libpq credential/service discovery.
    env.update(PGPASSFILE=os.devnull,PGSERVICEFILE=os.devnull,PGSSLMODE='disable',
               PYTHONPATH=os.pathsep.join((str(backend),str(backend/'tests'))),
               PYTHONDONTWRITEBYTECODE='1',AICOS_D0_PG_DSN=dsn,AICOS_D0_PG_ACK=ack)
    return env


def classify(proc, expected):
    lines=[s[len(MARKER):] for s in proc.stdout.splitlines() if s.startswith(MARKER)]
    if len(lines)!=1:
        return {'status':'HOLD','reason':'RESULT_MISSING_OR_AMBIGUOUS','ran':None}
    try:
        r=json.loads(lines[0])
        if set(r)!={'ran','failures','errors','skips','expected_failures','unexpected_successes'} or type(r['ran']) is not int or r['ran']<0:
            raise ValueError
        if any(type(r[k]) is not list or any(type(x) is not str for x in r[k]) for k in ('failures','errors','skips')) or any(type(r[k]) is not int or r[k]<0 for k in ('expected_failures','unexpected_successes')):
            raise ValueError
    except (ValueError,TypeError,AttributeError):
        return {'status':'HOLD','reason':'RESULT_INVALID','ran':None}
    passed=proc.returncode==0 and r['ran']==expected and not any(r[k] for k in ('failures','errors','skips','expected_failures','unexpected_successes'))
    return {'status':'PASS' if passed else 'HOLD','ran':r['ran'],
            'failures':len(r['failures']),'errors':len(r['errors']),'skips':len(r['skips']),
            'expected_failures':r['expected_failures'],'unexpected_successes':r['unexpected_successes']}


def run(root, manifest, env, *, execute=False):
    report={'revision':'0215','status':'HOLD','source_verified':False,'ddl_verified':False,
            'actual_pg':'NOT_RUN','rls':'NOT_RUN','independent_acceptance':'HOLD','suites':[]}
    # Do not inspect or contact the DB before authenticated source and explicit opt-in.
    try:
        from verify_product import verify
        if not re.fullmatch(r'[a-f0-9]{40}',manifest): raise ValueError('MANIFEST_PIN_HOLD')
        result=verify(root,manifest); report['source_verified']=True; report['source_files']=result['verified_files']
        check_ddl(root);report['ddl_verified']=True
    except (OSError,ValueError,KeyError,TypeError,AttributeError,ImportError):
        report['reason']='SOURCE_OR_DDL_HOLD';return report
    if not execute or env.get('AICOS_PG_RUN_ACK')!='0215_DISPOSABLE_LOCAL_ONLY':
        report['reason']='EXPLICIT_EXECUTION_ACK_REQUIRED';return report
    try:
        from psycopg.conninfo import conninfo_to_dict, make_conninfo
    except ImportError:
        report['reason']='PSYCOPG_MISSING';return report
    dsns={}
    try:
        for _, key, _, prefix, _, _ in SUITES:
            info=conninfo_to_dict(env.get(key,''));validate_info(info,prefix)
            info.update(sslmode='disable',connect_timeout='3',port=info.get('port','5432'))
            dsns[key]=make_conninfo(**info)
    except Exception:
        report['reason']='DISPOSABLE_DSN_HOLD';return report
    backend=root/'product/ai-company-os-backend'
    for label,key,ack,_,module,n in SUITES:
        try:
            proc=subprocess.run([sys.executable,'-B','-c',CHILD,module],cwd=backend,
                env=child_env(env,dsns[key],ack,backend),capture_output=True,text=True,timeout=120,check=False)
            outcome=classify(proc,n)
        except (OSError,subprocess.TimeoutExpired,UnicodeError):
            outcome={'status':'HOLD','reason':'CHILD_TIMEOUT_OR_IO','ran':None}
        report['suites'].append({'suite':label,'expected':n,**outcome})
        if outcome['status']!='PASS':
            report['actual_pg']='ATTEMPTED_HOLD';report['reason']='SUITE_NOT_PASS';return report
    report['actual_pg']='13/13_PASS';report['status']='D0_PG_DIAGNOSTIC_PASS'
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--manifest-blob',required=True)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--execute',action='store_true')
    a=p.parse_args();r=run(a.root.resolve(),a.manifest_blob,os.environ,execute=a.execute)
    # No DSN, password, raw child error, or connection string written.
    a.report.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))
    return 0 if r['status']=='D0_PG_DIAGNOSTIC_PASS' else 1


if __name__=='__main__':raise SystemExit(main())
