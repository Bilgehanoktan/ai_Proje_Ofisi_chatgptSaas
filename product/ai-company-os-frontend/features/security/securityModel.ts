/** D0 display adapter, not a Policy Engine, PEP, verifier or receipt validator. */
import catalog from '../../fixtures/company.catalog.json';
import snapshot from '../../fixtures/office.snapshot.json';
import core from '../../fixtures/core.preview.json';
export type SecurityRow={id:string;label:string;status:string;source:string;note:string};
export type SecurityView={ok:true;controls:SecurityRow[];trust:SecurityRow[];reasons:string[]}|{ok:false;reason:string};
const record=(x:unknown):x is Record<string,unknown>=>typeof x==='object'&&x!==null&&!Array.isArray(x);
const hold=(reason:string)=>({ok:false as const,reason});
const empty=(x:unknown)=>Array.isArray(x)&&x.length===0;
const expectedReasons=['CODE_REPO_DEV_NOT_EFFECTIVE','INDEPENDENT_ACCEPTANCE_MISSING','F0_F3_NOT_ACCEPTED','WA_UNPROVEN','NO_EXTERNAL_EFFECT'];
const controls:readonly SecurityRow[]=[
 {id:'normative',label:'Normatif CODE / REPO / DEV',status:'0/3 etkin',source:'company.catalog / office.snapshot.authority',note:'CEO-0174 çalışma izni normatif grant değildir.'},
 {id:'controls',label:'Repo / DEV kontrolleri',status:'0/24 PASS',source:'company.catalog / Güvenlik / C01–C24',note:'Bağımsız kontrol yuvaları; yerel test sayısı değil.'},
 {id:'f0',label:'F0 bağımsız makbuzları',status:'0/35',source:'company.catalog / Güvenlik / F0',note:'Makbuz üretilmedi.'},
 {id:'negative',label:'Negatif senaryolar',status:'0/30 · NOT_RUN',source:'company.catalog / Güvenlik / NEG-01–30',note:'Gerçek güvenlik senaryoları çalıştırılmadı.'}
];
const trust:readonly SecurityRow[]=[
 {id:'policy',label:'Policy / admission',status:'DENY',source:'core.preview.authority.decision',note:'Gerçek dispatch veya grant yok.'},
 {id:'pep',label:'PEP / ToolGateway',status:'HOLD',source:'gateway_review.py / DisabledToolGateway',note:'D0 teşhis; bağımsız izolasyon kanıtı yok.'},
 {id:'wa',label:'W-A witness',status:'HOLD',source:'witness_review.py / office.snapshot.wa_epoch',note:'Bağımsız kök ve epoch doğrulanmadı.'},
 {id:'qa',label:'QA',status:'HOLD',source:'company.catalog / Raporlar / Kanıt görünümü',note:'Kalite incelemesi, IV makbuzu değildir.'},
 {id:'iv',label:'Independent Verifier',status:'INCONCLUSIVE',source:'iv_review.py / receipt_review.py',note:'Yapısal eşleşme, bağımsız imza ve kök kanıtı değildir.'},
 {id:'release',label:'İnsan yayın yetkisi',status:'HOLD',source:'core.preview.authority.release_ready',note:'Yayın hazır değil; QA ve IV ayrı güven düzlemleridir.'}
];
const expectedCatalog=[['Başlangıç yetkileri','CODE / REPO / DEV','0/3 etkin'],['Repo / DEV kontrolleri','C01–C24','0/24 PASS'],['F0 bağımsız makbuzları','35 kabul yuvası','0/35'],['Negatif senaryolar','NEG-01–30','0/30 · NOT_RUN'],['W-A / PEP / IV','Gerçek bağımsız güven kökleri','HOLD']];
export function readSecurityView(c:unknown=catalog,s:unknown=snapshot,p:unknown=core):SecurityView{
 if(!record(c)||!record(s)||!record(p)||c.schema_version!=='company.catalog.v0-D0'||s.schema_version!=='office.snapshot.v0-D0'||p.schema_version!=='core.preview.v0-D0'||[c,s,p].some(x=>x.data_status!=='D0_SAMPLE_NO_RUNTIME')||s.tenant_id!=='synthetic-tenant'||s.world_id!=='demo-world'||s.environment_id!=='A0_SAMPLE_ONLY'||s.snapshot_seq!==0||s.policy_epoch!==null||s.wa_epoch!==null)return hold('SECURITY_SCOPE_HOLD');
 if(!record(c.authority)||!record(s.authority)||!record(p.authority))return hold('SECURITY_AUTHORITY_HOLD');
 const a=p.authority;
 if([c.authority,s.authority].some(x=>x.code_effective!==false||x.repo_effective!==false||x.dev_effective!==false||x.real_test!=='NOT_RUN')||s.authority.security_acceptance!=='HOLD'||s.authority.production!=='NOT_AUTHORIZED'||a.effective!==false||a.decision!=='DENY'||a.real_test!=='NOT_RUN'||a.release_ready!==false)return hold('SECURITY_AUTHORITY_HOLD');
 if(!empty(s.agents)||!empty(s.decision_cases)||!empty(s.activity)||!Array.isArray(c.limitations)||!c.limitations.includes('No actual agent instances')||!c.limitations.includes('No external effects')||!Array.isArray(s.metrics))return hold('SECURITY_EVIDENCE_HOLD');
 const verified=s.metrics.filter(x=>record(x)&&x.metric_id==='verified_outputs');if(verified.length!==1||verified[0].value!==null)return hold('SECURITY_EVIDENCE_HOLD');
 const reasons=a.reason_codes;if(!Array.isArray(reasons)||reasons.length!==expectedReasons.length||expectedReasons.some((r,i)=>reasons[i]!==r))return hold('SECURITY_REASON_HOLD');
 if(!record(c.sections))return hold('SECURITY_CATALOG_HOLD');
 const security=c.sections['Güvenlik'],reports=c.sections['Raporlar'];
 if(!Array.isArray(security)||security.length!==expectedCatalog.length||expectedCatalog.some(([title,description,status],i)=>{const r=security[i];return !record(r)||r.title!==title||r.description!==description||r.status!==status;}))return hold('SECURITY_CATALOG_HOLD');
 if(!Array.isArray(reports)||reports.length!==2||!record(reports[0])||reports[0].title!=='Kanıt görünümü'||reports[0].description!=='QA, IV ve release ayrı'||reports[0].status!=='Gerçek kanıt yok'||!record(reports[1])||reports[1].title!=='Raporlama'||reports[1].description!=='Sentetik katalog · dışa aktarma yok'||reports[1].status!=='HOLD')return hold('SECURITY_CATALOG_HOLD');
 return {ok:true,controls:controls.map(r=>({...r})),trust:trust.map(r=>({...r})),reasons:[...expectedReasons]};
}
export function filterReasons(reasons:readonly string[],query:string):string[]{const words=query.trim().toUpperCase().split(/\s+/).filter(Boolean);return reasons.filter(r=>words.every(w=>r.includes(w)));}
