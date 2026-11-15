/** Offline presentation only. No ledger, money arithmetic, network or spending authority. */
import catalog from '../../fixtures/company.catalog.json';
import snapshot from '../../fixtures/office.snapshot.json';
export type FinanceMetric={id:string;label:string;value:null;source:string;note:string};
const fields:readonly FinanceMetric[]=[
 {id:'budget',label:'Bütçe limiti',value:null,source:'BudgetSnapshot.limit_minor',note:'Yetkili bütçe kaydı yok'},
 {id:'reservation',label:'Açık rezervasyon',value:null,source:'BudgetSnapshot.outstanding_minor',note:'Gerçek rezervasyon kanıtı yok'},
 {id:'available',label:'Yetkili kalan bütçe',value:null,source:'FinanceProjection.authorized_remaining_minor',note:'Tanısal kapasite, harcama yetkisi değildir'},
 {id:'cost',label:'Gerçek maliyet',value:null,source:'FinanceProjection.actual_cost_minor',note:'Sağlayıcı ve settlement kanıtı yok'},
 {id:'revenue',label:'Muhasebeleştirilmiş gelir',value:null,source:'office.snapshot.metrics[revenue] / FinanceProjection.revenue_minor',note:'Gelir doğrulanmadı'},
 {id:'collection',label:'Tahsilat',value:null,source:'FinanceProjection.collection_minor',note:'Gelirden ayrı; ödeme kanıtı yok'},
 {id:'tokens',label:'Model token kullanımı',value:null,source:'Mevcut katalogda değer yok',note:'Model çağrısı ve kullanım kaydı yok'},
 {id:'quota',label:'Abonelik kotası',value:null,source:'company.catalog / Abonelik ve kota',note:'Entitlement etkin değil'}
];
export type CatalogRow={title:string;description:string;status:string};
export type FinanceView={ok:true;metrics:FinanceMetric[];saas:CatalogRow[];goals:CatalogRow[]}|{ok:false;reason:string};
const hold=(reason:string)=>({ok:false as const,reason});
const record=(x:unknown):x is Record<string,unknown>=>typeof x==='object'&&x!==null&&!Array.isArray(x);
function rows(value:unknown,expected:readonly (readonly [string,string,string])[]):CatalogRow[]|null{
 if(!Array.isArray(value)||value.length!==expected.length)return null;
 const result:CatalogRow[]=[];
 for(const [i,[title,description,status]] of expected.entries()){
  const x:unknown=value[i];if(!record(x)||x.title!==title||x.description!==description||x.status!==status)return null;
  result.push({title,description,status});
 }
 return result;
}
export function readFinanceView(c:unknown=catalog,s:unknown=snapshot):FinanceView{
 if(!record(c)||!record(s)||c.schema_version!=='company.catalog.v0-D0'||c.data_status!=='D0_SAMPLE_NO_RUNTIME'||s.schema_version!=='office.snapshot.v0-D0'||s.data_status!=='D0_SAMPLE_NO_RUNTIME'||s.tenant_id!=='synthetic-tenant'||s.environment_id!=='A0_SAMPLE_ONLY'||s.world_id!=='demo-world'||s.snapshot_seq!==0||s.policy_epoch!==null||s.wa_epoch!==null)return hold('FINANCE_SCOPE_HOLD');
 if(!record(c.authority)||!record(s.authority)||[c.authority,s.authority].some(a=>a.code_effective!==false||a.repo_effective!==false||a.dev_effective!==false||a.real_test!=='NOT_RUN')||s.authority.security_acceptance!=='HOLD'||s.authority.production!=='NOT_AUTHORIZED')return hold('FINANCE_AUTHORITY_HOLD');
 if(!Array.isArray(c.limitations)||!c.limitations.includes('No verified financial results')||!Array.isArray(s.metrics))return hold('FINANCE_SOURCE_HOLD');
 const revenue=s.metrics.filter(x=>record(x)&&x.metric_id==='revenue');
 if(revenue.length!==1||revenue[0].value!==null)return hold('FINANCE_REVENUE_HOLD');
 if(!record(c.sections))return hold('FINANCE_CATALOG_HOLD');
 const saas=rows(c.sections['SaaS ve Finans'],[
  ['Tenant / Company','ORG-A → genişlemeye açık','Gerçek müşteri yok'],['Abonelik ve kota','Paket ve kullanım tasarımı','Etkin değil'],['Gelir','Muhasebeleştirilmiş gelir, TRY','—'],['Tahsilat','Ayrı KPI','—']]);
 const goals=rows(c.sections['Hedefler'],[
  ['Kasım 2026','1.000.000 TRY · tarihsel stratejik hedef','Gerçekleşen: bilinmiyor'],['Nisan 2027','10.000.000 TRY · tarihsel stratejik hedef','Gerçekleşen: bilinmiyor'],['Tahsilat','Gelirden ayrı gösterilir','—']]);
 if(!saas||!goals)return hold('FINANCE_CATALOG_HOLD');
 return {ok:true,metrics:fields.map(m=>({...m})),saas,goals};
}
export function financeMetricText(_value:unknown):string{ return '—'; }
