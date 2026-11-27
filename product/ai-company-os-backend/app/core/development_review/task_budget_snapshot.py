"""D0 pair identity and stable dual readback; not a cross-database T1 or grant."""
from pathlib import Path
import re
from uuid import uuid4
from .paired_read_guard import guarded_read, PAIR_TABLES

PLAN = '6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9'
SCOPE = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY', PLAN,
         'research', 'demo-run', 'demo-agent', 'demo-principal')
DDL = '''CREATE TABLE sample_pair (id INTEGER PRIMARY KEY CHECK(id=1),
 pair_id TEXT NOT NULL, tenant TEXT NOT NULL, company TEXT NOT NULL,
 environment TEXT NOT NULL, plan_digest TEXT NOT NULL, task_id TEXT NOT NULL,
 run_id TEXT NOT NULL, agent_id TEXT NOT NULL, principal TEXT NOT NULL)'''


def new_pair_id():
    return uuid4().hex


def _valid_pair(pair_id):
    return type(pair_id) is str and re.fullmatch(r'[0-9a-f]{32}', pair_id) is not None


def write_pair_marker(db, pair_id):
    """Call only during exclusive creation of a new disposable store, in its transaction."""
    if not _valid_pair(pair_id):
        raise ValueError('D0_PAIR_ID_HOLD')
    db.execute(DDL)
    db.execute('INSERT INTO sample_pair VALUES (1,?,?,?,?,?,?,?,?,?)', (pair_id, *SCOPE))


def read_pair_marker(path, *, admission):
    p = Path(path)
    suffix = '.admission.d0.sqlite' if admission else '.workbench.d0.sqlite'
    if not p.name.endswith(suffix) or p.is_symlink() or not p.is_file():
        raise ValueError('D0_PAIR_PATH_HOLD')
    with guarded_read(p,suffix,PAIR_TABLES) as db:
        rows = db.execute('SELECT id,pair_id,tenant,company,environment,plan_digest,task_id,run_id,agent_id,principal FROM sample_pair LIMIT 2').fetchall()
    if len(rows) != 1 or rows[0][0] != 1 or not _valid_pair(rows[0][1]) or rows[0][2:] != SCOPE:
        raise ValueError('D0_PAIR_SCOPE_HOLD')
    return rows[0][1]


def _collect(workbench_path, admission_path, office_reader, budget_reader):
    """Two equal complete collects detect observed changes, not ABA or global atomicity."""
    if Path(workbench_path).samefile(admission_path):
        raise ValueError('D0_PAIR_PATH_HOLD')

    def once():
        w = read_pair_marker(workbench_path, admission=False)
        a = read_pair_marker(admission_path, admission=True)
        if w != a:
            raise ValueError('D0_PAIR_MISMATCH_HOLD')
        office = office_reader(workbench_path)
        budget = budget_reader(admission_path)
        if w != read_pair_marker(workbench_path, admission=False) or a != read_pair_marker(admission_path, admission=True):
            raise ValueError('D0_PAIR_CHANGED_HOLD')
        return w, office, budget

    first = once()
    if first != once():
        raise ValueError('D0_PAIR_CHANGED_HOLD')
    pair_id, office, budget = first
    if (office['tenant'], office['company'], office['plan_digest']) != (SCOPE[0], SCOPE[1], PLAN) or (budget['tenant'], budget['company']) != SCOPE[:2]:
        raise ValueError('D0_PAIR_SCOPE_HOLD')
    if any(office[k] is not False for k in ('dispatch_allowed','provider_called','spend_allowed','release_ready')) or any(budget[k] is not False for k in ('dispatch_allowed','spend_allowed','release_ready','authoritative')) or budget['admission'] != 'DENY':
        raise ValueError('D0_PAIR_AUTHORITY_HOLD')
    seq, version = office['sample_event_count'], budget['version']
    if type(seq) is not int or not 0 <= seq <= 5 or type(version) is not int or not 0 <= version <= 2:
        raise ValueError('D0_PAIR_VERSION_HOLD')
    return {'schema_version':'task.budget.snapshot.v1-D0', 'mode':'D0_PAIRED_SAMPLE_0188',
            'pair_id':pair_id, 'tenant':SCOPE[0], 'company':SCOPE[1], 'plan_digest':PLAN,
            'task_id':SCOPE[4], 'run_id':SCOPE[5], 'workbench_event_seq':seq,
            'research_event_seq':3 if seq >= 3 else None, 'admission_version':version,
            'sample_admission_ref':'demo-admission' if version else None,
            'sample_budget_ref':'demo-budget', 'office':office, 'budget':budget,
            'consistency':'STABLE_DOUBLE_READ_NOT_ATOMIC', 'freshness':'HISTORICAL_SAMPLE',
            'causality':'UNPROVEN', 'lease_binding':'HOLD', 'geometry_join':'HOLD',
            'dispatch_allowed':False, 'spend_allowed':False, 'release_ready':False,
            'authoritative':False}


def read_task_budget_snapshot(workbench_path, admission_path):
    from .office_workbench import read_office_workbench
    from .admission_sample import read_admission
    return _collect(workbench_path, admission_path, read_office_workbench, read_admission)
