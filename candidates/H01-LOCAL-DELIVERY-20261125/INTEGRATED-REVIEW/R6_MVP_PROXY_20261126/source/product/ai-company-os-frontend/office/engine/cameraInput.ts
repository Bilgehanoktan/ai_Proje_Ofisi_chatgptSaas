// D0 Phaser input math. Camera coordinates are presentation-only, not agent placement.
export type InputView = {zoom:number;x:number;y:number};
const clamp = (n:number,lo:number,hi:number) => Math.max(lo,Math.min(hi,n));
const finite = (n:number,fallback=0) => Number.isFinite(n)?n:fallback;
export function inputBounds(v:InputView):InputView {
  const zoom=clamp(finite(v.zoom,1),.75,1.45);
  const dx=Math.max(0,(900-900/zoom)/2),dy=Math.max(0,(510-510/zoom)/2);
  return {zoom,x:clamp(finite(v.x),-dx,dx),y:clamp(finite(v.y),-dy,dy)};
}
export function inputPan(v:InputView,dx:number,dy:number):InputView {
  const b=inputBounds(v);
  return inputBounds({zoom:b.zoom,x:b.x-finite(dx)/b.zoom,y:b.y-finite(dy)/b.zoom});
}
export function inputZoom(v:InputView,x:number,y:number,delta:number):InputView {
  const b=inputBounds(v);
  const z=clamp(b.zoom*Math.exp(-clamp(finite(delta),-600,600)*.0015),.75,1.45);
  const sx=clamp(finite(x,450),0,900)-450,sy=clamp(finite(y,255),0,510)-255;
  return inputBounds({zoom:z,x:b.x+sx*(1/b.zoom-1/z),y:b.y+sy*(1/b.zoom-1/z)});
}
export function inputDragged(x0:number,y0:number,x:number,y:number):boolean {
  return [x0,y0,x,y].every(Number.isFinite)&&Math.hypot(x-x0,y-y0)>5;
}
