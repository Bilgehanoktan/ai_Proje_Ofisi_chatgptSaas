import {localBackendPort} from '../../../../features/mvp/localBackend';
import {parsePlanProjection} from '../../../../features/core-review/planProjection';
import {readBoundedD0Json} from '../../../../features/mvp/readBoundedD0Json';

export const dynamic = 'force-dynamic';
const headers = {'Cache-Control': 'no-store'};

export async function GET() {
  try {
    const endpoint = `http://127.0.0.1:${localBackendPort()}/demo/v1/core/plan-projection`;
    const plan = await readBoundedD0Json(endpoint, parsePlanProjection, 16384);
    return Response.json(plan, {headers});
  } catch {
    return Response.json({mode: 'D0_PLAN_READBACK_HOLD'}, {status: 503, headers});
  }
}
