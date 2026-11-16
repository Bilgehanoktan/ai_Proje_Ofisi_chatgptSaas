/** Exact historical D0 sample inspection; never authorizes placement or task binding. */
const record=(x:unknown):x is Record<string,unknown>=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const exact=(x:Record<string,unknown>,expected:Record<string,unknown>)=>Object.keys(x).length===Object.keys(expected).length&&Object.entries(expected).every(([k,v])=>Object.hasOwn(x,k)&&x[k]===v);
const empty=(x:unknown)=>Array.isArray(x)&&x.length===0;
const fixed={schema_version:'office.snapshot.v0-D0',tenant_id:'synthetic-tenant',world_id:'demo-world',environment_id:'A0_SAMPLE_ONLY',snapshot_seq:0,layout_revision:'draft-hybrid-floor-1',as_of:'2026-11-01T00:00:00Z',data_status:'D0_SAMPLE_NO_RUNTIME',policy_epoch:null,wa_epoch:null} as const;
const authority={code_effective:false,repo_effective:false,dev_effective:false,security_acceptance:'HOLD',real_test:'NOT_RUN',production:'NOT_AUTHORIZED'};
const roleIds=['orchestrator','research','engineer','qa'];
const roleTemplates=[{id:'orchestrator',name:'Orchestrator',description:'Operasyon yönetimi',department:'Yönetim'},{id:'research',name:'Research',description:'Araştırma ve kaynak analizi',department:'Araştırma'},{id:'engineer',name:'Engineer',description:'Mühendislik ve üretim',department:'Mühendislik'},{id:'qa',name:'QA',description:'Kalite incelemesi; IV değildir',department:'Kalite'}];
const metrics=[{metric_id:'active_runs',label:'Doğrulanmış aktif işler',value:null},{metric_id:'pending_decisions',label:'Gerçek karar talepleri',value:null},{metric_id:'revenue',label:'Muhasebeleştirilmiş gelir (TRY)',value:null},{metric_id:'verified_outputs',label:'Bağımsız doğrulanmış çıktı',value:null}];
export function inspectOfficeV0(x:unknown){
 const hold={status:'JOIN_HOLD',source:'UNVERIFIED',authoritative:false,placement:false,taskBinding:false,activeRuns:null} as const;
 if(!record(x)||Object.keys(x).length!==18||Object.entries(fixed).some(([k,v])=>!Object.hasOwn(x,k)||x[k]!==v)||!empty(x.agents)||!empty(x.decision_cases)||!empty(x.activity)||!record(x.authority)||!exact(x.authority,authority)||!record(x.work_summary)||!exact(x.work_summary,{verified_active_runs:null,verification_status:'UNVERIFIED'}))return hold;
 if(!Array.isArray(x.role_templates)||x.role_templates.length!==4||!roleTemplates.every((v,i)=>record(x.role_templates instanceof Array?x.role_templates[i]:null)&&exact((x.role_templates as Record<string,unknown>[])[i],v)))return hold;
 if(!Array.isArray(x.metrics)||x.metrics.length!==4||!metrics.every((v,i)=>record((x.metrics as unknown[])[i])&&exact((x.metrics as Record<string,unknown>[])[i],v)))return hold;
 if(!Array.isArray(x.floors)||x.floors.length!==2)return hold;
 const [first,second]=x.floors;
 if(!record(first)||Object.keys(first).length!==3||first.id!=='floor-1'||first.name!=='Kat 1 · Çekirdek operasyon'||!Array.isArray(first.stations)||first.stations.length!==4||!record(second)||Object.keys(second).length!==3||second.id!=='floor-2'||second.name!=='Kat 2 · Genişleme rezervi'||!empty(second.stations))return hold;
 if(!roleIds.every((r,i)=>record((first.stations as unknown[])[i])&&exact((first.stations as Record<string,unknown>[])[i],{id:'station-'+r,role_template_id:r,x:i%2,y:Math.floor(i/2),agent_instance_id:null})))return hold;
 return {...hold,source:'EXACT_HISTORICAL_SAMPLE',snapshotSeq:0,layoutRevision:fixed.layout_revision} as const;
}
