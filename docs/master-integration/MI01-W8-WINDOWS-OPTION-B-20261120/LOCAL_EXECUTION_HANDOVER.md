# MI-01 W8 Windows / user-selected local option B — 20 November 2026

## Basis
H01 selected **B — Windows isolated PC validation**, instead of a new GitHub Actions scope. This does **not** alter CEO-0174/0179=B authorizations, independent security/IV, CI, production, source or owner boundaries. Workstream owner remains MI-01/Unified **PR #20**, immutable PR head observed `99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542`. Canonical source: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` (553 product files; 552 manifest entries). Owner runbook `docs/master-integration/MI01-W8-FROZEN-NPM-20261120/ARCHITECTURE_CATALOG_HANDOVER.md`.

## Supplied Windows PowerShell artifact
The chat has a downloadable plain-text PowerShell 5.1 file `AIOS_W8_WINDOWS_STAGE1_20261120.ps1` (9,292 bytes, **SHA-256 `9c16222b6673b41ba04cb2b2e120dd10eef5bf7fb0162bd423c3186c106ade06`**). The file itself is supplied as a conversation artifact, **not claimed committed to GitHub**; this record pins its exact bytes so the end-user's script can be checked locally. The current execution environment cannot run Windows PowerShell, and no user-PC test has yet taken place.

The script works in a unique `C:\AIOS\W8\W8_PR20_YYYYMMDD_HHMMSS` directory by default (configurable `-WorkRoot`), never modifies an existing source checkout, and downloads the exact PR #20 GitHub commit archive. It checks source manifest Git blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`, 552 manifest SHA-256 path/byte entries plus absence of unlisted product files, six W8 source Git blob pins and frozen npm lock SHA-256 `036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88`. It records a local `PRECHECK_RESULT.json`. No package installation by default.

### First user action: isolated source preflight
With the script saved to Downloads and after reading its text:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\AIOS_W8_WINDOWS_STAGE1_20261120.ps1"
```

This changes no machine-wide execution policy; the switch applies to this process only. The script downloads a GitHub archive; internet and disk capacity are required. For an available E: drive add `-WorkRoot "E:\AIOS\W8"`.

### Optional C04 actual network prepare — still not acceptance
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\AIOS_W8_WINDOWS_STAGE1_20261120.ps1" -RunPrepare
```

This verifies immutable source first and then runs the original pinned `tests/integration/w8_unified_u3.py prepare --repo <source> --stage <fresh isolated stage>`. Requires working Python 3.13 launcher `py -3.13`, Node, npm, GitHub and PyPI network, and sufficient free disk. C04 downloads pinned-package candidates and wheels but **does not perform the install/test/smoke phases**. `locks/REVIEW.json`, its printed SHA-256, `locks/python.lock`, npm lock, wheel SHA-256, source/version info and logs are presented to dependency/supply-chain owner for **C05 review**. Any failure is `HOLD`, not PASS. No user credentials should be included in shared logs.

### Strict continuation
Do not execute `install`, `test` or `smoke` before C05 independent dependency/legal/provenance owner review and explicit reviewed REVIEW SHA. After approval, the **existing** original U3 CLI is used for C06 install, C07 test/full Next build, and C08 native Chromium/5-screenshot same-document smoke on the *same immutable stage*. Results are not yet available. Use no automatic `npm install --package-lock-only` regeneration, provider activation, protected PostgreSQL effect, main merge, or production deployment.

## Current evidence / catalog / rollback
New design or product source: 0. New system API/DB/events/dependencies/CI: 0. Actual Windows execution: **NOT_RUN**. W8 operational previous/current **3/8 → 3/8**; C04 NOT_RUN, C05 HOLD, C06-C08 NOT_RUN; MVP 0/11, IV 0/7; global weighted 15/35/20/20/10 development **HESAPLANAMADI**. Next: user executes source preflight, submits `PRECHECK_RESULT.json`; MI-01 verifies exact pins and owner scope; optionally run C04 and seek C05. Recovery: delete only freshly created `W8_PR20_...` directory if failed, preserving repository branches and previous evidence. If script bytes differ from pinned SHA, do not execute pending review.

## R2 — private GitHub archive 404 / authenticated Git for Windows transport
The user executed the original Option B script on Windows PowerShell 5.1 and supplied two **actual** output receipts:
1. Default C: preparation stopped before source download: `HOLD: less than 5 GiB free`.
2. Re-executed with `-WorkRoot "E:\AIOS\W8"`; source ZIP URL `https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/archive/99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542.zip` returned HTTP **404**, `SOURCE_DIR:` blank, `STATUS: HOLD`. No W8 prepare executed.

Connected GitHub `get_repo` verified this repository is **private** and PR20 head still exactly `99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542`. The original script's unauthenticated `Invoke-WebRequest` was wrong for a private archive; 404 is an authentication/transport issue, **not a missing commit or failing product test**.

### Corrected Windows local script (conversation artifact R2)
- Filename: `AIOS_W8_WINDOWS_STAGE1_PRIVATE_GIT_R2_20261120.ps1`
- SHA256: `27f3600c83312b02cc22c4769b81b213787386f0217e49421167a5b46a283fe4`, 11,344 UTF-8 bytes.
- Transport: uses pre-installed Git for Windows and its existing Windows credential manager for a **shallow, exact PR20 branch checkout**. It does not request, log, print or persist a GitHub personal access token. It verifies the exact immutable HEAD SHA, all 552 product path/size/SHA256 manifest entries, Git blobs of six W8 pins and frozen npm lock SHA256.
- `-RunPrepare` is **not** the first step after an authentication error: first run source-only with `-WorkRoot "E:\AIOS\W8"`; review `PRECHECK_RESULT.json` and proceed only after source PASS. Running `-RunPrepare` then sets TEMP/TMP, Python and npm cache roots to the same isolated E: run directory, mitigating low C: storage; it runs **only C04**, never install/build/browser.
- If Git is not installed, script stops `HOLD`; Git for Windows installation and Git Credential Manager browser sign-in are **user-controlled** actions. Do not expose any tokens in chat or log files.
- Earlier script `AIOS_W8_WINDOWS_STAGE1_20261120.ps1` (SHA256 `9c16222b6673b41ba04cb2b2e120dd10eef5bf7fb0162bd423c3186c106ade06`) is historical/OBSOLETE for private repository checkout; preserve for audit, do not rerun.
- This current environment validated script source/text SHA and GitHub metadata only, **NOT Windows runtime execution**. W8 C04 NOT_RUN/C05 HOLD/C06–08 NOT_RUN; W8 **3/8 → 3/8**, product acceptance unchanged; weighted global development HESAPLANAMADI.
- Recovery: each run creates a unique directory. Previous HOLD receipts are retained. Manual deletion only of individually identified failed run folder after user inspection; do not delete existing worktrees or alter Git credentials.
