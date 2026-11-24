"""Opt-in local synthetic readback. No request-supplied database path or mutations."""
import os
import sqlite3
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.development_review.outbox_claim_sample import read_projection

router = APIRouter()


@router.get('/demo/v1/outbox/review-projection')
def outbox_projection():
    path = os.environ.get('AICOS_D0_REVIEW_DB')
    headers = {'Cache-Control':'no-store'}
    try:
        if not path:
            raise ValueError('SAMPLE_DB_NOT_CONFIGURED')
        return JSONResponse(read_projection(path),headers=headers)
    except (OSError,sqlite3.Error,ValueError,TypeError):
        return JSONResponse({'mode':'D0_OUTBOX_READBACK_HOLD'},status_code=503,headers=headers)
