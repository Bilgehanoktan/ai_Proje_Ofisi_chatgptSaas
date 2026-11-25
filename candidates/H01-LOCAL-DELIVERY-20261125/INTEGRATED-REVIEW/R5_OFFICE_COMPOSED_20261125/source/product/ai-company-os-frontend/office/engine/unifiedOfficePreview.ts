/** U1 isolated presentation fixture. No real snapshot input, command or identity join. */
import {createVisualIdentityRegistry} from './premiumActorIdentity';
import {createFloorTraffic,portalLandingCandidates,type FloorSeed} from './premiumFloorTraffic';
import {createHybridLayout} from './premiumHybridLayout';
import {createFloorRenderBridge} from './premiumFloorRender';
import {renderFloorSvg} from './premiumFloorSvg';
export function createUnifiedOfficePreview(){
 const floors:FloorSeed[]=[1,2,3].map(i=>({floorId:'d0-f'+i,scale:i===2?'expanded':'reference',lifecycle:i===3?'DRAFT':'ACTIVE',actors:i===3?[]:createVisualIdentityRegistry().actors.map(a=>({visualActorId:a.visualActorId+'-f'+i,roleTemplateId:a.roleTemplateId,stationId:a.stationId}))}));
 const world=createFloorTraffic({mode:'D0_SYNTHETIC_WORLD',revision:'d0-unified-preview-r1',floors,portals:[{id:'d0-preview-lift',capacity:1,stops:floors.map(f=>({floorId:f.floorId,cell:portalLandingCandidates(createHybridLayout(f.scale))[0]}))}]});
 const bridge=createFloorRenderBridge(world);const initial=bridge.frame();
 const views=initial.navigation.map(n=>{const f=bridge.selectFloor(n.floorId);return Object.freeze({floorId:f.selectedFloorId,lifecycle:f.lifecycle,visibleActors:f.actors.length,rooms:f.rooms.length,stations:f.stations.length,svgUri:'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(renderFloorSvg(f)),portalPhase:f.portals[0].phase,geometryJoin:f.geometryJoin,authoritative:f.authoritative});});
 return Object.freeze({mode:'D0_DECORATIVE_PREVIEW' as const,join:'JOIN_HOLD' as const,authoritative:false as const,views:Object.freeze(views),initialFloorId:initial.selectedFloorId});
}
