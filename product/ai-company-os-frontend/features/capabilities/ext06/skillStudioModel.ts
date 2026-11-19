/** Historical synthetic catalog projection, not registry, ACL or live assignment. */
import fixture from './skillData.json';
export type SkillRow=typeof fixture.skills[number];
export type Catalog=typeof fixture;
export type Filter={role:string;department:string;query:string};
const expected=JSON.stringify(fixture);
const ids=['superpowers','ui-ux-pro-max','watch'];
const roleIds=['orchestrator','research','engineer','qa'] as const;
const departments=['Yönetim','Araştırma','Mühendislik','Kalite'];
const roleHints=[['engineer','qa'],['engineer','research'],['research']];
const digest=(s:unknown)=>typeof s==='string'&&/^[0-9a-f]{64}$/.test(s);
const git=(s:unknown)=>typeof s==='string'&&/^[0-9a-f]{40}$/.test(s);
const empty=(x:unknown)=>Array.isArray(x)&&x.length===0;
const norm=(x:string)=>x.normalize('NFKC').toLocaleLowerCase('tr-TR').trim();
export function readSkillCatalog(raw:unknown=fixture):{ok:true;catalog:Catalog}|{ok:false;reason:string}{
 try {
  // Exact JSON snapshot comparison: not a signature, not a remote input API.
  if(JSON.stringify(raw)!==expected)return {ok:false,reason:'EXT06_SOURCE_MISMATCH'};
  const c:Catalog=JSON.parse(expected);
  if(c.profile!=='EXT05_LOCAL_SYNTHETIC_READBACK'||c.authority!=='NONE'||c.independent_acceptance!=='HOLD'||c.installed_count!==0||c.active_count!==0||c.actual_installed_count!==null||c.actual_active_count!==null||c.actual_assignments!==null||!git(c.source_commit)||!git(c.projection_blob)||!git(c.lock_blob)||!git(c.roles_source_blob)||c.skills.length!==3||c.shared_evidence.independent!=='HOLD')return {ok:false,reason:'EXT06_BOUNDARY_HOLD'};
  if(Object.keys(c.roles).length!==4||roleIds.some((r,i)=>c.roles[r]?.department!==departments[i]))return {ok:false,reason:'EXT06_ROLES_HOLD'};
  for(const [i,s] of c.skills.entries()){
   if(s.skill_id!==ids[i]||s.status!=='QUARANTINED'||s.enabled!==false||s.installed!==false||s.installation_evidence!=='NOT_RUN'||s.g7_ref!==null||s.g8_ref!==null||!empty(s.effective_tools)||JSON.stringify(s.role_hints)!==JSON.stringify(roleHints[i])||s.reviews.length!==s.role_hints.length||![s.artifact_sha256,s.manifest_sha256,s.input_schema_sha256,s.output_schema_sha256].every(digest)||![s.source_commit,s.artifact_git_blob,s.manifest_git_blob,s.upstream_commit,s.evidence.git_blob].every(git))return {ok:false,reason:'EXT06_SKILL_HOLD'};
   if(s.reviews.some((r,j)=>r.role_hint!==s.role_hints[j]||r.status!=='QUARANTINED'||r.decision!=='HOLD'||r.reason!=='INDEPENDENT_RECEIPTS_ABSENT'||r.structural_match!==true||r.enabled!==false||r.grant_created!==false||r.dispatch_allowed!==false||r.independent_verified!==false||!empty(r.effective_tools)))return {ok:false,reason:'EXT06_REVIEW_HOLD'};
  }
  return {ok:true,catalog:c};
 } catch {return {ok:false,reason:'EXT06_INVALID_PROJECTION'};}
}
export function filterSkills(c:Catalog,f:Filter):SkillRow[]{
 if(!f||typeof f.query!=='string'||f.query.length>200||!(f.role==='all'||roleIds.some(r=>r===f.role))||!(f.department==='all'||departments.includes(f.department)))return [];
 const q=norm(f.query);
 return c.skills.filter(s=>s.role_hints.some(r=>{const role=c.roles[r as keyof Catalog['roles']];return !!role&&(f.role==='all'||f.role===r)&&(f.department==='all'||f.department===role.department);})&&norm([s.name,s.skill_id,s.version,s.description,s.source_path,...s.role_hints].join(' ')).includes(q));
}
export function selectedSkill(rows:readonly SkillRow[],id:string):SkillRow|null{return rows.find(s=>s.skill_id===id)??null;}
export const emptyFilter=():Filter=>({role:'all',department:'all',query:''});
export const skillBoundary=()=>({actualInstalled:null,actualActive:null,actualAssignments:null,installAllowed:false,grantAllowed:false,dispatchAllowed:false,releaseAllowed:false,independentAcceptance:'HOLD'} as const);
