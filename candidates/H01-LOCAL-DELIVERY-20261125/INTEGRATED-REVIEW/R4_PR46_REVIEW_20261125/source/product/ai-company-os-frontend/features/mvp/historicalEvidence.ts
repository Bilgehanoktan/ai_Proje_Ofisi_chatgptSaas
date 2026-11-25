/** One fixed historical sample at a time. No live KPI, placement or join. */
import {parseLifecycleProjection} from './lifecycleProjection';
import {parseLifecyclePrefix} from './lifecyclePrefix';
export type HistoricalEvidence = {
 profile:'TERMINAL_SAMPLE'|'PREFIX_SAMPLE';
 run:string; revision:string; recordedState:string;
 observed:number; slots:readonly {version:number;state:string|null;kind:string|null}[];
 lease:'CLOSED_IN_SAMPLE'|'CURRENT_FRESHNESS_UNKNOWN';
 budget:{kind:'RELEASED_IN_SAMPLE'|'OUTSTANDING_IN_SAMPLE';minor:number;currency:'USD'};
 freshness:'HISTORICAL_SAMPLE'; liveRunCount:null; placementAllowed:false;
 dispatchAllowed:false; independentAccepted:false; join:'HOLD';
};
export function historicalEvidence(raw:unknown):HistoricalEvidence|null{
 const terminal=parseLifecycleProjection(raw);
 const prefix=terminal?null:parseLifecyclePrefix(raw);
 const data=terminal??prefix;
 if(!data)return null;
 // Unobserved slots are deliberately blank: no predicted state or completion KPI.
 const slots=Array.from({length:5},(_,i)=>({version:i+1,
   state:data.timeline[i]?.state??null,kind:data.timeline[i]?.kind??null}));
 return {profile:terminal?'TERMINAL_SAMPLE':'PREFIX_SAMPLE',run:data.run_id,
   revision:data.plan_revision,recordedState:data.state,observed:data.timeline.length,slots,
   lease:terminal?'CLOSED_IN_SAMPLE':'CURRENT_FRESHNESS_UNKNOWN',
   budget:terminal?{kind:'RELEASED_IN_SAMPLE',minor:terminal.sample_released_minor,currency:terminal.currency}
      :{kind:'OUTSTANDING_IN_SAMPLE',minor:prefix!.sample_outstanding_minor,currency:prefix!.currency},
   freshness:'HISTORICAL_SAMPLE',liveRunCount:null,placementAllowed:false,
   dispatchAllowed:false,independentAccepted:false,join:'HOLD'};
}
