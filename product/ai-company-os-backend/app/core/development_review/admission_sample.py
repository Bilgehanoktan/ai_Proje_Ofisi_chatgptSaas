"""Isolated D0 admission/reservation/settlement lab, never a canonical writer."""
from contextlib import closing, contextmanager
from pathlib import Path
import sqlite3
from app.core.agent_runtime.lifecycle import Scope, LeaseObservation, ClockSample
from app.core.policy.witness_review import WitnessSample
from app.core.transaction.review import LogicalIntent, Operation, RoleObservation, required_roles
from app.core.transaction.readback_review import HeadReadback, AdmissionPin
from app.core.transaction.admission_bundle import AdmissionBundle, inspect_admission_bundle
from app.engines.budget_engine.reservation_review import BudgetSnapshot, ReservationRequest

PROFILE = 'D0_ADMISSION_STORE_0186'
PLAN = '6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9'
SCOPE = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+PLAN,'research','demo-run','demo-agent','demo-principal')
OWNER = (SCOPE.tenant_id,SCOPE.company_id,SCOPE.principal_id)
DDL = """
CREATE TABLE meta(profile TEXT PRIMARY KEY CHECK(profile='D0_ADMISSION_STORE_0186'));
INSERT INTO meta VALUES('D0_ADMISSION_STORE_0186');
CREATE TABLE membership(tenant TEXT NOT NULL, company TEXT NOT NULL, principal TEXT NOT NULL, PRIMARY KEY(tenant,company,principal));
INSERT INTO membership VALUES('synthetic-tenant','synthetic-company','demo-principal');
CREATE TABLE sample_budget(id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL, phase TEXT NOT NULL, reserved INTEGER NOT NULL CHECK(reserved>=0), observed INTEGER NOT NULL CHECK(observed>=0), CHECK(reserved+observed<=1000));
INSERT INTO sample_budget VALUES(1,0,'PENDING',0,0);
CREATE TABLE sample_event(command TEXT PRIMARY KEY, version INTEGER UNIQUE NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('ADMIT','KNOWN_SAMPLE','UNKNOWN')));
CREATE TABLE sample_admission(id INTEGER PRIMARY KEY CHECK(id=1), command TEXT UNIQUE REFERENCES sample_event(command), tenant TEXT NOT NULL, company TEXT NOT NULL, principal TEXT NOT NULL, FOREIGN KEY(tenant,company,principal) REFERENCES membership);
CREATE TABLE sample_audit(command TEXT PRIMARY KEY REFERENCES sample_event(command), decision TEXT NOT NULL CHECK(decision='SAMPLE_ONLY'));
CREATE TABLE sample_outbox(command TEXT PRIMARY KEY REFERENCES sample_event(command), status TEXT NOT NULL CHECK(status='DENY'));
"""
# Fixed demonstration only; amounts are integer synthetic minor units, not money spent.
STATES = {'PENDING':(0,0,0,()), 'RESERVED':(1,100,0,('ADMIT',)),
          'SETTLED_SAMPLE':(2,0,60,('ADMIT','KNOWN_SAMPLE')), 'UNKNOWN_HOLD':(2,100,0,('ADMIT','UNKNOWN'))}


def fixed_bundle():
    s=SCOPE
    i=LogicalIntent(s,Operation.ADMISSION,0,PLAN,'demo-effect','demo-admit','demo-grant','demo-lease','demo-budget',3,4)
    h=HeadReadback(s,0,'demo-tx',PLAN,3,4)
    a=AdmissionPin(s,'demo-admission','demo-grant','demo-lease','demo-budget',PLAN,1,3,4)
    l=LeaseObservation(s,'demo-lease','demo-grant',1,1,1,3,4,15,7)
    c=ClockSample(8,3,4,3)
    q=ReservationRequest(s,'demo-budget',0,'TRY',100,'demo-admit',3,4)
    b=BudgetSnapshot(s,'demo-budget',0,'TRY',1000,0,0,False,3,4,PLAN)
    w=WitnessSample(s,'demo-root',4,1,PLAN,7)
    refs={'ADMISSION':'demo-admission','LEASE':'demo-lease','BUDGET':'demo-budget'}
    rows=tuple(RoleObservation(k,refs.get(k,k.lower()),s,PLAN,'demo-tx',0,3,4) for k in sorted(required_roles(i)))
    return AdmissionBundle(i,rows,h,h,a,a,l,l,c,q,b,b,w,w,3)


def _path(path):
    p=Path(path)
    if not p.name.endswith('.admission.d0.sqlite') or p.is_symlink():
        raise ValueError('ADMISSION_SAMPLE_PATH_HOLD')
    return p


def _state(db):
    if db.execute('SELECT profile FROM meta LIMIT 2').fetchall()!=[(PROFILE,)] or db.execute('SELECT tenant,company,principal FROM membership LIMIT 2').fetchall()!=[OWNER]:
        raise ValueError('ADMISSION_SAMPLE_SCOPE_HOLD')
    row=db.execute('SELECT version,phase,reserved,observed FROM sample_budget WHERE id=1').fetchone()
    if not row or row[1] not in STATES:
        raise ValueError('ADMISSION_SAMPLE_STATE_HOLD')
    version,reserved,observed,kinds=STATES[row[1]]
    expected=[('demo-admit' if n==1 else 'demo-settle',n,k) for n,k in enumerate(kinds,1)]
    if (row[0],row[2],row[3])!=(version,reserved,observed) or db.execute('SELECT command,version,kind FROM sample_event ORDER BY version LIMIT 3').fetchall()!=expected:
        raise ValueError('ADMISSION_SAMPLE_STATE_HOLD')
    commands=sorted(r[0] for r in expected)
    for table,column,value in (('sample_audit','decision','SAMPLE_ONLY'),('sample_outbox','status','DENY')):
        if db.execute(f'SELECT command,{column} FROM {table} ORDER BY command LIMIT 3').fetchall()!=[(c,value) for c in commands]:
            raise ValueError('ADMISSION_SAMPLE_BINDING_HOLD')
    if db.execute('SELECT command,tenant,company,principal FROM sample_admission LIMIT 2').fetchall()!=([('demo-admit',*OWNER)] if version else []):
        raise ValueError('ADMISSION_SAMPLE_BINDING_HOLD')
    return row


@contextmanager
def _open(path, readonly=False):
    p=_path(path)
    if not p.is_file():
        raise ValueError('ADMISSION_SAMPLE_MISSING')
    with closing(sqlite3.connect(p.resolve().as_uri()+('?mode=ro' if readonly else '?mode=rw'),uri=True,timeout=2)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        if readonly: db.execute('PRAGMA query_only=ON')
        with db:
            db.execute('BEGIN' if readonly else 'BEGIN IMMEDIATE')
            yield db


class AdmissionSample:
    def __init__(self,path): self.path=_path(path)

    def create(self):
        with self.path.open('xb'): pass
        try:
            with closing(sqlite3.connect(self.path)) as db:
                db.executescript('BEGIN;'+DDL+'COMMIT;')
        except BaseException:
            self.path.unlink(missing_ok=True)
            raise

    def apply(self,owner,kind,version):
        if type(owner) is not tuple or owner!=OWNER or type(kind) is not str or kind not in ('ADMIT','KNOWN_SAMPLE','UNKNOWN') or type(version) is not int or version!=(0 if kind=='ADMIT' else 1):
            raise ValueError('ADMISSION_SAMPLE_REQUEST_HOLD')
        command='demo-admit' if kind=='ADMIT' else 'demo-settle'
        with _open(self.path) as db:
            head=_state(db)
            prior=db.execute('SELECT kind FROM sample_event WHERE command=?',(command,)).fetchone()
            if prior:
                if prior!=(kind,): raise ValueError('ADMISSION_SAMPLE_IDEMPOTENCY_HOLD')
                return 'DUPLICATE_IGNORED'
            if head[0]!=version: raise ValueError('ADMISSION_SAMPLE_CAS_HOLD')
            if kind=='ADMIT':
                review=inspect_admission_bundle(fixed_bundle())
                if review.reason!='D0_BUNDLE_MATCH_AUTHORITY_UNPROVEN' or review.decision!='HOLD' or review.commit_allowed or review.dispatch_allowed or review.spend_allowed or review.authoritative:
                    raise ValueError('ADMISSION_SAMPLE_BUNDLE_HOLD')
            target={'ADMIT':'RESERVED','KNOWN_SAMPLE':'SETTLED_SAMPLE','UNKNOWN':'UNKNOWN_HOLD'}[kind]
            v,r,o,_=STATES[target]
            if db.execute('UPDATE sample_budget SET version=?,phase=?,reserved=?,observed=? WHERE id=1 AND version=?',(v,target,r,o,version)).rowcount!=1:
                raise ValueError('ADMISSION_SAMPLE_CAS_HOLD')
            db.execute('INSERT INTO sample_event VALUES(?,?,?)',(command,v,kind))
            if kind=='ADMIT': db.execute('INSERT INTO sample_admission VALUES(1,?,?,?,?)',(command,*OWNER))
            db.execute("INSERT INTO sample_audit VALUES(?,'SAMPLE_ONLY')",(command,))
            db.execute("INSERT INTO sample_outbox VALUES(?,'DENY')",(command,))
            _state(db)
            return target


def read_admission(path):
    with _open(path,readonly=True) as db:
        version,phase,reserved,observed=_state(db)
    return {'schema_version':'admission.sample.v1-D0','mode':PROFILE,'tenant':OWNER[0],'company':OWNER[1],
            'phase':phase,'version':version,'sample_reserved_minor':reserved,'sample_observed_minor':observed,
            'sample_remaining_minor':1000-reserved-observed,'admission':'DENY','dispatch_allowed':False,
            'spend_allowed':False,'release_ready':False,'actual_cost_minor':None,'authoritative':False}
