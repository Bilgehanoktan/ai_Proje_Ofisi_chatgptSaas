/** P10J21: source inventory, not a skill registry, ACL, or runtime projection. */
export const areas=['all','skill','memory','knowledge'] as const;
export const roles=['all','orchestrator','research','engineer','qa'] as const;
export type Area=typeof areas[number];
export type Role=typeof roles[number];
export type Entry={id:string;area:Exclude<Area,'all'>;title:string;path:string;blob:string;symbol:string;review:string;contexts:readonly Exclude<Role,'all'>[];boundary:'HOLD'|'QUARANTINED'};
const root='product/ai-company-os-backend/app/engines/';
export const entries:readonly Entry[]=[
 {id:'manifest',area:'skill',title:'Beceri manifest incelemesi',path:root+'skill_engine/manifest_review.py',blob:'26c4eea34bb938ae4e9a311d9331d3ccab77487d',symbol:'inspect_skill',review:'Scope ve exact manifest pin; F0 makbuzu yok.',contexts:['engineer','qa'],boundary:'QUARANTINED'},
 {id:'resolver',area:'skill',title:'Yetkinlik kesişimi',path:root+'skill_engine/resolver.py',blob:'fede5e35bf2221920a83b4d8183c9374b72d9668',symbol:'inspect_capabilities',review:'Kaynak, adaptör ve policy kesişimi; etkin araç veya grant değil.',contexts:['orchestrator','engineer','qa'],boundary:'QUARANTINED'},
 {id:'lineage',area:'memory',title:'Hafıza lineage / tombstone',path:root+'memory_engine/retrieval.py',blob:'c62c79bf9fa66d76505ca8e9e9195564e281cafe',symbol:'inspect_retrieval',review:'Eksik, eski veya döngülü lineage HOLD; içerik okunmaz.',contexts:['research','qa'],boundary:'HOLD'},
 {id:'access',area:'memory',title:'Run ve ACL bağlamı',path:root+'memory_engine/runtime_binding.py',blob:'b24c782973ec8731f8dbea17d0379ae5abe897f0',symbol:'inspect_run_memory_access',review:'Run, lease, ACL, policy/witness epoch ve tombstone eşleşmesi; erişim verilmez.',contexts:['orchestrator','research','qa'],boundary:'HOLD'},
 {id:'snapshot',area:'memory',title:'Sentetik snapshot deposu',path:root+'memory_engine/snapshot_store.py',blob:'5c7aa2b2a211970ea8fb3d90c55423157a1c10d1',symbol:'SnapshotPin',review:'Yerel D0 SQLite snapshot adayı; gerçek hafıza kaydı değil.',contexts:['engineer','qa'],boundary:'HOLD'},
 {id:'provenance',area:'knowledge',title:'Kaynak ve kanıt aralığı',path:root+'knowledge_engine/provenance.py',blob:'7d710685366a55c117e49043a64f1eeabf5079cf',symbol:'inspect_span',review:'Kaynak sürümü, ham hash, byte aralığı ve span hash; içerik veya doğrulanmış iddia değil.',contexts:['research','qa'],boundary:'HOLD'},
];
const normalize=(s:string)=>s.trim().toLocaleLowerCase('tr-TR');
export function filterEntries(area:string,role:string,query:string):readonly Entry[]{
 if(!areas.some(x=>x===area)||!roles.some(x=>x===role)||typeof query!=='string'||query.length>200)return [];
 const q=normalize(query);
 return entries.filter(e=>(area==='all'||e.area===area)&&(role==='all'||e.contexts.some(r=>r===role))&&normalize([e.title,e.path,e.symbol,e.review,e.id].join(' ')).includes(q));
}
export function selectedEntry(visible:readonly Entry[],id:string):Entry|null{return visible.find(e=>e.id===id)??null;}
export const studioBoundary=()=>({installedCount:null,enabledCount:null,memoryCount:null,sourceCount:null,actualAssignments:null,contentAvailable:false,grantAllowed:false,installAllowed:false,retrievalAllowed:false,releaseAllowed:false} as const);
