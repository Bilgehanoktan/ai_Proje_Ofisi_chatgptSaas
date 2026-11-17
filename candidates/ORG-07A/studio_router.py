"""ORG-07A: opt-in D0 Studio transport. Not registered in product, no IAM owner."""
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
import re
from typing import Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from jsonschema import Draft202012Validator

ROUTE = '/demo/v1/organization/studio-preview'
SCHEMA_BLOB = 'eed9627913502ebb09222cf404f867ca305a6a44'
HEADERS = {'Cache-Control': 'no-store', 'Pragma': 'no-cache', 'Vary': 'Authorization'}
DENIAL = {'decision': 'HOLD', 'reason': 'READ_UNAVAILABLE', 'authoritative': False}


@dataclass(frozen=True)
class ServerReadContext:
    """Trusted composition inputs; never populated from URL/body/headers."""
    path: Path
    expected_head: str
    resolve: Callable = field(repr=False)
    clock: Callable = field(repr=False)


def load_validator(schema_path):
    raw = Path(schema_path).read_bytes()
    blob = hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()
    if blob != SCHEMA_BLOB:
        raise ValueError('STUDIO_SCHEMA_PIN_HOLD')
    schema = json.loads(raw)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def deny():
    return JSONResponse(DENIAL, status_code=403, headers=HEADERS)


def build_router(context_provider, schema_path, *, reader=None):
    """Mount only in an isolated test composition. Original R3 owns read/session checks.

    context_provider() must be server-owned and must not derive context from request.
    reader injection is for isolated transport tests only, not a new authority.
    """
    validator = load_validator(schema_path)
    if reader is None:
        from durable_ops import studio_read
        reader = studio_read
    router = APIRouter()

    def read_preview(request: Request):
        try:
            if request.url.query or request.headers.get('transfer-encoding') is not None:
                return deny()
            lengths = request.headers.getlist('content-length')
            if lengths not in ([], ['0']):
                return deny()
            auth = request.headers.getlist('authorization')
            if len(auth) != 1 or len(auth[0]) > 4103:
                return deny()
            match = re.fullmatch(r'Bearer ([A-Za-z0-9._~+/-]{1,4096}={0,2})', auth[0], re.IGNORECASE | re.ASCII)
            if match is None or len(match[1]) > 4096:
                return deny()
            ctx = context_provider()
            if type(ctx) is not ServerReadContext or not re.fullmatch(r'[0-9a-f]{64}', ctx.expected_head):
                return deny()
            if not isinstance(ctx.path, Path) or not ctx.path.is_absolute():
                return deny()
            now = ctx.clock()
            if type(now) is not int or now < 0:
                return deny()
            resolved = []

            def resolve_once(credential):
                if resolved or credential != match[1]:
                    raise ValueError('RESOLVER_REPLAY_HOLD')
                session = ctx.resolve(credential)
                resolved.append(session)
                return session

            status, body = reader(ctx.path, match[1], resolve_once, ctx.expected_head, now)
            if type(status) is not int or status != 200 or len(resolved) != 1 or type(body) is not dict:
                return deny()
            # R3 validates ReadSession and permission. Transport only checks its scoped projection.
            if not validator.is_valid(body) or body['revision'] != ctx.expected_head:
                return deny()
            if tuple(body['scope'][k] for k in ('tenant_id','company_id','environment_id')) != resolved[0].scope.key():
                return deny()
            return JSONResponse(body, headers=HEADERS)
        except Exception:
            # Never serialize exception details, credential or filesystem paths.
            return deny()

    @router.get(ROUTE, include_in_schema=False)
    async def studio_preview(request: Request):
        try:
            # Reject a body even when an ASGI caller omitted Content-Length.
            async for chunk in request.stream():
                if chunk:
                    return deny()
            return await run_in_threadpool(read_preview, request)
        except Exception:
            return deny()

    return router
