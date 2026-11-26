/** D0 presentation overlay only. The underlying fixture stays pinned. */
export type CatalogRow = {title:string;description:string;status:string};
export type CatalogSections = Readonly<Record<string,readonly CatalogRow[]>>;
const allowed:Readonly<Record<string,CatalogRow>>={
 'Karar Kutusu':{title:'Yetki',description:'CEO-0174 kullanıcı çalışma kapsamı ayrı; normatif CODE=C · REPO=C · DEV=B',status:'Bağımsız kabul HOLD'},
 'Güvenlik':{title:'Başlangıç yetkileri',description:'Bağımsız normatif CODE / REPO / DEV',status:'0/3 etkin · HOLD'},
 'Tercihler':{title:'Görünüm',description:'Açık/koyu tema · sistem fontu',status:'Yerel arayüz · EDS adayı'},
};
export function presentCatalogRows(view:string,source:CatalogSections,display:CatalogSections):CatalogRow[]{
 const rows=Object.hasOwn(source,view)?source[view]:[];
 const expected=Object.hasOwn(allowed,view)?allowed[view]:undefined;
 if(!expected)return rows.map(row=>({...row}));
 const candidates=Object.hasOwn(display,view)?display[view].filter(row=>row.title===expected.title):[];
 return rows.map(row=>{
  if(row.title!==expected.title)return {...row};
  const overlay=candidates[0];
  if(candidates.length!==1||overlay.description!==expected.description||overlay.status!==expected.status)return {...row,description:'Sunum kaydı eksik veya çelişkili',status:'UNKNOWN · HOLD'};
  return {...row,description:expected.description,status:expected.status};
 });
}
