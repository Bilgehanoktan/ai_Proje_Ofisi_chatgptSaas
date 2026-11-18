"""D5-C-R5: fresh offline Windows execution of unchanged R4 diagnostic."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PORT = 55437  # proposed; explicit operator allocation at launch only
DB = 'd5c_r4_db'
ROLE = 'd5c_r4_role'
PINS = {'run_pg_expiry.py':'99dbb6320807478a516c726790c02491292739cf',
        'postgres_session.original.py':'8e65e4575a77b11c38c2d2e62ec91fc89d75e23c',
        'run_d1_0227_authfix.py':'d20bbb6740901e2abf02d445b20cfa34f4b93d50'}


def require(ok, code):
    if not ok:
        raise ValueError(code)


def blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def load_inputs(helper):
    for name, pin in PINS.items():
        p = helper if name.startswith('run_d1_') else HERE/name
        require(p.is_file() and blob(p) == pin, 'SOURCE_PIN_HOLD_'+name)
    spec = importlib.util.spec_from_file_location('pinned_d1', helper)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_port(port):
    require(type(port) is int and port == PORT, 'PORT_ALLOCATION_HOLD')
    with socket.socket() as sock:
        if sys.platform == 'win32':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        sock.bind(('127.0.0.1', port))


def check_roots(inputs, root):
    require(inputs.is_dir() and not root.exists() and root.parent.is_dir(), 'FRESH_STAGE_HOLD')
    require(not root.is_relative_to(inputs) and not inputs.is_relative_to(root)
            and not root.is_relative_to(HERE) and not HERE.is_relative_to(root), 'STAGE_OVERLAP_HOLD')


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2); f.write('\n')


def child(root, helper):
    d1 = load_inputs(helper)
    import psycopg
    from psycopg import sql
    import run_pg_expiry as r4
    require(psycopg.__version__ == '3.3.9' and psycopg.pq.__impl__ == 'binary', 'DRIVER_PIN_HOLD')
    creds = json.load(sys.stdin)
    admin, pwd = creds['admin'], creds['test']
    del creds
    with psycopg.connect(host='127.0.0.1', hostaddr='127.0.0.1', port=PORT,
            dbname='postgres', user=d1.ADMIN, password=admin, sslmode='disable',
            connect_timeout=5, passfile=os.devnull, autocommit=True) as c:
        version, addr, port, listen, auth, data = c.execute("SELECT current_setting('server_version_num'), inet_server_addr()::text, inet_server_port(), current_setting('listen_addresses'), current_setting('password_encryption'), current_setting('data_directory')").fetchone()
        require(version == '170012' and addr in ('127.0.0.1','127.0.0.1/32') and port == PORT and listen == '127.0.0.1' and auth == 'scram-sha-256' and Path(data).resolve() == root/'data', 'SERVER_IDENTITY_HOLD')
        rules = c.execute('SELECT DISTINCT auth_method,error FROM pg_hba_file_rules').fetchall()
        require(bool(rules) and all(m == 'scram-sha-256' and e is None for m,e in rules), 'HBA_HOLD')
        verifier = c.pgconn.encrypt_password(pwd.encode(c.info.encoding), ROLE.encode(c.info.encoding), b'scram-sha-256').decode('ascii')
        require(verifier.startswith('SCRAM-SHA-256$'), 'SCRAM_HOLD')
        c.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD {}').format(sql.Identifier(ROLE),sql.Literal(verifier)))
        c.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(DB),sql.Identifier(ROLE)))
    del admin, verifier
    write(root/'profile.json', {'server_version_num':version,'port':port,'address':addr,'scram':True,'fresh_data_directory_match':True,'psycopg':psycopg.__version__,'pq_impl':psycopg.pq.__impl__,'libpq':psycopg.pq.version()})
    # Only inject credential input; original SQL, transport, outcome and checks unchanged.
    with patch.object(r4, 'getpass', return_value=pwd), patch.object(sys, 'argv', ['run_pg_expiry.py','--isolated-d0','--port',str(PORT),'--db',DB,'--role',ROLE,'--out',str(root/'pg_evidence')]):
        return r4.main()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path)
    p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--helper',type=Path,default=HERE/'run_d1_0227_authfix.py')
    p.add_argument('--port',type=int,default=PORT)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--child',action='store_true',help=argparse.SUPPRESS)
    a = p.parse_args()
    require(sys.platform == 'win32' and sys.version.split()[0] == '3.14.3', 'WINDOWS_PYTHON_PIN_HOLD')
    root, helper = a.stage.resolve(), a.helper.resolve()
    if a.child:
        return child(root,helper)
    require(a.inputs is not None,'INPUTS_REQUIRED')
    inputs = a.inputs.resolve()
    check_roots(inputs,root)
    d1 = load_inputs(helper)
    server = inputs/'postgresql-17.12.zip'
    wheels = inputs/'wheels'
    require(d1.sha(d1.safe_file(server)) == d1.SERVER_HASH,'SERVER_HASH_HOLD')
    for n,(_,_,digest) in d1.WHEELS.items():
        require(d1.sha(d1.safe_file(wheels/n)) == digest,'WHEEL_HASH_HOLD')
    check_port(a.port)
    print('PREFLIGHT PASS: exact source, 1 server ZIP, 3 wheels, unused port at check time.')
    if not a.execute:
        return 0
    require(input('Allocate 127.0.0.1:55437 to this disposable D5-C-R5 stage? Type EVET: ') == 'EVET','OWNER_ALLOCATION_HOLD')
    check_port(a.port)
    root.mkdir(); (root/'tmp').mkdir()
    result = {'status':'HOLD','port':PORT,'source_pins':PINS,'server_sha256':d1.SERVER_HASH,'wheel_sha256':{n:v[2] for n,v in d1.WHEELS.items()},'pg_exit':None,'server_stopped':False,'activation':'HOLD'}
    ctl = None; e = None; start_attempted = False
    try:
        e = d1.env_local(root)
        d1.run([sys.executable,'-m','venv',root/'.venv'],root,e,root/'venv-private.log')
        py = root/'.venv/Scripts/python.exe'
        lock = root/'pg.lock'
        lock.write_text(''.join(f'{n}=={v} --hash=sha256:{h}\n' for n,v,h in d1.WHEELS.values()),encoding='ascii')
        d1.run([py,'-m','pip','--isolated','install','--no-index','--find-links',wheels,'--require-hashes','-r',lock],root,e,root/'pip-private.log')
        d1.run([py,'-m','pip','check'],root,e,root/'pipcheck-private.log')
        bindir = d1.extract_archive(server,root/'server'); e = d1.env_local(root,bindir)
        admin, pwd = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        d1.protected_initdb(root,bindir,e,admin)
        with (root/'data/postgresql.conf').open('a',encoding='ascii') as f:
            f.write("\nlisten_addresses = '127.0.0.1'\nport = 55437\nssl = off\npassword_encryption = 'scram-sha-256'\nlog_statement = 'none'\nlog_min_error_statement = panic\n")
        check_port(a.port)
        ctl = bindir/'pg_ctl.exe'; start_attempted = True
        d1.run([ctl,'-D',root/'data','-l',root/'server-private.log','-w','start'],root,e)
        result['pg_exit'] = subprocess.run([str(py),'-B',str(Path(__file__).resolve()),'--child','--stage',str(root),'--helper',str(helper)],cwd=root,env=e,input=json.dumps({'admin':admin,'test':pwd}).encode('ascii')).returncode
        del admin,pwd
    except Exception as exc:
        result['error_class'] = type(exc).__name__
    finally:
        if start_attempted:
            try:
                status = lambda: subprocess.run([str(ctl),'-D',str(root/'data'),'status'],cwd=root,env=e,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
                if status() == 0:
                    d1.run([ctl,'-D',root/'data','-m','fast','-w','stop'],root,e)
                result['server_stopped'] = status() == 3
            except Exception as exc:
                result['stop_error_class'] = type(exc).__name__
        reports = [root/'profile.json',root/'pg_evidence/report.json']
        result['report_sha256'] = {x.relative_to(root).as_posix():d1.sha(x) for x in reports if x.is_file()}
        try:
            load_inputs(helper)
            require(d1.sha(server) == d1.SERVER_HASH and all(d1.sha(wheels/n) == v[2] for n,v in d1.WHEELS.items()),'INPUT_POSTCHECK_HOLD')
            result['inputs_unchanged'] = True
        except Exception:
            result['inputs_unchanged'] = False
        if result['pg_exit'] == 0 and result['server_stopped'] and result['inputs_unchanged'] and len(result['report_sha256']) == 2:
            result['status'] = 'PG_DIAGNOSTIC_PASS_PENDING_RAW_REVIEW'
        write(root/'FINAL.json',result)
        print(result['status'], 'server_stopped=',result['server_stopped'])
    return 0 if result['status'].startswith('PG_DIAGNOSTIC_PASS') else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Exception,KeyboardInterrupt) as exc:
        print('HOLD:', type(exc).__name__, str(exc) if type(exc) is ValueError else 'Preserve stage; inspect privately.',file=sys.stderr)
        sys.exit(2)
