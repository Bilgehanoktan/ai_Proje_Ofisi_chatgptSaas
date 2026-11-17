"""Explicit opt-in, fresh R4 disposable PG fixture. Never run against Core or product.
Requires exact R3 modules, R4 schema installed, reviewed local credentials; no DDL here.
"""
import argparse, getpass, hashlib, json, sys, threading, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from unittest.mock import patch
from pg_transaction import SCHEMA, DATABASE, CLUSTER, TABLES, WRITERS, run, Hold, CommitUnknown, CleanupHold, lock_head
from pg_operations import PgOperations, TaskReference, ZERO

R3 = Path(__file__).resolve().parent.parent/'ORG-05R3'
R4 = Path(__file__).resolve().parent.parent/'ORG-05R4'
R3_PINS = {
 'durable_ops.py':'c68f07b1f802983ba87f3486ce51d330e7e4b3a59c4fc98ff7f80de3a5d6bdb1',
 'integration_guard.py':'3fba6f345356725be61f8d7aa5460a95f0a376705fc8dfefe37d3c7686c55042',
 'office_bridge.py':'e8a2eb953313bc2342fa9c0264358ab6eda16eb6a40b0a36036d2a04991615a3',
 'operations.py':'ac57a06a9f0c6a9b6a9886f04456962582f8aa080478a95654a2e1032c66e82b',
 'org_model.py':'a864d7bd6f1ca1fe17095c953529dc739f95ad2073e121bdb90014d1a16ea46e',
 'persistence.py':'beffb280340c1c3da13f13248d5049d6d51d87ad05e5448a3373168919ecfd34',
 'staffing.py':'51131102e6c601c2efaf6ec18e430b87dd221edec9650d9c8391a3bcff131d32',
}

def verify_sources():
    for p,h in [(R3/name,digest) for name,digest in R3_PINS.items()]+[(R4/'PG_SCHEMA_R4.sql','f5ebb556ccc9b37a0f2bd0e05f36c7cf85a5bd54de9c1d0244845f146f7b3731')]:
        if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise Hold('SOURCE_PIN_MISMATCH')
    sys.path.insert(0,str(R3))


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--execute-disposable',action='store_true'); parser.add_argument('--port',type=int,required=True); parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if not args.execute_disposable or not 1<=args.port<=65535 or args.report.exists(): parser.error('explicit disposable opt-in, valid port and new report required')
    verify_sources()
    import psycopg
    from org_model import Org, Unit, Seat
    from staffing import Staffing, Definition, Instance, Binding
    from operations import ProjectTeam
    from durable_ops import HistoryPin
    import pg_operations
    roles=('aicos_org_r4_writer_a','aicos_org_r4_writer_b','aicos_org_r4_reader_a','aicos_org_r4_unmapped')
    passwords={role:getpass.getpass(role+' password: ') for role in roles}
    def factory(role):
        return lambda:psycopg.connect(host='127.0.0.1',port=args.port,dbname=DATABASE,user=role,password=passwords[role],connect_timeout=5,autocommit=False)
    sa,sb=WRITERS[roles[0]],WRITERS[roles[1]]; fa,fb,fr,fu=map(factory,roles)
    a,b,reader=PgOperations(fa,sa),PgOperations(fb,sb),PgOperations(fr,sa)
    def staffing(scope):
        t,c,_=scope
        return Staffing(Org(t,c,(Unit(c,'company',None),Unit('a','department',c),Unit('b','department',c)),(Seat('l','a','lead'),Seat('w','a','research','l'),Seat('x','b','research'))),(Definition('dl','lead'),Definition('dr','research')),(Instance('demo-l','dl',t,c),Instance('demo-w','dr',t,c),Instance('demo-x','dr',t,c)),(Binding('l','demo-l'),Binding('w','demo-w'),Binding('x','demo-x')))
    def eq(actual,expected):
        if actual!=expected: raise AssertionError('RESULT_MISMATCH')
    def denied(action, code):
        try: action()
        except psycopg.Error as exc: eq(exc.sqlstate,code); return code
        raise AssertionError('EXPECTED_SQLSTATE')
    def held(action,reason):
        try: action()
        except Hold as exc: eq(str(exc),reason); return reason
        raise AssertionError('EXPECTED_HOLD')
    def query(factory,scope,sql,params=()): return run(factory,scope,False,lambda db:db.execute(sql,params).fetchall())
    def counts():
        return tuple(query(fa,sa,f'SELECT count(*) FROM {SCHEMA}.{t}')[0][0] for t in ('op_entry','op_notice'))
    results=[]; report={'profile':'ORG-05R5_DISPOSABLE_ONLY','source_pins':R3_PINS,'schema_sha256':'f5ebb556ccc9b37a0f2bd0e05f36c7cf85a5bd54de9c1d0244845f146f7b3731','driver':psycopg.__version__,'checks':results,'status':'FAIL_OR_INCOMPLETE'}
    def check(name, action):
        start=time.monotonic()
        try:
            detail=action(); results.append({'id':name,'status':'PASS','detail':detail,'elapsed_ms':round((time.monotonic()-start)*1000)})
        except Exception as exc:
            results.append({'id':name,'status':'FAIL','error_type':type(exc).__name__,'sqlstate':getattr(exc,'sqlstate',None)}); raise
    def race(action):
        barrier=threading.Barrier(2,timeout=10)
        def worker():
            barrier.wait()
            try: return ('ok',action())
            except (CommitUnknown,CleanupHold): raise
            except Hold as exc: return ('hold',str(exc))
            except psycopg.Error as exc: return ('sqlstate',exc.sqlstate)
        with ThreadPoolExecutor(2) as ex:
            f1,f2=ex.submit(worker),ex.submit(worker); return [f1.result(timeout=20),f2.result(timeout=20)]
    def winner(rows,allowed):
        good=[v for status,v in rows if status=='ok']; bad=[(status,v) for status,v in rows if status!='ok']
        eq(len(good),1); eq(len(bad),1)
        if bad[0] not in allowed: raise AssertionError('UNEXPECTED_RACE_LOSER')
        return good[0],bad[0]
    try:
        def fresh_inventory():
            for f,scope in ((fa,sa),(fb,sb),(fr,sa)):
                for table in TABLES: eq(query(f,scope,f'SELECT count(*) FROM {SCHEMA}.{table}'),[(0,)])
            policies=query(fa,sa,'SELECT tablename,policyname,cmd FROM pg_catalog.pg_policies WHERE schemaname=%s',(SCHEMA,))
            expected={(t,'org_read','SELECT') for t in TABLES}|{(t,'org_insert','INSERT') for t in TABLES}|{('org_head','org_head_update','UPDATE')}
            eq(set(policies),expected); return {'tables':len(TABLES),'policies':len(policies),'cluster':CLUSTER}
        check('PG01_FRESH_AND_RLS_INVENTORY',fresh_inventory)
        s=staffing(sa); ss=staffing(sb)
        def genesis():
            rows=race(lambda:a.record(s,None)); rev,loser=winner(rows,{('hold','STALE_HEAD'),('sqlstate','23505')}); eq(query(fa,sa,f'SELECT count(*) FROM {SCHEMA}.org_revision'),[(1,)]); return {'revision':rev,'loser':loser}
        check('PG02_GENESIS_RACE',genesis); rev=results[-1]['detail']['revision']
        check('PG03_OTHER_SCOPE_GENESIS',lambda:b.record(ss,None)); rb=results[-1]['detail']
        team=ProjectTeam(*sa[:2],s.revision(),'demo-project','l',('l','w','x'))
        check('PG04_TEAM',lambda:a.create_team(rev,team))
        p=TaskReference(sa,team.project,'sha256:'+'a'*64,'task','research','demo-x','demo-principal'); empty=HistoryPin(0,ZERO)
        def append(**kw):
            v=dict(rev=rev,observed=p,expected=p,sender='w',recipient='x',kind='handoff',history_pin=empty); v.update(kw); return a.append_proposal(**v)
        def notice_failure():
            original=pg_operations.insert
            def fail_notice(db,table,values): return original(db,table,values[:-1]+('BAD',) if table=='op_notice' else values)
            with patch.object(pg_operations,'insert',fail_notice): denied(append,'23514')
            eq(counts(),(0,0)); return {'sqlstate':'23514','counts':counts()}
        check('PG05_ATOMIC_ROLLBACK',notice_failure)
        def contention():
            def outer(db):
                eq(lock_head(db,sa),rev)
                def nowait(other): return other.execute(f'SELECT rev FROM {SCHEMA}.org_head WHERE t=%s AND c=%s AND e=%s FOR UPDATE NOWAIT',sa).fetchone()
                denied(lambda:run(fa,sa,True,nowait),'55P03')
                eq(run(fb,sb,True,lambda other:lock_head(other,sb)),rb)
            run(fa,sa,True,outer); return {'same_scope':'55P03','other_scope':'PASS'}
        check('PG06_LOCK_ISOLATION',contention)
        def proposal_race():
            pin,loser=winner(race(append),{('hold','HISTORY_CAS')}); eq(pin.count,1); eq(counts(),(1,1)); return {'count':pin.count,'head':pin.head,'loser':loser}
        check('PG07_HANDOFF_CAS_RACE',proposal_race); pin=HistoryPin(1,results[-1]['detail']['head'])
        check('PG08_STALE_HISTORY',lambda:held(append,'HISTORY_CAS'))
        p2=replace(p,task='task2',recipient_instance='demo-w')
        check('PG09_DELEGATION',lambda:vars(append(observed=p2,expected=p2,sender='l',recipient='w',kind='delegation',history_pin=pin))); pin2=HistoryPin(**results[-1]['detail'])
        check('PG10_REOPEN_HISTORY',lambda:eq(len(reader.history(rev,team.project,pin2)),2))
        check('PG11_CROSS_SCOPE_READ',lambda:eq(query(fa,sa,f'SELECT rev FROM {SCHEMA}.org_head WHERE t=%s AND c=%s AND e=%s',sb),[]))
        def foreign_insert(scope): return run(fa,sa,True,lambda db:db.execute(f'INSERT INTO {SCHEMA}.org_head VALUES (%s,%s,%s,%s)',scope+(rb,)))
        check('PG12_FOREIGN_TENANT',lambda:denied(lambda:foreign_insert(sb),'42501'))
        check('PG13_FOREIGN_COMPANY',lambda:denied(lambda:foreign_insert((sa[0],sb[1],sa[2])),'42501'))
        check('PG14_FOREIGN_ENV',lambda:denied(lambda:foreign_insert((sa[0],sa[1],'OTHER_ENV')),'42501'))
        check('PG15_CROSS_SCOPE_FK',lambda:denied(lambda:run(fa,sa,True,lambda db:db.execute(f'INSERT INTO {SCHEMA}.org_unit VALUES (%s,%s,%s,%s,%s,%s,%s)',sa+(rb,'bad','company',None))),'23503'))
        check('PG16_IMMUTABLE_UPDATE',lambda:denied(lambda:run(fa,sa,True,lambda db:db.execute(f'UPDATE {SCHEMA}.op_entry SET task=%s',('tamper',))),'42501'))
        check('PG17_IMMUTABLE_DELETE',lambda:denied(lambda:run(fa,sa,True,lambda db:db.execute(f'DELETE FROM {SCHEMA}.op_notice')),'42501'))
        def reader_denied():
            with fr() as db: denied(lambda:db.execute(f'INSERT INTO {SCHEMA}.org_head VALUES (%s,%s,%s,%s)',sa+(rev,)),'42501'); db.rollback()
            with fu() as db: denied(lambda:db.execute(f'SELECT * FROM {SCHEMA}.org_head'),'42501'); db.rollback()
            return {'reader':'42501','unmapped':'42501'}
        check('PG18_READER_UNMAPPED_DENIED',reader_denied)
        check('PG19_REFERENCE_MISMATCH',lambda:held(lambda:append(observed=replace(p,principal='demo-other'),history_pin=pin2),'TASK_REFERENCE'))
        check('PG20_REVISION_SUCCESSOR',lambda:a.record(replace(s,previous=s.revision()),rev)); new=results[-1]['detail']
        check('PG21_STALE_REVISION',lambda:held(lambda:append(history_pin=pin2),'STALE_ORG'))
        check('PG22_ARCHIVED_HISTORY',lambda:eq(len(reader.history(rev,team.project,pin2)),2))
        check('PG23_STALE_HEAD',lambda:held(lambda:a.record(replace(s,previous=s.revision()),rev),'STALE_HEAD'))
        check('PG24_READER_CURRENT',lambda:eq(reader.read_current(new)[0],new))
        check('PG25_READER_STALE_HEAD',lambda:held(lambda:reader.read_current(rev),'HEAD_MISMATCH'))
        check('PG26_FINAL_COUNTS',lambda:eq(counts(),(2,2)))
        report['status']='PASS_DISPOSABLE_FIXTURE_ONLY'
    finally:
        with args.report.open('x',encoding='utf-8') as f: json.dump(report,f,indent=2,sort_keys=True)
        passwords.clear()
    print(report['status'],len(results))

if __name__=='__main__': main()
