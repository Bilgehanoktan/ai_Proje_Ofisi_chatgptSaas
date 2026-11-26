/** Original decorative SVG assets, no placement, collision, identity or runtime authority. */
const items=[
 {id:'desk',label:'Çalışma masası',category:'furniture',art:'<path d="M8 28 38 12 62 25 32 42Z" fill="#d1ad86"/><path d="M8 28v8l24 14v-8M32 42v8l30-17v-8" fill="#87664f"/><path d="M13 38v14m44-16v14m-25 0v10" stroke="#63778d" stroke-width="4"/>'},
 {id:'monitor',label:'Monitör',category:'furniture',art:'<rect x="16" y="10" width="40" height="30" rx="4" fill="#263a52"/><rect x="20" y="14" width="32" height="22" rx="2" fill="#85c9e0"/><path d="M36 40v12m-13 2h26" stroke="#94a8ba" stroke-width="4"/>'},
 {id:'chair',label:'Ergonomik koltuk',category:'furniture',art:'<rect x="19" y="8" width="34" height="29" rx="8" fill="#647f9e"/><rect x="15" y="34" width="42" height="14" rx="5" fill="#9badc2"/><path d="M36 48v12m-17 0h34" stroke="#64778b" stroke-width="4"/>'},
 {id:'plant',label:'Bitki',category:'furniture',art:'<path d="M23 43h26l-5 20H28Z" fill="#b67857"/><path d="M36 45V10m0 20Q8 12 16 34Q24 43 36 30m0-4Q64 7 57 30Q47 38 36 26" fill="#4fb98d" stroke="#296a56" stroke-width="2"/>'},
 {id:'meeting',label:'Toplantı masası',category:'furniture',art:'<ellipse cx="36" cy="32" rx="28" ry="16" fill="#c5a583" stroke="#88694e" stroke-width="2"/><path d="M17 44v13m38-13v13" stroke="#788b9d" stroke-width="4"/><rect x="29" y="25" width="14" height="9" rx="2" fill="#82b5d1"/>'},
 {id:'avatar',label:'Rezerv rol sprite',category:'sprite',art:'<circle cx="36" cy="19" r="12" fill="#aab9cd"/><path d="M18 56V43a18 18 0 0 1 36 0v13Z" fill="#7084a5"/><path d="M24 56v8m24-8v8" stroke="#9eb0c6" stroke-width="5"/>'}
] as const;
export const decorCatalog=items.map(({id,label,category})=>({id,label,category}));
export function decorFragment(id:string):string|null{return items.find(x=>x.id===id)?.art??null;}
export function decorUri(id:string):string|null{
 const asset=items.find(x=>x.id===id);return asset?'data:image/svg+xml;charset=utf-8,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 72">'+asset.art+'</svg>'):null;
}
