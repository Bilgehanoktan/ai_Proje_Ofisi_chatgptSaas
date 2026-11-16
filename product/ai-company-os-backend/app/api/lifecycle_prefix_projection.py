"""Opt-in fixed historical prefix readback, not an active runtime API."""
import os
import sqlite3
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from app.core.development_review.lifecycle_prefix_projection import read_lifecycle_prefix

router=APIRouter()

@router.get('/demo/v1/lifecycle/prefix-projection')
def lifecycle_prefix_projection():
    headers={'Cache-Control':'no-store'}
    try:
        path=os.environ.get('AICOS_D0_LIFECYCLE_PREFIX_DB')
        if not path: raise ValueError('D0_PREFIX_PATH_HOLD')
        return JSONResponse(read_lifecycle_prefix(path),headers=headers)
    except (OSError,sqlite3.Error,ValueError,TypeError,KeyError):
        return JSONResponse({'mode':'D0_LIFECYCLE_PREFIX_HOLD'},status_code=503,headers=headers)


@router.get('/demo/v1/lifecycle/shared-snapshot')
def shared_snapshot(request: Request):
    """A single verified read, bounded SSE framing, no live subscription or resume."""
    headers={'Cache-Control':'no-store'}
    try:
        from app.core.development_review.shared_snapshot import build_shared_replay
        if 'last-event-id' in request.headers:
            raise ValueError('D0_SHARED_FULL_RESYNC_REQUIRED')
        path=os.environ.get('AICOS_D0_LIFECYCLE_PREFIX_DB')
        if not path:
            raise ValueError('D0_PREFIX_PATH_HOLD')
        return Response(build_shared_replay(read_lifecycle_prefix(path)),
                        media_type='text/event-stream',headers=headers)
    except (OSError,sqlite3.Error,ValueError,TypeError,KeyError):
        return JSONResponse({'mode':'D0_SHARED_SNAPSHOT_HOLD'},status_code=503,headers=headers)
