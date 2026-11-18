"""D5-C-R4: actual PG transport diagnostic, not IAM/T1 acceptance."""
import argparse
from contextlib import closing
from getpass import getpass
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import types
from unittest.mock import patch

PIN = '8e65e4575a77b11c38c2d2e62ec91fc89d75e23c'
SCHEMA = 'd5c_r4_probe'


def load_transport(path):
    raw = path.read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() != PIN:
        raise ValueError('SOURCE_PIN_HOLD')
    port = types.ModuleType('app.core.transaction.port')
    port.CommitReceipt = type('CommitReceipt', (), {})  # annotation only
    spec = importlib.util.spec_from_file_location('d5c_transport', path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'app.core.transaction.port': port}):
        spec.loader.exec_module(module)
    return module


def validate_target(port, db, role):
    if (type(port) is not int or not 1024 <= port <= 65535
            or port in {5432, 55432, 55434, 55435, 55436}
            or not re.fullmatch(r'd5c_r4_[a-z0-9_]{1,40}', db)
            or not re.fullmatch(r'd5c_r4_[a-z0-9_]{1,40}', role)):
        raise ValueError('FRESH_ISOLATED_TARGET_REQUIRED')


SETUP = (
    'CREATE SCHEMA d5c_r4_probe',
    '''CREATE TABLE d5c_r4_probe.observation(
        id text PRIMARY KEY, mode text NOT NULL, deadline timestamptz NOT NULL,
        body_at timestamptz NOT NULL, deferred_at timestamptz)''',
    '''CREATE FUNCTION d5c_r4_probe.check_at_end() RETURNS trigger
       LANGUAGE plpgsql AS $$ BEGIN
         IF NEW.mode IN ('late','guard') THEN
           PERFORM pg_catalog.pg_sleep(2.5);
         END IF;
         IF NEW.mode = 'guard' AND pg_catalog.clock_timestamp() >= NEW.deadline THEN
           RAISE EXCEPTION 'D5C_R4_EXPIRED' USING ERRCODE='P0001';
         END IF;
         UPDATE d5c_r4_probe.observation SET deferred_at=pg_catalog.clock_timestamp()
           WHERE id=NEW.id;
         RETURN NEW;
       END; $$''',
    '''CREATE CONSTRAINT TRIGGER expiry_probe AFTER INSERT ON d5c_r4_probe.observation
       DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
       EXECUTE FUNCTION d5c_r4_probe.check_at_end()''',
)


def run(args, report):
    import psycopg
    transport = load_transport(Path(__file__).with_name('postgres_session.original.py'))
    password = getpass('Disposable PostgreSQL role password: ')

    def connect():
        c = psycopg.connect(host='127.0.0.1', port=args.port, dbname=args.db,
                            user=args.role, password=password, sslmode='disable',
                            connect_timeout=5, options='-c search_path=pg_catalog -c statement_timeout=15000')
        try:
            with c.cursor() as cur:
                cur.execute('''SELECT current_database(), current_user, session_user,
                  inet_server_addr()::text, inet_server_port(), current_setting('server_version_num'),
                  rolsuper, rolbypassrls, rolcreaterole, rolcreatedb, rolreplication,
                  (SELECT count(*) FROM pg_auth_members WHERE member=r.oid),
                  (SELECT datdba=r.oid AND NOT datistemplate FROM pg_database WHERE datname=current_database())
                  FROM pg_roles r WHERE rolname=current_user''')
                facts = cur.fetchone()
            if facts != (args.db, args.role, args.role, '127.0.0.1/32', args.port, '170012',
                          False, False, False, False, False, 0, True) and facts != (
                          args.db, args.role, args.role, '127.0.0.1', args.port, '170012',
                          False, False, False, False, False, 0, True):
                raise ValueError('SERVER_IDENTITY_HOLD')
            c.rollback()
            return c
        except BaseException:
            c.close()
            raise

    with closing(connect()) as c:
        with c.cursor() as cur:
            cur.execute('''SELECT nspname FROM pg_namespace WHERE nspname NOT IN
                ('pg_catalog','information_schema','public') AND left(nspname,3) <> 'pg_' ''')
            if cur.fetchall():
                raise ValueError('NONEMPTY_DATABASE_HOLD')
            cur.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public'")
            if cur.fetchone() != (0,):
                raise ValueError('NONEMPTY_PUBLIC_HOLD')
            for sql in SETUP:
                cur.execute(sql)
        c.commit()
    report['schema_created'] = True
    for case, mode, seconds, expected in (
        ('PG01','valid',30,'COMMIT_VALID'), ('PG02','expired',-1,'BODY_REJECTED'),
        ('PG03','late',1,'COMMIT_LATE'), ('PG04','guard',1,'UNKNOWN_ZERO_READBACK')):
        rec = {'id':case, 'status':'FAIL'}
        report['cases'].append(rec)
        outcome = 'COMMIT'
        try:
            with transport.postgres_transaction(connect, None) as session:
                cur = session.cursor
                cur.execute("SELECT clock_timestamp() + (%s * interval '1 second')", (seconds,))
                deadline = cur.fetchone()[0]
                cur.execute('SELECT clock_timestamp()')
                body_at = cur.fetchone()[0]
                rec['body_before_deadline'] = body_at < deadline
                if body_at >= deadline:
                    raise ValueError('BODY_EXPIRED')
                cur.execute('INSERT INTO d5c_r4_probe.observation VALUES (%s,%s,%s,%s,NULL)',
                            (case,mode,deadline,body_at))
                cur.execute('SELECT clock_timestamp()')
                precommit_at = cur.fetchone()[0]
                rec['precommit_at'] = precommit_at.isoformat()
                rec['precommit_before_deadline'] = precommit_at < deadline
                if precommit_at >= deadline:
                    raise RuntimeError('PRECOMMIT_TIMING_HOLD')
        except ValueError as exc:
            if str(exc) != 'BODY_EXPIRED':
                raise
            outcome = 'BODY_REJECTED'
        except transport.CommitOutcomeUnknown as exc:
            outcome = 'UNKNOWN'
            rec['sqlstate'] = getattr(exc.__cause__, 'sqlstate', None)
            rec['expected_guard_error'] = getattr(getattr(exc.__cause__, 'diag', None), 'message_primary', None) == 'D5C_R4_EXPIRED'
        with closing(connect()) as c:
            with c.cursor() as cur:
                cur.execute('SELECT body_at, deadline, deferred_at FROM d5c_r4_probe.observation WHERE id=%s', (case,))
                rows = cur.fetchall()
        rec['outcome'] = outcome
        rec['readback_rows'] = len(rows)
        if len(rows) == 1:
            body, limit, deferred = rows[0]
            rec['body_at'], rec['deadline'], rec['deferred_at'] = body.isoformat(), limit.isoformat(), deferred.isoformat() if deferred else None
            if outcome == 'COMMIT' and deferred is not None and body < limit and rec.get('precommit_before_deadline'):
                outcome = 'COMMIT_LATE' if deferred >= limit else 'COMMIT_VALID'
        elif outcome == 'UNKNOWN' and not rows and rec.get('sqlstate') == 'P0001' and rec.get('expected_guard_error') and rec.get('body_before_deadline') and rec.get('precommit_before_deadline'):
            outcome = 'UNKNOWN_ZERO_READBACK'
        if outcome == 'BODY_REJECTED' and (rows or rec.get('body_before_deadline') is not False):
            outcome = 'UNEXPECTED_BODY_OUTCOME'
        rec['observed'] = outcome
        if outcome != expected:
            raise RuntimeError('CASE_MISMATCH_'+case)
        rec['status'] = 'PASS_DIAGNOSTIC'
    with closing(connect()) as c:
        with c.cursor() as cur:
            cur.execute('DROP SCHEMA d5c_r4_probe CASCADE')
        c.commit()
    with closing(connect()) as c:
        with c.cursor() as cur:
            cur.execute("SELECT to_regnamespace('d5c_r4_probe') IS NULL")
            if cur.fetchone() != (True,):
                raise RuntimeError('CLEANUP_HOLD')
    report['cleanup_verified'] = True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',type=int,required=True)
    p.add_argument('--db',required=True)
    p.add_argument('--role',required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--isolated-d0',action='store_true',required=True)
    a = p.parse_args()
    validate_target(a.port,a.db,a.role)
    load_transport(Path(__file__).with_name('postgres_session.original.py'))
    a.out.mkdir(parents=True,exist_ok=False)
    report = {'classification':'PG_TRANSPORT_DIAGNOSTIC_ONLY','source_pin':PIN,'cases':[],
              'schema_created':False,'cleanup_verified':False,'activation':'HOLD','status':'FAIL'}
    try:
        run(a,report)
        report['status'] = 'PASS_DIAGNOSTIC'
    except BaseException as exc:
        report['error_class'] = type(exc).__name__  # no DSN or credential in output
    finally:
        (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return 0 if report['status'] == 'PASS_DIAGNOSTIC' else 2


if __name__ == '__main__':
    sys.exit(main())
