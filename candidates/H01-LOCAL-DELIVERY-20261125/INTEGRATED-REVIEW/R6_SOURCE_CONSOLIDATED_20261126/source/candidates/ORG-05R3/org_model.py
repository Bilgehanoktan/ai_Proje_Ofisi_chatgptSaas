"""Isolated D0 organization candidate; no authorization or persistence."""
from dataclasses import dataclass
from hashlib import sha256
import json

@dataclass(frozen=True)
class Unit:
    id: str
    kind: str
    parent: str | None

@dataclass(frozen=True)
class Seat:
    id: str
    unit: str
    role: str
    reports_to: str | None = None

@dataclass(frozen=True)
class Org:
    tenant: str
    company: str
    units: tuple[Unit, ...]
    seats: tuple[Seat, ...]

    def revision(self):
        if not self.tenant or not self.company or type(self.units) is not tuple or type(self.seats) is not tuple:
            raise ValueError('SCOPE')
        u = {x.id:x for x in self.units}; s = {x.id:x for x in self.seats}
        if len(u)!=len(self.units) or len(s)!=len(self.seats) or set(u)&set(s): raise ValueError('DUPLICATE')
        if any(not x for x in (*u,*s)): raise ValueError('ID')
        if sum(x.kind=='company' for x in u.values())!=1 or self.company not in u or u[self.company].kind!='company': raise ValueError('ROOT')
        allowed={'company':(), 'division':('company',), 'department':('company','division'), 'team':('department',)}
        for x in u.values():
            if x.kind not in allowed or (x.kind=='company' and x.parent is not None) or (x.kind!='company' and (x.parent not in u or u[x.parent].kind not in allowed[x.kind])): raise ValueError('UNIT_PARENT')
        for x in s.values():
            if x.unit not in u or not x.role or x.role in ('independent-verifier','policy-review','w-a-witness'): raise ValueError('SEAT')
            seen={x.id}; p=x.reports_to
            while p is not None:
                if p in seen or p not in s: raise ValueError('REPORTING')
                seen.add(p); p=s[p].reports_to
        body=[self.tenant,self.company,sorted((x.id,x.kind,x.parent) for x in self.units),sorted((x.id,x.unit,x.role,x.reports_to) for x in self.seats)]
        return sha256(json.dumps(body,separators=(',',':')).encode()).hexdigest()

@dataclass(frozen=True)
class AssignmentProposal:
    revision: str
    task: str
    seat: str
    decision: str = 'HOLD'


def propose(org: Org, revision: str, task: str, seat: str):
    if org.revision()!=revision or not task or seat not in {x.id for x in org.seats}: raise ValueError('ASSIGNMENT')
    return AssignmentProposal(revision,task,seat)
