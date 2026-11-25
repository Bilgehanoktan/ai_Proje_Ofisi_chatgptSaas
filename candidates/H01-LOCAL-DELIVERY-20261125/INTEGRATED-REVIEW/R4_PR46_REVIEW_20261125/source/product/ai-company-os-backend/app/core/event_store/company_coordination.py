"""0204-C D0 company ordering and shared-pool replay; no scheduling authority."""
from dataclasses import dataclass, field
import json
import re

SCOPE = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY')
_SCOPE = 'tenant_id=%s AND company_id=%s AND environment_id=%s'
_ADMIT = 'D0_RUN_ADMISSION'
_ORDINARY = 'D0_RUN_TRANSITION'
_RENEW = 'D0_LEASE_RENEWAL'
_FAIL = 'D0_RUN_FAILURE'
_FAILURE = 'D0_LOCAL_FAILURE_NO_EFFECT'
_MAX = 5000


def _token(v):
    return type(v) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', v) is not None


def _sha(v):
    return type(v) is str and re.fullmatch(r'[0-9a-f]{64}', v) is not None


def _uint(v):
    return type(v) is int and 0 <= v < 2**63


def _revision(v):
    return type(v) is str and v.startswith('sha256:') and _sha(v[7:])


def _tx(v):
    return type(v) is str and v.startswith('d0-tx-') and _sha(v[6:])


@dataclass(frozen=True)
class Member:
    project_id: str
    plan_revision: str
    task_id: str
    run_id: str
    agent_instance_id: str
    principal_id: str
    initial_version: int

    def row(self):
        return (self.project_id,self.plan_revision,self.task_id,self.run_id,
                self.agent_instance_id,self.principal_id,self.initial_version)


@dataclass(frozen=True)
class Allocation:
    project_id: str
    cap_minor: int


@dataclass(frozen=True)
class Pool:
    budget_id: str
    currency: str
    limit_minor: int
    revision: int
    policy_epoch: int
    witness_epoch: int
    source_digest: str
    allocations: tuple[Allocation, ...]


@dataclass(frozen=True)
class CompanyEvent:
    sequence: int
    project_id: str
    run_id: str
    version: int
    transaction_ref: str
    request_digest: str
    kind: str
    predecessors: tuple[str, ...] = ()
    budget_revision: int | None = None
    amount_minor: int = 0

    def order_row(self):
        return (self.sequence,self.project_id,self.run_id,self.version,self.transaction_ref,
                self.request_digest,json.dumps(self.predecessors,separators=(',',':')))


@dataclass(frozen=True)
class CompanyReview:
    reason: str
    structural_match: bool = False
    event_count: int | None = None
    pool_revision: int | None = None
    outstanding_minor: int | None = None
    project_outstanding: tuple = ()
    decision: str = field(default='HOLD',init=False)
    dispatch_allowed: bool = field(default=False,init=False)
    spend_allowed: bool = field(default=False,init=False)
    independent_verified: bool = field(default=False,init=False)


def _member(m):
    return (type(m) is Member and _token(m.project_id) and _revision(m.plan_revision)
            and all(_token(v) for v in (m.task_id,m.run_id,m.agent_instance_id,m.principal_id))
            and all(v.startswith('demo-') for v in (m.run_id,m.agent_instance_id,m.principal_id))
            and _uint(m.initial_version))


def _event(e):
    return (type(e) is CompanyEvent and all(_uint(v) for v in (e.sequence,e.version,e.amount_minor))
            and e.sequence>0 and e.version>0 and _token(e.project_id) and _token(e.run_id)
            and _tx(e.transaction_ref) and _sha(e.request_digest)
            and type(e.kind) is str and e.kind in (_ADMIT,_ORDINARY,_RENEW,_FAIL)
            and type(e.predecessors) is tuple and len(e.predecessors)<=100
            and all(_tx(v) for v in e.predecessors)
            and e.predecessors==tuple(sorted(set(e.predecessors)))
            and (e.budget_revision is None or _uint(e.budget_revision)))


def _roster(members):
    if type(members) is not tuple or not 1<=len(members)<=100 or not all(_member(m) for m in members):
        raise ValueError('D0_COMPANY_ROSTER_HOLD')
    by_run={m.run_id:m for m in members}
    if len(by_run)!=len(members) or len({(m.project_id,m.plan_revision,m.task_id) for m in members})!=len(members):
        raise ValueError('D0_COMPANY_MEMBER_DUPLICATE')
    # Existing plan reader is revision-scoped. Reusing a revision across projects is not yet safe.
    projects={}
    for m in members:
        if projects.setdefault(m.plan_revision,m.project_id)!=m.project_id:
            raise ValueError('D0_COMPANY_PLAN_COLLISION')
    return by_run


def _pool(pool, members):
    if (type(pool) is not Pool or not _token(pool.budget_id) or type(pool.currency) is not str
            or re.fullmatch(r'[A-Z]{3}',pool.currency) is None or not _sha(pool.source_digest)
            or not all(_uint(v) for v in (pool.limit_minor,pool.revision,pool.policy_epoch,pool.witness_epoch))
            or type(pool.allocations) is not tuple or not 1<=len(pool.allocations)<=100
            or not all(type(a) is Allocation and _token(a.project_id) and _uint(a.cap_minor) for a in pool.allocations)):
        raise ValueError('D0_COMPANY_POOL_HOLD')
    caps={a.project_id:a.cap_minor for a in pool.allocations}
    if (len(caps)!=len(pool.allocations) or set(caps)!={m.project_id for m in members.values()}
            or sum(caps.values())>pool.limit_minor):
        raise ValueError('D0_COMPANY_ALLOCATION_HOLD')
    return caps


def _replay(members,pool,events):
    by_run=_roster(members);caps=_pool(pool,by_run)
    if type(events) is not tuple or len(events)>_MAX:
        raise ValueError('D0_COMPANY_EVENT_LIMIT')
    balances=dict.fromkeys(caps,0);version={r:m.initial_version for r,m in by_run.items()}
    active={};closed=set();seen=set();rev=pool.revision;claims={};settled={}
    for seq,e in enumerate(events,1):
        if (not _event(e) or e.sequence!=seq or e.transaction_ref in seen or e.run_id not in by_run
                or by_run[e.run_id].project_id!=e.project_id or e.version!=version[e.run_id]+1
                or not set(e.predecessors).issubset(seen)):
            raise ValueError('D0_COMPANY_ORDER_HOLD')
        if e.kind==_ORDINARY:
            if e.run_id not in active or e.budget_revision is not None or e.amount_minor:
                raise ValueError('D0_COMPANY_TRANSITION_HOLD')
        else:
            if e.budget_revision!=rev or rev==2**63-1:
                raise ValueError('D0_COMPANY_POOL_REVISION_HOLD')
            rev+=1
            if e.kind==_ADMIT:
                if e.run_id in active or e.run_id in closed or e.amount_minor<=0:
                    raise ValueError('D0_COMPANY_RESERVATION_HOLD')
                active[e.run_id]=e.amount_minor;balances[e.project_id]+=e.amount_minor
                claims[e.run_id]=(e.run_id,rev,e.amount_minor,pool.currency,e.request_digest,e.transaction_ref)
            elif e.kind==_RENEW:
                if e.run_id not in active or e.amount_minor:
                    raise ValueError('D0_COMPANY_RENEWAL_HOLD')
            else:
                if e.run_id not in active or e.amount_minor!=active[e.run_id]:
                    raise ValueError('D0_COMPANY_SETTLEMENT_HOLD')
                balances[e.project_id]-=active.pop(e.run_id);closed.add(e.run_id)
                settled[e.run_id]=(e.run_id,e.version,e.transaction_ref,e.request_digest,e.amount_minor,0,rev,_FAILURE)
        if not 0<=balances[e.project_id]<=caps[e.project_id] or sum(balances.values())>pool.limit_minor:
            raise ValueError('D0_COMPANY_PROJECT_CAP_HOLD')
        version[e.run_id]=e.version;seen.add(e.transaction_ref)
    return rev,balances,version,claims,settled


def replay_company(members,pool,events):
    """Replay independent caller pins from zero outstanding; not full lifecycle proof."""
    try:
        rev,b,_,_,_=_replay(members,pool,events)
        return CompanyReview('D0_COMPANY_REPLAY_MATCH_ONLY',True,len(events),rev,sum(b.values()),tuple(sorted(b.items())))
    except Exception:
        return CompanyReview('D0_COMPANY_REPLAY_HOLD')


def _rows(c,sql,params,limit):
    c.execute(sql,params);rows=[]
    while (row:=c.fetchone()) is not None:
        if len(rows)>=limit: raise ValueError('D0_COMPANY_ROW_LIMIT')
        rows.append(tuple(row))
    return rows


def _exact(c,sql,params,expected):
    if _rows(c,sql,params,len(expected))!=expected:
        raise ValueError('D0_COMPANY_ROW_HOLD')


_MEM='project_id,plan_revision,task_id,run_id,agent_instance_id,principal_id,initial_version'
_ORDER='sequence,project_id,run_id,version,transaction_ref,request_digest,predecessors'


def append_company_order(c,member,event):
    """Candidate same-cursor index append after existing EVENT write; caller owns T1.
    Does NOT validate or write shared budget allocations, nor commit or issue grants.
    """
    if not _member(member) or not _event(event) or (event.project_id,event.run_id)!=(member.project_id,member.run_id) or event.version<=member.initial_version:
        raise ValueError('D0_COMPANY_MEMBER_HOLD')
    _exact(c,'SELECT '+_MEM+' FROM t1_candidate.company_run_membership WHERE '+_SCOPE+' AND run_id=%s',(*SCOPE,member.run_id),[member.row()])
    _exact(c,'SELECT event_id,event_type,request_digest FROM t1_candidate.events WHERE '+_SCOPE+' AND run_id=%s AND version=%s',
           (*SCOPE,event.run_id,event.version),[(event.transaction_ref,event.kind,event.request_digest)])
    _exact(c,'SELECT plan_revision,task_id,agent_instance_id,principal_id,version FROM t1_candidate.run_heads WHERE '+_SCOPE+' AND run_id=%s',
           (*SCOPE,member.run_id),[(member.plan_revision,member.task_id,member.agent_instance_id,member.principal_id,event.version)])
    for predecessor in event.predecessors:
        rows=_rows(c,'SELECT sequence FROM t1_candidate.company_event_order WHERE '+_SCOPE+' AND transaction_ref=%s',(*SCOPE,predecessor),1)
        if len(rows)!=1 or not _uint(rows[0][0]) or not 0<rows[0][0]<event.sequence:
            raise ValueError('D0_COMPANY_CAUSAL_HOLD')
    # No skipped per-run versions, including when a different run was last in the company stream.
    rows=_rows(c,'SELECT version FROM t1_candidate.company_event_order WHERE '+_SCOPE+' AND run_id=%s ORDER BY version DESC LIMIT 1',(*SCOPE,event.run_id),1)
    last=rows[0][0] if rows else member.initial_version
    if not _uint(last) or event.version!=last+1: raise ValueError('D0_COMPANY_RUN_SEQUENCE_HOLD')
    c.execute('UPDATE t1_candidate.company_stream_heads SET sequence=sequence+1 WHERE '+_SCOPE+' AND sequence=%s RETURNING sequence',(*SCOPE,event.sequence-1))
    if c.fetchone()!=(event.sequence,) or c.fetchone() is not None:
        raise ValueError('D0_COMPANY_STREAM_CAS_HOLD')
    c.execute('INSERT INTO t1_candidate.company_event_order (tenant_id,company_id,environment_id,'+_ORDER+') VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(*SCOPE,*event.order_row()))
    _exact(c,'SELECT '+_ORDER+' FROM t1_candidate.company_event_order WHERE '+_SCOPE+' AND sequence=%s',(*SCOPE,event.sequence),[event.order_row()])


def inspect_company(c,members,pool,events):
    """Exact scoped membership, index, event and shared-pool readback; same read-only snapshot.
    Existing per-plan history and independent pin custody are additional prerequisites.
    """
    try:
        rev,b,versions,claims,settled=_replay(members,pool,events)
        _exact(c,'SELECT '+_MEM+' FROM t1_candidate.company_run_membership WHERE '+_SCOPE+' ORDER BY run_id',SCOPE,[m.row() for m in sorted(members,key=lambda x:x.run_id)])
        _exact(c,'SELECT plan_revision,task_id,run_id,agent_instance_id,principal_id,version FROM t1_candidate.run_heads WHERE '+_SCOPE+' ORDER BY run_id',SCOPE,[(m.plan_revision,m.task_id,m.run_id,m.agent_instance_id,m.principal_id,versions[m.run_id]) for m in sorted(members,key=lambda x:x.run_id)])
        _exact(c,'SELECT sequence FROM t1_candidate.company_stream_heads WHERE '+_SCOPE,SCOPE,[(len(events),)])
        _exact(c,'SELECT '+_ORDER+' FROM t1_candidate.company_event_order WHERE '+_SCOPE+' ORDER BY sequence',SCOPE,[e.order_row() for e in events])
        _exact(c,'SELECT run_id,version,event_id,event_type,request_digest FROM t1_candidate.events WHERE '+_SCOPE+' ORDER BY run_id,version',SCOPE,[(e.run_id,e.version,e.transaction_ref,e.kind,e.request_digest) for e in sorted(events,key=lambda x:(x.run_id,x.version))])
        _exact(c,'SELECT budget_id,revision,currency,limit_minor,outstanding_minor,recognized_cost_minor,unknown_cost,policy_epoch,witness_epoch,source_digest FROM t1_candidate.sample_budgets WHERE '+_SCOPE,SCOPE,[(pool.budget_id,rev,pool.currency,pool.limit_minor,sum(b.values()),0,False,pool.policy_epoch,pool.witness_epoch,pool.source_digest)])
        _exact(c,'SELECT budget_id,run_id,budget_revision,amount_minor,currency,request_digest,transaction_ref FROM t1_candidate.sample_reservations WHERE '+_SCOPE+' ORDER BY run_id',SCOPE,[(pool.budget_id,*claims[r]) for r in sorted(claims)])
        _exact(c,'SELECT budget_id,run_id,version,transaction_ref,request_digest,released_minor,recognized_minor,budget_revision,outcome FROM t1_candidate.sample_settlements WHERE '+_SCOPE+' ORDER BY run_id',SCOPE,[(pool.budget_id,*settled[r]) for r in sorted(settled)])
        return CompanyReview('D0_COMPANY_SNAPSHOT_MATCH_ONLY',True,len(events),rev,sum(b.values()),tuple(sorted(b.items())))
    except Exception:
        return CompanyReview('D0_COMPANY_SNAPSHOT_HOLD')



def prepare_company_step(c,members,pool,history,event):
    """Acquire company stream lock FIRST, then check exact preimage and candidate cap.
    All shared-pool writers must follow this lock order. No commit or default wiring.
    """
    _replay(members,pool,history+(event,))
    _exact(c,'SELECT sequence FROM t1_candidate.company_stream_heads WHERE '+_SCOPE+' FOR UPDATE',SCOPE,[(len(history),)])
    if not inspect_company(c,members,pool,history).structural_match:
        raise ValueError('D0_COMPANY_PREIMAGE_HOLD')


def finish_company_step(c,members,pool,history,event):
    """After the original writer's verified roles, append index and check postimage.
    Caller must roll back the entire transaction on any exception.
    """
    _replay(members,pool,history+(event,))
    append_company_order(c,_roster(members)[event.run_id],event)
    if not inspect_company(c,members,pool,history+(event,)).structural_match:
        raise ValueError('D0_COMPANY_POSTIMAGE_HOLD')


class CompanyCoordinatedMapping:
    """Opt-in T1 mapping decorator; original coordinator and receipt remain unchanged.
    Full lifecycle integration and PG lock semantics are not yet verified.
    """
    def __init__(self,mapping,members,pool,history,event):
        self._mapping=mapping;self._members=members;self._pool=pool
        self._history=history;self._event=event;self._intent=None;self._finished=False

    def lock_and_validate(self,c,i):
        from app.core.transaction.review import Operation, valid_intent
        from app.core.transaction.postgres_transition_mapping import transaction_ref
        if self._intent is not None or not valid_intent(i): raise ValueError('D0_COMPANY_INTENT_HOLD')
        e=self._event;m=_roster(self._members).get(e.run_id);s=i.scope
        kind={Operation.ADMISSION:_ADMIT,Operation.TERMINAL:_FAIL,
              Operation.STATE_MUTATION:_RENEW if i.lease_or_budget_changes else _ORDINARY}[i.operation]
        if (m is None or (s.tenant_id,s.company_id,s.environment_id)!=SCOPE
                or (s.plan_revision,s.task_id,s.run_id,s.agent_instance_id,s.principal_id)!=(m.plan_revision,m.task_id,m.run_id,m.agent_instance_id,m.principal_id)
                or (e.kind,e.version,e.transaction_ref,e.request_digest)!=(kind,i.expected_version+1,transaction_ref(i),i.request_digest)
                or (i.policy_epoch,i.witness_epoch)!=(self._pool.policy_epoch,self._pool.witness_epoch)
                or i.budget_ref!=(None if kind==_ORDINARY else self._pool.budget_id)):
            raise ValueError('D0_COMPANY_INTENT_HOLD')
        prepare_company_step(c,self._members,self._pool,self._history,e)
        self._mapping.lock_and_validate(c,i);self._intent=i

    def _guard(self,i):
        if self._intent is None or self._intent!=i or self._finished:
            raise ValueError('D0_COMPANY_INTENT_HOLD')

    def write_role(self,c,role,i):
        self._guard(i);self._mapping.write_role(c,role,i)

    def lock_transition(self,c,i):
        self._guard(i);return self._mapping.lock_transition(c,i)

    def write_transition_role(self,c,role,i,before,target):
        self._guard(i);self._mapping.write_transition_role(c,role,i,before,target)

    def read_transition(self,c,i):
        self._guard(i);return self._mapping.read_transition(c,i)

    def verify_write_set(self,c,i,roles):
        self._guard(i);receipt=self._mapping.verify_write_set(c,i,roles);e=self._event
        if (receipt.transaction_ref,receipt.committed_version,receipt.request_digest)!=(e.transaction_ref,e.version,e.request_digest):
            raise ValueError('D0_COMPANY_RECEIPT_HOLD')
        finish_company_step(c,self._members,self._pool,self._history,e)
        self._finished=True;return receipt
