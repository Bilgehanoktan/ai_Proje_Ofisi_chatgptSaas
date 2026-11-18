"""Read-only J2-R3 arithmetic comparison, using R2's disposable fixture projection.
Not a product settlement, a membership reader, a D5 grant, or a T1 mapping.
"""
from dataclasses import dataclass, field
from membership_review import ROW, _shape, _binding_ok, _phase, _uint, _token

@dataclass(frozen=True)
class TerminalReview:
    reason: str
    original_release: int | None = None
    unused_run_capacity: int | None = None
    historical_allocations: int | None = None
    unresolved_allocations: int | None = None
    hypothetical_outstanding_after_original: int | None = None
    hypothetical_outstanding_after_unused: int | None = None
    decision: str = field(default='HOLD', init=False)
    release_allowed: bool = field(default=False, init=False)
    settlement_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)


def inspect_terminal_projection(snapshot, run_id):
    """Compare legacy full issuance release with remaining run capacity.

    Caller supplies an R2 readback (not independent custody). For fully reconciled
    members the unused-capacity result is arithmetic only, not an approved policy.
    Never treat aggregate budget capacity as membership or permission.
    """
    try:
        if not _token(run_id) or type(snapshot) is not dict or set(snapshot) != {'budget','pools','members','journal','receipts'}:
            raise ValueError
        rev,limit,outstanding,recognized,unknown=snapshot['budget']
        if not all(_uint(x) for x in (rev,limit,outstanding,recognized,unknown)) or unknown not in (0,1) or outstanding+recognized>limit:
            raise ValueError
        pools=snapshot['pools']; members=snapshot['members']
        if type(pools) is not list or type(members) is not tuple or len(pools)>16 or len(members)>4096:
            raise ValueError
        indexed={}; identities=set(); budgets=set()
        for row in pools:
            if type(row) is not tuple or len(row)!=5: raise ValueError
            run,issued,free,closed,released=row
            if not _token(run) or run in indexed or not all(_uint(x) for x in row[1:]) or not issued or closed not in (0,1): raise ValueError
            indexed[run]=(issued,free,closed,released,[])
        for m in members:
            if not _shape(m,ROW) or not _binding_ok(m) or not _phase(m) or m['run_id'] not in indexed: raise ValueError
            keys=(('membership',m['membership_pin']),('invocation',m['invocation_pin']),('idem',m['invocation_idempotency_key']),('reservation',m['budget_id'],m['reservation_id']))
            if identities.intersection(keys): raise ValueError
            identities.update(keys); budgets.add(m['budget_id']); indexed[m['run_id']][4].append(m)
        if len(budgets)>1: raise ValueError
        total_pending=total_spent=0; has_unknown=False
        for issued,free,closed,released,rows in indexed.values():
            if issued!=free+released+sum(m['reserved_minor'] for m in rows) or (closed and (free or rows or released!=issued)) or (not closed and released): raise ValueError
            total_pending+=free+sum(m['reserved_minor'] for m in rows if m['state']!='RECONCILED')
            total_spent+=sum(m['recognized_minor'] for m in rows if m['state']=='RECONCILED')
            has_unknown |= any(m['state']=='UNKNOWN' for m in rows)
        if (outstanding,recognized,unknown)!=(total_pending,total_spent,int(has_unknown)): raise ValueError
        if run_id not in indexed: return TerminalReview('RUN_MISSING_HOLD')
        issued,free,closed,released,rows=indexed[run_id]
        historical=sum(m['reserved_minor'] for m in rows)
        unresolved=sum(m['reserved_minor'] for m in rows if m['state']!='RECONCILED')
        values=dict(original_release=issued,unused_run_capacity=free,historical_allocations=historical,unresolved_allocations=unresolved)
        if closed: return TerminalReview('ALREADY_CLOSED_HOLD',**values)
        if unknown: return TerminalReview('UNKNOWN_COST_HOLD',**values)
        if unresolved: return TerminalReview('UNRESOLVED_MEMBERSHIP_HOLD',**values)
        values.update(hypothetical_outstanding_after_original=outstanding-issued if outstanding>=issued else None,
                      hypothetical_outstanding_after_unused=outstanding-free)
        if historical: return TerminalReview('LEGACY_FULL_RELEASE_INCOMPATIBLE_HOLD',**values)
        return TerminalReview('UNTOUCHED_POOL_ARITHMETIC_ONLY_HOLD',**values)
    except (KeyError,TypeError,ValueError,OverflowError,AttributeError):
        return TerminalReview('PROJECTION_INVALID_HOLD')
