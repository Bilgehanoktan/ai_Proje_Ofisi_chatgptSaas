"""ORG-04 local synthetic scale probe; no runtime, render, dispatch or grants."""
from time import perf_counter
from statistics import median
import tracemalloc, json, platform
from org_model import Org, Unit, Seat
from staffing import Definition, Instance, Binding, Staffing
from operations import office_projection

SIZES=(4,12,30,60,100)
DEPARTMENTS=('engineering','research','design','marketing','sales','finance','support','product','project-management','security','testing','academic','game-development','gis','healthcare','paid-media','spatial-computing','specialized')

def fixture(n, catalog=0):
    if n not in SIZES and n!=0: raise ValueError('SCENARIO')
    if catalog not in (0,267): raise ValueError('CATALOG')
    if n and catalog: raise ValueError('SEPARATE_SCENARIOS')
    roles=('orchestrator','research','engineer','qa')
    k=min(n,len(DEPARTMENTS)); units=(Unit('company','company',None),)+tuple(Unit(d,'department','company') for d in DEPARTMENTS[:k])
    seats=tuple(Seat(f'p{i}',DEPARTMENTS[i%k],roles[i%4],None if i==0 else f'p{(i-1)//4}') for i in range(n))
    defs=tuple(Definition(f'd{i}',f'catalog-role-{i:03}') for i in range(catalog)) if catalog else tuple(Definition(f'd{i}',r) for i,r in enumerate(roles))
    instances=tuple(Instance(f'a{i}',f'd{i%4}','d0-tenant','company') for i in range(n)); bindings=tuple(Binding(f'p{i}',f'a{i}') for i in range(n))
    return Staffing(Org('d0-tenant','company',units,seats),defs,instances,bindings)

def run(n,catalog=0,repeats=15):
    # Time is uninstrumented; separate traced peak pass. No performance SLA implied.
    t=[]; p=[]; rev=None
    for _ in range(repeats):
        start=perf_counter(); s=fixture(n,catalog); r=s.revision(); t.append((perf_counter()-start)*1000)
        start=perf_counter(); out=office_projection(s); p.append((perf_counter()-start)*1000)
        assert len(out['rows'])==n and out['placement'] is None and out['authority'] is False and out['revision']==r
        assert rev is None or rev==r; rev=r
    tracemalloc.start()
    try:
        s=fixture(n,catalog); s.revision(); office_projection(s); _,peak=tracemalloc.get_traced_memory()
    finally: tracemalloc.stop()
    return {'synthetic_instances':n,'catalog_definitions':len(s.definitions),'departments':sum(u.kind=='department' for u in s.org.units),'bindings':len(s.bindings),'median_build_validate_ms':round(median(t),3),'median_projection_ms':round(median(p),3),'traced_peak_kib':round(peak/1024,1),'actual_runtime':'NOT_RUN','actual_render':'NOT_RUN','revision':rev}

def main():
    print(json.dumps({'python':platform.python_version(),'platform':platform.platform(),'repeats':15,'scope':'D0_LOCAL_SYNTHETIC','a5_existing_actor_cap':128,'scenarios':[run(n) for n in SIZES]+[run(0,267)]},indent=2))
if __name__=='__main__': main()
