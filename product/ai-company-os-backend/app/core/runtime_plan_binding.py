"""R09 bridge candidate: checks R3-shaped data; no runtime binding or assignment."""
import hashlib
import json
from .runtime_preview import token
from .orchestrator import canonical_plan
from .dag import GraphError


def inspect_plan_binding(projection: object, task_id: str, requested_role: str) -> dict:
    result = {'decision': 'HOLD', 'binding_created': False, 'run_id': None, 'agent_instance_id': None,
              'dispatch_allowed': False, 'reason': 'PLAN_INVALID'}
    if not isinstance(projection, dict) or not token(task_id) or not token(requested_role):
        return result
    if set(projection) != {'schema_version','scope','plan_id','worktype','tasks','waves','edges','validation','admission','dispatch_allowed','release_ready','real_run_count','digest','revision'}:
        return result
    if (projection.get('schema_version') != 'core.plan.projection.v1-D0'
            or projection.get('scope') != {'tenant_id':'synthetic-tenant','environment_id':'A0_SAMPLE_ONLY'}
            or projection.get('dispatch_allowed') is not False or projection.get('release_ready') is not False
            or projection.get('admission') != 'DENY' or projection.get('real_run_count') is not None
            or projection.get('validation') != 'VALIDATED_D0_GRAPH'):
        return result
    try:
        body = {k:v for k,v in projection.items() if k not in ('digest','revision')}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',',':'),
                        ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return result
    if projection.get('digest') != digest or projection.get('revision') != 'sha256:'+digest:
        return {**result, 'reason':'PLAN_DIGEST_MISMATCH'}
    tasks = projection.get('tasks')
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 100:
        return result
    if any(not isinstance(t, dict) or not token(t.get('id')) or not token(t.get('role'))
           or t.get('state') != 'HOLD' or 'run_id' not in t or t['run_id'] is not None for t in tasks):
        return result
    if len({t['id'] for t in tasks}) != len(tasks):
        return result
    # R3 is now recovered: recompile the logical plan using its actual graph authority.
    # Digest alone is not a graph validation or independent signature.
    try:
        raw = {'id': projection['plan_id'], 'worktype': projection['worktype'],
               'tasks': [{k:t[k] for k in ('id','label','role','depends_on')} for t in tasks]}
        if canonical_plan(raw) != projection:
            return {**result, 'reason':'CANONICAL_PLAN_MISMATCH'}
    except (GraphError, TypeError, KeyError, ValueError, UnicodeError, RecursionError):
        return {**result, 'reason':'CANONICAL_PLAN_INVALID'}
    match = next((t for t in tasks if t['id'] == task_id), None)
    if match is None or match['role'] != requested_role:
        return {**result, 'reason':'TASK_ROLE_MISMATCH'}
    if requested_role not in {'orchestrator','research','engineer','qa'}:
        return {**result, 'decision':'DENY', 'reason':'INDEPENDENT_OR_HUMAN_ROLE_NOT_AGENT'}
    return {**result, 'reason':'CANONICAL_D0_PLAN_ONLY_INSTANCE_AND_ADMISSION_REQUIRED'}
