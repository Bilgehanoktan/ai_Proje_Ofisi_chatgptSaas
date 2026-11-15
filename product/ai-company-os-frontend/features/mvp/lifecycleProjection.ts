/** Exact fixed historical sample, never a canonical run or authority. */
const sample = {
  "schema_version": "lifecycle.projection.v1-D0",
  "mode": "D0_LIFECYCLE_0196L_TERMINAL_FIXTURE",
  "tenant": "synthetic-tenant",
  "company": "synthetic-company",
  "environment": "A0_SAMPLE_ONLY",
  "plan_revision": "sha256:c75ec1070786538f38bdccdcf6a75de62a9e02e9bcb7e4a4bb9df5f7e96638a0",
  "task_id": "a",
  "run_id": "demo-a",
  "head_version": 5,
  "attempt": 0,
  "state": "FAILED",
  "timeline": [
    {
      "version": 1,
      "kind": "D0_RUN_ADMISSION",
      "state": "ADMITTED"
    },
    {
      "version": 2,
      "kind": "D0_RUN_TRANSITION",
      "state": "RUNNING"
    },
    {
      "version": 3,
      "kind": "D0_LEASE_RENEWAL",
      "state": "RUNNING"
    },
    {
      "version": 4,
      "kind": "D0_RUN_TRANSITION",
      "state": "VERIFYING"
    },
    {
      "version": 5,
      "kind": "D0_RUN_FAILURE",
      "state": "FAILED"
    }
  ],
  "lease_version": 2,
  "heartbeat_revision": 1,
  "lease_active": false,
  "sample_reserved_minor": 20,
  "sample_released_minor": 20,
  "sample_recognized_minor": 0,
  "sample_budget_revision": 3,
  "currency": "USD",
  "freshness": "HISTORICAL_SAMPLE",
  "causality": "EXACT_FIXED_SAMPLE_ONLY",
  "geometry_join": "HOLD",
  "independent_acceptance": "HOLD",
  "decision": "HOLD",
  "dispatch_allowed": false,
  "provider_called": false,
  "spend_allowed": false,
  "release_ready": false,
  "authoritative": false,
  "real_run_count": null
} as const;
export type LifecycleProjection=typeof sample;
function freeze<T>(value:T):T{
 if(value&&typeof value==='object'){
  for(const child of Object.values(value))freeze(child);
  Object.freeze(value);
 }
 return value;
}
export const expectedLifecycle=freeze(sample);
function same(a:unknown,b:unknown):boolean{
 if(a===b)return true;
 if(Array.isArray(b))return Array.isArray(a)&&a.length===b.length&&b.every((v,i)=>same(a[i],v));
 if(b!==null&&typeof b==='object'){
  if(a===null||typeof a!=='object'||Array.isArray(a))return false;
  const x=a as Record<string,unknown>,y=b as Record<string,unknown>;
  return Object.keys(x).length===Object.keys(y).length&&Object.keys(y).every(k=>Object.hasOwn(x,k)&&same(x[k],y[k]));
 }
 return false;
}
export function parseLifecycleProjection(raw:unknown):LifecycleProjection|null{
 return same(raw,expectedLifecycle)?structuredClone(expectedLifecycle):null;
}
