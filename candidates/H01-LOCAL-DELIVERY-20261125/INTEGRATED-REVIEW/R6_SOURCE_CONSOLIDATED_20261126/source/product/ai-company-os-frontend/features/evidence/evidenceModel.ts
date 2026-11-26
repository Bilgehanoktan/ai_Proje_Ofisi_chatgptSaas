/** Presentation only. Input is the output of the existing typed D0 reader, never proof of authority. */
export type RoleRow={id:string;name:string;department:string;description:string};
const norm=(s:string)=>s.toLocaleLowerCase('tr-TR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ı/g,'i');
export function roleDirectory<T extends RoleRow>(roles:readonly T[],query:string,department:string):T[]{
 const words=norm(query).trim().split(/\s+/).filter(Boolean);
 return roles.filter(r=>(!department||r.department===department)&&words.every(w=>norm([r.id,r.name,r.department,r.description].join(' ')).includes(w))).slice().sort((a,b)=>a.name.localeCompare(b.name,'tr'));
}
export function sortProjectRows<T extends {wave:number;task:{id:string;label:string;role:string}}>(rows:readonly T[],by:'wave'|'label'|'role',descending=false):T[]{
 return [...rows].sort((a,b)=>{const diff=by==='wave'?a.wave-b.wave:by==='label'?a.task.label.localeCompare(b.task.label,'tr'):a.task.role.localeCompare(b.task.role,'tr');return (descending?-diff:diff)||a.task.id.localeCompare(b.task.id,'en');});
}
export type SampleBar={label:string;value:number};
export function admissionBars(key:string,phase:string,data:unknown):SampleBar[]{
 if(key!=='admission'||phase!=='historical'||!data||typeof data!=='object'||Array.isArray(data))return [];
 const d=data as Record<string,unknown>,fields=[['sample_reserved_minor','Rezervasyon'],['sample_observed_minor','Gözlem'],['sample_remaining_minor','Kalan']] as const;
 if(!fields.every(([k])=>Object.hasOwn(d,k)&&typeof d[k]==='number'&&Number.isSafeInteger(d[k])&&(d[k] as number)>=0))return [];
 return fields.map(([k,label])=>({label,value:d[k] as number}));
}
export function evidenceNotice(phase:string):string{
 switch(phase){case 'historical':return 'Tarihsel örnek okundu; güncel yetki kanıtlanmadı.';case 'hold':return 'Okuma reddedildi; önceki kayıt gösterilmez.';case 'loading':return 'Okuma sürüyor; yeni kayıt bekleniyor.';default:return 'Henüz okunmadı; veri bilinmiyor.';}
}
