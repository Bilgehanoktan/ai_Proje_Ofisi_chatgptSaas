export type OutboxProjection = {
 phase:'LOCAL_HOLD'|'CLAIMED'|'UNKNOWN_HOLD'|'READBACK_HOLD';
 generation:number|null;
 readback_recorded:boolean;
};
const keys=['schema_version','mode','tenant','company','phase','generation','readback_recorded','admission','dispatch_allowed','retry_allowed','reconciled','provider_called','release_ready'];
export function parseOutboxProjection(x:unknown):OutboxProjection|null{
 if(!x||typeof x!=='object'||Array.isArray(x))return null;
 const v=x as Record<string,unknown>;
 if(Object.keys(v).length!==keys.length||!keys.every(k=>Object.hasOwn(v,k)))return null;
 if(v.schema_version!=='outbox.review.projection.v1-D0'||v.mode!=='D0_OUTBOX_REVIEW_0184'||v.tenant!=='synthetic-tenant'||v.company!=='synthetic-company'||v.admission!=='DENY'||['dispatch_allowed','retry_allowed','reconciled','provider_called','release_ready'].some(k=>v[k]!==false))return null;
 const p=v.phase,g=v.generation;
 if(p!=='LOCAL_HOLD'&&p!=='CLAIMED'&&p!=='UNKNOWN_HOLD'&&p!=='READBACK_HOLD')return null;
 if(p==='LOCAL_HOLD'?g!==null:typeof g!=='number'||!Number.isSafeInteger(g)||g<1)return null;
 if(v.readback_recorded!==(p==='READBACK_HOLD'))return null;
 return {phase:p,generation:g as number|null,readback_recorded:p==='READBACK_HOLD'};
}
