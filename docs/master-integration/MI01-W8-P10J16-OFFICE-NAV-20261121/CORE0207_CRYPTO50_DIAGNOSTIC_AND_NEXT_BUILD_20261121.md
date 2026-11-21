# MI-01 / W8 — Core 0207 cryptography 50 compatibility diagnostic and independent Next.js build

Date: 2026-11-21. Source owner: MI-01/W8. **This is a source-preserving diagnostic plan, not a replacement of the immutable historical acceptance gate.**

## Last actual user Windows results
- PR36 exact source SHA256 552/552, G3 original source audit **PASS**; C04 prior-approved 28-wheel certifi 2026.10.23 graph replay with PR36 manifest new REVIEW SHA256 **341e179afda3e344ac32b3f4643860e44c7dd350cfb66ac59ac5edc98c79a1b3 PASS**.
- Original Windows C06 offline SHA-locked install **PASS** in `E:\AIOS\W8\PR36_W8_CERTIFI_LOCKED_20261121_132808\stage`; original PR35 and both failed PR36 stages retained unchanged.
- Original C07 attempted, last visible isolated Node test group 43/43 PASS, **original `run_core_0207.py` exited 1** before full Next.js build. C07 as whole FAIL/HOLD, C08 browser NOT_RUN.
- **Exact native report** `stage/core29-p10f.json` read directly by user: `{"revision":"0207","status":"HOLD","passed":null,"scope":"D0 only","source_commit":"614aa63efbd0a95d0fa5fe47390df043d773370f","verified_files":55,"dependency_versions":{"fastapi":"0.163.0","starlette":"1.10.0","cryptography":"50.0.2","uvicorn":"0.34.2"},"reason":"DIRECT_DEPENDENCY_PIN_MISMATCH"}`. **Source integrity 55/55 verified**.
- Historic `tests/integration/core_0207_source_lock.json` Git blob **223f6fbd28cf4c428c07eb60dda4a36f644fa58c** fixes direct cryptography **46.0.4** (with same three other versions). Current PR36 approved graph uses cryptography **50.0.2**, intentionally security patched via PR34. Historic `run_core_0207.py` original Git blob **b019a5e60cfff4183b00e99f252ffe00bc164eda** hard-fails unless its four exact direct pins match.
- User's *additional manual dependency print* failed `NameError: fastapi is not defined` due to incorrect nested PowerShell/Python quoting in assistant-supplied command; it is **not an additional product/C07 failure**. The runner JSON already verifies all four installed direct dependency versions.
- Independent security C05 **HOLD**; W8 acceptance **3/8 → 3/8 (delta 0)**, weighted development **HESAPLANAMADI**. Product dev reference `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, no mutation.

## Why not adjust original historical gate directly
Old historic lock/runner records an *exact old dependency environment* and source slice. It cannot be asserted to have passed under newer cryptography 50.0.2, and current product may not downgrade to 46.0.4 to satisfy it. Marking the original C07 PASS based on patched equality, `--diagnostic-unpinned`, or skipping the step would falsify acceptance. Instead, preserve the lock/runner byte-for-byte and collect compatibility evidence in an isolated diagnostic.

## New independent diagnostic helper (local file, not product code)
- Conversation-delivered `AIOS_W8_PR36_CORE29_COMPAT_NEXT_DIAGNOSTIC_20261121.py`, **12,022 bytes**, SHA256 **8ff2de023fbae8588e55c380d4e84a349b90e245c78cc704144ea8f18d8030a9**.
- Static validation performed: AST parse/py_compile, CLI --help, destructive-call name scan; **NOT executed on Windows**. No source commit / implementation / production change.
- Requires exact Python 3.13.17, C free >=2GiB and E free >=4GiB. Verifies previous stage immutable SHA256 `341e179a...`, manifest Git blob `9660da1104617b4764d5f1e32009e4e3405b47f8`, original `run_core_0207.py` blob `b019a5...`, original `w8_p10j24.py` blob `0728ba...`, historical 55-file source lock blob `223f6f...`, original `INSTALL_OK` and **all 552 source file SHA256**. Rejects any unexpected `BUILD_TEST_OK` marker.
- In a new `E:\AIOS\W8\PR36_DIAGNOSTIC_ONLY_<timestamp>` folder, uses pinned `w8_p10j24.materialize_history` to reconstruct the original 55-file historical input, including the 4th history `postgres_session.py` blob `8e65e4575a77b11c38c2d2e62ec91fc89d75e23c`; verifies every historical Git blob and SHA256.
- Calls **unchanged exact `run_core_0207.py`** with explicit supported flag `--diagnostic-unpinned` and the **current approved PR36 venv** to determine whether 29/29 historical behavior cases pass under cryptography 50.0.2. This is **SYNTHETIC UNPINNED DIAGNOSTIC**, never old locked gate PASS, never C07 completion. Requires actual 29 PASS, 0 failed and 55 files verified for a positive diagnostic.
- In independent second line, clones **only current PR36 frontend plus existing installed `node_modules`** under new E folder, executes local Next.js `build` and TypeScript `tsc --noEmit` with a minimal environment allowlist and Next telemetry off. This **does not run or replace original full C07**, does not change the failed C06-approved stage. Any failure recorded as diagnostic failure, not false acceptance.
- User may select `--mode core`, `--mode build`, or default `--mode both`; default tests both independent probes. No Git calls/network setup/CI/prod/provider account actions, dependency upgrade, source patch, security policy change, permission change, file deletion or checkout mutation. Original stage hashes and all 552 source SHA256 reverified afterward.
- Output: `PR36_DIAGNOSTIC_ONLY_STATUS.json`, `PR36_DIAGNOSTIC_ONLY.log` and `core29_current_crypto50_DIAGNOSTIC_NOT_ACCEPTANCE.json`, all under new E diagnostic-only folder. A positive output is **diagnostic evidence only**.

### Windows operator command (must SHA-verify helper first)
```powershell
& {
  $ErrorActionPreference = 'Stop'
  $file = Join-Path $env:USERPROFILE 'Downloads\AIOS_W8_PR36_CORE29_COMPAT_NEXT_DIAGNOSTIC_20261121.py'
  $expected = '8ff2de023fbae8588e55c380d4e84a349b90e245c78cc704144ea8f18d8030a9'
  if (!(Test-Path -LiteralPath $file) -or
      (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
      throw 'PR36_DIAGNOSTIC_HELPER_INTEGRITY_HOLD'
  }
  & py -3.13 $file --mode both
  if ($LASTEXITCODE -ne 0) { throw 'PR36_DIAGNOSTIC_HOLD_SEE_NEW_REPORT' }
}
```

## Decision tree, catalog and rollback
- **If core29 compatibility 29/29 PASS**: propose a separate **owner-reviewed, versioned cryptography 50.0.2 compatibility contract** while preserving historical 46.0.4 exact lock as historical evidence. Such new contract must demonstrate the same 55-file inputs, same 29 test IDs/case outcomes, direct pin table, and current secure wheel SHA; it is **not yet approved**, and C07 remains HOLD until correctly approved and original full product run passes.
- **If core29 diagnostic FAIL**: inspect per-test reason, pinpoint product behavior regression without downgrading runtime or falsifying old exact evidence. The diagnostic must not promote acceptance.
- **If isolated Next build/tsc PASS**: independent PR36 UI build evidence is available, not full C07; C08 remains NOT_RUN. If build fails: inspect exact log in new diagnostic folder, fix actual frontend source or environment in scoped candidate, not yet claim acceptance.
- **Independent C05, final owner acceptance and canonical product merge remain HOLD**. No new product classes/functions, APIs, DB, contracts, events, runtime dependencies or source branches were introduced in this turn. New file is a local diagnostic/maintenance artifact; add reference here to technical catalog/handover.
- Rollback: leave old PR35 and failed PR36 stages unchanged. New diagnostic output folder can be retained or archived by operator, no automatic deletion. Only owner-reviewed source and test-contract successor may be merged to product staging, never auto-merge to `integration/product-dev`/main.
