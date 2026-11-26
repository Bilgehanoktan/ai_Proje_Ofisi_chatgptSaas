"""R10: byte-range provenance; never grants retrieval or source authority."""
from dataclasses import dataclass, fields
from hashlib import sha256
from ...core.runtime_preview import Scope, valid_scope, token, uint
from ...core.t1_review import digest_ok


@dataclass(frozen=True)
class SourceVersion:
    scope: Scope
    source_id: str
    revision: str
    raw_digest: str


@dataclass(frozen=True)
class ClaimSpan:
    source: SourceVersion
    start: int
    end: int
    span_digest: str


def valid_source(source: object) -> bool:
    # Reject caller-controlled equality before comparing provenance records.
    return (type(source) is SourceVersion and type(source.scope) is Scope
            and all(type(getattr(source.scope, f.name)) is str for f in fields(Scope))
            and valid_scope(source.scope)
            and all(type(v) is str and token(v) for v in (source.source_id, source.revision))
            and type(source.raw_digest) is str and digest_ok(source.raw_digest))


def inspect_span(span: ClaimSpan, source: SourceVersion, raw: bytes) -> str:
    if type(span) is not ClaimSpan or not valid_source(source) or not valid_source(span.source) or span.source != source:
        return 'SOURCE_PIN_HOLD'
    if type(raw) is not bytes or len(raw) > 1024 * 1024 or sha256(raw).hexdigest() != source.raw_digest:
        return 'SOURCE_DIGEST_HOLD'
    if not uint(span.start) or not uint(span.end) or not 0 <= span.start < span.end <= len(raw):
        return 'SPAN_BOUNDS_HOLD'
    if type(span.span_digest) is not str or not digest_ok(span.span_digest) or sha256(raw[span.start:span.end]).hexdigest() != span.span_digest:
        return 'SPAN_DIGEST_HOLD'
    return 'D0_SPAN_MATCH_ONLY'
