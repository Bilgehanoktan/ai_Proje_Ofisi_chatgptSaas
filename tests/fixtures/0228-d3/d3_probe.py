"""D3-R1 disposable policy probes. No bootstrap, production or canonical acceptance."""
import argparse
import json
import os
from pathlib import Path

ACK = '0228_D3_DISPOSABLE_LOCAL_ONLY'
DB = 'aicos_d3_0228'
PORT = 55433
CLUSTER = 'aicos_d3_0228_disposable'
SCHEMA = 'aicos_d3_fixture'
OWNER = 'aicos_d3_owner'
ROLES = ('aicos_d3_tenant_a', 'aicos_d3_tenant_b')
UNMAPPED = 'aicos_d3_unmapped'
SCOPES = (('synthetic-tenant-a', 'synthetic-company-a', 'D3_SAMPLE_ONLY'),
          ('synthetic-tenant-b', 'synthetic-company-b', 'D3_SAMPLE_ONLY'))
TABLES = ('events', 'outbox', 'fences', 'run_heads', 'run_leases', 'run_mutations',
          'run_audit', 'sample_budgets', 'run_admissions', 'sample_reservations',
          'run_lease_renewals', 'sample_settlements')
UPDATE = {'run_heads': ('state', 'version'),
          'run_leases': ('lease_version', 'heartbeat_revision', 'expires_tick', 'heartbeat_tick'),
          'sample_budgets': ('revision', 'outstanding_minor')}
KEY = ('tenant_id', 'company_id', 'environment_id')
ENV_KEYS = ('AICOS_D3_A_DSN', 'AICOS_D3_B_DSN', 'AICOS_D3_UNMAPPED_DSN')


class Hold(Exception):
    pass


def require(value, label):
    if not value:
        raise Hold(label)


def validate_dsn(info, role):
    expected = {'host': '127.0.0.1', 'port': str(PORT), 'dbname': DB,
                'user': role, 'sslmode': 'disable', 'connect_timeout': '3'}
    require(set(info) == set(expected) | {'password'}, 'DSN_KEYS')
    require(all(info[k] == v for k, v in expected.items()), 'DSN_PROFILE')
    require(isinstance(info['password'], str) and bool(info['password']), 'DSN_PASSWORD')
    return dict(info)


def table(name):
    require(name in TABLES, 'TABLE_ALLOWLIST')
    return SCHEMA + '.' + name


def run_probe(report, dsns, psycopg):
    from psycopg import sql

    def ok(label, value=True, **details):
        require(value, label)
        report['checks'].append({'id': label, 'status': 'PASS', **details})

    def deny(conn, label, action, state='42501'):
        actual = None
        try:
            with conn.transaction(force_rollback=True):
                action()
        except psycopg.Error as exc:
            actual = exc.sqlstate
        ok(label, actual == state, sqlstate=actual)

    def connect(role):
        conn = psycopg.connect(**dsns[role], autocommit=True, passfile=os.devnull)
        try:
            row = conn.execute("SELECT current_database(), session_user, current_user, "
                               "host(inet_server_addr()), inet_server_port(), "
                               "current_setting('cluster_name'), current_setting('server_version_num')").fetchone()
            require(row == (DB, role, role, '127.0.0.1', PORT, CLUSTER, '170012'), 'SERVER_PROFILE')
            conn.execute("SET statement_timeout = '5s'")
            conn.execute("SET lock_timeout = '1s'")
            conn.execute("SET idle_in_transaction_session_timeout = '20s'")
            flags = conn.execute("SELECT rolsuper, rolbypassrls, rolcreatedb, rolcreaterole, "
                                 "rolreplication, rolinherit, rolcanlogin FROM pg_roles WHERE rolname=%s",
                                 (role,)).fetchone()
            require(flags == (False, False, False, False, False, False, True), 'ROLE_FLAGS')
            memberships = conn.execute("SELECT count(*) FROM pg_auth_members m JOIN pg_roles r "
                                       "ON m.member=r.oid WHERE r.rolname=%s", (role,)).fetchone()[0]
            require(memberships == 0, 'ROLE_MEMBERSHIP')
            return conn
        except BaseException:
            conn.close()
            raise

    def count(conn, name, where='', args=()):
        return conn.execute('SELECT count(*) FROM ' + table(name) + where, args).fetchone()[0]

    def budget(conn):
        return conn.execute('SELECT revision,outstanding_minor FROM ' + table('sample_budgets')).fetchone()

    with connect(ROLES[0]) as a, connect(ROLES[1]) as b, connect(UNMAPPED) as u:
        ok('authenticated_runtime_and_unmapped_profiles')
        owner_flags = a.execute("SELECT rolsuper,rolbypassrls,rolcreatedb,rolcreaterole,"
                                "rolreplication,rolinherit,rolcanlogin FROM pg_roles WHERE rolname=%s",
                                (OWNER,)).fetchone()
        ok('owner_nologin_nobypass', owner_flags == (False,) * 7)
        inventory = a.execute("SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,r.rolname "
                              "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                              "JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname=%s AND c.relkind='r'",
                              (SCHEMA,)).fetchall()
        ok('all_12_owned_enabled_forced', set(inventory) == {(t, True, True, OWNER) for t in TABLES})
        policies = a.execute("SELECT tablename,policyname,cmd,roles,qual,with_check,permissive "
                             "FROM pg_policies WHERE schemaname=%s", (SCHEMA,)).fetchall()
        expected = {(t, 'd3_' + op.lower(), op) for t in TABLES for op in ('SELECT','INSERT','UPDATE','DELETE')}
        ok('all_48_command_policies', len(policies) == 48 and
           {(t,n,cmd) for t,n,cmd,_,_,_,_ in policies} == expected and
           all(set(roles)==set(ROLES) and mode=='PERMISSIVE' and
               (qual is not None)==(cmd!='INSERT') and (check is not None)==(cmd in ('INSERT','UPDATE'))
               for _,_,cmd,roles,qual,check,mode in policies))
        funcs = a.execute("SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON p.pronamespace=n.oid "
                          "WHERE n.nspname=%s", (SCHEMA,)).fetchone()[0]
        ok('no_fixture_definer_functions', funcs == 0)
        ok('unmapped_no_rows', count(u, 'run_heads') == 0, rows=0)
        deny(u, 'unmapped_insert_denied', lambda: u.execute('INSERT INTO ' + table('run_heads') +
             " (tenant_id,company_id,environment_id) VALUES ('x','x','x')"))
        for i, conn in enumerate((a, b)):
            label = 'a' if i == 0 else 'b'
            own, other = SCOPES[i], SCOPES[1-i]
            for name in TABLES:
                base = label + '_' + name
                fq = table(name)
                visible = conn.execute('SELECT DISTINCT tenant_id,company_id,environment_id FROM ' + fq).fetchall()
                n = count(conn, name)
                ok(base + '_own_read', visible == [own] and n == (2 if i == 1 and name == 'events' else 1), rows=n)
                where = ' WHERE (tenant_id,company_id,environment_id)=(%s,%s,%s)'
                ok(base + '_cross_read', count(conn, name, where, other) == 0, rows=0)
                cols = [r[0] for r in conn.execute("SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position", (SCHEMA,name)).fetchall()]
                require(tuple(cols[:3]) == KEY and len(cols) > 3, 'COLUMN_INVENTORY')
                ident = sql.Identifier(SCHEMA, name)
                insert = sql.SQL('INSERT INTO {} ({}) SELECT %s,%s,%s,{} FROM {}').format(
                    ident, sql.SQL(',').join(map(sql.Identifier,cols)),
                    sql.SQL(',').join(map(sql.Identifier,cols[3:])),ident)
                deny(conn, base + '_cross_insert', lambda: conn.execute(insert, other))
                deny(conn, base + '_scope_rebind', lambda: conn.execute('UPDATE ' + fq + ' SET tenant_id=%s', (other[0],)))
                if name in UPDATE:
                    col = UPDATE[name][0]
                    with conn.transaction(force_rollback=True):
                        own_n = conn.execute('UPDATE ' + fq + ' SET ' + col + '=' + col + where, own).rowcount
                        cross_n = conn.execute('UPDATE ' + fq + ' SET ' + col + '=' + col + where, other).rowcount
                        ok(base + '_update_scope', own_n == 1 and cross_n == 0, own=own_n, cross=cross_n)
                else:
                    deny(conn, base + '_append_only_update', lambda: conn.execute('UPDATE ' + fq + ' SET tenant_id=tenant_id'))
                if name == 'run_leases':
                    with conn.transaction(force_rollback=True):
                        cross_n = conn.execute('DELETE FROM ' + fq + where, other).rowcount
                        own_n = conn.execute('DELETE FROM ' + fq + where, own).rowcount
                        ok(base + '_delete_scope', own_n == 1 and cross_n == 0, own=own_n, cross=cross_n)
                else:
                    deny(conn, base + '_delete_privilege', lambda: conn.execute('DELETE FROM ' + fq + where, other))
                elevated = conn.execute("SELECT has_table_privilege(current_user,%s,'TRUNCATE'),"
                                        "has_table_privilege(current_user,%s,'TRIGGER'),"
                                        "has_table_privilege(current_user,%s,'REFERENCES')", (fq,fq,fq)).fetchone()
                ok(base + '_no_elevated_table_privilege', elevated == (False, False, False))
                allowed_updates = {c for c in cols if conn.execute("SELECT has_column_privilege(current_user,%s,%s,'UPDATE')",(fq,c)).fetchone()[0]}
                ok(base + '_column_update_grants', allowed_updates == set(UPDATE.get(name,())))
            conn.execute("SELECT set_config('aicos.tenant_id',%s,false)", (other[0],))
            ok(label + '_forged_context_denied', conn.execute('SELECT DISTINCT tenant_id FROM ' + table('run_heads')).fetchall() == [(own[0],)])
            conn.execute('RESET ALL')
            ok(label + '_reset_preserves_authenticated_scope', conn.execute('SELECT DISTINCT tenant_id FROM ' + table('run_heads')).fetchall() == [(own[0],)])
            conn.execute("SET statement_timeout = '5s'")
            conn.execute("SET lock_timeout = '1s'")
            conn.execute("SET idle_in_transaction_session_timeout = '20s'")
            for target in (ROLES[1-i], OWNER):
                deny(conn, label + '_set_role_' + target, lambda: conn.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(target))))
            deny(conn, label + '_session_authorization_denied', lambda: conn.execute(sql.SQL('SET SESSION AUTHORIZATION {}').format(sql.Identifier(ROLES[1-i]))))
            def rls_off():
                conn.execute('SET LOCAL row_security=off')
                conn.execute('SELECT count(*) FROM ' + table('run_heads')).fetchone()
            deny(conn, label + '_rls_off_denied', rls_off)
            joined = conn.execute('SELECT DISTINCT h.tenant_id,e.tenant_id FROM ' + table('run_heads') + ' h JOIN ' +
                                  table('events') + ' e ON h.run_id=e.run_id').fetchall()
            ok(label + '_join_scope', joined == [(own[0],own[0])])
        ok('b_only_event_exists', count(b,'events',' WHERE event_id=%s',('foreign-only',)) == 1)
        deny(a,'cross_scope_fk_missing',lambda: a.execute('INSERT INTO '+table('outbox')+' VALUES (%s,%s,%s,%s,%s,%s)',
             (*SCOPES[0],'run-1','foreign-only','foreign-only-digest')), '23503')
        before = budget(a)
        with a.transaction(force_rollback=True):
            a.execute('UPDATE '+table('sample_budgets')+' SET revision=revision+1')
            ok('rollback_visible_inside', budget(a)[0] == before[0]+1)
        ok('rollback_restores', budget(a)==before)
        with connect(ROLES[0]) as a2:
            with a.transaction(force_rollback=True):
                a.execute('SELECT revision FROM '+table('sample_budgets')+' FOR UPDATE').fetchall()
                deny(a2,'same_scope_nowait_contention',lambda: a2.execute('SELECT revision FROM '+table('sample_budgets')+' FOR UPDATE NOWAIT').fetchall(),'55P03')
                with b.transaction(force_rollback=True):
                    ok('other_scope_not_blocked',b.execute('UPDATE '+table('sample_budgets')+' SET revision=revision+1').rowcount==1)
            with a2.transaction(force_rollback=True):
                ok('lock_released',len(a2.execute('SELECT revision FROM '+table('sample_budgets')+' FOR UPDATE NOWAIT').fetchall())==1)
            old = budget(a); old_b = budget(b)
            ok('two_connections_same_revision',budget(a2)==old)
            ok('first_budget_cas',a.execute('UPDATE '+table('sample_budgets')+' SET revision=revision+1,outstanding_minor=outstanding_minor+1 WHERE revision=%s',(old[0],)).rowcount==1)
            ok('stale_budget_cas',a2.execute('UPDATE '+table('sample_budgets')+' SET revision=revision+1 WHERE revision=%s',(old[0],)).rowcount==0)
            deny(a,'cap_constraint',lambda: a.execute('UPDATE '+table('sample_budgets')+' SET outstanding_minor=limit_minor+1'),'23514')
            ok('other_budget_unchanged',budget(b)==old_b)
            with a.transaction(force_rollback=True):
                a.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                snap=budget(a)
                ok('second_connection_commit',a2.execute('UPDATE '+table('sample_budgets')+' SET revision=revision+1').rowcount==1)
                ok('snapshot_stable',budget(a)==snap)
                deny(a,'read_only_write_denied',lambda: a.execute('UPDATE '+table('sample_budgets')+' SET revision=revision+1'),'25006')
            ok('fresh_snapshot_visible',budget(a)[0]==snap[0]+1)
            ok('other_budget_still_unchanged',budget(b)==old_b)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args()
    report={'revision':'0228-D3-R1','status':'HOLD','classification':'DISPOSABLE_FIXTURE_ONLY',
            'canonical_mapping':'HOLD','independent_acceptance':'HOLD','checks':[]}
    with args.report.open('x',encoding='utf-8',newline='\n') as out:
        try:
            require(os.environ.get('AICOS_D3_ACK')==ACK,'EXPLICIT_ACK')
            import psycopg
            from psycopg.conninfo import conninfo_to_dict
            require(psycopg.__version__=='3.3.9' and psycopg.pq.__impl__=='binary','DRIVER_PROFILE')
            dsns={role:validate_dsn(conninfo_to_dict(os.environ.get(key,'')),role)
                  for role,key in zip((*ROLES,UNMAPPED),ENV_KEYS)}
            for key in tuple(os.environ):
                if key.startswith('PG') or key in ENV_KEYS:
                    os.environ.pop(key,None)
            os.environ['PGPASSFILE']=os.devnull
            os.environ['PGSERVICEFILE']=os.devnull
            run_probe(report,dsns,psycopg)
            report['status']='D3_FIXTURE_PROBES_PASS'
        except Hold as exc:
            report['reason']=str(exc)
        except Exception as exc:
            report['reason']=type(exc).__name__
            state=getattr(exc,'sqlstate',None)
            if isinstance(state,str) and len(state)==5:
                report['sqlstate']=state
        report['passed']=len(report['checks'])
        json.dump(report,out,indent=2)
        out.write('\n')
    print(json.dumps({'status':report['status'],'passed':report['passed'],'reason':report.get('reason')}))
    return 0 if report['status']=='D3_FIXTURE_PROBES_PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
