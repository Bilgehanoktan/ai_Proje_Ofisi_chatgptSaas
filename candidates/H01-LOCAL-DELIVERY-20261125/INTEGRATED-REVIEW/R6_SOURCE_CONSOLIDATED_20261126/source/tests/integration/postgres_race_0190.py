"""Two-session probe against the existing 0183 schema, only in runner's fresh cluster.
Not a canonical T1 writer. Uses bootstrap exclusively for candidate DB mechanics.
"""
from contextlib import contextmanager
import subprocess
import time

SCHEMA = 'aicos_d0_candidate'
CASES = {'commit': ('race-commit', 'COMMIT', 'a'), 'rollback': ('race-rollback', 'ROLLBACK', 'b')}


def writer_sql(case: str, side: str) -> str:
    aggregate, _, _ = CASES[case]
    if side not in ('a', 'b'):
        raise ValueError('RACE_SIDE_INVALID')
    command = aggregate + '-' + side
    digest = side * 64
    return f"""DO $$
DECLARE n integer;
BEGIN
  UPDATE {SCHEMA}.head SET version=1,state='OBSERVED'
   WHERE tenant_id='synthetic-tenant' AND company_id='synthetic-company'
     AND aggregate_id='{aggregate}' AND version=0;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n=0 THEN RETURN; END IF;
  IF n<>1 THEN RAISE EXCEPTION 'unexpected CAS count'; END IF;
  INSERT INTO {SCHEMA}.event VALUES ('synthetic-tenant','synthetic-company','{aggregate}','{command}',1,'{digest}');
  INSERT INTO {SCHEMA}.audit VALUES ('synthetic-tenant','synthetic-company','{command}','SAMPLE_ONLY');
  INSERT INTO {SCHEMA}.outbox VALUES ('synthetic-tenant','synthetic-company','{command}','DENY');
END $$;"""


def readback_sql(case: str, before: bool) -> str:
    aggregate, _, winner = CASES[case]
    scope = "tenant_id='synthetic-tenant' AND company_id='synthetic-company'"
    command = aggregate+'-'+winner
    version = 0 if before else 1
    count = 0 if before else 1
    extra = '' if before else f""" AND EXISTS (SELECT FROM {SCHEMA}.event e
       JOIN {SCHEMA}.audit a USING(tenant_id,company_id,command_id)
       JOIN {SCHEMA}.outbox o USING(tenant_id,company_id,command_id)
       WHERE e.tenant_id='synthetic-tenant' AND e.company_id='synthetic-company'
       AND e.aggregate_id='{aggregate}' AND e.command_id='{command}' AND e.version=1
       AND e.request_sha='{winner*64}' AND a.decision='SAMPLE_ONLY' AND o.status='DENY')"""
    return f"""SELECT ((SELECT count(*) FROM {SCHEMA}.head WHERE {scope} AND aggregate_id='{aggregate}' AND version={version} AND state='{'PENDING' if before else 'OBSERVED'}')=1
      AND (SELECT count(*) FROM {SCHEMA}.event WHERE {scope} AND aggregate_id='{aggregate}')={count}
      AND (SELECT count(*) FROM {SCHEMA}.audit WHERE {scope} AND command_id IN ('{aggregate}-a','{aggregate}-b'))={count}
      AND (SELECT count(*) FROM {SCHEMA}.outbox WHERE {scope} AND command_id IN ('{aggregate}-a','{aggregate}-b'))={count}
      {extra})::text;"""


def wait_for(check, label, timeout=8):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if check(): return
        time.sleep(.05)
    raise RuntimeError('PG_RACE_TIMEOUT: '+label)


@contextmanager
def session(executable, args, env, name):
    # Only caller-provided private-socket arguments from the fresh cluster runner.
    proc=subprocess.Popen([executable,*args,'-Atq'],env={**env,'PGAPPNAME':name},stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        yield proc
    finally:
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=3)
        for stream in (proc.stdin,proc.stdout,proc.stderr):
            if stream: stream.close()


def send(proc, sql):
    if proc.poll() is not None: raise RuntimeError('PG_RACE_SESSION_EXITED')
    proc.stdin.write(sql+'\n'); proc.stdin.flush()


def finish(proc):
    out,err=proc.communicate(timeout=12)
    if proc.returncode!=0: raise RuntimeError(f'PG_RACE_SESSION_FAILED: {err}')
    return out


def run_races(executable, args, env, ddl, query):
    """Commit candidate DDL only in a new disposable cluster; always drop afterwards."""
    if not ddl.endswith(b'ROLLBACK;\n'): raise ValueError('PG_RACE_DDL_HOLD')
    query(ddl[:-len(b'ROLLBACK;\n')].decode()+'COMMIT;')
    try:
        for case,(aggregate,end,winner) in CASES.items():
            query(f"INSERT INTO {SCHEMA}.head VALUES ('synthetic-tenant','synthetic-company','{aggregate}',0,'PENDING');")
            a_name=f'aicos0190-{case}-a'; b_name=f'aicos0190-{case}-b'
            with session(executable,args,env,a_name) as a, session(executable,args,env,b_name) as b:
                send(a,"BEGIN ISOLATION LEVEL READ COMMITTED; SET LOCAL statement_timeout='20s'; SET LOCAL idle_in_transaction_session_timeout='25s';\n"+writer_sql(case,'a')+"\nSELECT 'A_READY';")
                wait_for(lambda: query(f"SELECT EXISTS(SELECT FROM pg_stat_activity WHERE application_name='{a_name}' AND state='idle in transaction' AND query LIKE '%A_READY%')::text;")=='true',case+' A ready')
                if query(readback_sql(case,True))!='true': raise RuntimeError('PG_RACE_UNCOMMITTED_VISIBLE')
                print(f'PASS {case}: independent read sees no uncommitted writes',flush=True)
                send(b,"BEGIN ISOLATION LEVEL READ COMMITTED; SET LOCAL statement_timeout='20s';\n"+writer_sql(case,'b')+"\nCOMMIT;\n\\q")
                wait_for(lambda: query(f"SELECT EXISTS(SELECT FROM pg_stat_activity b JOIN pg_stat_activity a ON a.pid=ANY(pg_blocking_pids(b.pid)) WHERE a.application_name='{a_name}' AND b.application_name='{b_name}')::text;")=='true',case+' B blocked by A')
                send(a,end+';\n\\q'); finish(a); finish(b)
                if query(readback_sql(case,False))!='true': raise RuntimeError('PG_RACE_COMMITTED_READBACK_HOLD')
                print(f'PASS {case}: B actually blocked; exactly one winner {winner}, matching event/audit/outbox',flush=True)
    finally:
        query(f'DROP SCHEMA {SCHEMA} CASCADE;')
        if query(f"SELECT (to_regnamespace('{SCHEMA}') IS NULL)::text;")!='true':
            raise RuntimeError('PG_RACE_CLEANUP_HOLD')
    print('PASS race schema removed from disposable cluster',flush=True)
