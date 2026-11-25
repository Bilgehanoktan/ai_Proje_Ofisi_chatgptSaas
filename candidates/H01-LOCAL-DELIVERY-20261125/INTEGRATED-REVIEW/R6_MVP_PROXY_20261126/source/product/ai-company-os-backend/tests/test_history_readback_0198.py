"""Actual disposable SQLite integration of pinned history; not PostgreSQL evidence."""
import unittest
import sqlite3
from contextlib import closing
from dataclasses import replace
import test_lifecycle_mapping_0196 as lifecycle
from test_transition_mapping_0194 import SQLiteCursorShim
from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime.transition_command import transition_digest
from app.core.transaction.review import LogicalIntent, Operation
from app.core.event_store.history_readback import OrdinaryPin, LifecyclePin, inspect_history, office_history_projection

class HistoryTests(unittest.TestCase):
    def setUp(self):
        f=lifecycle.LifecycleTests(); f.setUp(); self.addCleanup(f.doCleanups)
        self.f=f; self.pins=[]
    def ordinary(self,before,lease,target):
        f=self.f
        i=LogicalIntent(before.scope,Operation.STATE_MUTATION,before.version,transition_digest(before,target),'ordinary-'+str(before.version),'ordinary-idem-'+str(before.version),lease.grant_id,lease.lease_id,None,lease.policy_epoch,lease.witness_epoch)
        receipt=f.ordinary(before,lease,target)
        self.pins.append(OrdinaryPin(i,before,target,lease))
        return replace(before,state=target,version=receipt.committed_version)
    def life(self,spec):
        f=self.f; i=f.intent(spec); r=f.execute(spec,i)
        self.pins.append(LifecyclePin(i,spec))
        return replace(spec.before,state=spec.before.state if spec.renewal else RunState.FAILED,version=r.committed_version)
    def chain(self):
        f=self.f
        running=self.ordinary(f.before,f.lease,RunState.RUNNING)
        renewal=f.renewal(running); running=self.life(renewal)
        verifying=self.ordinary(running,renewal.renewal,RunState.VERIFYING)
        self.life(f.failure(verifying,renewal.renewal,replace(f.budget,revision=2)))
    def inspect(self,pins=None,binding=None):
        f=self.f
        with closing(sqlite3.connect(f.path)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            with SQLiteCursorShim(db) as c:
                return inspect_history(c,binding or f.binding,tuple(self.pins) if pins is None else pins)
    def change(self,sql):
        with closing(sqlite3.connect(self.f.path)) as db,db: db.execute(sql)
    def hold(self,r):
        self.assertFalse(r.structural_match); self.assertIsNone(r.state); self.assertEqual(r.observations,())
        self.assertFalse(r.dispatch_allowed); self.assertFalse(r.release_ready)
        self.assertIsNone(office_history_projection(r)['event_count'])
    def test_admission_only(self):
        r=self.inspect(); self.assertTrue(r.structural_match); self.assertEqual(r.state,'ADMITTED'); self.assertEqual(len(r.observations),1)
    def test_full_history_and_projection(self):
        self.chain(); old=self.f.dump(); r=self.inspect()
        self.assertTrue(r.structural_match); self.assertEqual(r.state,'FAILED'); self.assertEqual(len(r.observations),5)
        self.assertEqual([x[1] for x in r.observations],['D0_RUN_ADMISSION','D0_RUN_TRANSITION','D0_LEASE_RENEWAL','D0_RUN_TRANSITION','D0_RUN_FAILURE'])
        self.assertEqual(office_history_projection(r),{'mode':'D0_HISTORY_SAMPLE','state':'FAILED','version':5,'event_count':5,'freshness':'HISTORICAL_SAMPLE','dispatch_allowed':False,'release_ready':False})
        self.assertEqual(self.f.dump(),old)
    def test_open_renewed(self):
        running=self.ordinary(self.f.before,self.f.lease,RunState.RUNNING); self.life(self.f.renewal(running))
        r=self.inspect(); self.assertTrue(r.structural_match); self.assertEqual(r.state,'RUNNING')
    def test_missing_pin(self):
        self.chain(); self.hold(self.inspect(tuple(self.pins[:-1])))
    def test_wrong_order(self):
        self.chain(); self.hold(self.inspect(tuple(reversed(self.pins))))
    def test_bad_intent(self):
        self.chain(); p=self.pins[0]; self.pins[0]=replace(p,intent=replace(p.intent,request_digest='0'*64)); self.hold(self.inspect())
    def test_wrong_lease_pin(self):
        self.chain(); p=self.pins[0]; self.pins[0]=replace(p,lease=replace(p.lease,expires_tick=99)); self.hold(self.inspect())
    def test_extra_pin_after_terminal(self):
        self.chain(); self.hold(self.inspect(tuple(self.pins+[self.pins[0]])))
    def test_missing_historical_mutation(self):
        self.chain(); self.change('DELETE FROM run_mutations WHERE version=2'); self.hold(self.inspect())
    def test_changed_historical_event(self):
        self.chain(); self.change("UPDATE events SET event_type='D0_RUN_FAILURE' WHERE version=2"); self.hold(self.inspect())
    def test_changed_historical_audit(self):
        self.chain(); self.change("UPDATE run_audit SET lease_digest='bad' WHERE version=2"); self.hold(self.inspect())
    def test_missing_outbox(self):
        self.chain(); self.change('DELETE FROM outbox WHERE event_id=(SELECT event_id FROM events WHERE version=2)'); self.hold(self.inspect())
    def test_missing_fence(self):
        self.chain(); self.change("DELETE FROM fences WHERE effect_key='ordinary-1'"); self.hold(self.inspect())
    def test_renewal_tamper(self):
        self.chain(); self.change("UPDATE run_lease_renewals SET new_lease_digest='bad'"); self.hold(self.inspect())
    def test_settlement_tamper(self):
        self.chain(); self.change('UPDATE sample_settlements SET released_minor=21'); self.hold(self.inspect())
    def test_extra_event(self):
        self.chain(); self.change("INSERT INTO events SELECT tenant_id,company_id,environment_id,run_id,99,'extra','D0_RUN_TRANSITION',request_digest FROM events WHERE version=1"); self.hold(self.inspect())
    def test_head_tamper(self):
        self.chain(); self.change("UPDATE run_heads SET version=99 WHERE task_id='a'"); self.hold(self.inspect())
    def test_open_lease_tamper(self):
        self.change('UPDATE run_leases SET expires_tick=99'); self.hold(self.inspect())
    def test_reservation_tamper(self):
        self.chain(); self.change('UPDATE sample_reservations SET amount_minor=21'); self.hold(self.inspect())
    def test_scope_pin_mismatch(self):
        self.chain(); p=self.pins[0]; self.pins[0]=replace(p,intent=replace(p.intent,scope=replace(p.intent.scope,run_id='demo-other'))); self.hold(self.inspect())
    def test_invalid_commands(self):
        self.hold(self.inspect([])); self.hold(self.inspect((None,)*1000))
    def test_invalid_projection(self):
        self.assertEqual(office_history_projection(None)['freshness'],'UNKNOWN')

if __name__=='__main__': unittest.main()
