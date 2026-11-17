"""D0 staffing candidate. No grants, dispatch, persistence or authentication."""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from org_model import Org

@dataclass(frozen=True)
class Definition:
    id: str
    role: str

@dataclass(frozen=True)
class Instance:
    id: str
    definition: str
    tenant: str
    company: str

@dataclass(frozen=True)
class Binding:
    seat: str
    instance: str

@dataclass(frozen=True)
class Staffing:
    org: Org
    definitions: tuple[Definition, ...]
    instances: tuple[Instance, ...]
    bindings: tuple[Binding, ...]
    previous: str | None = None

    def revision(self):
        base = self.org.revision()
        for rows, cls in ((self.definitions, Definition),(self.instances, Instance),(self.bindings, Binding)):
            if type(rows) is not tuple or any(type(x) is not cls or any(type(v) is not str or not v.strip() for v in asdict(x).values()) for x in rows):
                raise ValueError('SHAPE')
        d = {x.id:x for x in self.definitions}; i = {x.id:x for x in self.instances}; s = {x.id:x for x in self.org.seats}
        if len(d)!=len(self.definitions) or len(i)!=len(self.instances): raise ValueError('DUPLICATE')
        if any(x.role in {'independent-verifier','policy-review','w-a-witness'} for x in d.values()): raise ValueError('TRUST_ROLE')
        if any(x.definition not in d or (x.tenant,x.company)!=(self.org.tenant,self.org.company) for x in i.values()): raise ValueError('INSTANCE_SCOPE')
        if len({x.seat for x in self.bindings})!=len(self.bindings) or len({x.instance for x in self.bindings})!=len(self.bindings): raise ValueError('OCCUPANCY')
        for x in self.bindings:
            if x.seat not in s or x.instance not in i or s[x.seat].role!=d[i[x.instance].definition].role: raise ValueError('BINDING')
        if self.previous is not None and (type(self.previous) is not str or len(self.previous)!=64 or any(c not in '0123456789abcdef' for c in self.previous)): raise ValueError('PREVIOUS')
        body=['staffing.v0-D0',base,self.previous,*[sorted((asdict(x) for x in rows),key=lambda x:tuple(x.values())) for rows in (self.definitions,self.instances,self.bindings)]]
        return sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()

@dataclass(frozen=True)
class DelegationProposal:
    revision: str
    task: str
    sender: str
    recipient: str
    decision: str = 'HOLD'


def delegate(staffing: Staffing, revision: str, task: str, sender: str, recipient: str):
    if staffing.revision()!=revision or type(task) is not str or not task.strip() or sender==recipient: raise ValueError('PROPOSAL')
    occupied={x.seat for x in staffing.bindings}; seats={x.id:x for x in staffing.org.seats}
    if sender not in occupied or recipient not in occupied or seats[recipient].reports_to!=sender: raise ValueError('REPORTING_SCOPE')
    return DelegationProposal(revision,task,sender,recipient)


def verify_successor(old: Staffing, new: Staffing):
    if (old.org.tenant,old.org.company)!=(new.org.tenant,new.org.company) or new.previous!=old.revision(): raise ValueError('HISTORY')
    return new.revision()
