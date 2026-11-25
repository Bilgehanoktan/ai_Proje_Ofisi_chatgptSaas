/** Static room-only signage, never a collision tile, clock or live status. */
const assets=[
 {id:'room-sign',label:'Oda yönlendirme levhası',svg:'<rect x="4" y="16" width="56" height="28" rx="4" fill="#253e54" stroke="#a9c1d0" stroke-width="2"/><path d="M13 30h24m-7-7 7 7-7 7" fill="none" stroke="#c8e5ee" stroke-width="3"/><circle cx="48" cy="30" r="4" fill="#d8c7a0"/>'},
 {id:'notice-board',label:'Duyuru panosu',svg:'<rect x="5" y="6" width="54" height="51" rx="3" fill="#9e8165" stroke="#5c5145" stroke-width="2"/><rect x="11" y="12" width="19" height="29" fill="#e4d9bd"/><rect x="34" y="18" width="17" height="31" fill="#c1d6d1"/><circle cx="20" cy="16" r="2" fill="#a96557"/><circle cx="42" cy="22" r="2" fill="#5b7a9b"/>'}
] as const;
export const roomAccentCatalog=assets.map(({id,label})=>({id,label}));
export function roomAccentUri(id:string){const a=assets.find(v=>v.id===id);return a?'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">${a.svg}</svg>`):null;}
export function roomAccentAt(room:string,x:number,y:number){
 if(!Number.isFinite(x)||!Number.isFinite(y)||x<0||x>900||y<0||y>510)return '';
 const id=room==='management'||room==='quality'?'room-sign':room==='research'||room==='engineering'?'notice-board':null;
 const a=assets.find(v=>v.id===id);return a?`<g data-room-accent="${a.id}" transform="translate(${x} ${y}) scale(.32)" aria-hidden="true">${a.svg}</g>`:'';
}
