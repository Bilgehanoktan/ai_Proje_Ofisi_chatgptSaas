/** D0 source inventory only; not an economic event, grant, or independent receipt. */
export type Domain='finance'|'security';
export type Source={id:string;domain:Domain;title:string;path:string;blob:string;symbol:string;boundary:'HOLD'|'DENY'|'INCONCLUSIVE'|'UNVERIFIED';requires:string;limit:string};
const root='product/ai-company-os-backend/app/';
export const sources:readonly Source[]=[
 {id:'reservation',domain:'finance',title:'Bütçe ve rezervasyon',path:root+'engines/budget_engine/reservation_review.py',blob:'b1d7ee6a08604b7726e1b0ec98d00723e7d75961',symbol:'inspect_reservation',boundary:'HOLD',requires:'Kapsam, bütçe revizyonu, para birimi, idempotency, policy ve witness epoch.',limit:'Tanısal kapasite, rezervasyon veya harcama yetkisi değildir.'},
 {id:'admission',domain:'finance',title:'Admission ve bütçe bağı',path:root+'core/transaction/admission_bundle.py',blob:'276b4330afdce7cde98f92f8051c019eb7345fe1',symbol:'inspect_admission_bundle',boundary:'HOLD',requires:'Intent, head, admission, lease, budget ve witness referansları.',limit:'Yapısal eşleşme commit, dispatch veya harcama oluşturmaz.'},
 {id:'projection',domain:'finance',title:'Maliyet, gelir ve tahsilat',path:root+'observability/finance_projection.py',blob:'39a0b6fc99b272549fb9d5ec2e1aaa8018bf08fc',symbol:'project_finance',boundary:'UNVERIFIED',requires:'Tanısal kapasite ve yetkili finansal kanıtın ayrı tutulması.',limit:'Yetkili bakiye, gerçek maliyet, gelir ve tahsilat bilinmiyor.'},
 {id:'gateway',domain:'security',title:'Policy / PEP',path:root+'core/policy/gateway_review.py',blob:'d2f5b2fe04ce160f416bcae2e748dfeae730f68e',symbol:'inspect_gateway',boundary:'DENY',requires:'Effect scope, grant, lease, fence ve witness referansı.',limit:'Tanısal eşleşme tool veya sağlayıcı çağrısına izin vermez.'},
 {id:'witness',domain:'security',title:'W-A witness',path:root+'core/policy/witness_review.py',blob:'da6414affbf9207b10b65fbb5aa327a021dc05a6',symbol:'inspect_witness',boundary:'HOLD',requires:'Bağımsız kök, kapsam, epoch, sequence, digest ve freshness.',limit:'Referans eşleşmesi bağımsız kök sahipliği değildir.'},
 {id:'iv',domain:'security',title:'Independent Verifier',path:root+'core/policy/iv_review.py',blob:'8dc0bec51401650ca59a7dc8a1b490643f64b4fb',symbol:'inspect_iv',boundary:'INCONCLUSIVE',requires:'Artifact/readback CAS ve ayrı QA, IV, release trust plane.',limit:'Yapısal eşleşme bağımsız imza veya release değildir.'},
 {id:'receipt',domain:'security',title:'Makbuz ve byte kanıtı',path:root+'core/policy/receipt_review.py',blob:'3f335a148519f3e79862745187f89cd2e5105747',symbol:'inspect_receipt',boundary:'INCONCLUSIVE',requires:'Makbuz referansı, signer, key, geçerlilik, tombstone ve byte hash.',limit:'Gerçek imza ve güven kökü sahipliği kanıtlanmaz.'},
 {id:'outbox',domain:'security',title:'Outbox / UNKNOWN',path:root+'core/event_store/outbox_review.py',blob:'40bb09dfd9023739c4d0ed730f745d6e8688140e',symbol:'inspect_outbox',boundary:'HOLD',requires:'Effect key, request digest, commit, claim, lease ve mutabakat referansı.',limit:'Belirsiz sonuç karantinada kalır; otomatik retry veya gönderim yok.'},
];
const norm=(s:string)=>s.trim().toLocaleLowerCase('tr-TR');
export function filterSources(domain:string,query:unknown):readonly Source[]{
 if((domain!=='finance'&&domain!=='security')||typeof query!=='string'||query.length>200)return [];
 const words=norm(query).split(/\s+/).filter(Boolean);
 return sources.filter(s=>s.domain===domain&&words.every(w=>norm([s.title,s.path,s.symbol,s.requires,s.limit,s.boundary].join(' ')).includes(w)));
}
export function selectSource(domain:string,query:unknown,id:string):Source|null{return filterSources(domain,query).find(s=>s.id===id)??null;}
export function sourceBoundary(){return {actualBudget:null,actualCost:null,actualRevenue:null,actualCollection:null,actualReceipts:null,spendAllowed:false,grantAllowed:false,retryAllowed:false,releaseAllowed:false} as const;}
