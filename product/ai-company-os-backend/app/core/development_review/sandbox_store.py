"""File-backed D0 workbench, never canonical T1, admission, lease or event authority."""
from contextlib import closing, contextmanager
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from app.core.orchestrator.engine import canonical_plan
from app.core.agent_runtime.lifecycle import token, uint
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.sample_adapter import sample_model
from app.core.agent_runtime.lifecycle import Scope

TENANT = 'synthetic-tenant'
COMPANY = 'synthetic-company'
ENV = 'A0_SAMPLE_ONLY'
PROFILE = 'D0_WORKBENCH_0182'
DDL = """CREATE TABLE meta(profile TEXT PRIMARY KEY CHECK(profile='D0_WORKBENCH_0182'), tenant TEXT NOT NULL CHECK(tenant='synthetic-tenant'), company TEXT NOT NULL CHECK(company='synthetic-company'), plan_digest TEXT NOT NULL);
CREATE TABLE sample_task(id TEXT PRIMARY KEY, role TEXT NOT NULL, deps TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('PENDING','OBSERVED')), version INTEGER NOT NULL CHECK(version>=0));
CREATE TABLE sample_lease(task_id TEXT PRIMARY KEY REFERENCES sample_task(id), holder TEXT NOT NULL, fence INTEGER NOT NULL CHECK(fence>0), issued INTEGER NOT NULL CHECK(issued>=0), expires INTEGER NOT NULL CHECK(expires>issued));
CREATE TABLE sample_event(seq INTEGER PRIMARY KEY, command_id TEXT UNIQUE NOT NULL, request_sha TEXT NOT NULL, task_id TEXT NOT NULL REFERENCES sample_task(id), fence INTEGER NOT NULL, tick INTEGER NOT NULL, output_sha TEXT NOT NULL);"""


def digest(v):
    return sha256(json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


class Workbench:
    """Only caller-owned new synthetic file. No server route or arbitrary customer inputs."""
    def __init__(self, path: Path, plan: dict, tenant: str = TENANT, company: str = COMPANY):
        if (tenant, company) != (TENANT, COMPANY):
            raise ValueError('SAMPLE_SCOPE_DENY')
        self.path = Path(path)
        if not self.path.name.endswith('.d0.sqlite') or self.path.is_symlink():
            raise ValueError('SAMPLE_PATH_INVALID')
        self.plan = canonical_plan(plan)
        self.tasks = {t['id']: t for t in self.plan['tasks']}

    @contextmanager
    def _db(self):
        if not self.path.is_file() or self.path.is_symlink():
            raise ValueError('SAMPLE_DB_MISSING')
        with closing(sqlite3.connect(self.path.resolve().as_uri()+'?mode=rw', uri=True, timeout=3)) as db:
            db.execute('PRAGMA foreign_keys=ON')
            with db:
                db.execute('BEGIN IMMEDIATE')
                meta = db.execute('SELECT profile,tenant,company,plan_digest FROM meta').fetchall()
                if meta != [(PROFILE,TENANT,COMPANY,self.plan['digest'])]:
                    raise ValueError('SAMPLE_DB_SCOPE_MISMATCH')
                actual = db.execute('SELECT id,role,deps FROM sample_task ORDER BY id').fetchall()
                expected = [(t['id'], t['role'], json.dumps(t['depends_on'])) for t in self.plan['tasks']]
                if actual != expected:
                    raise ValueError('SAMPLE_TASK_PIN_MISMATCH')
                yield db

    def create(self):
        # Exclusive creation, never open or overwrite an unrelated existing database.
        with self.path.open('xb'):
            pass
        try:
            with closing(sqlite3.connect(self.path)) as db:
                db.execute('PRAGMA foreign_keys=ON')
                with db:
                    db.executescript(DDL)
                    db.execute('INSERT INTO meta VALUES (?,?,?,?)', (PROFILE,TENANT,COMPANY,self.plan['digest']))
                    db.executemany('INSERT INTO sample_task VALUES (?,?,?,?,?)', [(t['id'],t['role'],json.dumps(t['depends_on']),'PENDING',0) for t in self.plan['tasks']])
        except BaseException:
            self.path.unlink(missing_ok=True)
            raise

    def _task(self, db, task):
        if task not in self.tasks or self.tasks[task]['role'] not in {'orchestrator','research','engineer','qa'}:
            raise ValueError('SAMPLE_ROLE_HOLD')
        state, version = db.execute('SELECT state,version FROM sample_task WHERE id=?',(task,)).fetchone()
        if state != 'PENDING':
            raise ValueError('SAMPLE_TASK_TERMINAL')
        for dep in self.tasks[task]['depends_on']:
            if db.execute('SELECT state FROM sample_task WHERE id=?',(dep,)).fetchone()[0] != 'OBSERVED':
                raise ValueError('SAMPLE_DEPENDENCY_HOLD')
        return version

    def lease(self, task: str, holder: str, now: int, ttl: int) -> int:
        if not token(holder) or not holder.startswith('demo-') or not uint(now) or not uint(ttl) or not 1 <= ttl <= 100 or now+ttl > 2**63-1:
            raise ValueError('SAMPLE_LEASE_INVALID')
        with self._db() as db:
            self._task(db,task)
            old = db.execute('SELECT fence,issued,expires FROM sample_lease WHERE task_id=?',(task,)).fetchone()
            if old and now < old[2]:
                raise ValueError('SAMPLE_LEASE_BUSY')
            fence = 1 if old is None else old[0]+1
            db.execute('INSERT INTO sample_lease VALUES (?,?,?,?,?) ON CONFLICT(task_id) DO UPDATE SET holder=excluded.holder,fence=excluded.fence,issued=excluded.issued,expires=excluded.expires',(task,holder,fence,now,now+ttl))
            return fence

    def observe(self, task: str, holder: str, fence: int, now: int, command_id: str) -> str:
        if not token(command_id) or not token(holder) or not uint(fence) or fence == 0 or not uint(now):
            raise ValueError('SAMPLE_COMMAND_INVALID')
        request = digest([self.plan['digest'],task,holder,fence,now])
        with self._db() as db:
            prior = db.execute('SELECT request_sha FROM sample_event WHERE command_id=?',(command_id,)).fetchone()
            if prior:
                if prior[0] != request:
                    raise ValueError('SAMPLE_IDEMPOTENCY_CONFLICT')
                return 'DUPLICATE_IGNORED'
            version = self._task(db,task)
            lease = db.execute('SELECT holder,fence,issued,expires FROM sample_lease WHERE task_id=?',(task,)).fetchone()
            if not lease or lease[:2] != (holder,fence) or not lease[2] <= now < lease[3]:
                raise ValueError('SAMPLE_LEASE_STALE')
            scope = Scope(TENANT,COMPANY,ENV,self.plan['revision'],task,'demo-run','demo-agent','demo-principal')
            a = AdapterPin(scope,'demo-model','v1',self.plan['digest'],('demo-tool',),())
            b = AdapterPin(scope,'demo-fallback','v1',self.plan['digest'],('demo-tool',),())
            output = sample_model(a,b,(a,b))
            if output.output is None or output.provider_called or output.spend_allowed or output.dispatch_allowed:
                raise ValueError('SAMPLE_ADAPTER_HOLD')
            cur = db.execute("UPDATE sample_task SET state='OBSERVED',version=version+1 WHERE id=? AND version=? AND state='PENDING'",(task,version))
            if cur.rowcount != 1:
                raise ValueError('SAMPLE_CAS_HOLD')
            db.execute('INSERT INTO sample_event(command_id,request_sha,task_id,fence,tick,output_sha) VALUES (?,?,?,?,?,?)',(command_id,request,task,fence,now,digest(output.output)))
            return 'SAMPLE_OBSERVED'

    def snapshot(self):
        with self._db() as db:
            tasks = db.execute('SELECT id,state,version FROM sample_task ORDER BY id').fetchall()
            events = db.execute('SELECT seq,task_id,fence,tick,output_sha FROM sample_event ORDER BY seq').fetchall()
        return {'mode':PROFILE,'tenant':TENANT,'company':COMPANY,'plan_digest':self.plan['digest'],'tasks':tasks,'events':events,'admission':'DENY','dispatch_allowed':False,'release_ready':False,'provider_called':False,'spend_allowed':False,'independent_accepted':False}
