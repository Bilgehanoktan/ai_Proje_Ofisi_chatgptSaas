"""Fixed opt-in D0 readback. No DB path or scope supplied by HTTP caller."""
import os
import sqlite3
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.development_review.lifecycle_projection import read_lifecycle_projection

router=APIRouter()

@router.get('/demo/v1/lifecycle/sample-projection')
def lifecycle_projection():
    headers={'Cache-Control':'no-store'}
    try:
        path=os.environ.get('AICOS_D0_LIFECYCLE_DB')
        if not path: raise ValueError('D0_LIFECYCLE_PATH_HOLD')
        return JSONResponse(read_lifecycle_projection(path),headers=headers)
    except (OSError,sqlite3.Error,ValueError,TypeError,KeyError):
        return JSONResponse({'mode':'D0_LIFECYCLE_PROJECTION_HOLD'},status_code=503,headers=headers)
