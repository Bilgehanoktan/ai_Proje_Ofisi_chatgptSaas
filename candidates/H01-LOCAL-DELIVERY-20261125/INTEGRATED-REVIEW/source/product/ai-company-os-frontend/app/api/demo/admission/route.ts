import {parseAdmissionProjection} from '../../../../features/mvp/admissionProjection';
import {readBoundedD0Json} from '../../../../features/mvp/readBoundedD0Json';
import {localBackendPort} from '../../../../features/mvp/localBackend';
export const dynamic='force-dynamic';
const headers={'Cache-Control':'no-store'};
export async function GET(){
 try{
  const endpoint=`http://127.0.0.1:${localBackendPort()}/demo/v1/admission/sample-projection`;
  const body=await readBoundedD0Json(endpoint,parseAdmissionProjection,4096);
  return Response.json(body,{headers});
 }catch{return Response.json({mode:'D0_ADMISSION_READBACK_HOLD'},{status:503,headers});}
}
