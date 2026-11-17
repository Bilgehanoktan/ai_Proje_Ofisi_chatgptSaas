"""ORG-10 derived R5 fixture transaction boundary; no production authority."""
from dataclasses import dataclass
import re

SCHEMA = 'aicos_org10_fixture'
DATABASE = 'aicos_org10_disposable'
CLUSTER = 'aicos_org10_disposable'
PORT = 55436
WRITERS = {
    'aicos_org10_writer_a': ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY'),
    'aicos_org10_writer_b': ('synthetic-tenant-org10-control', 'synthetic-company-org10-control', 'A0_SAMPLE_ONLY'),
}
READERS = {**WRITERS, 'aicos_org10_reader_a': WRITERS['aicos_org10_writer_a']}
TABLES = frozenset('org_revision org_head org_unit org_position org_definition_ref org_instance_ref org_binding org_notice op_team op_member op_entry op_notice'.split())

class Hold(ValueError):
    pass

class CommitUnknown(Hold):
    """No retry: reconcile independently retained history/head before further writes."""

class CleanupHold(Hold):
    """No successful result returned if cleanup fails; no automatic retry."""


def require(ok, reason):
    if not ok:
        raise Hold(reason)


def context(db, scope, write):
    row = db.execute("SELECT current_database(), current_user, session_user, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole, rolreplication, rolinherit, host(inet_server_addr()), host(inet_client_addr()), current_setting('transaction_isolation'), current_setting('transaction_read_only'), current_setting('cluster_name'), current_setting('server_version_num'), current_setting('port') FROM pg_catalog.pg_roles WHERE rolname=current_user").fetchone()
    require(isinstance(row, (tuple,list)) and len(row)==16, 'PG_CONTEXT')
    allowed = WRITERS if write else READERS
    require(row[0]==DATABASE and row[1]==row[2] and row[1] in allowed and allowed[row[1]]==scope, 'PG_SCOPE_ROLE')
    require(tuple(row[3:9])==(False,)*6 and all(type(v) is bool for v in row[3:9]), 'PG_ROLE_FLAGS')
    require(row[9] in ('127.0.0.1','::1') and row[10] in ('127.0.0.1','::1'), 'PG_LOCAL_ONLY')
    require(tuple(row[11:13])==(('read committed','off') if write else ('repeatable read','on')), 'PG_TX_MODE')
    require(row[13]==CLUSTER and type(row[14]) is str and re.fullmatch(r'17[0-9]{4}',row[14]) is not None, 'PG_CLUSTER_VERSION')
    require(row[15]==str(PORT), 'PG_PORT')
    inventory = db.execute("SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity, r.rolname FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_roles r ON r.oid=c.relowner WHERE n.nspname=%s AND c.relkind='r' ORDER BY c.relname", (SCHEMA,)).fetchall()
    require(len(inventory)==len(TABLES) and {x[0] for x in inventory}==TABLES and all(tuple(x[1:])==(True,True,'aicos_org10_owner') for x in inventory),'PG_RLS_INVENTORY')
    member = db.execute("SELECT count(*) FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.member OR r.oid=m.roleid WHERE r.rolname=current_user").fetchone()
    require(member==(0,), 'PG_ROLE_MEMBERSHIP')
    return tuple(row)


def run(connect, scope, write, operation):
    """Exclusive fresh connection factory, trusted fixture caller only."""
    require(type(scope) is tuple and scope in WRITERS.values() and type(write) is bool, 'PG_SCOPE')
    db = connect()
    committed = False
    commit_started = False
    try:
        require(db.autocommit is False and not isinstance(db.info.transaction_status,bool) and db.info.transaction_status==0, 'PG_FRESH_CONNECTION')
        db.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED READ WRITE' if write else 'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        db.execute("SET LOCAL statement_timeout='5s'")
        db.execute("SET LOCAL lock_timeout='2s'")
        db.execute('SET LOCAL search_path=pg_catalog')
        before = context(db,scope,write)
        value = operation(db)
        require(context(db,scope,write)==before,'PG_CONTEXT_CHANGED')
        if write:
            commit_started = True
            try:
                db.commit()
            except BaseException as exc:
                raise CommitUnknown('PG_COMMIT_UNKNOWN_NO_RETRY') from exc
            committed = True
        else:
            db.rollback()
        return value
    except BaseException:
        if not commit_started:
            try: db.rollback()
            except BaseException as exc: raise CleanupHold('PG_ROLLBACK_FAILED') from exc
        raise
    finally:
        try: db.close()
        except BaseException as exc:
            if commit_started and not committed:
                raise CommitUnknown('PG_COMMIT_UNKNOWN_CLOSE_FAILED') from exc
            raise CleanupHold('PG_CLOSE_FAILED_NO_RETRY') from exc


class R3Read:
    """Adapt only pinned R3 SELECT statements, not arbitrary SQL or writes."""
    def __init__(self, db): self.db = db
    def execute(self, sql, args=()):
        require(type(sql) is str and sql.startswith('SELECT ') and ';' not in sql and '--' not in sql and '/*' not in sql, 'R3_SELECT_ONLY')
        names = re.findall(r'\bFROM ([a-z_]+)\b',sql)
        require(len(names)==1 and names[0] in TABLES and sql.count('?')==len(args), 'R3_QUERY_SHAPE')
        if sql.endswith('ORDER BY 1'):
            first = re.match(r'SELECT ([a-z_]+)[, ]',sql)
            require(first is not None, 'R3_ORDER')
            sql = sql[:-1]+first.group(1)+' COLLATE "C"'
        elif sql.endswith('ORDER BY seat'):
            sql += ' COLLATE "C"'
        sql = re.sub(r'\bFROM ([a-z_]+)\b',lambda m: 'FROM '+SCHEMA+'.'+m[1],sql)
        return self.db.execute(sql.replace('?','%s'),args)


def lock_head(db, scope):
    row = db.execute(f'SELECT rev FROM {SCHEMA}.org_head WHERE t=%s AND c=%s AND e=%s FOR UPDATE',scope).fetchone()
    return row[0] if row else None


def insert(db, table, values):
    require(table in TABLES, 'PG_TABLE')
    return db.execute(f'INSERT INTO {SCHEMA}.{table} VALUES ({",".join(["%s"]*len(values))})',values)
