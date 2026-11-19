"""D0 composition of existing historical Core/ORG readers and G5 IAM review.

No current assignment, role issuance, atomic snapshot, claim or commit authority.
The cursor belongs to a server-owned consistent read-only Core snapshot; ORG and
IAM use separate existing stores. This is not a public or execution entry point.
"""
from app.core.transaction.identity_binding import Review, digest, valid_request


def inspect_core_org_session_reference(cursor, resolver, credential, intent, initial,
        session, session_sha, read_latest, *, plan, pins, members, pool, events,
        anchor, store, org_reference, org_sha, org_head, seat, history_pin,
        root, owner_pin, domain, evidence=None):
    """Join exact retained member, historical task role/version and G5 proposal.

    Reuse the ORG-06 bridge for the historical join; its summary deliberately
    omits run version, so reuse the Core reader on the same snapshot for that
    field. No interpretation of D4 revision/digests as ORG assignment evidence.
    All structural matches remain HOLD. Never use this as authorization.
    """
    try:
        from app.core.development_review.research_slice import (
            inspect_research_slice, ResearchSliceReview)
        from app.core.event_store.plan_history_review import TaskHistory
        from app.core.event_store.company_coordination import Member, _member
        from app.core.transaction.identity_fence_review import IdentityReadback, SessionReference
        from app.core.transaction.intent_identity import derive_request
        from app.core.transaction.org_membership_review import OrgReadback, inspect_org_session_reference
        from org_core_bridge import BindingReview, review_research_binding

        if (type(initial) is not IdentityReadback or type(session) is not SessionReference
                or type(org_reference) is not OrgReadback or not callable(read_latest)
                or type(members) is not tuple or not all(_member(m) for m in members)):
            return Review('D5G6_CORE_ORG_INPUT_HOLD')
        req = derive_request(intent, initial.member, initial.scope, initial.principal)
        if not valid_request(req) or session.request != req:
            return Review('D5G6_CORE_ORG_REQUEST_HOLD')
        selected = [m for m in members if (m.project_id, m.plan_revision, m.task_id)
                    == (req.project, req.plan_revision, req.task)]
        if (len(selected) != 1 or type(selected[0]) is not Member
                or selected[0] != initial.member):
            return Review('D5G6_CORE_MEMBER_HOLD')
        member = selected[0]
        args = dict(plan=plan, expected_revision=req.plan_revision, project_id=req.project,
                    pins=pins, members=members, pool=pool, events=events, anchor=anchor,
                    evidence=evidence)
        core = inspect_research_slice(cursor, **args)
        if (type(core) is not ResearchSliceReview or core.structural_match is not True
                or core.decision != 'HOLD' or core.freshness != 'HISTORICAL_SAMPLE'
                or core.dispatch_allowed is not False or core.release_ready is not False
                or core.project_id != req.project or core.plan_revision != req.plan_revision
                or type(core.tasks) is not tuple or not all(type(t) is TaskHistory for t in core.tasks)):
            return Review('D5G6_CORE_READBACK_HOLD')
        tasks = [t for t in core.tasks if t.task_id == req.task]
        if (len(tasks) != 1 or type(tasks[0].version) is not int
                or tasks[0].version != intent.expected_version
                or tasks[0].role not in ('orchestrator', 'research', 'engineer', 'qa')
                or tasks[0].role != org_reference.role or org_reference.seat != seat):
            return Review('D5G6_CORE_TASK_ROLE_VERSION_HOLD')
        role = tasks[0].role
        def historical_join():
            joined = review_research_binding(cursor, **args, store=store, org_head=org_head,
                        history_pin=history_pin, task_id=req.task, seat_id=seat)
            return (type(joined) is BindingReview and joined.structural_match is True
                    and joined.reason == 'D0_HISTORICAL_REFERENCE_MATCH_ONLY'
                    and joined.decision == 'HOLD' and joined.freshness == 'HISTORICAL_SAMPLE'
                    and joined.authoritative is False and joined.runtime_binding is None
                    and joined.dispatch_allowed is False and joined.release_ready is False
                    and (joined.org_revision, joined.plan_revision, joined.project_id,
                         joined.task_id, joined.seat_id, joined.role) ==
                        (org_head, req.plan_revision, req.project, req.task, seat, role))
        if not historical_join():
            return Review('D5G6_HISTORICAL_JOIN_HOLD')
        latest_reads = 0
        latest_verified = False
        def latest_member():
            nonlocal latest_reads, latest_verified
            latest_reads += 1
            if latest_reads != 1:
                raise ValueError('D5G6_CORE_MEMBER_DRIFT_HOLD')
            sample = read_latest()
            if (type(sample) is not IdentityReadback or not _member(sample.member)
                    or sample.member != member or sample.scope != initial.scope
                    or sample.principal != initial.principal
                    or derive_request(intent, sample.member, sample.scope, sample.principal) != req
                    or not historical_join()):
                raise ValueError('D5G6_CORE_MEMBER_DRIFT_HOLD')
            latest_verified = True
            return sample
        result = inspect_org_session_reference(resolver, credential, intent, initial, session,
                    session_sha, latest_member, store=store, org_reference=org_reference,
                    org_sha=org_sha, org_head=org_head, seat=seat, role=role,
                    history_pin=history_pin, root=root, owner_pin=owner_pin, domain=domain)
        if (latest_reads != 1 or latest_verified is not True
                or type(result) is not Review or result.structural_match is not True
                or result.reason != 'D5G5_ORG_PROPOSAL_SESSION_MATCH_ONLY'
                or result.decision != 'HOLD' or not digest(result.binding_sha)
                or result.commit_allowed is not False or result.dispatch_allowed is not False
                or result.retry_allowed is not False):
            return Review('D5G6_G5_REVIEW_HOLD')
        if not historical_join():
            return Review('D5G6_HISTORICAL_JOIN_DRIFT_HOLD')
        return Review('D5G6_CORE_ORG_HISTORY_SESSION_MATCH_ONLY', True, result.binding_sha)
    except Exception:
        return Review('D5G6_CORE_ORG_UNAVAILABLE_HOLD')
