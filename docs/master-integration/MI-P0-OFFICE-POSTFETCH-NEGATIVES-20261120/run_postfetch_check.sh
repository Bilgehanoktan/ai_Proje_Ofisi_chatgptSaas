#!/usr/bin/env bash
# Execute isolated, exact-blob Office route deadline checks. Never modifies the source checkout.
set -euo pipefail
if [[ $# -lt 1 || ! -f "$1" ]]; then
  echo 'Usage: run_postfetch_check.sh /absolute/path/to/pr22/route.ts [output.tap]' >&2
  exit 2
fi
ROUTE=$(realpath "$1")
BASE=$(cd -- "$(dirname -- "$0")" && pwd)
TEST="$BASE/test_postfetch_stall.cjs"
EXPECTED_ROUTE_SHA256='bf03304a9e8705d68c9c8987f7c03a928eb27b728d9daca44d33b86b2b9677aa'
EXPECTED_TEST_SHA256='f2d0856c3cbad979c94b6048cb51c6a70ca6e011358a2085490683b2d895f17a'
[[ $(sha256sum "$ROUTE" | awk '{print $1}') == "$EXPECTED_ROUTE_SHA256" ]] || { echo 'ROUTE_SOURCE_BLOB_MISMATCH_HOLD' >&2; exit 2; }
[[ $(sha256sum "$TEST" | awk '{print $1}') == "$EXPECTED_TEST_SHA256" ]] || { echo 'QA_TEST_BLOB_MISMATCH_HOLD' >&2; exit 2; }
[[ $(node --version) == 'v22.16.0' ]] || { echo 'NODE_VERSION_HOLD' >&2; exit 2; }
[[ $(tsc --version) == 'Version 5.8.3' ]] || { echo 'TSC_VERSION_HOLD' >&2; exit 2; }
STAGE=$(mktemp -d)
trap 'rm -rf -- "$STAGE"' EXIT
ROOT="$STAGE/source/product/ai-company-os-frontend"
mkdir -p "$ROOT/app/api/demo/office-workbench" "$ROOT/features/mvp"
cp -- "$ROUTE" "$ROOT/app/api/demo/office-workbench/route.ts"
cat > "$ROOT/features/mvp/officeWorkbenchProjection.ts" <<'TS'
// Isolated test double. The real contract/parser is deliberately NOT tested here.
export function parseOfficeWorkbench(_value:unknown): boolean {return true;}
TS
cat > "$ROOT/features/mvp/localBackend.ts" <<'TS'
// Isolated test double; no network request is made, fetch is replaced in QA.
export function localBackendPort():number{return 8765;}
TS
tsc --target ES2022 --module commonjs --lib ES2022,DOM --rootDir "$ROOT" --outDir "$STAGE/compiled" --skipLibCheck --strict "$ROOT/app/api/demo/office-workbench/route.ts"
if [[ $# -ge 2 ]]; then
  MI_P0_OFFICE_COMPILED_MODULE="$STAGE/compiled/app/api/demo/office-workbench/route.js" node --test "$TEST" | tee "$2"
else
  MI_P0_OFFICE_COMPILED_MODULE="$STAGE/compiled/app/api/demo/office-workbench/route.js" node --test "$TEST"
fi
