"""0203-T candidate T1 terminal command anchor. No independent signature or grant."""
from dataclasses import dataclass
import re
from app.core.event_store.retained_history import digest, reference_bytes

_SCOPE = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY')
_FAILURE = 'D0_LOCAL_FAILURE_NO_EFFECT'
_KEY = 'tenant_id=%s AND company_id=%s AND environment_id=%s AND run_id=%s'
_COLUMNS = 'plan_revision,run_id,version,transaction_ref,request_digest,command_sha'


def _sha(v):
    return type(v) is str and re.fullmatch(r'[0-9a-f]{64}', v) is not None


@dataclass(frozen=True)
class TerminalAnchor:
    plan_revision: str
    run_id: str
    version: int
    transaction_ref: str
    request_digest: str
    command_sha: str

    def row(self):
        return (self.plan_revision,self.run_id,self.version,self.transaction_ref,self.request_digest,self.command_sha)


def _valid(a):
    return (type(a) is TerminalAnchor and type(a.plan_revision) is str and a.plan_revision.startswith('sha256:')
            and _sha(a.plan_revision[7:]) and type(a.run_id) is str
            and re.fullmatch(r'demo-[A-Za-z0-9_.:-]{1,123}',a.run_id) is not None
            and type(a.version) is int and 0 < a.version < 2**63
            and type(a.transaction_ref) is str and re.fullmatch(r'd0-tx-[0-9a-f]{64}',a.transaction_ref) is not None
            and _sha(a.request_digest) and _sha(a.command_sha))


def anchor_from_pin(pin):
    """Derive from the original typed lifecycle command, not a caller-selected digest."""
    from app.core.event_store.history_readback import LifecyclePin
    from app.core.transaction.postgres_lifecycle_mapping import D0PostgresLifecycleMapping
    from app.core.transaction.postgres_transition_mapping import transaction_ref
    from app.core.transaction.review import Operation
    if type(pin) is not LifecyclePin or pin.intent.operation != Operation.TERMINAL or pin.spec.renewal is not None or pin.spec.outcome != _FAILURE:
        raise ValueError('D0_ANCHOR_TERMINAL_ONLY')
    D0PostgresLifecycleMapping(pin.spec,None)._validate(pin.intent)
    i=pin.intent;s=i.scope
    if (s.tenant_id,s.company_id,s.environment_id)!=_SCOPE:
        raise ValueError('D0_ANCHOR_SCOPE_HOLD')
    a=TerminalAnchor(s.plan_revision,s.run_id,i.expected_version+1,transaction_ref(i),i.request_digest,
                     digest(reference_bytes('terminal-command-v1',pin)))
    if not _valid(a): raise ValueError('D0_ANCHOR_FORMAT_HOLD')
    return a


def _exact(c,sql,args,expected):
    c.execute(sql,args)
    row=c.fetchone()
    if row is None or tuple(row)!=expected or c.fetchone() is not None:
        raise ValueError('D0_ANCHOR_ROW_HOLD')


def _terminal_rows(c,a):
    if not _valid(a): raise ValueError('D0_ANCHOR_FORMAT_HOLD')
    k=(*_SCOPE,a.run_id)
    # Both rows are written and checked by the original mapping. Recheck the exact binding.
    _exact(c,'SELECT version,transaction_ref,request_digest,after_state FROM t1_candidate.run_mutations WHERE '+_KEY+' AND version=%s',
           (*k,a.version),(a.version,a.transaction_ref,a.request_digest,'FAILED'))
    _exact(c,'SELECT version,transaction_ref,request_digest,outcome FROM t1_candidate.sample_settlements WHERE '+_KEY,
           k,(a.version,a.transaction_ref,a.request_digest,_FAILURE))
    _exact(c,'SELECT plan_revision,state,version FROM t1_candidate.run_heads WHERE '+_KEY,
           k,(a.plan_revision,'FAILED',a.version))


def verify_anchor(c,a):
    _terminal_rows(c,a)
    _exact(c,'SELECT '+_COLUMNS+' FROM t1_candidate.terminal_command_anchors WHERE '+_KEY,
           (*_SCOPE,a.run_id),a.row())


def write_anchor(c,a):
    """Caller owns original T1 transaction; no commit, upsert, retry or fallback."""
    _terminal_rows(c,a)
    c.execute('INSERT INTO t1_candidate.terminal_command_anchors (tenant_id,company_id,environment_id,'+_COLUMNS+') VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
              (*_SCOPE,*a.row()))
    verify_anchor(c,a)


class TerminalAnchorMapping:
    """Explicit terminal-only extension of existing 0196-L mapping.

    Archive must be staged before T1. If rollback occurs, an orphan archive is
    harmless; never delete/retry based on absence. Independent signing is postcommit.
    """
    def __init__(self,spec,clock,archive,expected_command_sha):
        from app.core.transaction.postgres_lifecycle_mapping import D0PostgresLifecycleMapping
        self._mapping=D0PostgresLifecycleMapping(spec,clock)
        self._archive=archive;self._expected=expected_command_sha;self._anchor=None;self._intent=None

    def lock_and_validate(self,c,i):
        from app.core.event_store.history_readback import LifecyclePin
        if self._anchor is not None: raise ValueError('D0_ANCHOR_REUSE_HOLD')
        pin=LifecyclePin(i,self._mapping.spec);a=anchor_from_pin(pin)
        body=reference_bytes('terminal-command-v1',pin)
        if a.command_sha!=self._expected or self._archive.read(self._expected)!=body:
            raise ValueError('D0_ANCHOR_ARCHIVE_HOLD')
        self._mapping.lock_and_validate(c,i)
        self._anchor=a;self._intent=i

    def write_role(self,c,role,i):
        if self._anchor is None or i!=self._intent: raise ValueError('D0_ANCHOR_INTENT_HOLD')
        self._mapping.write_role(c,role,i)

    def verify_write_set(self,c,i,roles):
        a=self._anchor
        if a is None or i!=self._intent: raise ValueError('D0_ANCHOR_INTENT_HOLD')
        receipt=self._mapping.verify_write_set(c,i,roles)
        if (receipt.transaction_ref,receipt.committed_version,receipt.request_digest)!=(a.transaction_ref,a.version,a.request_digest):
            raise ValueError('D0_ANCHOR_RECEIPT_HOLD')
        # Same cursor/transaction as eight existing write roles. No second transaction.
        write_anchor(c,a)
        return receipt


def verify_plan_anchors(c,revision,pins):
    """Exact anchor set in the same snapshot as historical plan readback."""
    from app.core.event_store.history_readback import LifecyclePin
    if type(revision) is not str or not revision.startswith('sha256:') or not _sha(revision[7:]) or type(pins) is not tuple or len(pins)>100:
        raise ValueError('D0_ANCHOR_PLAN_HOLD')
    expected={}; seen=set()
    for pin in pins:
        s=pin.initial.scope
        if (s.tenant_id,s.company_id,s.environment_id)!=_SCOPE or s.plan_revision!=revision or s.run_id in seen:
            raise ValueError('D0_ANCHOR_SCOPE_HOLD')
        seen.add(s.run_id)
        if type(pin.commands) is not tuple or len(pin.commands)>1000:
            raise ValueError('D0_ANCHOR_COMMAND_LIMIT')
        for cmd in pin.commands:
            if isinstance(cmd,LifecyclePin) and cmd.spec.renewal is None:
                a=anchor_from_pin(cmd)
                if a.plan_revision!=revision or a.run_id!=s.run_id or s.run_id in expected:
                    raise ValueError('D0_ANCHOR_PLAN_HOLD')
                expected[s.run_id]=a
        if s.run_id in expected:
            verify_anchor(c,expected[s.run_id])
        else:
            c.execute('SELECT run_id FROM t1_candidate.terminal_command_anchors WHERE '+_KEY,(*_SCOPE,s.run_id))
            if c.fetchone() is not None: raise ValueError('D0_ANCHOR_EXTRA_HOLD')
    c.execute('SELECT '+_COLUMNS+' FROM t1_candidate.terminal_command_anchors WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND plan_revision=%s ORDER BY run_id',(*_SCOPE,revision))
    for a in sorted(expected.values(),key=lambda a:a.run_id):
        row=c.fetchone()
        if row is None or tuple(row)!=a.row(): raise ValueError('D0_ANCHOR_PLAN_SET_HOLD')
    if c.fetchone() is not None: raise ValueError('D0_ANCHOR_EXTRA_HOLD')
