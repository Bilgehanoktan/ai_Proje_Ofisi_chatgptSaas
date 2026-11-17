"""D4-R2 opt-in read/rollback probe. Never provisions roles, DB or server."""
import argparse
import json
import os
from pathlib import Path
import psycopg
from psycopg import sql

CONFIG = json.loads(Path(__file__).with_name("scope.json").read_text(encoding="utf-8"))
SCOPES = CONFIG["scope"]
TABLES = CONFIG["tables"]
SCHEMA = "t1_candidate"

def connect_checked(label, role):
    dsn = os.environ["D4_DSN_" + label.upper()]
    from psycopg.conninfo import conninfo_to_dict
    opts = conninfo_to_dict(dsn)
    if (opts.get("host") != "127.0.0.1" or opts.get("port") != "55434"
            or opts.get("dbname") != CONFIG["database"] or opts.get("user") != role
            or set(opts) - {"host", "port", "dbname", "user", "password", "connect_timeout"}):
        raise RuntimeError("D4_DSN_HOLD")
    c = psycopg.connect(dsn, connect_timeout=4, autocommit=True)
    try:
        row = c.execute("""SELECT current_database(), current_setting('cluster_name'),
            current_setting('server_version_num')::int, current_user, session_user,
            inet_server_addr()::text, inet_server_port(), rolsuper, rolbypassrls,
            rolcreaterole, rolcreatedb, rolreplication
            FROM pg_roles WHERE rolname=session_user""").fetchone()
        if row != (CONFIG["database"], CONFIG["cluster_name"], 170012, role, role,
                   "127.0.0.1/32", 55434, False, False, False, False, False):
            # inet::text may include a prefix; normalize only the returned IP.
            if not row or row[:5] != (CONFIG["database"], CONFIG["cluster_name"],170012,role,role) or row[5] not in ("127.0.0.1","127.0.0.1/32") or row[6:] != (55434,False,False,False,False,False):
                raise RuntimeError("D4_SESSION_HOLD")
        if c.execute("SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=session_user)").fetchone()[0]:
            raise RuntimeError("D4_ROLE_MEMBERSHIP_HOLD")
        c.execute("SET statement_timeout='4s'")
        c.execute("SET lock_timeout='2s'")
        return c
    except BaseException:
        c.close()
        raise

def expect_error(c, statement, args, code, deferred=False):
    c.execute("BEGIN")
    try:
        try:
            c.execute(statement,args)
            if deferred:
                c.execute("SET CONSTRAINTS ALL IMMEDIATE")
        except psycopg.Error as e:
            if e.sqlstate != code:
                raise RuntimeError("D4_SQLSTATE_MISMATCH") from None
        else:
            raise RuntimeError("D4_EXPECTED_DENIAL_MISSING")
    finally:
        c.execute("ROLLBACK")

def require(ok, label, checks):
    if not ok:
        raise RuntimeError(label)
    checks.append(label)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reviewed-disposable", action="store_true")
    args=ap.parse_args()
    if not args.reviewed_disposable:
        raise SystemExit("NOT_RUN: review and separate fresh-cluster preparation required")
    checks=[]
    for k,scope in SCOPES.items():
        with connect_checked(k,CONFIG["runtime_roles"][k]) as c:
            for t in TABLES:
                name=sql.Identifier(SCHEMA,t)
                rows=c.execute(sql.SQL("SELECT tenant_id,company_id,environment_id FROM {}").format(name)).fetchall()
                expected=2 if k=="a" and t in ("run_heads","company_run_membership") else 1
                require(len(rows)==expected and all(tuple(scope)==row for row in rows),f"{k}.{t}.visible",checks)
                meta=c.execute("""SELECT relrowsecurity,relforcerowsecurity FROM pg_class x
                    JOIN pg_namespace n ON n.oid=x.relnamespace WHERE n.nspname=%s AND x.relname=%s""",(SCHEMA,t)).fetchone()
                require(meta==(True,True),f"{k}.{t}.force",checks)
                for foreign in (v for v in SCOPES.values() if v!=scope):
                    n=c.execute(sql.SQL("SELECT count(*) FROM {} WHERE (tenant_id,company_id,environment_id)=(%s,%s,%s)").format(name),foreign).fetchone()[0]
                    require(n==0,f"{k}.{t}.foreign.{foreign}",checks)
                require(not c.execute("SELECT has_table_privilege(current_user,%s,'TRUNCATE')",(SCHEMA+"."+t,)).fetchone()[0],f"{k}.{t}.no_truncate",checks)
            c.execute("SELECT set_config('app.tenant_id','synthetic-tenant-b',false)")
            require(c.execute("SELECT DISTINCT tenant_id,company_id,environment_id FROM t1_candidate.events").fetchall()==[tuple(scope)],f"{k}.guc_ignored",checks)
            other=next(v for v in SCOPES.values() if v!=scope)
            expect_error(c,"INSERT INTO t1_candidate.company_event_order VALUES (%s,%s,%s,99,'project-1','run-1',1,'new-tx',%s,'[]')",(*other,"c"*64),"42501")
            checks.append(f"{k}.cross_scope_insert")
            expect_error(c,"INSERT INTO t1_candidate.company_run_membership VALUES (%s,%s,%s,'other','p','t','r','a','u',0)",scope,"42501")
            checks.append(f"{k}.provision_denied")
            expect_error(c,"UPDATE t1_candidate.terminal_command_anchors SET command_sha=%s",("c"*64,),"42501")
            checks.append(f"{k}.anchor_append_only")
            expect_error(c,"DELETE FROM t1_candidate.company_event_order",(),"42501")
            checks.append(f"{k}.order_append_only")
            expect_error(c,"UPDATE t1_candidate.company_stream_heads SET tenant_id=%s",("foreign",),"42501")
            checks.append(f"{k}.scope_column_immutable")
            expect_error(c,"INSERT INTO t1_candidate.company_event_order VALUES (%s,%s,%s,99,'missing-project','missing-run',1,'new-tx',%s,'[]')",(*scope,"c"*64),"23503",True)
            checks.append(f"{k}.scoped_fk")
            expect_error(c,"INSERT INTO t1_candidate.terminal_command_anchors VALUES (%s,%s,%s,'missing-plan','missing-run',1,'missing-tx',%s,%s)",(*scope,"c"*64,"d"*64),"23503",True)
            checks.append(f"{k}.anchor_deferred_fk")
            expect_error(c,sql.SQL("SET ROLE {}").format(sql.Identifier(CONFIG["runtime_roles"][next(x for x in SCOPES if x!=k)])),(),"42501")
            checks.append(f"{k}.role_switch_denied")
    with connect_checked("unmapped",CONFIG["unmapped"]) as c:
        for t in TABLES:
            require(c.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(SCHEMA,t))).fetchone()==(0,),f"unmapped.{t}",checks)
    # Real distinct sessions, no persisted test writes. NOWAIT is a diagnostic, not a change to the product lock SQL.
    with connect_checked("a",CONFIG["runtime_roles"]["a"]) as first, connect_checked("a",CONFIG["runtime_roles"]["a"]) as second:
        require(first.info.backend_pid!=second.info.backend_pid,"distinct_sessions",checks)
        first.execute("BEGIN")
        try:
            require(first.execute("SELECT sequence FROM t1_candidate.company_stream_heads FOR UPDATE").fetchone()==(1,),"stream_first_lock",checks)
            expect_error(second,"SELECT sequence FROM t1_candidate.company_stream_heads FOR UPDATE NOWAIT",(),"55P03")
            checks.append("stream_nowait_denied")
            require(first.execute("UPDATE t1_candidate.company_stream_heads SET sequence=sequence+1 WHERE sequence=0 RETURNING sequence").fetchall()==[],"stale_cas_no_write",checks)
        finally:
            first.execute("ROLLBACK")
        require(second.execute("SELECT sequence FROM t1_candidate.company_stream_heads").fetchone()==(1,),"stream_rollback_unchanged",checks)
    if len(set(checks)) != len(checks):
        raise RuntimeError("D4_DUPLICATE_CHECK")
    print(json.dumps({"status":"FIXTURE_PROBE_ONLY","checks":checks,"count":len(checks),"canonical":False}))

if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never dump DSN, driver diagnostic or data from an untrusted endpoint.
        raise SystemExit("D4_HOLD: probe failed; inspect private local logs and preconditions") from None
