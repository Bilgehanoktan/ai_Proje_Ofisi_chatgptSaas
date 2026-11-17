"""J2-R1: read-only D0 owner-row crosswalk; no SQL, receipt issuance or writes.
Projected fields are a proposed review interface, NOT a physical schema or owner adapter.
A match is diagnostic only. Absence from supplied rows proves nothing about the DB.
"""
from dataclasses import dataclass, field
import re

SCOPE = ('tenant_id','company_id','environment_id')
BINDING = SCOPE + ('plan_revision','task_id','run_id','agent_instance_id','principal_id',
    'attempt','project_id','effect_id','invocation_pin','route_pin','profile_pin',
    'budget_id','reservation_id','invocation_idempotency_key','currency','reserved_minor',
    'admission_id','admission_tx','admission_request_digest','reservation_tx',
    'reservation_budget_revision','lease_id','grant_id','fence','policy_epoch','witness_epoch',
    'membership_pin','reservation_pin')
ROW = BINDING + ('state','consume_tx','consume_receipt_pin','usage_tx','usage_pin',
                 'actual_minor','input_tokens','output_tokens','reconciliation_tx',
                 'reconciliation_pin','recognized_minor','released_minor')
BUDGET = SCOPE + ('budget_id','revision','currency','limit_minor','outstanding_minor',
                  'recognized_cost_minor','unknown_cost','policy_epoch','witness_epoch','source_digest')
STATES = ('RESERVED','CONSUMED','UNKNOWN','USAGE_KNOWN','RECONCILED')
NUM = ('attempt','reserved_minor','reservation_budget_revision','fence','policy_epoch','witness_epoch')
PINS = ('invocation_pin','route_pin','profile_pin','admission_request_digest','membership_pin','reservation_pin')

@dataclass(frozen=True)
class Review:
    reason: str
    structural_match: bool = False
    quarantine_required: bool = False
    decision: str = field(default='HOLD', init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)
    settlement_allowed: bool = field(default=False, init=False)
    receipt_available: bool = field(default=False, init=False)


def _uint(v):
    return type(v) is int and 0 <= v <= 2**63-1


def _token(v):
    return type(v) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}',v) is not None


def _pin(v):
    return type(v) is str and re.fullmatch(r'[a-f0-9]{64}',v) is not None


def _currency(v):
    return type(v) is str and re.fullmatch(r'[A-Z]{3}',v) is not None


def _shape(d, fields):
    return type(d) is dict and set(d) == set(fields)


def _scope(d):
    return tuple(d[k] for k in SCOPE)


def _binding_ok(d):
    return (_scope(d)==('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
        and all(_uint(d[k]) for k in NUM)
        and d['reserved_minor']>0 and d['fence']>0 and d['reservation_budget_revision']>0
        and all(_pin(d[k]) for k in PINS)
        and _currency(d['currency'])
        and type(d['plan_revision']) is str and re.fullmatch(r'sha256:[a-f0-9]{64}',d['plan_revision']) is not None
        and all(_token(d[k]) for k in BINDING if k not in NUM+PINS+('currency','plan_revision'))
        and all(d[k].startswith('demo-') for k in ('run_id','agent_instance_id','principal_id')))


def _keys(d):
    # W5-H replay key semantics; no attempt/route/tx reset of economic identity.
    s=_scope(d)
    return (('reservation',s,d['budget_id'],d['reservation_id']), ('idempotency',s,d['invocation_idempotency_key']),
            ('invocation',s,d['invocation_pin']), ('membership',s,d['membership_pin']))


def _budget_ok(b):
    return (_shape(b,BUDGET) and _scope(b)==('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
        and _token(b['budget_id']) and _currency(b['currency']) and _pin(b['source_digest'])
        and type(b['unknown_cost']) is bool
        and all(_uint(b[k]) for k in ('revision','limit_minor','outstanding_minor','recognized_cost_minor',
                                       'policy_epoch','witness_epoch'))
        and b['outstanding_minor']<=b['limit_minor']-b['recognized_cost_minor'])


def _phase(r):
    # Consumed receipt is a historical observation; never a permission to invoke.
    c=('consume_tx','consume_receipt_pin')
    u=('usage_tx','usage_pin','actual_minor','input_tokens','output_tokens')
    q=('reconciliation_tx','reconciliation_pin','recognized_minor','released_minor')
    present=lambda keys: all(r[k] is not None for k in keys)
    absent=lambda keys: all(r[k] is None for k in keys)
    state=r['state']
    if state=='RESERVED': return absent(c+u+q)
    if state=='UNKNOWN':
        # Unknown outcome may follow a lost ACK, with or without consume readback.
        return (absent(c) or present(c)) and absent(u+q) and (absent(c) or _consumed(r))
    if not present(c) or not _consumed(r): return False
    if state=='CONSUMED': return absent(u+q)
    if not present(u) or not (_token(r['usage_tx']) and _pin(r['usage_pin'])
        and all(_uint(r[k]) for k in u[2:]) and r['actual_minor']<=r['reserved_minor']): return False
    if len({r['reservation_pin'],r['consume_receipt_pin'],r['usage_pin']})!=3: return False
    if state=='USAGE_KNOWN': return absent(q)
    return (state=='RECONCILED' and present(q) and _token(r['reconciliation_tx'])
        and _pin(r['reconciliation_pin']) and len({r['reservation_pin'],r['consume_receipt_pin'],
        r['usage_pin'],r['reconciliation_pin']})==4
        and all(_uint(r[k]) for k in q[2:]) and r['recognized_minor']==r['actual_minor']
        and r['recognized_minor']+r['released_minor']==r['reserved_minor'])


def _consumed(r):
    return (_token(r['consume_tx']) and r['consume_tx']!=r['reservation_tx']
        and _pin(r['consume_receipt_pin']) and r['consume_receipt_pin']!=r['reservation_pin'])


def review_membership(expected, rows, budget, budget_reference):
    """Expected and budget_reference are separate supplied observations, not trusted custody.
    Caller supplies all potentially matching rows from one owner snapshot. No DB read occurs.
    No inferred receipt, no automatic retry, no financial mutation even on structural match.
    """
    try:
        if not _shape(expected,BINDING) or not _binding_ok(expected): return Review('EXPECTED_BINDING_HOLD')
        if type(rows) is not tuple or len(rows)>4096: return Review('OWNER_ROWSET_HOLD')
        if not _budget_ok(budget) or not _budget_ok(budget_reference) or budget!=budget_reference:
            return Review('BUDGET_REFERENCE_HOLD')
        if (_scope(budget),budget['budget_id'],budget['currency'],budget['policy_epoch'],budget['witness_epoch']) != (
            _scope(expected),expected['budget_id'],expected['currency'],expected['policy_epoch'],expected['witness_epoch']):
            return Review('BUDGET_SCOPE_CURRENCY_EPOCH_HOLD')
        if budget['unknown_cost']: return Review('UNKNOWN_COST_HOLD',quarantine_required=True)
        if budget['revision']<expected['reservation_budget_revision']: return Review('BUDGET_REVISION_HOLD')
        matched=[]
        target=set(_keys(expected))
        for row in rows:
            if not _shape(row,ROW) or not _binding_ok(row) or row['state'] not in STATES or not _phase(row):
                return Review('OWNER_ROW_SHAPE_OR_PHASE_HOLD')
            if set(_keys(row)).intersection(target): matched.append(row)
        if len(matched)!=1: return Review('MEMBERSHIP_MISSING_HOLD' if not matched else 'MEMBERSHIP_AMBIGUOUS_HOLD')
        r=matched[0]
        if any(r[k]!=expected[k] for k in BINDING): return Review('MEMBERSHIP_BINDING_HOLD')
        if r['state']=='UNKNOWN': return Review('UNKNOWN_OUTCOME_HOLD',quarantine_required=True)
        if r['state']!='RECONCILED' and r['reserved_minor']>budget['outstanding_minor']:
            return Review('OUTSTANDING_BALANCE_HOLD')
        if r['state']=='RECONCILED' and r['recognized_minor']>budget['recognized_cost_minor']:
            return Review('RECOGNIZED_BALANCE_HOLD')
        return Review('D0_'+r['state']+'_MEMBERSHIP_MATCH_ONLY',True)
    except (KeyError,TypeError,ValueError,OverflowError,RecursionError):
        return Review('INVALID_REFERENCE_HOLD')
