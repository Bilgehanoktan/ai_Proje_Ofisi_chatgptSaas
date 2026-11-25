/** Wall-only graphic accents, fixed icons, not real displays or clocks. */
const assets=[
 {id:'whiteboard',label:'Yazı tahtası',svg:'<rect x="4" y="7" width="56" height="37" rx="3" fill="#d9e8e6" stroke="#58758a" stroke-width="2"/><path d="M12 17h33m-33 8h41m-41 8h22" stroke="#53877e" stroke-width="3"/><path d="M8 46h48" stroke="#889cae" stroke-width="4"/>'},
 {id:'wall-shelf',label:'Duvar rafı',svg:'<path d="M4 42h56v5H4Z" fill="#8d6e53"/><rect x="10" y="19" width="9" height="23" rx="1" fill="#84a9c6"/><rect x="21" y="13" width="10" height="29" rx="1" fill="#a0bea4"/><path d="M36 20l9-3 8 25H43Z" fill="#d8bd89"/>'}
] as const;
export const wallDecorCatalog=assets.map(({id,label})=>({id,label}));
export function wallDecorUri(id:string){const a=assets.find(x=>x.id===id);return a?'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">${a.svg}</svg>`):null;}
export function wallDecorAt(id:string,x:number,y:number){
 const a=assets.find(v=>v.id===id);
 if(!a||!Number.isFinite(x)||!Number.isFinite(y)||x<0||x>900||y<0||y>510)return '';
 return `<g data-wall-decor="${a.id}" transform="translate(${x} ${y}) scale(.45)" aria-hidden="true">${a.svg}</g>`;
}
