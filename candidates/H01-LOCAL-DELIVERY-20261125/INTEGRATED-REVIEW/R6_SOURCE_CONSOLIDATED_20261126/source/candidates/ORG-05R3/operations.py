"""D0 proposal-only operations; no authority, dispatch, or durable storage."""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from staffing import Staffing

def digest(x):
    return sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def ident(x):
    if type(x) is not str or not x or x.strip()!=x: raise ValueError('IDENTITY')
    return x

@dataclass(frozen=True)
class ProjectTeam:
    tenant: str
    company: str
    revision: str
    project: str
    coordinator: str
    members: tuple[str,...]

@dataclass(frozen=True)
class Proposal:
    tenant: str
    company: str
    revision: str
    project: str
    task: str
    sender: str
    recipient: str
    kind: str
    team_digest: str
    decision: str = 'HOLD'

@dataclass(frozen=True)
class Entry:
    sequence: int
    previous: str
    proposal: Proposal
    digest: str

def context(s: Staffing, team: ProjectTeam):
    if type(team) is not ProjectTeam or (team.tenant,team.company,team.revision)!=(s.org.tenant,s.org.company,s.revision()): raise ValueError('SCOPE_REVISION')
    ident(team.project); ident(team.coordinator)
    if type(team.members) is not tuple: raise ValueError('MEMBERS')
    for x in team.members: ident(x)
    occupied={b.seat:b.instance for b in s.bindings}
    if len(set(team.members))!=len(team.members) or team.coordinator not in team.members or not set(team.members)<=occupied.keys(): raise ValueError('MEMBERS')
    return occupied

def department(s, seat):
    units={u.id:u for u in s.org.units}; pos={p.id:p for p in s.org.seats}[seat]; u=units[pos.unit]
    while u.kind!='department' and u.parent is not None: u=units[u.parent]
    return u.id if u.kind=='department' else None

def propose(s,team,task,sender,recipient,kind):
    context(s,team)
    for x in (task,sender,recipient): ident(x)
    if sender==recipient or not {sender,recipient}<=set(team.members): raise ValueError('PARTICIPANTS')
    seats={x.id:x for x in s.org.seats}
    if kind=='delegation':
        if seats[recipient].reports_to!=sender: raise ValueError('REPORTING')
    elif kind=='handoff':
        a,b=department(s,sender),department(s,recipient)
        if a is None or b is None or a==b: raise ValueError('DEPARTMENT')
    else: raise ValueError('KIND')
    return Proposal(team.tenant,team.company,team.revision,team.project,task,sender,recipient,kind,digest(asdict(team)))

def verify_history(s,team,entries):
    context(s,team)
    if type(entries) is not tuple: raise ValueError('HISTORY')
    prev='0'*64; seen=set()
    for n,e in enumerate(entries,1):
        if type(e) is not Entry or type(e.proposal) is not Proposal: raise ValueError('ENTRY')
        p=e.proposal
        expected=propose(s,team,p.task,p.sender,p.recipient,p.kind)
        key=digest(asdict(p))
        if p!=expected or key in seen or e.sequence!=n or e.previous!=prev or e.digest!=digest([n,prev,asdict(p)]): raise ValueError('HISTORY')
        seen.add(key); prev=e.digest
    return prev

def append(s,team,entries,p):
    prev=verify_history(s,team,entries); n=len(entries)+1
    e=Entry(n,prev,p,digest([n,prev,asdict(p)])); result=entries+(e,)
    verify_history(s,team,result); return result

def office_projection(s):
    """Read-only staffing projection, never geometry or runtime state."""
    rev=s.revision()
    return {'schema':'org.office.preview.v0-D0','tenant':s.org.tenant,'company':s.org.company,'revision':rev,'authority':False,'placement':None,'rows':[{'seat':b.seat,'instance':b.instance,'department':department(s,b.seat)} for b in sorted(s.bindings,key=lambda x:x.seat)]}
