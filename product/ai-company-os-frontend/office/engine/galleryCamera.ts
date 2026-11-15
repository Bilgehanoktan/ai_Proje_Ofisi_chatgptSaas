/** Local artwork camera only; no placement, routing or runtime state. */
export type GalleryCamera={zoom:number;x:number;y:number};
export const ART_WIDTH=900,ART_HEIGHT=510,MIN_ZOOM=1,MAX_ZOOM=3;
export const HOME:Readonly<GalleryCamera>={zoom:1,x:450,y:255};
const finite=(n:number,fallback:number)=>Number.isFinite(n)?n:fallback;
const clamp=(n:number,lo:number,hi:number)=>Math.min(hi,Math.max(lo,n));
export function constrainCamera(camera:GalleryCamera):GalleryCamera{
 const zoom=clamp(finite(camera.zoom,1),MIN_ZOOM,MAX_ZOOM),hx=ART_WIDTH/(2*zoom),hy=ART_HEIGHT/(2*zoom);
 return {zoom,x:clamp(finite(camera.x,HOME.x),hx,ART_WIDTH-hx),y:clamp(finite(camera.y,HOME.y),hy,ART_HEIGHT-hy)};
}
export function zoomCamera(camera:GalleryCamera,zoom:number):GalleryCamera{return constrainCamera({...camera,zoom});}
export function panCamera(camera:GalleryCamera,dx:number,dy:number):GalleryCamera{
 const c=constrainCamera(camera);return constrainCamera({...c,x:c.x+finite(dx,0),y:c.y+finite(dy,0)});
}
export function dragCamera(camera:GalleryCamera,dx:number,dy:number,viewportWidth:number,viewportHeight:number):GalleryCamera{
 const c=constrainCamera(camera);if(!Number.isFinite(viewportWidth)||viewportWidth<=0||!Number.isFinite(viewportHeight)||viewportHeight<=0)return c;
 return panCamera(c,-finite(dx,0)*ART_WIDTH/(viewportWidth*c.zoom),-finite(dy,0)*ART_HEIGHT/(viewportHeight*c.zoom));
}
export function focusCamera(x:number,y:number):GalleryCamera{return constrainCamera({zoom:2.5,x,y});}
export function imagePlacement(camera:GalleryCamera){
 const c=constrainCamera(camera);return {width:c.zoom*100,left:50-c.x*c.zoom/ART_WIDTH*100,top:50-c.y*c.zoom/ART_HEIGHT*100};
}
