"""Opt-in, read-only synthetic admission projection."""
import os
import sqlite3
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.development_review.admission_sample import read_admission

router=APIRouter()


@router.get('/demo/v1/admission/sample-projection')
def admission_projection():
    path=os.environ.get('AICOS_D0_ADMISSION_DB')
    headers={'Cache-Control':'no-store'}
    try:
        if not path: raise ValueError('ADMISSION_SAMPLE_MISSING')
        return JSONResponse(read_admission(path),headers=headers)
    except (OSError,sqlite3.Error,ValueError,TypeError):
        return JSONResponse({'mode':'D0_ADMISSION_READBACK_HOLD'},status_code=503,headers=headers)
