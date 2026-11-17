"""Opt-in fixed historical prefix readback, not an active runtime API."""
import os
import sqlite3
from fastapi import APIRouter
from fastapi.responses import JSONResponse
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
