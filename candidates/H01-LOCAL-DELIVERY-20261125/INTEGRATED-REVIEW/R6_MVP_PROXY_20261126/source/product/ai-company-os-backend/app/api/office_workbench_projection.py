"""Opt-in fixed local workbench readback; no mutation route."""
import os
import sqlite3
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.development_review.office_workbench import read_office_workbench

router = APIRouter()


@router.get('/demo/v1/office/workbench-projection')
def office_workbench_projection():
    headers = {'Cache-Control':'no-store'}
    try:
        path = os.environ.get('AICOS_D0_WORKBENCH_DB')
        if not path:
            raise ValueError('OFFICE_WORKBENCH_MISSING')
        return JSONResponse(read_office_workbench(path),headers=headers)
    except (OSError,sqlite3.Error,ValueError,TypeError,KeyError):
        return JSONResponse({'mode':'D0_OFFICE_WORKBENCH_HOLD'},status_code=503,headers=headers)
