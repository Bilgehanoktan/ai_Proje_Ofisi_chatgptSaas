"""D4-R3: original D0 Company T1 mappings, real psycopg connections; no product wiring."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from contextlib import contextmanager
from pathlib import Path
from threading import Event
from time import monotonic, sleep
from unittest.mock import patch
import copy
import psycopg
from psycopg import sql
import test_admission_mapping_0195 as base
from test_transition_mapping_0194 import PLAN, obs
from test_company_terminal_0212 import CompanyTerminalTests
from test_company_multiproject_0213 import TwoProjectTests
from app.core.agent_runtime.lifecycle import RunState
from app.core.orchestrator.engine import canonical_plan
from app.core.event_store.company_coordination import (
    SCOPE, Member, Allocation, Pool, CompanyCoordinatedMapping, inspect_company)
from app.core.event_store.retained_history import ReferenceStore, ReferenceReader
from app.core.event_store.terminal_anchor import anchor_from_pin, verify_anchor
from app.core.transaction.postgres_admission_mapping import D0PostgresAdmissionMapping, reconcile_admission
from app.core.transaction.postgres_lifecycle_mapping import AdmissionBinding, reconcile_lifecycle
from app.core.transaction.postgres_session import postgres_transaction, CommitOutcomeUnknown
from app.core.transaction.port import LogicalT1Coordinator

TABLES = ("events","outbox","fences","run_heads","run_leases","run_mutations","run_audit",
          "sample_budgets","run_admissions","sample_reservations","run_lease_renewals",
          "sample_settlements","terminal_command_anchors","company_run_membership",
          "company_stream_heads","company_event_order")

def need(ok, code):
    if not ok:
        raise RuntimeError(code)

class LostAck:
    """Synthetic fault AFTER real server COMMIT; not a real network outage."""
    autocommit = False
    def __init__(self, db): self.db = db
    def cursor(self): return self.db.cursor()
    def commit(self):
        self.db.commit()
        raise OSError("D4_INJECTED_LOST_ACK")
    def rollback(self): self.db.rollback()
    def close(self): self.db.close()

class CompanyFixture:
    event = CompanyTerminalTests.event
    ordinary = CompanyTerminalTests.ordinary
    renewal = CompanyTerminalTests.renewal
    terminal = CompanyTerminalTests.terminal
    _claim_b = TwoProjectTests._claim_b
    _event = TwoProjectTests._event

    def __init__(self, connect_runtime, archive_path):
        self.connect_runtime = connect_runtime
        self.initial = base.spec_for()
        self.admit = base.intent_for(self.initial)
        self.binding = AdmissionBinding(self.initial,self.admit)
        self.clock = replace(base.CLOCK,now_tick=11)
        self.before = self.initial.before
        self.lease = self.initial.lease
        self.budget = base.BUDGET
        self.history = ()
        self.commands = ()
        self.plan_b = copy.deepcopy(PLAN)
        self.plan_b["id"] = "plan-b"
        self.rev_b = canonical_plan(self.plan_b)["revision"]
        a = tuple(obs(t) for t in "abcq")
        b = tuple(replace(r,scope=replace(r.scope,plan_revision=self.rev_b,
                  run_id="demo-b-"+r.scope.task_id)) for r in a)
        self.observations = a+b
        self.members = tuple(Member(project,r.scope.plan_revision,r.scope.task_id,
            r.scope.run_id,r.scope.agent_instance_id,r.scope.principal_id,r.version)
            for project,rs in (("project-a",a),("project-b",b)) for r in rs)
        p = base.BUDGET
        self.pool = Pool(p.budget_id,p.currency,p.limit_minor,p.revision,p.policy_epoch,
            p.witness_epoch,p.source_digest,(Allocation("project-a",60),Allocation("project-b",40)))
        self.archive = ReferenceStore(archive_path)
        self.reader = ReferenceReader(self.archive.path)

    def seed(self, seed_connection):
        """Only the dedicated fixture provisioning role can perform initial inserts."""
        with seed_connection.transaction():
            for r,m in zip(self.observations,self.members):
                s=r.scope
                seed_connection.execute("INSERT INTO t1_candidate.run_heads VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (*SCOPE,s.plan_revision,s.task_id,s.run_id,s.agent_instance_id,s.principal_id,r.state.value,r.version,r.attempt))
                seed_connection.execute("INSERT INTO t1_candidate.company_run_membership VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(*SCOPE,*m.row()))
            p=base.BUDGET
            seed_connection.execute("INSERT INTO t1_candidate.sample_budgets VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (*SCOPE,p.budget_id,p.revision,p.currency,p.limit_minor,p.outstanding_minor,p.recognized_cost_minor,p.unknown_cost,p.policy_epoch,p.witness_epoch,p.source_digest))
            seed_connection.execute("INSERT INTO t1_candidate.company_stream_heads VALUES (%s,%s,%s,0)",SCOPE)

    def connect(self):
        db=self.connect_runtime()
        try:
            db.autocommit=False
            db.execute("SET LOCAL lock_timeout='10s'")
            db.execute("SET LOCAL statement_timeout='15s'")
            return db
        except BaseException:
            db.close()
            raise

    @contextmanager
    def snapshot(self):
        db=self.connect_runtime()
        try:
            db.autocommit=False
            db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            yield db
        finally:
            try: db.rollback()
            finally: db.close()

    def dump(self):
        with self.snapshot() as db:
            return tuple((t,tuple(sorted(db.execute(sql.SQL("SELECT row_to_json(x)::text FROM {} AS x").format(
                sql.Identifier("t1_candidate",t))).fetchall()))) for t in TABLES)

    def company(self, history=None):
        with self.snapshot() as db, db.cursor() as c:
            return inspect_company(c,self.members,self.pool,self.history if history is None else history)

    def pool_budget(self):
        with self.snapshot() as db:
            row=db.execute("SELECT revision,currency,limit_minor,outstanding_minor,recognized_cost_minor,unknown_cost,policy_epoch,witness_epoch,source_digest FROM t1_candidate.sample_budgets").fetchone()
            return base.SampleBudget(self.pool.budget_id,*row)

    def execute(self,mapping,i,event,transition=None,unknown=False,record=True):
        wrapper=CompanyCoordinatedMapping(mapping,self.members,self.pool,self.history,event)
        c=LogicalT1Coordinator(lambda:postgres_transaction(lambda:LostAck(self.connect()) if unknown else self.connect(),wrapper))
        result=c.commit(i) if transition is None else c.commit_transition(i,*transition)
        if record: self.history+=(event,)
        return result

    def race(self):
        """A locks the actual stream inside the original wrapper; B must wait on A."""
        a=self.initial;ia=self.admit;ea=self._event(ia,"project-a",(),20)
        b,ib=self._claim_b(amount=40,budget=base.BUDGET);eb=self._event(ib,"project-b",(),40)
        a_locked=Event(); b_open=Event(); pids={}
        fixture=self
        class HoldA(CompanyCoordinatedMapping):
            def lock_and_validate(self,c,i):
                super().lock_and_validate(c,i)
                a_locked.set()
                need(b_open.wait(5),"D4_B_NOT_STARTED")
                deadline=monotonic()+5
                with fixture.connect_runtime() as watcher:
                    while monotonic()<deadline:
                        if pids["a"] in watcher.execute("SELECT pg_blocking_pids(%s)",(pids["b"],)).fetchone()[0]:
                            return
                        sleep(.025)
                raise RuntimeError("D4_ACTUAL_LOCK_WAIT_NOT_OBSERVED")
        def conn(label):
            db=self.connect();pids[label]=db.info.backend_pid
            if label=="b": b_open.set()
            return db
        def attempt(label,plan,spec,intent,event,wrapper):
            if label=="b": need(a_locked.wait(5),"D4_A_NOT_LOCKED")
            m=wrapper(D0PostgresAdmissionMapping(plan,spec,lambda:base.CLOCK),
                self.members,self.pool,(),event)
            co=LogicalT1Coordinator(lambda:postgres_transaction(lambda:conn(label),m))
            try: return ("commit",co.commit(intent))
            except ValueError as exc: return ("rejected",str(exc))
        with ThreadPoolExecutor(max_workers=2) as pool:
            x=pool.submit(attempt,"a",PLAN,a,ia,ea,HoldA)
            y=pool.submit(attempt,"b",self.plan_b,b,ib,eb,CompanyCoordinatedMapping)
            ra,rb=x.result(timeout=25),y.result(timeout=25)
        need(pids["a"]!=pids["b"] and ra[0]=="commit" and rb==("rejected","D0_COMPANY_ROW_HOLD"),"D4_RACE_RESULT_HOLD")
        self.history=(ea,)
        self.before=replace(self.before,state=RunState.ADMITTED,version=1)
        self.budget=self.pool_budget()
        need(self.budget.revision==1 and self.budget.outstanding_minor==20,"D4_RACE_BUDGET_HOLD")
        need(self.company().structural_match,"D4_RACE_COMPANY_POSTIMAGE_HOLD")
        with self.snapshot() as db:
            for t in ("events","outbox","fences","run_leases","run_mutations","run_audit","run_admissions","sample_reservations","company_event_order"):
                need(db.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier("t1_candidate",t))).fetchone()==(1,),"D4_RACE_EXTRA_ROW_"+t)
            for t in ("sample_settlements","run_lease_renewals","terminal_command_anchors"):
                need(db.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier("t1_candidate",t))).fetchone()==(0,),"D4_RACE_EXTRA_ROW_"+t)
        with self.snapshot() as db, db.cursor() as cur:
            winner=reconcile_admission(cur,PLAN,a,ia)
            need(winner.exact_sample_match and not winner.retry_allowed,"D4_WINNER_RECONCILIATION_HOLD")
        return ea

    def run(self, mark):
        need(self.company().structural_match and self.budget==base.BUDGET,"D4_INITIAL_HOLD")
        with self.snapshot() as db:
            for t in TABLES:
                n=db.execute(sql.SQL("SELECT count(*) FROM {} WHERE (tenant_id,company_id,environment_id)<>(%s,%s,%s)").format(sql.Identifier("t1_candidate",t)),SCOPE).fetchone()
                need(n==(0,),"D4_FOREIGN_VISIBLE_"+t)
        mark("coherent_two_project_preimage")
        mark("foreign_scope_hidden_all_16")
        self.race()
        mark("actual_two_connections_stream_wait_single_winner")
        mark("race_full_company_postimage")
        # Project B exceeds its own cap even though global available budget is sufficient.
        s,i=self._claim_b(amount=41)
        e=self._event(i,"project-b",self.history,41)
        old=self.dump()
        try: self.execute(D0PostgresAdmissionMapping(self.plan_b,s,lambda:base.CLOCK),i,e)
        except ValueError as exc: need(str(exc)=="D0_COMPANY_PROJECT_CAP_HOLD","D4_CAP_REASON_HOLD")
        else: raise RuntimeError("D4_CAP_ACCEPTED")
        need(self.dump()==old,"D4_CAP_WROTE")
        mark("project_cap_rejected_no_writes")
        s,i=self._claim_b(amount=40)
        e=self._event(i,"project-b",self.history,40)
        self.execute(D0PostgresAdmissionMapping(self.plan_b,s,lambda:base.CLOCK),i,e)
        self.budget=self.pool_budget()
        review=self.company()
        need(review.structural_match and (review.event_count,review.pool_revision,review.outstanding_minor,review.project_outstanding)==(2,2,60,(("project-a",20),("project-b",40))),"D4_TWO_PROJECT_HOLD")
        mark("fresh_second_project_shared_budget")
        self.ordinary(RunState.RUNNING)
        self.renewal()
        self.ordinary(RunState.VERIFYING)
        need(self.company().structural_match,"D4_CHAIN_HOLD")
        mark("original_transition_renewal_chain")
        m,i,e,p=self.terminal()
        old=self.dump()
        # Real SQL CHECK failure at the anchor insert after the original T1 writes.
        def bad_anchor(c,a):
            c.execute("INSERT INTO t1_candidate.terminal_command_anchors VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(*SCOPE,*a.row()[:-1],"bad"))
        with patch("app.core.event_store.terminal_anchor.write_anchor",bad_anchor):
            try: self.execute(m,i,e)
            except psycopg.Error as exc: need(exc.sqlstate=="23514","D4_ANCHOR_SQLSTATE_HOLD")
            else: raise RuntimeError("D4_ANCHOR_FAILURE_MISSING")
        need(self.dump()==old and self.company().structural_match,"D4_ANCHOR_ROLLBACK_HOLD")
        mark("anchor_sql_failure_all_16_postimages_unchanged")
        # Independently inject deferred FK violation AFTER original company postimage;
        # commit attempt must be UNKNOWN even when server reports 23503. No retry.
        m,i,e,p=self.terminal()
        class DeferredFailure(CompanyCoordinatedMapping):
            def verify_write_set(inner,c,intent,roles):
                receipt=super().verify_write_set(c,intent,roles)
                c.execute("INSERT INTO t1_candidate.company_event_order VALUES (%s,%s,%s,999,'project-b','demo-b-a',999,%s,%s,'[]')",(*SCOPE,"d0-tx-"+"f"*64,"f"*64))
                return receipt
        wrapper=DeferredFailure(m,self.members,self.pool,self.history,e)
        co=LogicalT1Coordinator(lambda:postgres_transaction(self.connect,wrapper))
        try: co.commit(i)
        except CommitOutcomeUnknown as exc: need(getattr(exc.__cause__,"sqlstate",None)=="23503","D4_DEFERRED_SQLSTATE_HOLD")
        else: raise RuntimeError("D4_DEFERRED_FAILURE_MISSING")
        need(self.dump()==old and self.company().structural_match,"D4_DEFERRED_ROLLBACK_HOLD")
        with self.snapshot() as db, db.cursor() as c:
            rejected=reconcile_lifecycle(c,p.spec,i)
            need(not rejected.exact_sample_match and not rejected.retry_allowed,"D4_ABSENCE_RETRY_HOLD")
        mark("deferred_fk_unknown_absence_no_retry")
        # UNKNOWN is quarantined; do NOT retry the same terminal intent. This
        # isolated run ends here. Positive lost-ack case uses a separate fresh stage.
        return {"status":"D4_R3_DEFERRED_UNKNOWN_HOLD","retry_allowed":False}

    def run_lost_ack(self,mark):
        need(self.company().structural_match,"D4_INITIAL_HOLD")
        # Separate fresh cluster, original admission and lifecycle chain.
        e=self.event(self.admit,"D0_RUN_ADMISSION",0,self.initial.amount_minor)
        self.execute(D0PostgresAdmissionMapping(PLAN,self.initial,lambda:base.CLOCK),self.admit,e)
        self.before=replace(self.before,state=RunState.ADMITTED,version=1)
        self.budget=self.pool_budget()
        self.ordinary(RunState.RUNNING)
        self.renewal()
        self.ordinary(RunState.VERIFYING)
        mark("lost_ack_preimage")
        m,i,e,p=self.terminal()
        # Pin a repeatable-read snapshot before the real commit.
        with self.snapshot() as reader:
            before=reader.execute("SELECT sequence FROM t1_candidate.company_stream_heads").fetchone()
            try: self.execute(m,i,e,unknown=True)
            except CommitOutcomeUnknown as exc: need(isinstance(exc.__cause__,OSError),"D4_LOST_ACK_CAUSE_HOLD")
            else: raise RuntimeError("D4_LOST_ACK_MISSING")
            need(reader.execute("SELECT sequence FROM t1_candidate.company_stream_heads").fetchone()==before,"D4_SNAPSHOT_CHANGED")
            try:
                with reader.transaction():
                    reader.execute("UPDATE t1_candidate.company_stream_heads SET sequence=sequence+1")
            except psycopg.Error as exc: need(exc.sqlstate=="25006","D4_READ_ONLY_SQLSTATE_HOLD")
            else: raise RuntimeError("D4_READ_ONLY_WRITE_ALLOWED")
        mark("repeatable_read_and_read_only")
        # No retry, fresh physical read-only connection; not independent authority.
        with self.snapshot() as db,db.cursor() as c:
            rr=reconcile_lifecycle(c,p.spec,i)
            verify_anchor(c,anchor_from_pin(p))
            cr=inspect_company(c,self.members,self.pool,self.history+(e,))
            need(rr.exact_sample_match and not rr.retry_allowed and not rr.committed and not rr.dispatch_allowed
                and cr.structural_match and cr.outstanding_minor==0 and cr.event_count==5,"D4_UNKNOWN_READBACK_HOLD")
        mark("lost_ack_actual_commit_exact_readback_no_retry")
        return {"status":"D4_R3_LOST_ACK_RECONCILED_HOLD","retry_allowed":False}
