"""Read-only projection of the exact D0 CLI workbench prefix into office role templates."""
from contextlib import closing, contextmanager
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

PLAN_DIGEST = '6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9'
PLAN_FILE = 'e564bed4f4edfb5dd94488b08cbba3205b6f018491fadd8d200d884a85e1f4bb'
OFFICE_FILE = '313b8072ec1e4bdc1feb945540c31e0a762be4151f616bd6a25e4772a790baa5'
ORDER = ('plan','draft','research','merge','qa')
ROLES = ('orchestrator','research','engineer','qa')
FIXTURES = Path(__file__).resolve().parents[3]/'fixtures'


def _digest(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',', ':'),ensure_ascii=True,allow_nan=False).encode('ascii')).hexdigest()


def _fixture(name, expected):
    data = (FIXTURES/name).read_bytes()
    if sha256(data).hexdigest() != expected:
        raise ValueError('OFFICE_FIXTURE_PIN_HOLD')
    return json.loads(data)


# D0 Workbench profile, including databases with the optional sample_pair table.
TABLES = frozenset({'meta','sample_event','sample_task','sample_lease'})
MAX_BYTES = 8 * 1024 * 1024
MAX_STEPS = 1_000_000


def _authorizer(action, arg1, arg2, database, source):
    if source is not None:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ and arg1 in TABLES and database == 'main':
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


@contextmanager
def _workbench_snapshot(path):
    """Disposable D0 read boundary; not DDL attestation or a filesystem trust root."""
    p = Path(path)
    if (not p.name.endswith('.d0.sqlite') or p.is_symlink() or not p.is_file()
            or p.stat().st_size > MAX_BYTES):
        raise ValueError('OFFICE_WORKBENCH_PATH_HOLD')
    resolved = p.resolve()
    if any(Path(str(resolved)+suffix).exists() or Path(str(resolved)+suffix).is_symlink()
           for suffix in ('-wal','-shm','-journal')):
        raise ValueError('OFFICE_WORKBENCH_SIDECAR_HOLD')
    with closing(sqlite3.connect(resolved.as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA trusted_schema=OFF')
        if db.execute('PRAGMA trusted_schema').fetchone() != (0,):
            raise ValueError('OFFICE_WORKBENCH_SCHEMA_HOLD')
        if db.execute('PRAGMA journal_mode').fetchone() != ('delete',):
            raise ValueError('OFFICE_WORKBENCH_JOURNAL_HOLD')
        db.execute('BEGIN')
        steps = 0
        def progress():
            nonlocal steps
            steps += 1000
            return int(steps >= MAX_STEPS)
        db.set_progress_handler(progress,1000)
        try:
            rows = db.execute('SELECT name,type FROM main.sqlite_schema').fetchall()
            kinds = {name:kind for name,kind in rows if name in TABLES}
            if kinds != dict.fromkeys(TABLES,'table') or any(kind in ('view','trigger') for _,kind in rows):
                raise ValueError('OFFICE_WORKBENCH_SCHEMA_HOLD')
            ordinary = {name for schema,name,kind,*_ in db.execute('PRAGMA table_list')
                        if schema == 'main' and kind == 'table'}
            if not TABLES <= ordinary:
                raise ValueError('OFFICE_WORKBENCH_SCHEMA_HOLD')
            db.set_authorizer(_authorizer)
            yield db
        finally:
            db.set_authorizer(None)
            db.set_progress_handler(None,0)


def read_office_workbench(path):
    """Fixed CLI prefix only. Historical observations, not freshness or real run state."""
    plan = _fixture('core.plan.projection.json', PLAN_FILE)
    office = _fixture('office.snapshot.json', OFFICE_FILE)
    expected = plan['tasks']
    with _workbench_snapshot(path) as db:
        if db.execute('SELECT profile,tenant,company,plan_digest FROM meta LIMIT 2').fetchall() != [('D0_WORKBENCH_0182','synthetic-tenant','synthetic-company',PLAN_DIGEST)]:
            raise ValueError('OFFICE_WORKBENCH_SCOPE_HOLD')
        events = db.execute('SELECT seq,command_id,request_sha,task_id,fence,tick,output_sha FROM sample_event ORDER BY seq LIMIT 6').fetchall()
        if len(events)>5:
            raise ValueError('OFFICE_WORKBENCH_EVENT_HOLD')
        observed = ORDER[:len(events)]
        output = _digest('Synthetic adapter review output; not a model response.')
        required_events = [(i,'demo-command-'+t,_digest([PLAN_DIGEST,t,'demo-holder',1,i]),t,1,i,output) for i,t in enumerate(observed,1)]
        if events != required_events:
            raise ValueError('OFFICE_WORKBENCH_EVENT_HOLD')
        rows = db.execute('SELECT id,role,deps,state,version FROM sample_task ORDER BY id LIMIT 8').fetchall()
        required_tasks = [(t['id'],t['role'],json.dumps(t['depends_on']),'OBSERVED' if t['id'] in observed else 'PENDING',int(t['id'] in observed)) for t in expected]
        if rows != required_tasks:
            raise ValueError('OFFICE_WORKBENCH_TASK_HOLD')
        leases = db.execute('SELECT task_id,holder,fence,issued,expires FROM sample_lease ORDER BY task_id LIMIT 6').fetchall()
        if leases != sorted((t,'demo-holder',1,i,i+10) for i,t in enumerate(observed,1)):
            raise ValueError('OFFICE_WORKBENCH_LEASE_HOLD')
    stations = {s['role_template_id']:s for f in office['floors'] for s in f['stations']}
    roles = []
    for role in ROLES:
        station = stations[role]
        tasks = [t for t in expected if t['role']==role]
        roles.append({'role':role,'station_id':station['id'],'observed':sum(t['id'] in observed for t in tasks),'total':len(tasks)})
    return {'schema_version':'office.workbench.v1-D0','mode':'D0_OFFICE_WORKBENCH_0187','tenant':'synthetic-tenant','company':'synthetic-company','world_id':'demo-world','plan_digest':PLAN_DIGEST,'layout_revision':office['layout_revision'],'sample_event_count':len(events),'roles':roles,'iv':'HOLD','release':'HOLD','freshness':'HISTORICAL_SAMPLE','dispatch_allowed':False,'provider_called':False,'spend_allowed':False,'release_ready':False,'real_run_count':None,'geometry_join':'HOLD'}
