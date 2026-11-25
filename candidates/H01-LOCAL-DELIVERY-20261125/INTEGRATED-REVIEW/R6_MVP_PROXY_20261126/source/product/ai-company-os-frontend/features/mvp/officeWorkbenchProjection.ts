export type OfficeRole = {role:string;station_id:string;observed:number;total:number};
export type OfficeWorkbench = {sample_event_count:number;roles:OfficeRole[]};
const fixed = {schema_version:'office.workbench.v1-D0',mode:'D0_OFFICE_WORKBENCH_0187',tenant:'synthetic-tenant',company:'synthetic-company',world_id:'demo-world',plan_digest:'6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9',layout_revision:'draft-hybrid-floor-1',iv:'HOLD',release:'HOLD',freshness:'HISTORICAL_SAMPLE',dispatch_allowed:false,provider_called:false,spend_allowed:false,release_ready:false,real_run_count:null,geometry_join:'HOLD'} as const;
const roleIds=['orchestrator','research','engineer','qa'];
const totals=[1,1,2,1];
function record(x:unknown): x is Record<string,unknown>{return !!x&&typeof x==='object'&&!Array.isArray(x);}
function exact(x:Record<string,unknown>,keys:string[]){return Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));}
export function parseOfficeWorkbench(x:unknown):OfficeWorkbench|null{
 if(!record(x)||!exact(x,[...Object.keys(fixed),'sample_event_count','roles'])||Object.entries(fixed).some(([k,v])=>x[k]!==v))return null;
 const n=x.sample_event_count;
 if(typeof n!=='number'||!Number.isInteger(n)||n<0||n>5||!Array.isArray(x.roles)||x.roles.length!==4)return null;
 const counts=[Number(n>=1),Number(n>=3),Number(n>=2)+Number(n>=4),Number(n>=5)];
 const roles:OfficeRole[]=[];
 for(let i=0;i<4;i++){
  const r=x.roles[i],role=roleIds[i],station_id='station-'+role;
  if(!record(r)||!exact(r,['role','station_id','observed','total'])||r.role!==role||r.station_id!==station_id||r.observed!==counts[i]||r.total!==totals[i])return null;
  roles.push({role,station_id,observed:counts[i],total:totals[i]});
 }
 return {sample_event_count:n,roles};
}
