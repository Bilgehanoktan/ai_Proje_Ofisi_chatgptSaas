/** Decorative identities only: no agent, grant, runtime state or topology. */
export type RoleVisual=Readonly<{initials:string;accent:string;department:string;motif:string;glyph:string}>;
const profiles:Readonly<Record<string,RoleVisual>>=Object.freeze({
 orchestrator:Object.freeze({initials:'OR',accent:'#75d9d0',department:'Yönetim',motif:'Komuta ve koordinasyon',glyph:'<path d="M20 26 32 18 44 26M24 30v9m8-9v9m8-9v9M19 42h26"/>'}),
 research:Object.freeze({initials:'RE',accent:'#85b5ff',department:'Araştırma',motif:'Kaynak ve inceleme',glyph:'<circle cx="29" cy="28" r="8"/><path d="m35 34 9 9"/>'}),
 engineer:Object.freeze({initials:'EN',accent:'#c3a7f9',department:'Mühendislik',motif:'Tasarım ve üretim',glyph:'<path d="m25 23-9 9 9 9m14-18 9 9-9 9m-5-21-5 24"/>'}),
 qa:Object.freeze({initials:'QA',accent:'#f0c780',department:'Kalite',motif:'Kontrol ve kalite',glyph:'<path d="M32 18 44 23v9c0 8-12 15-12 15S20 40 20 32v-9Z M26 32l4 4 8-9"/>'})
});
const rooms:Readonly<Record<string,string>>=Object.freeze({management:'orchestrator',research:'research',engineering:'engineer',quality:'qa'});
const owns=(r:object,k:string)=>Object.prototype.hasOwnProperty.call(r,k);
export function roleVisual(id:string):RoleVisual|null{return owns(profiles,id)?profiles[id]:null;}
export function roomVisual(id:string):RoleVisual|null{return owns(rooms,id)?roleVisual(rooms[id]):null;}
const neutral:RoleVisual=Object.freeze({initials:'?',accent:'#a9b5c5',department:'Bilinmeyen',motif:'Görsel kimlik yok',glyph:'<path d="M32 22v12m0 7v1"/>'});
export function rolePortraitSvg(id:string):string{
 const p=roleVisual(id)??neutral;
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="#142338"/><path d="M7 50h50M7 14h50" stroke="${p.accent}" stroke-opacity=".18"/><path d="M11 58v-7c0-8 10-12 21-12s21 4 21 12v7" fill="${p.accent}" fill-opacity=".18" stroke="${p.accent}" stroke-width="1.5"/><rect x="13" y="12" width="38" height="36" rx="11" fill="#0b1424" stroke="${p.accent}" stroke-width="2"/><path d="M32 12V6m-3 0h6M9 25v10m46-10v10" stroke="${p.accent}" stroke-width="2" stroke-linecap="round"/><g fill="none" stroke="${p.accent}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">${p.glyph}</g><circle cx="32" cy="54" r="2" fill="${p.accent}"/></svg>`;
}
export function rolePortraitUri(id:string):string{return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(rolePortraitSvg(id));}
