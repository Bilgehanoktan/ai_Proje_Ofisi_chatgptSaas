"""ORG-05R5R3: explicit local disposable fixture launcher, never a product migration."""
import argparse
import ctypes
import hashlib
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile

CLUSTER = 'aicos_org_r5_disposable'
ADMIN = 'org_r5_admin'
DATABASE = 'aicos_org_r4_disposable'
REVIEW_SHA256 = 'c5bad78cf6c139a40f012eb986a1f0993b3d904a7f786664f8ef1ff4e921550e'

class Hold(RuntimeError):
    pass

def require(condition, reason):
    if not condition:
        raise Hold(reason)

def safe_env():
    # Do not inherit libpq connection/service/password variables or Python import overrides.
    return {**{k:v for k,v in os.environ.items() if not k.upper().startswith(('PG','PYTHON'))}, 'PGCLIENTENCODING':'UTF8'}

def non_admin():
    if os.name == 'nt':
        return not bool(ctypes.windll.shell32.IsUserAnAdmin())
    return hasattr(os, 'geteuid') and os.geteuid() != 0

def executable(directory, name):
    path = directory / (name + ('.exe' if os.name == 'nt' else ''))
    require(path.is_file(), 'MISSING_PG_BINARY_'+name.upper())
    return str(path)

def validate_port(port):
    require(type(port) is int and 1024 <= port <= 65535 and port not in (5432,55433), 'PORT_RESERVED_OR_INVALID')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try: s.bind(('127.0.0.1',port))
        except OSError as exc: raise Hold('PORT_IN_USE') from exc

def child(args, *, capture=False, timeout=None):
    try:
        result=subprocess.run(args, env=safe_env(), check=False, text=True, encoding='utf-8', errors='replace', stdout=subprocess.PIPE if capture else None, timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise Hold('CHILD_EXECUTION_HOLD') from exc
    require(result.returncode==0, 'CHILD_EXIT_'+str(result.returncode))
    return result.stdout if capture else None

def verify_reviewer(path):
    require(path.is_file() and not path.is_symlink(), 'R5R2_REVIEW_MISSING')
    require(hashlib.sha256(path.read_bytes()).hexdigest()==REVIEW_SHA256, 'R5R2_REVIEW_HASH')

def verify_version(binary):
    out=child([binary,'--version'],capture=True,timeout=10)
    require(type(out) is str and re.search(r'\b17(?:\.\d+)+(?:\s|$)',out) is not None, 'PG17_REQUIRED')

def verify_driver():
    result=child([sys.executable,'-E','-c','import psycopg; print(psycopg.__version__)'],capture=True,timeout=15)
    require(result.strip()=='3.3.9','PSYCOPG_3_3_9_REQUIRED')

def verify_location(raw,data):
    rows=raw.strip().splitlines()
    require(len(rows)==1,'CLUSTER_QUERY_SHAPE')
    parts=rows[0].split('\t')
    require(len(parts)==4,'CLUSTER_QUERY_SHAPE')
    cluster, version, role, actual=parts
    require(cluster==CLUSTER and re.fullmatch(r'17[0-9]{4}',version) and role==ADMIN,'CLUSTER_IDENTITY')
    require(Path(actual).resolve()==data.resolve(),'CLUSTER_DATA_DIRECTORY')

def launch(candidates, pg_bin, stage_parent, port):
    require(non_admin(),'NON_ADMIN_OS_ACCOUNT_REQUIRED')
    candidates=candidates.resolve(); pg_bin=pg_bin.resolve(); stage_parent=stage_parent.resolve()
    require(stage_parent.is_dir(),'STAGE_PARENT_MISSING')
    r5=candidates/'ORG-05R5'; r4=candidates/'ORG-05R4'; r2=candidates/'ORG-05R5R2'
    review=r2/'review_pg_evidence.py'
    verify_reviewer(review)
    # Source checkout remains untouched. The verifier does not establish custody.
    child([sys.executable,'-E',str(review),'--candidates',str(candidates)],timeout=30)
    verify_driver()
    binaries={name:executable(pg_bin,name) for name in ('postgres','initdb','pg_ctl','psql')}
    for binary in binaries.values(): verify_version(binary)
    validate_port(port)
    stage=Path(tempfile.mkdtemp(prefix='aicos_org_r5_',dir=stage_parent)).resolve()
    data=stage/'data'; report=stage/'ORG_R5_PG_RESULT.json'; log=stage/'server.log'
    print('NEW_DISPOSABLE_STAGE:',stage,flush=True)
    print('Keep paths and credentials local; no automatic retry or deletion.',flush=True)
    # All mutation below is scoped to this newly created directory and fixed loopback port.
    child([binaries['initdb'],'-D',str(data),'--username='+ADMIN,'--auth=scram-sha-256','--pwprompt'])
    # Recheck before starting, but port binding remains a race; pg_ctl failure stops the flow.
    validate_port(port)
    child([binaries['pg_ctl'],'-D',str(data),'-l',str(log),'-o',f'-p {port} -h 127.0.0.1 -c cluster_name={CLUSTER}','-w','-t','30','start'],timeout=45)
    psql=[binaries['psql'],'-X','-W','-v','ON_ERROR_STOP=1','-h','127.0.0.1','-p',str(port),'-U',ADMIN]
    query="SELECT current_setting('cluster_name'),current_setting('server_version_num'),current_user,current_setting('data_directory');"
    actual=child(psql+['-d','postgres','-At','-F','\t','-c',query],capture=True)
    verify_location(actual,data)
    child(psql+['-d','postgres','-f',str(r5/'bootstrap_roles.sql')])
    child(psql+['-d',DATABASE,'-f',str(r4/'PG_SCHEMA_R4.sql')])
    child([sys.executable,'-E',str(r5/'run_pg_acceptance.py'),'--execute-disposable','--port',str(port),'--report',str(report)])
    child([sys.executable,'-E',str(review),'--candidates',str(candidates),'--report',str(report)],timeout=30)
    # Successful reviewed-format run only; a failure preserves stage and logs for manual review.
    child([binaries['pg_ctl'],'-D',str(data),'-w','-t','30','stop','-m','fast'],timeout=45)
    print('REPORT_COMPLETE_UNATTESTED; PRODUCT_HOLD',flush=True)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidates',type=Path,required=True)
    p.add_argument('--pg-bin',type=Path,required=True)
    p.add_argument('--stage-parent',type=Path,required=True)
    p.add_argument('--port',type=int,default=55435)
    p.add_argument('--execute-disposable',action='store_true')
    a=p.parse_args()
    if not a.execute_disposable: p.error('Explicit --execute-disposable required')
    try:
        launch(a.candidates,a.pg_bin,a.stage_parent,a.port)
    except (Hold,OSError,KeyboardInterrupt) as exc:
        print('HOLD:',str(exc) if isinstance(exc,Hold) else type(exc).__name__,file=sys.stderr)
        print('Preserve any printed stage; do not retry or delete. Review locally before stopping only that cluster.',file=sys.stderr)
        return 2
    return 0

if __name__=='__main__':
    raise SystemExit(main())
