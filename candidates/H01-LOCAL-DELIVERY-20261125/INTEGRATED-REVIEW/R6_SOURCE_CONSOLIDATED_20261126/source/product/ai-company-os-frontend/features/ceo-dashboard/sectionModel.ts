/** View-local presentation selection only; no runtime state or authority. */
export const ceoSections=[
 {id:'summary',label:'Yönetim özeti',description:'Kaynak, göstergeler ve operasyon örneği'},
 {id:'operations',label:'Operasyonlar',description:'Ofis, roller ve görev gözlemleri'},
 {id:'evidence',label:'Teknik kanıtlar',description:'Yaşam döngüsü, güvenlik ve veri okumaları'}
] as const;
export const workSections=[
 {id:'projects',label:'Project Studio',description:'Referans plan, görevler ve bağımlılıklar'},
 {id:'workflow',label:'Workflow Studio',description:'Yerel bağlantı taslağı · kayıt yok'},
 {id:'audit',label:'İş denetimi',description:'Görev örnekleri ve teknik kanıtlar'}
] as const;
export type CeoSection=typeof ceoSections[number]['id'];
export type WorkSection=typeof workSections[number]['id'];
export type SectionOption<T extends string>={readonly id:T;readonly label:string;readonly description:string};
export function isSection<T extends string>(options:readonly SectionOption<T>[],id:unknown):id is T{
 return typeof id==='string'&&options.some(option=>option.id===id);
}
