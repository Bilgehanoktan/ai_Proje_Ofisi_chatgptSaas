"""J2-R2 disposable synthetic SQL experiment, not a product adapter or migration.
No provider, independent custody, real budget or authority. Uses the exact R1 row contract.
"""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from membership_review import (BINDING, ROW, SCOPE, _binding_ok, _shape, _phase,
                               _pin, _uint, _token, _scope)

SYNTHETIC = ('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
DDL = '''
CREATE TABLE b (id TEXT PRIMARY KEY, revision INTEGER NOT NULL CHECK(revision>=0),
 limit_minor INTEGER NOT NULL CHECK(limit_minor>=0), outstanding INTEGER NOT NULL CHECK(outstanding>=0),
 recognized INTEGER NOT NULL CHECK(recognized>=0), unknown INTEGER NOT NULL CHECK(unknown IN (0,1)),
 CHECK(outstanding<=limit_minor-recognized));
CREATE TABLE pool (run TEXT PRIMARY KEY, budget TEXT NOT NULL REFERENCES b(id),
 issued INTEGER NOT NULL CHECK(issued>0), free INTEGER NOT NULL CHECK(free>=0 AND free<=issued),
 closed INTEGER NOT NULL DEFAULT 0 CHECK(closed IN (0,1)), owner TEXT NOT NULL,
 released INTEGER NOT NULL DEFAULT 0 CHECK(released>=0 AND released<=issued));
CREATE TABLE member (pin TEXT PRIMARY KEY, run TEXT NOT NULL REFERENCES pool(run),
 budget TEXT NOT NULL REFERENCES b(id), reservation TEXT NOT NULL, idem TEXT NOT NULL UNIQUE,
 invocation TEXT NOT NULL UNIQUE, amount INTEGER NOT NULL CHECK(amount>0),
 state TEXT NOT NULL CHECK(state IN ('RESERVED','CONSUMED','UNKNOWN','USAGE_KNOWN','RECONCILED')),
 ceiling INTEGER NOT NULL CHECK(ceiling>0 AND ceiling<=amount), max_input INTEGER NOT NULL CHECK(max_input>=0),
 max_output INTEGER NOT NULL CHECK(max_output>=0), body TEXT NOT NULL, UNIQUE(budget,reservation));
CREATE TABLE receipt (pin TEXT PRIMARY KEY, member TEXT NOT NULL REFERENCES member(pin),
 role TEXT NOT NULL CHECK(role IN ('RESERVATION','CONSUME','USAGE','RECONCILIATION')),
 tx TEXT NOT NULL UNIQUE, UNIQUE(member,role));
CREATE TABLE journal (tx TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('EVENT','OUTBOX','AUDIT')),
 kind TEXT NOT NULL, target TEXT NOT NULL, revision INTEGER NOT NULL, PRIMARY KEY(tx,role));
'''
OWNER_FIELDS = SCOPE + ('plan_revision','task_id','run_id','agent_instance_id','principal_id',
 'attempt','project_id','budget_id','currency','admission_id','admission_tx','admission_request_digest',
 'lease_id','grant_id','fence','policy_epoch','witness_epoch')

class Hold(ValueError):
    """Fixture rejected; no authorization semantics."""

class LostAck(RuntimeError):
    """Fixture commit occurred but response lost; inspect via separate connection."""


def require(ok, reason):
    if not ok: raise Hold(reason)


def encode(row):
    return json.dumps(row, sort_keys=True, separators=(',',':'), allow_nan=False)


class AllocationFixture:
    """Use only on a newly created temporary fixture DB. No migration of existing files."""
    def __init__(self, path):
        self.path = Path(path)

    def connect(self):
        db=sqlite3.connect(self.path, isolation_level=None, timeout=0)
        db.execute('PRAGMA foreign_keys=ON')
        return db

    def seed(self, owners, limit=200):
        """Test setup: owner rows supplied by tests; all pools pre-reserved, no admission writer."""
        require(not self.path.exists(), 'FRESH_DB_REQUIRED')
        require(type(owners) is tuple and 0<len(owners)<=16 and _uint(limit), 'FIXTURE_SETUP_HOLD')
        for owner,amount in owners:
            require(_shape(owner,BINDING) and _binding_ok(owner) and _uint(amount) and amount>0,'OWNER_SHAPE_HOLD')
        budget=owners[0][0]['budget_id']; total=sum(n for _,n in owners)
        require(total<=limit and all(tuple(o[k] for k in ('budget_id','currency','policy_epoch','witness_epoch'))==tuple(owners[0][0][k] for k in ('budget_id','currency','policy_epoch','witness_epoch')) for o,_ in owners),'FIXTURE_SETUP_HOLD')
        require(len({o['admission_tx'] for o,_ in owners})==len(owners) and len({o['admission_id'] for o,_ in owners})==len(owners),'ADMISSION_ALIAS_HOLD')
        db=self.connect()
        try:
            db.executescript(DDL)
            db.execute('BEGIN IMMEDIATE')
            try:
                db.execute('INSERT INTO b VALUES (?,?,?,?,?,0)',(budget,2,limit,total,0))
                for owner,amount in owners:
                    # The original run issuance revision is retained separately, not reused as invocation revision.
                    root={k:owner[k] for k in OWNER_FIELDS};root['run_issuance_revision']=2
                    db.execute('INSERT INTO pool VALUES (?,?,?,?,0,?,0)',(owner['run_id'],budget,amount,amount,encode(root)))
                self._invariant(db,budget);db.commit()
            except BaseException: db.rollback();raise
        finally: db.close()

    @staticmethod
    def _budget(db,budget):
        r=db.execute('SELECT revision,limit_minor,outstanding,recognized,unknown FROM b WHERE id=?',(budget,)).fetchone()
        require(r is not None,'BUDGET_MISSING_HOLD');return r

    @staticmethod
    def _pool(db,run,budget):
        r=db.execute('SELECT issued,free,closed,owner,released FROM pool WHERE run=? AND budget=?',(run,budget)).fetchone()
        require(r is not None,'RUN_MEMBERSHIP_MISSING_HOLD');return r

    @staticmethod
    def _member(db,pin,budget):
        r=db.execute('SELECT body,ceiling,max_input,max_output FROM member WHERE pin=? AND budget=?',(pin,budget)).fetchone()
        require(r is not None,'INVOCATION_MISSING_HOLD');return json.loads(r[0]),*r[1:]

    def _invariant(self,db,budget):
        rev,limit,outstanding,recognized,unknown=self._budget(db,budget)
        pools=db.execute('SELECT run,issued,free,closed,released,owner FROM pool WHERE budget=?',(budget,)).fetchall()
        pending=0;spent=0;quarantined=False
        for run,issued,free,closed,released,owner in pools:
            owner=json.loads(owner)
            rows=db.execute('SELECT pin,amount,state,body,reservation,idem,invocation FROM member WHERE run=? AND budget=?',(run,budget)).fetchall()
            require(issued==free+released+sum(r[1] for r in rows),'RUN_CONSERVATION_HOLD')
            require(not closed or (free==0 and not rows),'NO_EFFECT_RELEASE_HOLD')
            pending+=free
            for pin,amount,state,body,reservation,idem,invocation in rows:
                r=json.loads(body)
                require(_shape(r,ROW) and _binding_ok(r) and _phase(r) and (pin,amount,state,reservation,idem,invocation)==(r['membership_pin'],r['reserved_minor'],r['state'],r['reservation_id'],r['invocation_idempotency_key'],r['invocation_pin']),'ROW_DRIFT_HOLD')
                expected={'RESERVATION':(r['reservation_pin'],r['reservation_tx'])}
                for role,p,t in [('CONSUME','consume_receipt_pin','consume_tx'),('USAGE','usage_pin','usage_tx'),('RECONCILIATION','reconciliation_pin','reconciliation_tx')]:
                    if r[p] is not None: expected[role]=(r[p],r[t])
                actual={role:(p,t) for role,p,t in db.execute('SELECT role,pin,tx FROM receipt WHERE member=?',(pin,))}
                require(expected==actual and all(r[k]==owner[k] for k in OWNER_FIELDS),'RECEIPT_OR_OWNER_DRIFT_HOLD')
                if state=='RECONCILED': spent+=r['recognized_minor']
                else: pending+=amount
                quarantined|=state=='UNKNOWN'
        require((outstanding,recognized,unknown)==(pending,spent,int(quarantined)) and outstanding+recognized<=limit,'BUDGET_CONSERVATION_HOLD')
        # Fixture journal coherence: all three roles, exact target and one revision per tx.
        # No cryptographic custody or protection against coherent full-database rewrites.
        journal={}
        for tx,role,kind,target,revision in db.execute('SELECT tx,role,kind,target,revision FROM journal'):
            entry=journal.setdefault(tx,[kind,target,revision,set()])
            require(entry[:3]==[kind,target,revision],'JOURNAL_ROLE_DRIFT_HOLD');entry[3].add(role)
        require(len(journal)==rev-2 and all(n==i for i,n in enumerate(sorted(v[2] for v in journal.values()),3)),'JOURNAL_REVISION_HOLD')
        receipts={t:(m,role) for m,role,t in db.execute('SELECT member,role,tx FROM receipt')}
        require(set(receipts)<=set(journal),'JOURNAL_RECEIPT_MISSING_HOLD')
        for tx,(kind,target,_,roles) in journal.items():
            require(roles=={'EVENT','OUTBOX','AUDIT'},'JOURNAL_ROLE_MISSING_HOLD')
            if kind in ('ALLOCATE','CONSUME','USAGE','RECONCILE'):
                require(receipts.get(tx)==(target,{'ALLOCATE':'RESERVATION','CONSUME':'CONSUME','USAGE':'USAGE','RECONCILE':'RECONCILIATION'}[kind]),'JOURNAL_RECEIPT_DRIFT_HOLD')
            elif kind=='UNKNOWN':
                require(tx not in receipts and db.execute("SELECT 1 FROM member WHERE pin=? AND state='UNKNOWN'",(target,)).fetchone(),'JOURNAL_UNKNOWN_DRIFT_HOLD')
            elif kind=='CLOSE_UNUSED':
                require(tx not in receipts and db.execute('SELECT 1 FROM pool WHERE run=? AND closed=1',(target,)).fetchone(),'JOURNAL_RELEASE_DRIFT_HOLD')
            else: raise Hold('JOURNAL_KIND_HOLD')
        require(sorted(v[1] for v in journal.values() if v[0]=='UNKNOWN')==[x[0] for x in db.execute("SELECT pin FROM member WHERE state='UNKNOWN' ORDER BY pin")] and sorted(v[1] for v in journal.values() if v[0]=='CLOSE_UNUSED')==[x[0] for x in db.execute('SELECT run FROM pool WHERE closed=1 ORDER BY run')],'JOURNAL_TERMINAL_DRIFT_HOLD')

    @contextmanager
    def _transaction(self,budget,expected_revision,tx,kind,target,*,allow_unknown=False,fault=None):
        require(_token(budget) and _token(tx) and _token(target) and _uint(expected_revision),'COMMAND_SHAPE_HOLD')
        db=self.connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            rev,limit,outstanding,recognized,unknown=self._budget(db,budget)
            require(rev==expected_revision and rev<2**63-1,'STALE_BUDGET_CAS_HOLD')
            require(allow_unknown or not unknown,'UNKNOWN_COST_HOLD')
            require(not db.execute('SELECT 1 FROM journal WHERE tx=?',(tx,)).fetchone(),'TRANSACTION_REPLAY_HOLD')
            require(all(tx!=json.loads(o[0])['admission_tx'] for o in db.execute('SELECT owner FROM pool')),'ADMISSION_TRANSACTION_ALIAS_HOLD')
            self._invariant(db,budget)
            yield db
            self._fault(fault,'before_budget')
            require(db.execute('UPDATE b SET revision=revision+1 WHERE id=? AND revision=?',(budget,rev)).rowcount==1,'STALE_BUDGET_CAS_HOLD')
            self._fault(fault,'after_budget')
            for role in ('EVENT','OUTBOX','AUDIT'):
                db.execute('INSERT INTO journal VALUES (?,?,?,?,?)',(tx,role,kind,target,rev+1))
                self._fault(fault,'after_'+role.lower())
            self._invariant(db,budget);db.commit()
            if fault=='lost_ack': raise LostAck('COMMITTED_ACK_LOST_HOLD')
        except BaseException:
            if db.in_transaction: db.rollback()
            raise
        finally: db.close()

    @staticmethod
    def _fault(fault,stage):
        if fault==stage: raise RuntimeError('INJECTED_'+stage)

    @staticmethod
    def _receipt(db,pin,member,role,tx):
        require(_pin(pin),'RECEIPT_PIN_HOLD')
        db.execute('INSERT INTO receipt VALUES (?,?,?,?)',(pin,member,role,tx))

    def allocate(self,binding,expected_revision,*,ceiling,max_input,max_output,fault=None):
        require(_shape(binding,BINDING) and _binding_ok(binding),'BINDING_HOLD')
        require(all(_uint(x) for x in (ceiling,max_input,max_output)) and 0<ceiling<=binding['reserved_minor'],'CEILING_HOLD')
        require(_uint(expected_revision) and binding['reservation_budget_revision']==expected_revision+1,'ISSUANCE_REVISION_HOLD')
        b=binding;budget=b['budget_id'];run=b['run_id'];pin=b['membership_pin'];tx=b['reservation_tx'];amount=b['reserved_minor']
        with self._transaction(budget,expected_revision,tx,'ALLOCATE',pin,fault=fault) as db:
            issued,free,closed,owner,released=self._pool(db,run,budget);owner=json.loads(owner)
            require(all(b[k]==owner[k] for k in OWNER_FIELDS) and tx!=owner['admission_tx'],'OWNER_BINDING_HOLD')
            require(not closed and amount<=free,'RUN_CAPACITY_HOLD')
            r=dict.fromkeys(ROW);r.update(b,state='RESERVED')
            db.execute('INSERT INTO member VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(pin,run,budget,b['reservation_id'],b['invocation_idempotency_key'],b['invocation_pin'],amount,'RESERVED',ceiling,max_input,max_output,encode(r)))
            self._fault(fault,'after_member')
            self._receipt(db,b['reservation_pin'],pin,'RESERVATION',tx)
            self._fault(fault,'after_receipt')
            require(db.execute('UPDATE pool SET free=free-? WHERE run=? AND budget=? AND closed=0 AND free>=?',(amount,run,budget,amount)).rowcount==1,'RUN_CAPACITY_HOLD')
            # Allocation does not increment outstanding: admission reserved it already.

    def advance(self,budget,pin,expected_revision,tx,action,*,receipt=None,consume_pin=None,usage_pin=None,
                actual=None,input_tokens=None,output_tokens=None,fault=None):
        require(action in ('CONSUME','UNKNOWN','USAGE','RECONCILE') and _pin(pin),'ACTION_HOLD')
        with self._transaction(budget,expected_revision,tx,action,pin,allow_unknown=action=='UNKNOWN',fault=fault) as db:
            r,ceiling,mi,mo=self._member(db,pin,budget)
            require(tx!=r['admission_tx'],'ADMISSION_TRANSACTION_ALIAS_HOLD')
            if action=='CONSUME':
                require(r['state']=='RESERVED' and all(x is None for x in (consume_pin,usage_pin,actual,input_tokens,output_tokens)),'CONSUME_PHASE_HOLD')
                r.update(state='CONSUMED',consume_tx=tx,consume_receipt_pin=receipt)
            elif action=='UNKNOWN':
                require(r['state'] in ('RESERVED','CONSUMED') and all(x is None for x in (receipt,consume_pin,usage_pin,actual,input_tokens,output_tokens)),'UNKNOWN_PHASE_HOLD')
                r.update(state='UNKNOWN');db.execute('UPDATE b SET unknown=1 WHERE id=?',(budget,))
            elif action=='USAGE':
                require(r['state']=='CONSUMED' and consume_pin==r['consume_receipt_pin'] and usage_pin is None,'USAGE_PHASE_HOLD')
                require(all(_uint(x) for x in (actual,input_tokens,output_tokens)) and actual<=ceiling and input_tokens<=mi and output_tokens<=mo,'USAGE_LIMIT_HOLD')
                r.update(state='USAGE_KNOWN',usage_tx=tx,usage_pin=receipt,actual_minor=actual,input_tokens=input_tokens,output_tokens=output_tokens)
            else:
                require(r['state']=='USAGE_KNOWN' and usage_pin==r['usage_pin'] and consume_pin==r['consume_receipt_pin'] and all(x is None for x in (actual,input_tokens,output_tokens)),'RECONCILIATION_PHASE_HOLD')
                n=r['actual_minor'];a=r['reserved_minor'];r.update(state='RECONCILED',reconciliation_tx=tx,reconciliation_pin=receipt,recognized_minor=n,released_minor=a-n)
                require(db.execute('UPDATE b SET outstanding=outstanding-?,recognized=recognized+? WHERE id=? AND outstanding>=? AND unknown=0',(a,n,budget,a)).rowcount==1,'BALANCE_HOLD')
            require(_phase(r),'PHASE_SHAPE_HOLD')
            db.execute('UPDATE member SET state=?,body=? WHERE pin=? AND budget=?',(r['state'],encode(r),pin,budget));self._fault(fault,'after_member')
            if action!='UNKNOWN': self._receipt(db,receipt,pin,{'CONSUME':'CONSUME','USAGE':'USAGE','RECONCILE':'RECONCILIATION'}[action],tx)
            self._fault(fault,'after_receipt')

    def close_unused(self,budget,run,expected_revision,tx,*,fault=None):
        """Only untouched pool; not a replacement for original failure-only settlement."""
        with self._transaction(budget,expected_revision,tx,'CLOSE_UNUSED',run,fault=fault) as db:
            issued,free,closed,owner,released=self._pool(db,run,budget)
            require(tx!=json.loads(owner)['admission_tx'] and not closed and free==issued and not db.execute('SELECT 1 FROM member WHERE run=?',(run,)).fetchone(),'RUN_RELEASE_HOLD')
            db.execute('UPDATE pool SET free=0,closed=1,released=? WHERE run=?',(free,run))
            require(db.execute('UPDATE b SET outstanding=outstanding-? WHERE id=? AND outstanding>=?',(free,budget,free)).rowcount==1,'BALANCE_HOLD')

    def readback(self,budget):
        """Coherent diagnostic read; fixture data only, no owner receipt or freshness authority."""
        db=self.connect()
        try:
            db.execute('BEGIN');self._invariant(db,budget)
            result={'budget':self._budget(db,budget),'pools':db.execute('SELECT run,issued,free,closed,released FROM pool WHERE budget=? ORDER BY run',(budget,)).fetchall(),
                    'members':tuple(json.loads(x[0]) for x in db.execute('SELECT body FROM member WHERE budget=? ORDER BY pin',(budget,))),
                    'journal':db.execute('SELECT tx,role,kind,target,revision FROM journal ORDER BY tx,role').fetchall(),
                    'receipts':db.execute('SELECT pin,member,role,tx FROM receipt ORDER BY pin').fetchall()}
            db.commit();return result
        finally: db.close()
