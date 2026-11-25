/** Visual-only desk accents. No placement, collision or instance authority. */
const assets=[
 {id:'keyboard',label:'Klavye',svg:'<path d="M4 15h46l10 23H14Z" fill="#aab9c9" stroke="#25384a"/><path d="M13 22h33m-30 6h33m-27 6h26" stroke="#53667a" stroke-width="2"/>'},
 {id:'notebook',label:'Not defteri',svg:'<path d="M13 7l38 11-6 38L7 45Z" fill="#e9c88f" stroke="#735a3b"/><path d="M19 16l24 7m-26 1l24 7m-26 1l19 6" stroke="#9d8055" stroke-width="2"/>'}
] as const;
export const deskAccessoryCatalog=assets.map(({id,label})=>({id,label}));
export function deskAccessoryUri(id:string){const asset=assets.find(a=>a.id===id);return asset?'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">${asset.svg}</svg>`):null;}
export function reservedDeskAccessories(x:number,y:number,instance:unknown){
 if(instance!==null||!Number.isFinite(x)||!Number.isFinite(y)||x<0||x>900||y<0||y>510)return '';
 return assets.map((a,i)=>`<g data-accessory="${a.id}" transform="translate(${x+(i?6:-15)} ${y+(i?-22:-24)}) scale(.28)">${a.svg}</g>`).join('');
}
