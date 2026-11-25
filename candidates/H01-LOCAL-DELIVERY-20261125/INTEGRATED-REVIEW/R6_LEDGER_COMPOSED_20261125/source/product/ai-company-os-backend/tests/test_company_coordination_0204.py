"""D0 deterministic replay and actual SQLite index transactions; not PG/T1 proof."""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from app.core.event_store.company_coordination import (SCOPE, Member, Allocation, Pool,
    CompanyEvent, replay_company, append_company_order, inspect_company, prepare_company_step, finish_company_step)

ROOT=Path(__file__).resolve().parents[3]
A=Member('project-a','sha256:'+'a'*64,'task','demo-a','demo-agent','demo-principal',0)
B=Member('project-b','sha256:'+'b'*64,'task','demo-b','demo-agent','demo-principal',0)
MEMBERS=(A,B)
POOL=Pool('sample-budget','USD',100,0,2,3,'c'*64,(Allocation('project-a',40),Allocation('project-b',60)))
ADMIT='D0_RUN_ADMISSION';MOVE='D0_RUN_TRANSITION';RENEW='D0_LEASE_RENEWAL';FAIL='D0_RUN_FAILURE'


def event(seq,m,version,kind,revision=None,amount=0,parents=()):
    return CompanyEvent(seq,m.project_id,m.run_id,version,'d0-tx-'+format(seq,'064x'),
                        format(seq+100,'064x'),kind,parents,revision,amount)


E1=event(1,A,1,ADMIT,0,20)
E2=event(2,B,1,ADMIT,1,30,(E1.transaction_ref,))
E3=event(3,A,2,MOVE,parents=(E2.transaction_ref,))
E4=event(4,B,2,RENEW,2)
E5=event(5,A,3,FAIL,3,20)
E6=event(6,B,3,FAIL,4,30)
EVENTS=(E1,E2,E3,E4,E5)


class ReplayTests(TestCase):
    def hold(self,events=EVENTS,members=MEMBERS,pool=POOL):
        r=replay_company(members,pool,events);self.assertFalse(r.structural_match)
        self.assertIsNone(r.event_count);self.assertIsNone(r.outstanding_minor)
        self.assertEqual(r.project_outstanding,());self.assertEqual(r.decision,'HOLD')
        self.assertFalse(r.dispatch_allowed or r.spend_allowed or r.independent_verified)
    def test_interleaved_projects(self):
        r=replay_company(MEMBERS,POOL,EVENTS);self.assertTrue(r.structural_match)
        self.assertEqual((r.event_count,r.pool_revision,r.outstanding_minor),(5,4,30))
        self.assertEqual(r.project_outstanding,(('project-a',0),('project-b',30)))
        self.assertFalse(r.dispatch_allowed or r.spend_allowed or r.independent_verified)
    def test_all_released(self):
        r=replay_company(MEMBERS,POOL,EVENTS+(E6,));self.assertTrue(r.structural_match);self.assertEqual(r.outstanding_minor,0)
    def test_empty_history(self): self.assertTrue(replay_company(MEMBERS,POOL,()).structural_match)
    def test_same_actor_allowed(self): self.assertTrue(replay_company(MEMBERS,POOL,EVENTS).structural_match)
    def test_wrong_project(self): self.hold((replace(E1,project_id=B.project_id),))
    def test_duplicate_run(self): self.hold(members=(A,replace(B,run_id=A.run_id)))
    def test_revision_collision(self): self.hold(members=(A,replace(B,plan_revision=A.plan_revision)))
    def test_missing_allocation(self): self.hold(pool=replace(POOL,allocations=(POOL.allocations[0],)))
    def test_duplicate_allocation(self): self.hold(pool=replace(POOL,allocations=(POOL.allocations[0],)*2))
    def test_overallocated_pool(self): self.hold(pool=replace(POOL,limit_minor=99))
    def test_project_cap(self): self.hold((replace(E1,amount_minor=41),))
    def test_gap_and_wrong_run_version(self):
        self.hold((E1,E3));self.hold((replace(E1,version=2),))
    def test_duplicate_transaction(self): self.hold((E1,replace(E2,transaction_ref=E1.transaction_ref)))
    def test_future_parent(self): self.hold((replace(E1,predecessors=(E2.transaction_ref,)),E2))
    def test_self_parent(self): self.hold((replace(E1,predecessors=(E1.transaction_ref,)),))
    def test_duplicate_parents(self): self.hold((E1,replace(E2,predecessors=(E1.transaction_ref,)*2)))
    def test_stale_budget(self): self.hold((E1,replace(E2,budget_revision=0)))
    def test_wrong_release(self): self.hold(EVENTS[:-1]+(replace(E5,amount_minor=30),))
    def test_duplicate_admission(self): self.hold((E1,event(2,A,2,ADMIT,1,1)))
    def test_renew_without_admission(self): self.hold((event(1,A,1,RENEW,0),))
    def test_no_budget_change_on_ordinary(self): self.hold((E1,event(2,A,2,MOVE,1,1)))
    def test_failure_no_success(self): self.hold(EVENTS[:-1]+(replace(E5,kind='SUCCEEDED'),))
    def test_reopen_closed_run(self): self.hold(EVENTS+(event(6,A,4,ADMIT,4,1),))
    def test_bool_rejected(self): self.hold((replace(E1,sequence=True),))
    def test_unknown_run(self): self.hold((replace(E1,run_id='demo-unknown'),))


class Cursor:
    def __init__(self,db): self.c=db.cursor()
    def execute(self,sql,args=()): return self.c.execute(sql.replace('t1_candidate.','').replace('%s','?').replace(' FOR UPDATE',''),args)
    def fetchone(self): return self.c.fetchone()


class CompanySQLTests(TestCase):
    def setUp(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);self.path=Path(tmp.name)/'company.sqlite'
        with closing(self.connect()) as db,db:
            db.executescript('''
            CREATE TABLE run_heads(tenant_id text,company_id text,environment_id text,plan_revision text,task_id text,run_id text,agent_instance_id text,principal_id text,version int,PRIMARY KEY(tenant_id,company_id,environment_id,run_id));
            CREATE TABLE events(tenant_id text,company_id text,environment_id text,run_id text,version int,event_id text,event_type text,request_digest text,PRIMARY KEY(tenant_id,company_id,environment_id,run_id,version));
            CREATE TABLE sample_budgets(tenant_id text,company_id text,environment_id text,budget_id text,revision int,currency text,limit_minor int,outstanding_minor int,recognized_cost_minor int,unknown_cost int,policy_epoch int,witness_epoch int,source_digest text);
            CREATE TABLE sample_reservations(tenant_id text,company_id text,environment_id text,budget_id text,run_id text,budget_revision int,amount_minor int,currency text,request_digest text,transaction_ref text);
            CREATE TABLE sample_settlements(tenant_id text,company_id text,environment_id text,budget_id text,run_id text,version int,transaction_ref text,request_digest text,released_minor int,recognized_minor int,budget_revision int,outcome text);
            ''')
            db.executescript((ROOT/'database/0204C/company_event_order.sql').read_text().replace('t1_candidate.',''))
            db.execute('INSERT INTO company_stream_heads VALUES (?,?,?,0)',SCOPE)
            for m in MEMBERS:
                db.execute('INSERT INTO company_run_membership VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,*m.row()))
                db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?)',(*SCOPE,m.plan_revision,m.task_id,m.run_id,m.agent_instance_id,m.principal_id,m.initial_version))
            db.execute('INSERT INTO sample_budgets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(*SCOPE,POOL.budget_id,0,'USD',100,0,0,0,2,3,POOL.source_digest))
    def connect(self):
        db=sqlite3.connect(self.path,timeout=3);db.execute('PRAGMA foreign_keys=ON');return db
    def stage(self,db,m,e):
        # Explicit stand-in for existing T1 writes; not the actual lifecycle mapping.
        db.execute('UPDATE run_heads SET version=? WHERE run_id=?',(e.version,e.run_id))
        db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?)',(*SCOPE,e.run_id,e.version,e.transaction_ref,e.kind,e.request_digest))
        if e.kind!=MOVE:
            delta=e.amount_minor if e.kind==ADMIT else -e.amount_minor if e.kind==FAIL else 0
            db.execute('UPDATE sample_budgets SET revision=revision+1,outstanding_minor=outstanding_minor+?',(delta,))
        if e.kind==ADMIT:
            db.execute('INSERT INTO sample_reservations VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,POOL.budget_id,e.run_id,e.budget_revision+1,e.amount_minor,'USD',e.request_digest,e.transaction_ref))
        if e.kind==FAIL:
            db.execute('INSERT INTO sample_settlements VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(*SCOPE,POOL.budget_id,e.run_id,e.version,e.transaction_ref,e.request_digest,e.amount_minor,0,e.budget_revision+1,'D0_LOCAL_FAILURE_NO_EFFECT'))
    def write(self,e):
        m=A if e.run_id==A.run_id else B
        with closing(self.connect()) as db,db:
            db.execute('BEGIN IMMEDIATE');self.stage(db,m,e);append_company_order(Cursor(db),m,e)
    def guarded_write(self,history,e,wrong_post=False):
        m=A if e.run_id==A.run_id else B
        with closing(self.connect()) as db,db:
            db.execute('BEGIN IMMEDIATE');c=Cursor(db)
            prepare_company_step(c,MEMBERS,POOL,history,e);self.stage(db,m,e)
            if wrong_post:db.execute('UPDATE sample_budgets SET outstanding_minor=0')
            finish_company_step(c,MEMBERS,POOL,history,e)
    def full(self):
        for e in EVENTS:self.guarded_write(EVENTS[:e.sequence-1],e)
    def read(self,events=EVENTS):
        with closing(self.connect()) as db:
            db.execute('PRAGMA query_only=ON');db.execute('BEGIN');return inspect_company(Cursor(db),MEMBERS,POOL,events)
    def dump(self):
        with closing(self.connect()) as db:return tuple(tuple(db.execute('SELECT * FROM '+t).fetchall()) for t in ('run_heads','events','sample_budgets','sample_reservations','sample_settlements','company_stream_heads','company_event_order','company_run_membership'))
    def change(self,sql,args=()):
        with closing(self.connect()) as db,db:db.execute(sql,args)
    def test_readback_two_projects(self):
        self.full();before=self.dump();r=self.read();self.assertTrue(r.structural_match);self.assertEqual(r.outstanding_minor,30);self.assertEqual(self.dump(),before)
    def test_rollback_after_index(self):
        before=self.dump()
        with self.assertRaises(RuntimeError),closing(self.connect()) as db,db:
            self.stage(db,A,E1);append_company_order(Cursor(db),A,E1);raise RuntimeError('fault')
        self.assertEqual(self.dump(),before)
    def test_index_failure_rollback(self):
        self.change("CREATE TRIGGER reject_order BEFORE INSERT ON company_event_order BEGIN SELECT RAISE(ABORT,'fault'); END")
        before=self.dump()
        with self.assertRaises(sqlite3.IntegrityError):self.write(E1)
        self.assertEqual(self.dump(),before)
    def test_missing_event(self):
        before=self.dump()
        with self.assertRaises(ValueError),closing(self.connect()) as db,db:append_company_order(Cursor(db),A,E1)
        self.assertEqual(self.dump(),before)
    def test_stream_cas_rejects_gap(self):
        before=self.dump()
        with self.assertRaisesRegex(ValueError,'CAS'):self.write(replace(E1,sequence=2))
        self.assertEqual(self.dump(),before)
    def test_run_gap(self):
        before=self.dump()
        with self.assertRaisesRegex(ValueError,'RUN_SEQUENCE'):self.write(replace(E1,version=2))
        self.assertEqual(self.dump(),before)
    def test_missing_predecessor(self):
        before=self.dump()
        with self.assertRaisesRegex(ValueError,'CAUSAL'):self.write(replace(E1,predecessors=(E2.transaction_ref,)))
        self.assertEqual(self.dump(),before)
    def test_member_mismatch(self):
        before=self.dump()
        with self.assertRaises(ValueError):self.write(replace(E1,project_id=B.project_id))
        self.assertEqual(self.dump(),before)
    def test_changed_index(self):
        self.full();self.change("UPDATE company_event_order SET predecessors='[]' WHERE sequence=2");self.assertFalse(self.read().structural_match)
    def test_missing_index(self):
        self.full();self.change('DELETE FROM company_event_order WHERE sequence=2');self.assertFalse(self.read().structural_match)
    def test_wrong_stream_head(self):
        self.full();self.change('UPDATE company_stream_heads SET sequence=99');self.assertFalse(self.read().structural_match)
    def test_wrong_pool_postimage(self):
        self.full();self.change('UPDATE sample_budgets SET outstanding_minor=31');self.assertFalse(self.read().structural_match)
    def test_unknown_cost(self):
        self.full();self.change('UPDATE sample_budgets SET unknown_cost=1');self.assertFalse(self.read().structural_match)
    def test_wrong_reservation_project_pool(self):
        self.full();self.change("UPDATE sample_reservations SET budget_id='other' WHERE run_id='demo-b'");self.assertFalse(self.read().structural_match)
    def test_wrong_settlement(self):
        self.full();self.change('UPDATE sample_settlements SET released_minor=19');self.assertFalse(self.read().structural_match)
    def test_foreign_pool(self):
        self.full();self.change("INSERT INTO sample_budgets SELECT tenant_id,company_id,environment_id,'other',revision,currency,limit_minor,outstanding_minor,recognized_cost_minor,unknown_cost,policy_epoch,witness_epoch,source_digest FROM sample_budgets");self.assertFalse(self.read().structural_match)
    def test_foreign_event(self):
        self.full();self.change('INSERT INTO events VALUES (?,?,?,?,?,?,?,?)',(*SCOPE,'demo-other',1,E6.transaction_ref,ADMIT,E6.request_digest));self.assertFalse(self.read().structural_match)
    def test_old_prefix(self): self.full();self.assertFalse(self.read(EVENTS[:-1]).structural_match)
    def test_wrong_principal(self):
        self.full();self.change("UPDATE run_heads SET principal_id='demo-other' WHERE run_id='demo-a'");self.assertFalse(self.read().structural_match)
    def test_empty_snapshot(self): self.assertTrue(self.read(()).structural_match)
    def test_cap_before_write(self):
        before=self.dump()
        with self.assertRaisesRegex(ValueError,'PROJECT_CAP'):self.guarded_write((),replace(E1,amount_minor=41))
        self.assertEqual(self.dump(),before)
    def test_cap_across_runs_same_project(self):
        other=replace(B,project_id=A.project_id,plan_revision=A.plan_revision,task_id='task2')
        pool=replace(POOL,allocations=(Allocation(A.project_id,40),))
        event2=event(2,other,1,ADMIT,1,30)
        self.assertFalse(replay_company((A,other),pool,(E1,event2)).structural_match)
    def test_wrong_postimage_rolls_back_everything(self):
        before=self.dump()
        with self.assertRaisesRegex(ValueError,'POSTIMAGE'):self.guarded_write((),E1,wrong_post=True)
        self.assertEqual(self.dump(),before)
    def test_old_history_guard(self):
        self.guarded_write((),E1);before=self.dump()
        with self.assertRaises(ValueError):self.guarded_write((),event(1,B,1,ADMIT,0,30))
        self.assertEqual(self.dump(),before)
    def test_preimage_tamper(self):
        self.change('UPDATE sample_budgets SET unknown_cost=1');before=self.dump()
        with self.assertRaisesRegex(ValueError,'PREIMAGE'):self.guarded_write((),E1)
        self.assertEqual(self.dump(),before)
    def test_concurrent_project_sequence_one_winner(self):
        barrier=Barrier(2,timeout=3)
        second=event(1,B,1,ADMIT,0,30)
        def compete(e):
            barrier.wait()
            try:self.guarded_write((),e);return ('OK',e)
            except ValueError:return ('HOLD',e)
        with ThreadPoolExecutor(max_workers=2) as p:results=list(p.map(compete,(E1,second)))
        self.assertCountEqual([r[0] for r in results],['OK','HOLD'])
        winner=next(e for status,e in results if status=='OK')
        self.assertTrue(self.read((winner,)).structural_match)


if __name__=='__main__': main()
