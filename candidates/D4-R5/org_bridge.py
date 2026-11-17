"""D4-R5 cross-contract review. No resolver, role grant, writes or scope alias."""
from dataclasses import dataclass, asdict, field
from identity_binding import review_binding, digest, token, revision
from staffing import Staffing
from operations import ProjectTeam, Proposal, context, department, propose, digest as org_digest


@dataclass(frozen=True)
class OrgPin:
    scope: tuple
    head: str
    sequence: int
    staffing_sha: str
    team_sha: str
    seat: str
    department_id: str
    task_role: str
    binding_sha: str
    member_sha: str


@dataclass(frozen=True)
class Review:
    reason: str
    structural_match: bool = False
    decision: str = field(default='HOLD', init=False)
    commit_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)


def valid_pin(p):
    return (type(p) is OrgPin and type(p.scope) is tuple and len(p.scope)==3
            and all(token(x) for x in (*p.scope,p.seat,p.department_id,p.task_role))
            and revision(p.sequence) and all(digest(x) for x in (p.head,p.staffing_sha,p.team_sha,p.binding_sha,p.member_sha)))


def inspect_org(request, binding, latest_binding, tick, pin, latest_pin,
                staffing, team, task_ref, core_scope, member_row, plan_role):
    """Inputs are normalized owner readbacks, not HTTP data or proof of provenance.

    task_ref follows R5 TaskReference fields; member_row follows Core Member.row().
    Core scope is separately pinned because Member.row() omits it. No run is inferred
    from an ORG proposal. Initial/latest pins are separately retained observations.
    """
    b=review_binding(request,binding,latest_binding,tick)
    if not b.structural_match:
        return Review(b.reason)
    if not valid_pin(pin) or not valid_pin(latest_pin) or pin!=latest_pin:
        return Review('D4_ORG_REVISION_HOLD')
    if pin.binding_sha!=b.binding_sha:
        return Review('D4_IDENTITY_PIN_HOLD')
    if pin.scope!=request.scope or core_scope!=request.scope or type(core_scope) is not tuple:
        return Review('D4_COMMON_SCOPE_HOLD')
    if type(staffing) is not Staffing or type(team) is not ProjectTeam:
        return Review('D4_ORG_INPUT_HOLD')
    try:
        if (staffing.org.tenant,staffing.org.company)!=pin.scope[:2] or staffing.revision()!=pin.staffing_sha:
            return Review('D4_STAFFING_HOLD')
        occupied=context(staffing,team)
        if team.project!=request.project or org_digest(asdict(team))!=pin.team_sha:
            return Review('D4_TEAM_HOLD')
        if pin.seat not in team.members or occupied.get(pin.seat)!=request.agent:
            return Review('D4_SEAT_AGENT_HOLD')
        seat=next(x for x in staffing.org.seats if x.id==pin.seat)
        if (seat.role!=pin.task_role or plan_role!=pin.task_role
                or pin.task_role not in ('orchestrator','research','engineer','qa')):
            return Review('D4_TASK_ROLE_HOLD')
        if department(staffing,pin.seat)!=pin.department_id:
            return Review('D4_DEPARTMENT_HOLD')
        expected=(request.scope,request.project,request.plan_revision,request.task,
                  pin.task_role,request.agent,request.principal)
        if type(task_ref) is not tuple or task_ref!=expected:
            return Review('D4_ORG_TASK_REFERENCE_HOLD')
        expected_member=(request.project,request.plan_revision,request.task,request.run,
                         request.agent,request.principal)
        if (type(member_row) is not tuple or len(member_row)!=7 or member_row[:6]!=expected_member
                or type(member_row[6]) is not int or not 0<=member_row[6]<2**63):
            return Review('D4_CORE_RUN_MEMBERSHIP_HOLD')
        if org_digest(['d4-r5-core-member-review-v1',core_scope,member_row])!=pin.member_sha:
            return Review('D4_CORE_MEMBER_PIN_HOLD')
    except (ValueError,TypeError,AttributeError,KeyError,StopIteration,RecursionError):
        return Review('D4_ORG_STRUCTURE_HOLD')
    return Review('D4_ORG_MATCH_REVIEW_ONLY',True)


def inspect_proposal(staffing, team, task, sender, recipient, kind, observed):
    """Original ORG proposal rules only. Not durable history or a delegation grant."""
    try:
        expected=propose(staffing,team,task,sender,recipient,kind)
        if type(observed) is Proposal and observed==expected and observed.decision=='HOLD':
            return Review('D4_PROPOSAL_MATCH_ONLY',True)
    except (ValueError,TypeError,AttributeError,KeyError,RecursionError):
        pass
    return Review('D4_PROPOSAL_HOLD')
