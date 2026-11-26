/** ORG-07C: strict R3 historical projection, never a live assignment. */
export const organizationCap=1048576;
const token=(v:unknown):v is string=>typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(v);
const sha=(v:unknown):v is string=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const role=(v:unknown):v is string=>typeof v==='string'&&v.length<=128&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(v)&&!['independent-verifier','policy-review','w-a-witness','iv','wa','w-a','pep','policy-engine','tool-gateway-pep','h01','human-ceo'].includes(v);
function exact(v:unknown,keys:string):v is Record<string,unknown>{
 if(v===null||typeof v!=='object'||Array.isArray(v))return false;
 const k=keys.split(' ');return Object.keys(v).length===k.length&&k.every(x=>Object.hasOwn(v,x));
}
type Kind='company'|'division'|'department'|'team';
export type Unit={id:string;kind:Kind;parent:string|null};
export type Position={id:string;unit:string;role:string;reports_to:string|null;occupied:boolean};
export type OrganizationProjection={schema:'org.studio.preview.v0-D0';scope:{tenant_id:string;company_id:string;environment_id:'A0_SAMPLE_ONLY'|'A0_REVIEW_ONLY'};revision:string;sequence:number;previous_revision:string|null;units:Unit[];positions:Position[];decision:'HOLD';authoritative:false;identity_owner:'HOLD';geometry_join:'HOLD';runtime_binding:null;dispatch_allowed:false};
export function parseOrganization(raw:unknown):OrganizationProjection|null{
 if(!exact(raw,'schema scope revision sequence previous_revision units positions decision authoritative identity_owner geometry_join runtime_binding dispatch_allowed'))return null;
 if(raw.schema!=='org.studio.preview.v0-D0'||raw.decision!=='HOLD'||raw.authoritative!==false||raw.identity_owner!=='HOLD'||raw.geometry_join!=='HOLD'||raw.runtime_binding!==null||raw.dispatch_allowed!==false)return null;
 const s=raw.scope;
 if(!exact(s,'tenant_id company_id environment_id')||!token(s.tenant_id)||!token(s.company_id)||!/^synthetic-[A-Za-z0-9_.:-]+$/.test(s.tenant_id)||!/^synthetic-[A-Za-z0-9_.:-]+$/.test(s.company_id)||(s.environment_id!=='A0_SAMPLE_ONLY'&&s.environment_id!=='A0_REVIEW_ONLY'))return null;
 if(!sha(raw.revision)||typeof raw.sequence!=='number'||!Number.isSafeInteger(raw.sequence)||raw.sequence<1||(raw.sequence===1?raw.previous_revision!==null:!sha(raw.previous_revision))||raw.previous_revision===raw.revision)return null;
 if(!Array.isArray(raw.units)||raw.units.length<1||raw.units.length>4096||!Array.isArray(raw.positions)||raw.positions.length>4096)return null;
 const units=new Map<string,Unit>(),positions=new Map<string,Position>();
 for(const u of raw.units){
  if(!exact(u,'id kind parent')||!token(u.id)||!['company','division','department','team'].includes(u.kind as string)||(u.parent!==null&&!token(u.parent))||units.has(u.id))return null;
  units.set(u.id,u as Unit);
 }
 const allowed:Record<Kind,Kind[]>={company:[],division:['company'],department:['company','division'],team:['department']};
 if([...units.values()].filter(u=>u.kind==='company').length!==1||units.get(s.company_id)?.kind!=='company')return null;
 for(const u of units.values())if(u.kind==='company'?u.parent!==null:u.parent===null||!allowed[u.kind].includes(units.get(u.parent)?.kind as Kind))return null;
 for(const p of raw.positions){
  if(!exact(p,'id unit role reports_to occupied')||!token(p.id)||!token(p.unit)||!units.has(p.unit)||!role(p.role)||(p.reports_to!==null&&!token(p.reports_to))||typeof p.occupied!=='boolean'||positions.has(p.id)||units.has(p.id))return null;
  positions.set(p.id,p as Position);
 }
 const checked=new Set<string>();
 for(const p of positions.values()){
  const chain=new Set<string>();let id:string|null=p.id;
  while(id!==null&&!checked.has(id)){
   if(chain.has(id)||!positions.has(id))return null;
   chain.add(id);id=positions.get(id)!.reports_to;
  }
  for(const x of chain)checked.add(x);
 }
 return raw as OrganizationProjection;
}
