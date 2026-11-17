"""ORG-03 D0 metadata bridge. No geometry, movement, runtime join or authority."""
from dataclasses import dataclass, asdict
import re
from operations import context, department, digest, ident, ProjectTeam
from staffing import Staffing, verify_successor

ROLES = frozenset(('orchestrator','research','engineer','qa'))

def require(ok, reason):
    if not ok: raise ValueError(reason)

def exact_rows(rows, cls):
    require(type(rows) is tuple and all(type(r) is cls for r in rows), 'SHAPE')

def index(rows, key):
    out = {}
    for r in rows:
        k = getattr(r,key); ident(k); require(k not in out,'DUPLICATE'); out[k]=r
    return out

@dataclass(frozen=True)
class Room:
    id: str
    floor: str
    kind: str

@dataclass(frozen=True)
class Station:
    id: str
    room: str
    role: str
    kind: str = 'CORE'

@dataclass(frozen=True)
class Avatar:
    id: str
    home_station: str
    role: str
    agent_instance_id: None = None

@dataclass(frozen=True)
class OfficeView:
    tenant: str
    company: str
    world: str
    layout_revision: str
    rooms: tuple[Room,...]
    stations: tuple[Station,...]
    avatars: tuple[Avatar,...]

    def revision(self):
        for v in (self.tenant,self.company,self.world,self.layout_revision): ident(v)
        require(re.fullmatch(r'd0-[a-z0-9][a-z0-9-]{0,30}',self.world) is not None,'WORLD')
        for rows,cls in ((self.rooms,Room),(self.stations,Station),(self.avatars,Avatar)): exact_rows(rows,cls)
        rooms=index(self.rooms,'id'); stations=index(self.stations,'id'); avatars=index(self.avatars,'id')
        for r in rooms.values():
            ident(r.floor); require(r.id.startswith(r.floor+'/') and r.kind in ('WORK','MEETING','OTHER'),'ROOM')
        for s in stations.values():
            require(s.room in rooms and s.id.startswith(rooms[s.room].floor+'/') and s.role in ROLES and s.kind in ('CORE','SYNTHETIC_TEST'),'STATION')
        seen=set()
        for a in avatars.values():
            require(re.fullmatch(r'd0-visual-[a-z0-9][a-z0-9-]{0,52}',a.id) is not None and a.agent_instance_id is None and a.home_station in stations and stations[a.home_station].role==a.role and a.home_station not in seen,'AVATAR')
            seen.add(a.home_station)
        return digest(['org.office.view.v0-D0',self.tenant,self.company,self.world,self.layout_revision,*[sorted((asdict(r) for r in rows),key=lambda r:r['id']) for rows in (self.rooms,self.stations,self.avatars)]])

@dataclass(frozen=True)
class RoomLink:
    department: str
    room: str

@dataclass(frozen=True)
class PairProposal:
    instance: str
    seat: str
    avatar: str
    station: str

@dataclass(frozen=True)
class MeetingProposal:
    team: ProjectTeam
    room: str


def project(s: Staffing, view: OfficeView, staffing_revision: str, office_revision: str,
            links: tuple[RoomLink,...], pairs: tuple[PairProposal,...], meetings: tuple[MeetingProposal,...]=()):
    """Validate explicit proposals; emit a fresh detached dictionary, HOLD always."""
    require((s.org.tenant,s.org.company)==(view.tenant,view.company),'SCOPE')
    require(s.revision()==staffing_revision and view.revision()==office_revision,'STALE_REVISION')
    for rows,cls in ((links,RoomLink),(pairs,PairProposal),(meetings,MeetingProposal)): exact_rows(rows,cls)
    rooms=index(view.rooms,'id'); stations=index(view.stations,'id'); avatars=index(view.avatars,'id')
    deps={u.id for u in s.org.units if u.kind=='department'}; seats={p.id:p for p in s.org.seats}; bound={b.seat:b.instance for b in s.bindings}
    linkset=set()
    for l in links:
        require(l.department in deps and l.room in rooms and rooms[l.room].kind=='WORK','ROOM_LINK')
        k=(l.department,l.room); require(k not in linkset,'DUPLICATE_ROOM_LINK'); linkset.add(k)
    used=[set() for _ in range(4)]; rows=[]
    for p in pairs:
        require(p.seat in bound and bound[p.seat]==p.instance and p.avatar in avatars and p.station in stations,'PAIR_REFERENCE')
        a=avatars[p.avatar]; st=stations[p.station]; dep=department(s,p.seat)
        require(a.home_station==p.station and seats[p.seat].role==a.role==st.role and (dep,st.room) in linkset,'PAIR_SCOPE')
        for bucket,k in zip(used,(p.instance,p.seat,p.avatar,p.station)):
            require(k not in bucket,'PAIR_COLLISION'); bucket.add(k)
        rows.append({'candidateInstanceId':p.instance,'seatId':p.seat,'visualActorId':p.avatar,'homeStationId':p.station,'departmentId':dep,'roomId':st.room,'floorId':rooms[st.room].floor,'agentInstanceId':None,'decision':'HOLD'})
    sessions=[]; seen=set()
    for m in meetings:
        context(s,m.team); require(m.room in rooms and rooms[m.room].kind=='MEETING','MEETING_ROOM')
        key=(m.team.project,m.room); require(key not in seen,'DUPLICATE_MEETING'); seen.add(key)
        sessions.append({'projectId':m.team.project,'teamDigest':digest(asdict(m.team)),'memberSeats':sorted(m.team.members),'roomId':m.room,'decision':'HOLD','reserved':False})
    body={'schema':'org.office.bridge.v0-D0','mode':'D0_PROPOSAL_ONLY','tenant':view.tenant,'company':view.company,'world':view.world,'staffingRevision':staffing_revision,'officeRevision':office_revision,'layoutRevision':view.layout_revision,'authoritative':False,'geometryJoin':'HOLD','placement':None,'roomLinks':[{'departmentId':d,'roomId':r} for d,r in sorted(linkset)],'pairs':sorted(rows,key=lambda x:x['seatId']),'unmappedInstances':sorted(set(bound.values())-used[0]),'meetings':sorted(sessions,key=lambda x:(x['projectId'],x['roomId']))}
    return {**body,'digest':digest(body)}


def review_change(old: Staffing, new: Staffing, view: OfficeView, prior: dict):
    """Invalidate *all* old proposals on staffing revision change; no auto-rebinding."""
    next_rev=verify_successor(old,new)
    # Reconstruct and validate the complete old proposal rather than trust caller digest.
    require(type(prior) is dict and prior.get('meetings')==[],'REVIEW_REQUIRES_MEETING_FREE_PROJECTION')
    links=tuple(RoomLink(x['departmentId'],x['roomId']) for x in prior['roomLinks'])
    pairs=tuple(PairProposal(x['candidateInstanceId'],x['seatId'],x['visualActorId'],x['homeStationId']) for x in prior['pairs'])
    require(prior==project(old,view,old.revision(),view.revision(),links,pairs),'PRIOR_PROJECTION')
    old_map={b.instance:b.seat for b in old.bindings}; new_map={b.instance:b.seat for b in new.bindings}
    changed=sorted(i for i in old_map.keys()|new_map.keys() if old_map.get(i)!=new_map.get(i) or (i in old_map and i in new_map and department(old,old_map[i])!=department(new,new_map[i])))
    return {'oldRevision':old.revision(),'newRevision':next_rev,'invalidatedActors':sorted(x.avatar for x in pairs),'changedInstances':changed,'requiresReproposal':True,'geometryJoin':'HOLD','placement':None,'authoritative':False}


def from_a5_metadata(tenant: str, company: str, world: str, snapshot: dict) -> OfficeView:
    """Project A5R2 snapshot metadata only. Caller-supplied scope is NOT authenticated.
    No current cell, motion, portal, event or identity is joined. Active floors only.
    """
    require(type(snapshot) is dict and snapshot.get('mode')=='D0_SYNTHETIC_WORLD' and snapshot.get('authoritative') is False and snapshot.get('geometryJoin')=='HOLD','A5_BOUNDARY')
    token=snapshot['token']; ident(token['revision']); require(type(token['sequence']) is int and token['sequence']>=0,'A5_TOKEN')
    rooms=[]; stations=[]; actors=[]; layouts=[]; floors=set(); active=set(); all_stations=set(); all_actors=set()
    for f in snapshot['floors']:
        fid=ident(f['floorId']); require(fid not in floors,'A5_FLOOR'); floors.add(fid)
        lifecycle=f['lifecycle']; require(lifecycle in ('PLANNED','DRAFT','VALIDATING','APPROVAL_PENDING','PUBLISHED','ACTIVE','DRAINING','ARCHIVED'),'A5_LIFECYCLE')
        layouts.append((fid,ident(f['layoutRevision']),lifecycle))
        if lifecycle=='ACTIVE': active.add(fid)
        for r in f['rooms']:
            k=r['kind']; require(k in ('SEMI_OPEN_POD','COMMAND_HUB','SEMI_ENCLOSED_POD','MEETING_ZONE','OPEN_CIRCULATION','SIDE_CIRCULATION','RESERVED_POD','ENTRY_THRESHOLD','FLOOR_PORTAL'),'A5_ZONE')
            if lifecycle=='ACTIVE': rooms.append(Room(r['id'],fid,'WORK' if k in ('SEMI_OPEN_POD','COMMAND_HUB','SEMI_ENCLOSED_POD') else 'MEETING' if k=='MEETING_ZONE' else 'OTHER'))
        for st in f['stations']:
            require(st['agentInstanceId'] is None and st['floorId']==fid and st['stationId'] not in all_stations and st['kind'] in ('CORE','PASSIVE','SYNTHETIC_TEST'),'A5_STATION'); all_stations.add(st['stationId'])
            if lifecycle=='ACTIVE' and st['kind']!='PASSIVE': stations.append(Station(st['stationId'],st['roomId'],st['roleTemplateId'],st['kind']))
    for a in snapshot['actors']:
        home=a['home']; require(a['agentInstanceId'] is None and a['visualActorId'] not in all_actors and home['floorId'] in active and a['floorId'] in active,'A5_ACTOR'); all_actors.add(a['visualActorId'])
        actors.append(Avatar(a['visualActorId'],home['stationId'],a['roleTemplateId']))
    result=OfficeView(tenant,company,world,digest([token['revision'],sorted(layouts)]),tuple(rooms),tuple(stations),tuple(actors)); result.revision(); return result
