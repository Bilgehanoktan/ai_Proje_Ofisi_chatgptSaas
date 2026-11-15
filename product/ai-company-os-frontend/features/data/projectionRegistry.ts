/** Endpoint and parser pair are fixed, not caller-selected. */
import {parseMvpDiagnostics} from '../mvp/mvpDiagnostics';
import {parseAdmissionProjection} from '../mvp/admissionProjection';
import {parseOutboxProjection} from '../mvp/outboxProjection';
import {parseOfficeWorkbench} from '../mvp/officeWorkbenchProjection';
import {parseTaskBudgetProjection} from '../mvp/taskBudgetProjection';
import {parseLifecycleProjection} from '../mvp/lifecycleProjection';
import {createProjectionReader,type Parser,type ProjectionKey,type ReadState} from './projectionRead';
export const projectionParsers=Object.freeze({mvp:parseMvpDiagnostics,admission:parseAdmissionProjection,outbox:parseOutboxProjection,'office-workbench':parseOfficeWorkbench,'task-budget':parseTaskBudgetProjection,lifecycle:parseLifecycleProjection} satisfies Record<ProjectionKey,Parser<unknown>>);
export type ProjectionValue<K extends ProjectionKey>=NonNullable<ReturnType<(typeof projectionParsers)[K]>>;
export function registeredReader<K extends ProjectionKey>(key:K,publish:(state:ReadState<ProjectionValue<K>>)=>void,transport:typeof fetch=fetch,timeoutMs=4000){
 if(!Object.hasOwn(projectionParsers,key))throw Error('D0_REGISTRY_HOLD');
 return createProjectionReader(key,projectionParsers[key] as Parser<ProjectionValue<K>>,publish,transport,timeoutMs);
}
