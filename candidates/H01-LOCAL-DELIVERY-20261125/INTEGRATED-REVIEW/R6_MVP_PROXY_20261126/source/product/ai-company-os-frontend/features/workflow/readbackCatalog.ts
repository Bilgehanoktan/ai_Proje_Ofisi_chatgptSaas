/** View-local endpoint inventory; never aggregates runtime observations. */
export const readbackLabels = Object.freeze({mvp:'MVP tanılama',admission:'Admission / rezervasyon',outbox:'Outbox inceleme','office-workbench':'Ofis iş istasyonu','task-budget':'Görev / bütçe',lifecycle:'Terminal yaşam döngüsü','lifecycle-prefix':'Lease geçmişi'} as const);
export type ReadbackKey=keyof typeof readbackLabels;
const all:readonly ReadbackKey[]=['mvp','admission','outbox','office-workbench','task-budget','lifecycle','lifecycle-prefix'];
const byView:Record<string,readonly ReadbackKey[]>={'Genel Bakış':all,'Sanal Ofis':['office-workbench','lifecycle','lifecycle-prefix'],'AI Çalışanlar':['mvp','lifecycle-prefix'],'İş ve Denetim':['task-budget','lifecycle','lifecycle-prefix'],'SaaS ve Finans':['admission','task-budget','lifecycle'],'Güvenlik':['admission','outbox','lifecycle-prefix'],'Raporlar':['outbox','lifecycle'],'Beceriler':['mvp','lifecycle-prefix'],'Olaylar':['outbox','lifecycle','lifecycle-prefix']};
const groups={runtime:['mvp','office-workbench','lifecycle','lifecycle-prefix'],finance:['admission','task-budget','lifecycle'],security:['admission','outbox','lifecycle','lifecycle-prefix']} as const;
export type ReadbackGroup='all'|keyof typeof groups;
export const readbackGroups:readonly {id:ReadbackGroup;label:string}[]=[{id:'all',label:'Tümü'},{id:'runtime',label:'Runtime'},{id:'finance',label:'Finans'},{id:'security',label:'Güvenlik'}];
const normalize=(s:string)=>s.normalize('NFKC').toLocaleLowerCase('tr').trim();
export function filterReadbackCards(view:string,query:string,group:ReadbackGroup='all'):{total:number;ids:ReadbackKey[]}|null{
 if(!Object.hasOwn(byView,view)||(group!=='all'&&!Object.hasOwn(groups,group)))return null;
 const ids=byView[view],q=normalize(query.slice(0,120));
 const allowed:readonly string[]=group==='all'?all:groups[group];
 return {total:ids.length,ids:ids.filter(id=>allowed.includes(id)&&normalize(id+' '+readbackLabels[id]).includes(q))};
}
