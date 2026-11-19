"""Owner-review-only source-pinned U3 SSE/CDP compatibility candidate.

Transforms the existing immutable original U3 test in a temporary copy, keeps
all test assertions, and changes only how the same fetch response body is read.
No checkout, CI, production code or original test file is modified in place.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ORIGINAL_BLOB = '2a3f2b8e286c5d79847a6b00cdbd046d0429773'
PAGE = "        page = browser.new_page(viewport={'width':1440,'height':900}, reduced_motion='reduce')"
BEFORE_READ = '            with page.expect_response(lambda r: r.url == url) as response:'
BODY = '            lines = r.text().splitlines()'


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def transform(original: bytes, script: str) -> str:
    if git_blob(original) != ORIGINAL_BLOB:
        raise ValueError('MI10_ORIGINAL_U3_BLOB_HOLD')
    source = original.decode('utf-8')
    for marker in (PAGE, BEFORE_READ, BODY):
        if source.count(marker) != 1:
            raise ValueError('MI10_U3_PATCH_SCOPE_HOLD: ' + marker)
    source = source.replace(PAGE, PAGE + '\n' + '        page.add_init_script(script=' + repr(script) + ')', 1)
    source = source.replace(
        BEFORE_READ,
        '            __mi10_before = page.evaluate("window.__mi10Capture.issued()")\n' + BEFORE_READ,
        1,
    )
    source = source.replace(
        BODY,
        '            __mi10_expected = __mi10_before + 1\n'
        "            page.wait_for_function('(seq) => window.__mi10Capture.ready(seq)', arg=__mi10_expected, timeout=4000)\n"
        "            assert page.evaluate('window.__mi10Capture.issued()') == __mi10_expected, 'MI10_SSE_EXTRA_FETCH_HOLD'\n"
        "            lines = page.evaluate('async (seq) => await window.__mi10Capture.take(seq)', __mi10_expected).splitlines()",
        1,
    )
    compile(source, '<owner_review_u3_compat>', 'exec')
    return source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', required=True, type=Path)
    parser.add_argument('--init-script', default=Path(__file__).with_name('sse_capture_init.js'), type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.original.is_symlink() or args.output.exists() or args.output.resolve() == args.original.resolve():
        raise ValueError('MI10_U3_OUTPUT_SCOPE_HOLD')
    code = transform(args.original.read_bytes(), args.init_script.read_text(encoding='utf-8'))
    with args.output.open('x', encoding='utf-8') as output:
        output.write(code)
    print('MI10_ORIGINAL_U3_PIN_PASS; FRESH_SEQUENCE_PATCH_COMPILED; REAL_BROWSER_NOT_RUN')


if __name__ == '__main__':
    main()
