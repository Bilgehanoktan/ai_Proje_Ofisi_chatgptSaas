"""Opt-in local D0 combined readback; no path input or mutation."""
import os
import sqlite3
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.development_review.task_budget_snapshot import read_task_budget_snapshot

router = APIRouter()


@router.get('/demo/v1/task-budget/sample-projection')
def task_budget_projection():
    headers = {'Cache-Control':'no-store'}
    try:
        w = os.environ.get('AICOS_D0_WORKBENCH_DB')
        a = os.environ.get('AICOS_D0_ADMISSION_DB')
        if not w or not a:
            raise ValueError('D0_PAIR_MISSING_HOLD')
        return JSONResponse(read_task_budget_snapshot(w, a), headers=headers)
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError):
        return JSONResponse({'mode':'D0_TASK_BUDGET_HOLD'}, status_code=503, headers=headers)
