"""D0 SQLite lab: scoped immutable staffing snapshots, no product DB or grant."""
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from org_model import Org, Unit, Seat
from staffing import Staffing, Definition, Instance, Binding
from operations import digest
from integration_guard import token, require, validate_staffing, hex_digest

SCHEMA = Path(__file__).with_name('schema.sql')
IMMUTABLE = ('org_revision','org_unit','org_position','org_definition_ref','org_instance_ref','org_binding','org_notice')

@dataclass(frozen=True)
class Scope:
    tenant: str
    company: str
    environment: str
    def key(self):
        for v in (self.tenant,self.company,self.environment): token(v)
        require(self.tenant.startswith('synthetic-') and self.company.startswith('synthetic-') and self.environment in ('A0_SAMPLE_ONLY','A0_REVIEW_ONLY'), 'D0_SCOPE')
        return self.tenant,self.company,self.environment


def initialize(path):
    """Fresh disposable file only; no migration or existing database adoption."""
    p = Path(path)
    with p.open('xb'): pass
    db = sqlite3.connect(p)
    try:
        db.executescript(SCHEMA.read_text(encoding='utf-8'))
        for table in IMMUTABLE:
            for verb in ('UPDATE','DELETE'):
                db.execute(f"CREATE TRIGGER {table}_{verb.lower()} BEFORE {verb} ON {table} BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END")
        db.commit()
    finally:
        db.close()


def revision_id(key, seq, prev, staffing_digest):
    return digest(['org.persistence.v0-D0',key,seq,prev,staffing_digest])


def notice_id(key, rev, seq, prev):
    return digest(['ORG_REVISION_RECORDED_D0',key,rev,seq,prev,'HOLD'])


class Store:
    """Local trusted caller binds scope once. This is NOT DB-enforced tenant RLS."""
    def __init__(self,path,scope):
        require(type(scope) is Scope,'SCOPE'); self._key=scope.key()
        self._path=Path(path).resolve().as_uri()
    def _connect(self,write=False):
        db=sqlite3.connect(self._path+('?mode=rw' if write else '?mode=ro'),uri=True,isolation_level=None,timeout=2)
        db.execute('PRAGMA foreign_keys=ON')
        if not write: db.execute('PRAGMA query_only=ON')
        return db
    def _head(self,db):
        row=db.execute('SELECT rev FROM org_head WHERE t=? AND c=? AND e=?',self._key).fetchone()
        return row[0] if row else None
    def _read(self,db,rev):
        hex_digest(rev); k=self._key+(rev,)
        row=db.execute('SELECT seq,prev,staffing_digest,prev_staffing FROM org_revision WHERE t=? AND c=? AND e=? AND rev=?',k).fetchone()
        require(row is not None,'REVISION_NOT_FOUND')
        seq,prev,sd,ps=row
        if prev is not None:
            parent=db.execute('SELECT seq,staffing_digest FROM org_revision WHERE t=? AND c=? AND e=? AND rev=?',self._key+(prev,)).fetchone()
            require(parent==(seq-1,ps),'PARENT_MISMATCH')
        def rows(table,cols):
            # Identifiers below are internal constants, never supplied by caller.
            return db.execute(f'SELECT {cols} FROM {table} WHERE t=? AND c=? AND e=? AND rev=? ORDER BY 1',k).fetchall()
        s=Staffing(Org(*self._key[:2],tuple(Unit(*x) for x in rows('org_unit','id,kind,parent')),tuple(Seat(*x) for x in rows('org_position','id,unit,role,manager'))),tuple(Definition(*x) for x in rows('org_definition_ref','id,role')),tuple(Instance(*x,*self._key[:2]) for x in rows('org_instance_ref','id,definition')),tuple(Binding(*x) for x in rows('org_binding','seat,instance')),ps)
        require(all(i.id.startswith('demo-') for i in s.instances),'D0_INSTANCE_REFERENCE')
        roles={d.id:d.role for d in s.definitions}; seats={p.id:p.role for p in s.org.seats}
        require(rows('org_instance_ref','id,definition,role')==sorted((i.id,i.definition,roles.get(i.definition)) for i in s.instances) and rows('org_binding','seat,instance,role')==sorted((b.seat,b.instance,seats.get(b.seat)) for b in s.bindings),'ROLE_REFERENCE')
        require(validate_staffing(s)==sd and revision_id(self._key,seq,prev,sd)==rev,'REVISION_DIGEST')
        notice=rows('org_notice','digest,kind,state')
        require(notice==[(notice_id(self._key,rev,seq,prev),'ORG_REVISION_RECORDED_D0','HOLD')],'NOTICE_MISMATCH')
        return s,seq,prev,notice[0][0]
    def record(self,s,expected_head):
        """D0-only compare-and-swap, snapshot + notice + head in one transaction."""
        sd=validate_staffing(s)
        require((s.org.tenant,s.org.company)==self._key[:2],'STAFFING_SCOPE')
        require(all(i.id.startswith('demo-') for i in s.instances),'D0_INSTANCE_REFERENCE')
        db=self._connect(True)
        try:
            db.execute('BEGIN IMMEDIATE'); old=self._head(db)
            require(old==expected_head,'STALE_HEAD')
            if old is None:
                seq=1; require(s.previous is None,'GENESIS')
            else:
                prior,n,_,_=self._read(db,old); seq=n+1
                require(s.previous==prior.revision(),'STAFFING_PARENT')
            rev=revision_id(self._key,seq,old,sd); k=self._key+(rev,)
            db.execute('INSERT INTO org_revision VALUES (?,?,?,?,?,?,?,?)',k+(seq,old,sd,s.previous))
            for table,values in (
                ('org_unit',[(u.id,u.kind,u.parent) for u in s.org.units]),
                ('org_position',[(p.id,p.unit,p.role,p.reports_to) for p in s.org.seats]),
                ('org_definition_ref',[(d.id,d.role) for d in s.definitions]),
                ('org_instance_ref',[(i.id,i.definition,{d.id:d.role for d in s.definitions}[i.definition]) for i in s.instances]),
                ('org_binding',[(b.seat,b.instance,{p.id:p.role for p in s.org.seats}[b.seat]) for b in s.bindings]),
            ):
                for value in values:
                    db.execute(f'INSERT INTO {table} VALUES ({",".join("?" for _ in k+value)})',k+value)
            db.execute('INSERT INTO org_notice VALUES (?,?,?,?,?,?,?)',k+(notice_id(self._key,rev,seq,old),'ORG_REVISION_RECORDED_D0','HOLD'))
            if old is None: db.execute('INSERT INTO org_head VALUES (?,?,?,?)',k)
            else:
                cur=db.execute('UPDATE org_head SET rev=? WHERE t=? AND c=? AND e=? AND rev=?',(rev,)+self._key+(old,))
                require(cur.rowcount==1,'CAS')
            self._read(db,rev); db.commit(); return rev
        except BaseException:
            db.rollback(); raise
        finally: db.close()
    def read(self,rev=None):
        db=self._connect()
        try:
            db.execute('BEGIN'); target=self._head(db) if rev is None else rev
            require(target is not None,'EMPTY'); return target,self._read(db,target)
        finally: db.close()
    def audit(self,expected_head):
        """Check full local lineage against separately retained head; not a signature."""
        hex_digest(expected_head); db=self._connect()
        try:
            db.execute('BEGIN'); require(self._head(db)==expected_head,'HEAD_MISMATCH')
            rows=db.execute('SELECT rev FROM org_revision WHERE t=? AND c=? AND e=? ORDER BY seq',self._key).fetchall()
            prev=None
            for n,(rev,) in enumerate(rows,1):
                _,seq,parent,_=self._read(db,rev); require(seq==n and parent==prev,'LINEAGE'); prev=rev
            require(prev==expected_head,'LINEAGE_HEAD'); return len(rows)
        finally: db.close()
    def studio_view(self,expected_head):
        hex_digest(expected_head); rev,(s,seq,prev,_)=self.read(); require(rev==expected_head,'HEAD_MISMATCH')
        occupied={b.seat for b in s.bindings}
        return {'schema':'org.studio.preview.v0-D0','scope':dict(zip(('tenant_id','company_id','environment_id'),self._key)), 'revision':rev,'sequence':seq,'previous_revision':prev,'units':[{'id':u.id,'kind':u.kind,'parent':u.parent} for u in s.org.units],'positions':[{'id':p.id,'unit':p.unit,'role':p.role,'reports_to':p.reports_to,'occupied':p.id in occupied} for p in s.org.seats],'decision':'HOLD','authoritative':False,'identity_owner':'HOLD','geometry_join':'HOLD','runtime_binding':None,'dispatch_allowed':False}
