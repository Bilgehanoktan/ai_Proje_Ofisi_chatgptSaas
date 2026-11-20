# MI-01 W8 — cryptography 50.0.2 G1 compatibility assessment / G3 native execution runbook
Date: 2026-11-20. This is a source and public-metadata review, **NOT** a source-owner approval, native Windows test, C05 security clearance or permission to skip G4.

## Pinned source baseline
- Isolated candidate: draft PR #34, branch `review/mi01-w8-cryptography-50-0-2-20261120`, initial exact **product source** commit `3523a0b595799480a6ef03fa57de6dc2903f796e` (documents on branch may advance head); based on PR33 `9166afe299cd8f1ab9c52355ec21ec06c465d6ef`. Future documentation commits may change branch head, not the 553-file product source tree.
- Candidate source pin: `product/ai-company-os-backend/requirements-history-signatures.txt`, blob `921818de26b481ed94603d8e596a384abf04bfa9`, SHA256 `14f7abb23f8fa599eec9103ef59f26ead5650b0075c7d93b1da5c2494473bcd2`. Product manifest Git blob `589a77c2115bf255600d130087fc8973ecf2b7e5`; 552 entries. Original `tests/integration/w8_unified_u3.py` candidate blob `c67b6d0f3234cedbb7d1dc22ebc2511829b2ff04`.
- `integration/product-dev` baseline `254e0188998d0d245bd8ee4eb901aead02951a66`, unchanged until controlled owner decision. Original 46.0.4 evidence and PR20/PR33 remain authoritative for historical tests only.

## G1 review — actual source/API usage versus upstream contract
- `app/core/event_store/signed_history.py` blob `d4d379a7e4e55fd6f81f102d3fcb0903d50db0a1`: `Ed25519PublicKey.from_public_bytes(public_key).verify(signature, body)`, with explicit D0 pin/time checks; successful match does **not** issue independent custody or dispatch rights. Code catches all signature/backend errors and fails closed.
- `app/core/transaction/signed_consume_reference.py` blob `477bcde63418dd43f886df7b32c5acd006d64a79`: uses `Ed25519PrivateKey`, `Ed25519PublicKey.from_public_bytes().verify` and `InvalidSignature`. The fixture signs a synthetic consumed observation, not an actual execution authority. Negative cases, signing and verified readback require actual tests on 50.0.2.
- `tests/integration/w8_p10f.py` blob `155a2179eb71bd554aa34dff36147be4658473e0` extends the original W8 `pip --isolated download` invocation with the exact optional `requirements-history-signatures.txt`; the later frozen-npm hook preserves this path. This means the changed pin should appear in a **new** `python.lock` and wheelhouse; do not recycle the 46.0.4 fingerprint.
- Upstream PyCA release 50.0.2 dated 2026-09-30, Python>=3.9, published Windows x64 CPython abi3 wheels; the upstream **50.0.2 changelog states bundled Windows/macOS/Linux OpenSSL 4.0.3** (50.0.1 was 4.0.2). Official PyPI lists trusted publishing/provenance on release files and Apache-2.0 OR BSD-3-Clause metadata. Source compatibility analysis is not a binary-wheel/OpenSSL/hash proof.
- Upstream 47–50 contains API/deprecation/compatibility changes; no change has been made to Ed25519 callers. No exact live OSV report for 50.0.2, no independent source/security/license verdict, no new binary wheel bytes or installed OpenSSL version verified in this review. G1 owner/security signoff **HOLD**.

Authoritative public references (checked 2026-11-20):
- https://cryptography.io/en/50.0.2/changelog/
- https://pypi.org/project/cryptography/50.0.2/

## G3 — execute **existing original W8**, without a new runner or bypass
User workstation only, PowerShell 5.1, Windows x64 Python 3.13 in existing **E:**-drive W8 workspace. The following is a **runbook, not a claim of execution**. The user workstation's Git checkout/root must be verified; do not assume a path is available. No C06/C07/C08 before separately signed-off C05.

```powershell
$ErrorActionPreference = 'Stop'
$repo = 'E:\AIOS\W8\W8_PR20_20261120_211752' # prior user-reported checkout; verify Git repo exists
$reviewBranch = 'review/mi01-w8-cryptography-50-0-2-20261120'
$sourcePin = '3523a0b595799480a6ef03fa57de6dc2903f796e'
$disk = Get-PSDrive E
if (-not $disk -or $disk.Free -lt 5GB) { throw 'E_DRIVE_SPACE_HOLD' }
if (-not (Test-Path -LiteralPath $repo)) { throw 'EXISTING_GIT_REPO_MISSING_HOLD' }
$inside = & git -C $repo rev-parse --is-inside-work-tree
if ($LASTEXITCODE -ne 0 -or $inside.Trim() -ne 'true') { throw 'NOT_A_GIT_WORKTREE_HOLD' }
& git -C $repo fetch origin "refs/heads/$reviewBranch"
if ($LASTEXITCODE -ne 0) { throw 'GITHUB_FETCH_HOLD' }
$head = (& git -C $repo rev-parse FETCH_HEAD).Trim()
& git -C $repo merge-base --is-ancestor $sourcePin $head
if ($LASTEXITCODE -ne 0) { throw "SOURCE_CANDIDATE_ANCESTRY_HOLD: $head" }
$manifestBlob = (& git -C $repo rev-parse "${head}:product/SOURCE_MANIFEST.json").Trim()
$requirementsBlob = (& git -C $repo rev-parse "${head}:product/ai-company-os-backend/requirements-history-signatures.txt").Trim()
$adapterBlob = (& git -C $repo rev-parse "${head}:tests/integration/w8_unified_u3.py").Trim()
if ($manifestBlob -ne '589a77c2115bf255600d130087fc8973ecf2b7e5' -or
    $requirementsBlob -ne '921818de26b481ed94603d8e596a384abf04bfa9' -or
    $adapterBlob -ne 'c67b6d0f3234cedbb7d1dc22ebc2511829b2ff04') {
    throw 'EXACT_SOURCE_BLOB_PIN_HOLD'
}
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$src = "E:\AIOS\W8\CRYPT50_SRC_$stamp"
$stage = "E:\AIOS\W8\CRYPT50_STAGE_$stamp"
& git -C $repo worktree add --detach $src $head
if ($LASTEXITCODE -ne 0) { throw 'WORKTREE_HOLD' }
$runner = Join-Path $src 'tests\integration\w8_unified_u3.py'
& python -B $runner audit --repo $src
if ($LASTEXITCODE -ne 0) { throw 'ORIGINAL_W8_AUDIT_HOLD' }
& python -B $runner prepare --repo $src --stage $stage
if ($LASTEXITCODE -ne 0) { throw 'FRESH_C04_PREPARE_HOLD' }
$review = Join-Path $stage 'locks\REVIEW.json'
$pylock = Join-Path $stage 'locks\python.lock'
if (-not (Test-Path $review) -or -not (Test-Path $pylock)) { throw 'C04_LOCK_OUTPUT_HOLD' }
$reviewSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $review).Hash.ToLowerInvariant()
$crypt = Select-String -LiteralPath $pylock -Pattern '^cryptography==50\.0\.2\s'
if (-not $crypt) { throw 'CRYPT50_PYLOCK_MISSING_HOLD' }
$wheelNames = @(Get-ChildItem -LiteralPath (Join-Path $stage 'locks\wheels') -Filter '*.whl' -File)
if ($wheelNames.Count -eq 0) { throw 'WHEELHOUSE_EMPTY_HOLD' }
Write-Output "G3_C04_SOURCE=$head"
Write-Output "G3_C04_STAGE=$stage"
Write-Output "G3_C04_REVIEW_SHA256=$reviewSha"
Write-Output "G3_C04_WHEEL_COUNT=$($wheelNames.Count)"
Write-Output 'G3_C04_PREPARED_ONLY_C05_SECURITY_OWNER_HOLD'
```

Important: above snippet intentionally stops after **audit/prepare + file checks**. Capture complete native stdout/stderr separately and preserve `$stage/locks/REVIEW.json`, `python.lock`, all wheel SHA256, `package-lock.json`, review source SHA, Python/Node/npm versions and exact any errors. Public SCA of every dependency and independent wheel/license reviewer verdict must be bound to **new** `REVIEW.json` SHA. DO NOT automatically call `install`, `test`, or `smoke`; DO NOT reuse legacy C04/C05 review hash. Native browser requires an explicit verified Chromium executable, owned by the PC.

## G4–G8 hard gates / diagnostics / rollback
- C05: repeat owner-approved public OSV, PyPI/npm registry metadata, actual Windows wheel SHA/provenance/embedded OpenSSL checks and license evaluation for all packages, Sharp/libvips LGPL and caniuse-lite CC-BY-4.0. No independent approval = HOLD, even if OSV matches are zero. Owners must review the exact stage lock and freeze its SHA.
- C06 original W8 `install --stage ... --approve <NEW_REVIEW_SHA256>` after C05 PASS only; C07 `test` after C06 real install PASS; C08 `smoke --chromium <real path>` after C07 PASS. The `--approve` flag checks fingerprint consistency, not independent security authorization; never use it to evade C05 review.
- Any test rejection: mark HOLD, keep the old 46.0.4 stage, new read-only evidence, logs and new source worktree for diagnosis; no `product-dev` or `main` automatic merge. Normal revert/close PR34 only by owner decision.
- Progress: before and after this review W8 canonical **3/8**, MVP **0/11**, IV **0/7**, development weighted **HESAPLANAMADI**, because no new actual Windows functional/full integration and no approved denominator. G1 evidence added is a **source/API/public-metadata research delta only**.
