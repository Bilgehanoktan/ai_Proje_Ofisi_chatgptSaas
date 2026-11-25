import {localBackendPort} from '../../../../features/mvp/localBackend';
import {parseMvpDiagnostics} from '../../../../features/mvp/mvpDiagnostics';
import {readBoundedD0Json} from '../../../../features/mvp/readBoundedD0Json';

export const dynamic = 'force-dynamic';
const headers = {'Cache-Control': 'no-store'};

export async function GET() {
  try {
    const endpoint = `http://127.0.0.1:${localBackendPort()}/demo/v1/mvp/diagnostics`;
    const body = await readBoundedD0Json(endpoint, parseMvpDiagnostics, 16384);
    return Response.json(body, {headers});
  } catch {
    return Response.json({mode: 'D0_READBACK_HOLD'}, {status: 503, headers});
  }
}
