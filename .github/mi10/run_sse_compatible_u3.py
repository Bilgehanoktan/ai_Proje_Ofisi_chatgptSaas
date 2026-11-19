"""MI-10 Chromium CDP/SSE compatibility diagnostic.

Uses the immutable original U3 Playwright test, preserves its assertions,
route isolation, response metadata and all five screenshots. Only the
same-response SSE body acquisition is adapted from Playwright CDP
Network.getResponseBody to an in-page cloned Fetch response.
This is NOT the original byte-exact test run or formal W8 acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile

ORIGINAL_BLOB = "2a3f2b8e286c5d79847a6b00cdb6d046d0429773"
MARKER = "        page = browser.new_page(viewport={'width':1440,'height':900}, reduced_motion='reduce')"
LINE = "            lines = r.text().splitlines()"
INSTRUMENT = """        page.add_init_script(script=r\'''(() => {
  const upstream = window.fetch;
  window.__mi10LastStreamBody = null;
  window.fetch = function(...args) {
    return upstream.apply(this, args).then(response => {
      const url = new URL(response.url, window.location.href);
      if (url.origin === window.location.origin && url.pathname === '/api/demo/shared-snapshot') {
        window.__mi10LastStreamBody = response.clone().text();
      }
      return response;
    });
  };
})()\''')
"""

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--chromium",type=Path,required=True)
    p.add_argument("--frontend-port",type=int,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    source=args.original.resolve(strict=True)
    raw=source.read_bytes()
    if args.original.is_symlink() or blob(raw)!=ORIGINAL_BLOB:
        raise ValueError("MI10_ORIGINAL_U3_BLOB_HOLD")
    original=raw.decode("utf-8")
    if original.count(MARKER)!=1 or original.count(LINE)!=1:
        raise ValueError("MI10_U3_PATCH_SCOPE_HOLD")
    changed=original.replace(MARKER, MARKER+"\n"+INSTRUMENT,1)
    changed=changed.replace(LINE,
        "            page.wait_for_function(\"window.__mi10LastStreamBody !== null\", timeout=4000)\n"
        "            lines = page.evaluate(\"async () => await window.__mi10LastStreamBody\").splitlines()",1)
    compile(changed,"mi10-u3-sse-compat.py","exec")
    with tempfile.TemporaryDirectory(prefix="mi10-browser-sse-") as temp:
        script=Path(temp)/"browser_unified_u3_sse_compat.py"
        script.write_text(changed,encoding="utf-8")
        print("U3_TEST_SOURCE_PIN=PASS; SAME_NETWORK_RESPONSE_BODY=PAGE_FETCH_CLONE; PLAYWRIGHT_CDP_BYPASS=YES",flush=True)
        subprocess.run([sys.executable,"-B",str(script),
                        "--chromium",str(args.chromium),
                        "--frontend-port",str(args.frontend_port),
                        "--output",str(args.output)],check=True)
        print("U3_COMPATIBLE_BROWSER_FLOW=PASS; ORIGINAL_CDP_RESPONSE_TEXT=UNRESOLVED; FULL_W8_ACCEPTANCE=HOLD",flush=True)

if __name__=="__main__":
    main()
