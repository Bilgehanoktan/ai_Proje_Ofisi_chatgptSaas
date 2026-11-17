"""Pure D0 review composition. Never a route, IAM resolver, runtime binding or geometry join."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import re
from jsonschema import Draft202012Validator

COMMON_SCOPE = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY')
SCOPE_KEYS = ('tenant_id', 'company_id', 'environment_id')
SCHEMAS = {'studio.schema.json':'eed9627913502ebb09222cf404f867ca305a6a44',
           'combined.schema.json':'f48e063b453e36f6d864918a77e08f239d1accac'}
REVIEW_FIELDS = frozenset(('reason','structural_match','org_revision','plan_revision','project_id','task_id','seat_id','role','decision','freshness','authoritative','runtime_binding','geometry_join','dispatch_allowed','release_ready'))
ROLES = frozenset(('orchestrator','research','engineer','qa'))
ZERO = '0'*64

class Hold(ValueError):
    pass

def require(ok, reason):
    if not ok:
        raise Hold(reason)

def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()

def token(v):
    return type(v) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}',v) is not None

def digest(v):
    return type(v) is str and re.fullmatch(r'[0-9a-f]{64}',v) is not None

def schema_validator(schema_dir, name):
    require(name in SCHEMAS, 'SCHEMA_NAME')
    path = Path(schema_dir)/name
    require(path.is_file() and not path.is_symlink(), 'SCHEMA_MISSING')
    raw = path.read_bytes()
    require(blob(raw)==SCHEMAS[name], 'SCHEMA_PIN_HOLD')
    schema = json.loads(raw)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)

def validate(schema_dir, name, value):
    require(type(value) is dict, 'SHAPE')
    require(schema_validator(schema_dir,name).is_valid(value), 'OWNER_SCHEMA_HOLD')

def scope_ok(value):
    return type(value) is dict and value==dict(zip(SCOPE_KEYS,COMMON_SCOPE))

def validate_studio(schema_dir, studio, expected_head):
    validate(schema_dir,'studio.schema.json',studio)
    require(scope_ok(studio['scope']) and digest(expected_head) and studio['revision']==expected_head, 'STUDIO_SCOPE_HEAD_HOLD')
    require(type(studio['sequence']) is int, 'STUDIO_SEQUENCE_HOLD')
    positions=studio['positions']; units=studio['units']
    require(len({x['id'] for x in positions})==len(positions) and len({x['id'] for x in units})==len(units), 'STUDIO_DUPLICATE_HOLD')
    unit_ids={u['id'] for u in units}
    require(all(x['unit'] in unit_ids for x in positions), 'STUDIO_POSITION_HOLD')
    return studio

@dataclass(frozen=True)
class ReviewPins:
    org_revision: str
    project_id: str
    plan_revision: str
    task_id: str
    seat_id: str
    role: str
    history_count: int
    history_head: str
    office_revision: str

    def check(self):
        require(type(self) is ReviewPins and all(digest(v) for v in (self.org_revision,self.history_head,self.office_revision)), 'PIN_DIGEST_HOLD')
        require(all(token(v) for v in (self.project_id,self.task_id,self.seat_id)) and self.project_id.startswith('demo-') and len(self.project_id)>5, 'PIN_REFERENCE_HOLD')
        require(type(self.plan_revision) is str and re.fullmatch(r'sha256:[0-9a-f]{64}',self.plan_revision) and type(self.role) is str and self.role in ROLES, 'PIN_ROLE_PLAN_HOLD')
        require(type(self.history_count) is int and 0<=self.history_count<=4096 and (self.history_count!=0 or self.history_head==ZERO), 'PIN_HISTORY_HOLD')


def hold_preview():
    # No exception text, credentials, or input-controlled values in a denial.
    return {'decision':'HOLD','reason':'READ_UNAVAILABLE','authoritative':False}


def join_historical(schema_dir, pins, studio, combined, binding):
    """Internal review-only; input references are not authority or a shared snapshot.
    The owner adapter obtains these readbacks; never accept JSON from a client here.
    """
    require(type(pins) is ReviewPins,'PIN_SHAPE'); pins.check()
    validate_studio(schema_dir,studio,pins.org_revision)
    validate(schema_dir,'combined.schema.json',combined)
    require(scope_ok(combined['scope']) and combined['org_revision']==pins.org_revision and combined['project']==pins.project_id, 'COMBINED_SCOPE_PROJECT_HEAD_HOLD')
    require(combined['office_revision']==pins.office_revision, 'OFFICE_REVISION_HOLD')
    history=combined['history']; rows=combined['proposals']
    require(type(history['count']) is int and history=={'count':pins.history_count,'head':pins.history_head} and len(rows)==pins.history_count, 'HISTORY_PIN_HOLD')
    require(all(type(r['sequence']) is int and r['sequence']==i for i,r in enumerate(rows,1)) and (rows[-1]['digest'] if rows else ZERO)==pins.history_head,'HISTORY_ORDER_HOLD')
    require(type(combined['office_pairs']) is int and combined['office_pairs']<=len(studio['positions']), 'OFFICE_COUNT_HOLD')
    require(type(binding) is dict and set(binding)==REVIEW_FIELDS, 'RUNTIME_SHAPE_HOLD')
    fixed={'reason':'D0_HISTORICAL_REFERENCE_MATCH_ONLY','structural_match':True,'decision':'HOLD','freshness':'HISTORICAL_SAMPLE','authoritative':False,'runtime_binding':None,'geometry_join':'HOLD','dispatch_allowed':False,'release_ready':False}
    require(all(type(binding[k]) is type(v) and binding[k]==v for k,v in fixed.items()), 'RUNTIME_BOUNDARY_HOLD')
    require(all(binding[k]==v for k,v in {'org_revision':pins.org_revision,'project_id':pins.project_id,'plan_revision':pins.plan_revision,'task_id':pins.task_id,'seat_id':pins.seat_id,'role':pins.role}.items()), 'RUNTIME_REFERENCE_HOLD')
    seats=[p for p in studio['positions'] if p['id']==pins.seat_id]
    require(len(seats)==1 and seats[0]['role']==pins.role and seats[0]['occupied'] is True,'STUDIO_SEAT_HOLD')
    # Explicit output allowlist. No raw proposal list, instance/run/principal IDs, visual actor or station.
    return {'schema':'org.runtime.office.readback.v0-D0', 'mode':'D0_INTERNAL_REVIEW_ONLY',
            'org_revision':pins.org_revision,'project_id':pins.project_id,'plan_revision':pins.plan_revision,
            'task_id':pins.task_id,'seat_id':pins.seat_id,'role':pins.role,
            'history_count':pins.history_count,'history_head':pins.history_head,'office_revision':pins.office_revision,
            'office_pairs':combined['office_pairs'],'meeting_proposed':combined['meeting_proposed'],
            'structural_match':True,'freshness':'HISTORICAL_SAMPLE','decision':'HOLD',
            'authoritative':False,'identity_owner':'HOLD','geometry_join':'HOLD','runtime_binding':None,
            'dispatch_allowed':False,'release_ready':False,'atomic_cross_store':False}
