/** Presentation-only menu model: never adds a route or grants authority. */
export type NavItem=readonly [name:string,icon:string];
export type NavGroup={label:string;items:NavItem[]};
const groups:Readonly<Record<string,string>>={
 'Genel Bakış':'Komuta Merkezi','Sanal Ofis':'Komuta Merkezi','AI Çalışanlar':'Komuta Merkezi',
 'İş ve Denetim':'Operasyon','Beceriler':'Operasyon','WorkType':'Operasyon','Hedefler':'Operasyon',
 'Karar Kutusu':'Yönetim ve Güvence','Güvenlik':'Yönetim ve Güvence','SaaS ve Finans':'Yönetim ve Güvence',
 'Raporlar':'İzleme ve Ayarlar','Tercihler':'İzleme ve Ayarlar','Olaylar':'İzleme ve Ayarlar'
};
const aliases:Readonly<Record<string,string>>={
 'Genel Bakış':'dashboard ceo kontrol paneli overview','Sanal Ofis':'office kat oda istasyon harita',
 'AI Çalışanlar':'ajan agent rol ekip personel','İş ve Denetim':'workflow studio dag görev task proje orchestrator audit',
 'Beceriler':'skill araç tool bilgi hafıza','WorkType':'iş türü research excel obligation verifier',
 'Hedefler':'goal hedef kpi strateji','Karar Kutusu':'decision onay karar approval',
 'Güvenlik':'security iam grant yetki pep risk','SaaS ve Finans':'finance billing maliyet gelir tahsilat kota',
 'Raporlar':'report kanıt rapor evidence','Tercihler':'settings tema ayar theme','Olaylar':'event log stream olay kayıt'
};
export function normalizeNav(value:string):string{
 return value.toLocaleLowerCase('tr-TR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ı/g,'i').trim();
}
const own=(record:Readonly<Record<string,string>>,key:string)=>Object.prototype.hasOwnProperty.call(record,key)?record[key]:undefined;
export function groupNavigation(items:readonly NavItem[],query:string):NavGroup[]{
 const terms=normalizeNav(query).split(/\s+/).filter(Boolean);
 const grouped=new Map<string,NavItem[]>();
 for(const item of items){
  const name=item[0],group=own(groups,name)??'Diğer';
  const haystack=normalizeNav([name,own(aliases,name)??'',group].join(' '));
  if(!terms.every(term=>haystack.includes(term)))continue;
  const bucket=grouped.get(group);if(bucket)bucket.push(item);else grouped.set(group,[item]);
 }
 return [...grouped].map(([label,items])=>({label,items}));
}
