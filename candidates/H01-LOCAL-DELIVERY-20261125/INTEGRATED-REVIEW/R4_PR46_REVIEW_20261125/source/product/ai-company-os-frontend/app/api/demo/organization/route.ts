import {readOwnerBoundOrganization} from '../../../../features/organization/organizationOwnerBinding';
import {localBackendPort} from '../../../../features/mvp/localBackend';
// No canonical server owner is registered. Do not supply a demo credential.
export const dynamic='force-dynamic';
export async function GET(request:Request){
 try{return await readOwnerBoundOrganization(request,localBackendPort());}
 catch{return Response.json({mode:'D0_ORGANIZATION_READ_HOLD'},{status:503,headers:{'Cache-Control':'no-store'}});}
}
