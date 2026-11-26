/** Read-only view model for CEO and Office; does not join independent samples. */
import {historicalEvidence} from './historicalEvidence';
import {parseLifecycleProjection} from './lifecycleProjection';
import {parseLifecyclePrefix} from './lifecyclePrefix';
export function historicalPresentation(raw:unknown){
 const terminal=parseLifecycleProjection(raw);
 const source=terminal??parseLifecyclePrefix(raw);
 if(!source)return null;
 const evidence=historicalEvidence(source);
 if(!evidence)return null;
 const scope=`${source.tenant} / ${source.company} / ${source.environment}`;
 return {evidence,scope,task:source.task_id,revision:source.plan_revision,
   sampleIdentity:`${source.mode} / ${source.run_id} / v${source.head_version}`,
   recordLabel:`${evidence.observed}/5 kayıt adımı`,
   budgetLabel:evidence.budget.kind==='RELEASED_IN_SAMPLE'?'Örnekte serbest bırakılan rezervasyon':'Örnekte açık rezervasyon',
   budgetValue:`${evidence.budget.minor} minor ${evidence.budget.currency}`,
   leaseLabel:evidence.lease==='CLOSED_IN_SAMPLE'?'Örnek lease kapandı':'Güncel lease bilinmiyor',
   liveLabel:'CANLI VERİ DEĞİL',placementLabel:'HOLD',runCountLabel:'Bilinmiyor',
   independentLabel:'HOLD',releaseLabel:'HOLD'} as const;
}
