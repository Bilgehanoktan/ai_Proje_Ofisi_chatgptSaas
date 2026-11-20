# MI-01 / W8 — final owner decision packet and gated C06–C08 instructions
Date: 2026-11-20. Status: **G3 actual PASS; G4 C05 independent owner/security/legal HOLD; G5–G7 NOT_RUN; G8 HOLD**. No product merge, CI expansion or authorization implied.

## Exact pinned candidate (do not regenerate)
- Draft PR #34: `review/mi01-w8-cryptography-50-0-2-20261120`. Actual user Windows C04 source commit **`388c8a9ed539aba4e645267f00035f6f2ef0ff3e`**; subsequent documentation commits may move the head without changing the three pinned source blobs.
- Product manifest Git blob **`589a77c2115bf255600d130087fc8973ecf2b7e5`**; dependency Git blob **`921818de26b481ed94603d8e596a384abf04bfa9`**; W8 adapter Git blob **`c67b6d0f3234cedbb7d1dc22ebc2511829b2ff04`**. Original `integration/product-dev` baseline commit `254e0188998d0d245bd8ee4eb901aead02951a66` remains untouched.
- Exact user Windows C04 stage: **`E:\AIOS\W8\CRYPT50_STAGE_20261120_224742`**. Independent-review **target** is `locks/REVIEW.json` SHA256 **`7335e1dd2525aa5639d276344c617b68fc323387e584b8c1c2c8ef81272d20aa`**; Python lock SHA256 `dfc5da1b553c71ae209d31e70209de699503973dbc8146ba611e35703f5367a5`; npm lock SHA256 `036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88`.
- Actual Windows source audit **PASS: 552 source SHA-256, 17 shared file pairs, 29 aux Git blobs**. Original W8 `prepare` **PASS: 28 wheel files**. Original downloaded `cryptography-50.0.2-cp311-abi3-win_amd64.whl` SHA256 **`7afa5a6602a9f29af1f3a2965f831bae7c9d5d597b7cbb716d41ab3b7d89879c`** matches publisher PyPI.
- Uploaded original native C05 JSON; all 28 exact wheel **names/versions/SHA256 match official PyPI**; all 28 wheel METADATA carry a license expression or field/classifier. Frozen npm lock **61 entries**, all registry HTTPS and valid SRI metadata; actual native `REVIEW.json`, Python lock, npm lock and all 28 wheel hashes passed. Live public OSV `querybatch`: **28 PyPI +61 npm exact versions =89 queries, 0 returned OSV matches** at query time (not zero risk).

## Independent C05 decision required — exact four-part disposition
The actual **independent source/security/legal reviewers**, not the assistant or W8 runner, must document the following **against the immutable REVIEW SHA256 above**, with named reviewer, date, artifact/version, reasoning and explicit ACCEPT or REJECT:
1. **Runtime/native cryptographic provenance:** PyPI official wheel identity and SHA are verified; upstream PyCA changelog says Windows wheels for 50.0.2 compiled with **OpenSSL 4.0.3**. Actual loaded Windows wheel/native OpenSSL 4.0.3 has NOT been independently runtime-confirmed; upstream changelog and publisher hash alone are not binary runtime attestation. PyPI provenance attestations are not independently signature-verified by this work.
2. **Distribution/legal:** `cryptography` Apache-2.0 OR BSD-3-Clause, `certifi` MPL-2.0, Windows `@img/sharp-win32-x64` Apache-2.0 AND LGPL-3.0-or-later, remaining libvips platform variants in frozen lock LGPL-3.0-or-later, `caniuse-lite` CC-BY-4.0 and associated attribution/notices/source/relinking obligations. Determine which third-party libraries actually ship and where notices are delivered. Lock presence does not prove a platform package was installed or shipped.
3. **Security:** current scoped OSV zero matches does not exclude advisories outside OSV, transitive native binaries, exploitable misconfiguration or runtime incompatibility. Independent reviewer assesses risk, actual name/version fingerprints, exact hash and operating environment. Validate both Ed25519 positive and negative paths later in C07.
4. **Source/code and controls:** G1 source owner must review the narrow dependency patch, API compatibility, rollback and isolated stage. G8 integration remains a separate decision; neither reviewer action grants database authority, production keys, provider access or general product acceptance.

**C05 verdict is HOLD until all four are independently reviewed and the exact REVIEW hash is explicitly accepted.** The command-line `--approve` flag below only verifies a lock digest and is NOT an independent security authorization.

## After C05 independent approval only — original existing W8 commands
Do NOT execute this section before C05 written approval is recorded in the corresponding PR review/central decision ledger.

Use the existing original `tests/integration/w8_unified_u3.py` in the **same source tree** used for actual C04; resolve the source directory by matching its expected pinned blobs. Do not change or recreate stage `CRYPT50_STAGE_20261120_224742`.

PowerShell 5.1 session:
```powershell
$ErrorActionPreference = 'Stop'
$root = 'E:\AIOS\W8'
$stage = Join-Path $root 'CRYPT50_STAGE_20261120_224742'
$reviewHash = '7335e1dd2525aa5639d276344c617b68fc323387e584b8c1c2c8ef81272d20aa'
$actual = (Get-FileHash -Algorithm SHA256 (Join-Path $stage 'locks\REVIEW.json')).Hash.ToLowerInvariant()
if ($actual -ne $reviewHash) { throw 'CHANGED_REVIEW_LOCK_HOLD' }
# MANDATORY: independent source/security/legal owner C05 ACCEPT for this hash must be recorded outside this script.
# Do NOT treat this digest comparison as authorization.
$sources = @(Get-ChildItem $root -Directory -Filter 'CRYPT50_SRC_*' | Sort-Object LastWriteTime -Descending)
$source = $null
foreach ($entry in $sources) {
    $p = Join-Path $entry.FullName 'tests\integration\w8_unified_u3.py'
    if (!(Test-Path $p)) { continue }
    $gitBlob = (& git -C $entry.FullName rev-parse 'HEAD:tests/integration/w8_unified_u3.py' 2>$null)
    if ($LASTEXITCODE -ne 0 -or !$gitBlob -or $gitBlob.Trim() -ne 'c67b6d0f3234cedbb7d1dc22ebc2511829b2ff04') { continue }
    $source = $entry.FullName
    break
}
if (!$source) { throw 'EXACT_REVIEW_SOURCE_MISSING_HOLD' }
$runner = Join-Path $source 'tests\integration\w8_unified_u3.py'
# Once C05 acceptance and source owner review are documented:
& py -3.13 -B $runner install --repo $source --stage $stage --approve $reviewHash
if ($LASTEXITCODE -ne 0) { throw 'C06_INSTALL_HOLD' }
& py -3.13 -B $runner test --repo $source --stage $stage --approve $reviewHash
if ($LASTEXITCODE -ne 0) { throw 'C07_TEST_BUILD_HOLD' }
# C08: supply a REAL existing local Chrome/Chromium binary; never guess a path:
$chromium = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
if (!(Test-Path -LiteralPath $chromium)) { throw 'CHROMIUM_EXE_NOT_FOUND_HOLD' }
& py -3.13 -B $runner smoke --repo $source --stage $stage --approve $reviewHash --chromium $chromium
if ($LASTEXITCODE -ne 0) { throw 'C08_BROWSER_HOLD' }
Write-Output 'C06_C07_C08_ORIGINAL_RUNNER_PASS_REQUIRES_LOG_AND_OWNER_REVIEW'
```
Source `w8_unified_u3.py` delegates to unchanged original W8 install/test/smoke: isolate venv, pip install with exact hashes, `npm ci` with frozen registry lock, real Python unittest + Ed25519, Next.js build and real Chromium loopback smoke. Any failure is real HOLD; preserve logs, stage and user environment for diagnosis. No production/real credential use.

## Delivery/rollback and acceptance
Do not alter `integration/product-dev` or `main` without post-test source owner/central G8 review. PR34 remains draft while C05 security review pending. Keep original PR20/PR33 stages for normal rollback; no force push, no branch protection changes, no new CI workflow.

**Development percent:** HESAPLANAMADI (frozen weighted denominators still absent). **Canonical W8 product acceptance:** 3/8 -> 3/8 (delta 0 percentage points); MVP 0/11, IV 0/7. Source/build subtest achievements must not be counted as independent acceptance without an approved W8 criterion.
