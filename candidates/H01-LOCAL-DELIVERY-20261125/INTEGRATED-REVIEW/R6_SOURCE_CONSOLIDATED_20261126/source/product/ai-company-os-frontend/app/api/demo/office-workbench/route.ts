import {parseOfficeWorkbench} from '../../../../features/mvp/officeWorkbenchProjection';
import {localBackendPort} from '../../../../features/mvp/localBackend';
import {readBoundedD0Json} from '../../../../features/mvp/readBoundedD0Json';
export const dynamic='force-dynamic';
const headers={'Cache-Control':'no-store'};
export async function GET(){
 try{
  const endpoint=`http://127.0.0.1:${localBackendPort()}/demo/v1/office/workbench-projection`;
  const body=await readBoundedD0Json(endpoint,parseOfficeWorkbench,4096);
  return Response.json(body,{headers});
 }catch{return Response.json({mode:'D0_OFFICE_WORKBENCH_HOLD'},{status:503,headers});}
}
