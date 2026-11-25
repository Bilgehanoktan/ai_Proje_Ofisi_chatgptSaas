import {parseTaskBudgetProjection} from '../../../../features/mvp/taskBudgetProjection';
import {readBoundedD0Json} from '../../../../features/mvp/readBoundedD0Json';
import {localBackendPort} from '../../../../features/mvp/localBackend';
export const dynamic='force-dynamic';
const headers={'Cache-Control':'no-store'};
export async function GET(){
 try{
  const endpoint=`http://127.0.0.1:${localBackendPort()}/demo/v1/task-budget/sample-projection`;
  const body=await readBoundedD0Json(endpoint,parseTaskBudgetProjection,8192);
  return Response.json(body,{headers});
 }catch{return Response.json({mode:'D0_TASK_BUDGET_HOLD'},{status:503,headers});}
}
