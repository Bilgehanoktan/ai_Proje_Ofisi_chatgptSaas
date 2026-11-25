/** Fixed decorative overlays on reserved desks, not floor occupancy or agent placement. */
import {decorFragment} from './decorCatalog';
export type DeskDecor={asset:'plant'|'monitor';dx:number;dy:number;scale:number};
const overlays:readonly DeskDecor[]=Object.freeze([Object.freeze({asset:'plant',dx:-27,dy:-34,scale:.24}),Object.freeze({asset:'monitor',dx:-5,dy:-46,scale:.34})]);
export function reservedDeskDecor(x:number,y:number,instance:unknown):string{
 if(instance!==null||!Number.isFinite(x)||!Number.isFinite(y)||x<0||x>900||y<0||y>510)return '';
 return `<g data-decor="reserved-desk" aria-hidden="true">${overlays.map(o=>`<g data-asset="${o.asset}" transform="translate(${x+o.dx} ${y+o.dy}) scale(${o.scale})">${decorFragment(o.asset)??''}</g>`).join('')}</g>`;
}
