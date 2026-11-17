# W5-EXT-07R5 — source-only acceptance handoff
Base ba20cd64eba0f09390818c294ae8894fab9a3acf; unchanged product manifest b0ad4ae6f6caaaf37e20f99f19e551272e16956b. User requested explicit GitHub transfer. Candidate-only branch planning/w5-ext-07r5-acceptance-transfer; no product source modification, API/DB/contract/dependency changes or merge. EXT02–06 sources already exist at the parent; no duplicate product recovery tree. R1–R4 source helpers and exact historical records are transferred, raw package ZIPs and untransferred raw evidence remain in the original local delivery archives; not a claim of complete archive mirroring. Prior progress documents are historical and not overwritten.

## Acceptance sequence
1. Clone authenticated repository on connected disposable DEV. Separate tools worktree at the R5 delivery branch and exact clean source worktree at EXT06. Use core.autocrlf=false. Do not overlay partial sources, edit manifest, downgrade pins, reuse old REVIEW approval or run default startup with live data.
2. Run R1 verifier against exact EXT06 checkout (508 SHA256, 19 core pins, three catalog and projection entries). Run canonical collect_preflight.py after fresh fetch for all relevant owner refs. Inspect common ancestors, manual rows, aliases, modes, shared manifest and contracts. This transfer's remote full-tree namespace check is not execution of the canonical Python on actual Git checkout. Full gate remains NOT_RUN.
3. Recover historical A0F raw npm lock; expected SHA256 036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88. Original A0C evidence ZIP SHA256 1d9267628a6b253840cf4144fa99026729ba64f7f779b1cd6d02493f4672c68c; no raw lock in inspected Git trees. Same package.json blob 55a6d296ee20daad2cd36f4552f9feb3f4440ba3. If raw lock missing, stop; W8 owner must review replacement separately.
4. Run R3 adapter audit then prepare; review actual lock and wheel provenance and new REVIEW.json fingerprint; only then install/test/smoke in isolated DEV. Original adapter pinned to EXT06 commit, so use tools worktree separately. Local artifact screenshots and product build remain NOT_RUN. No CI/main/PROD, real data, external provider effects, paid calls or independent acceptance.

## PowerShell / connected DEV commands
Use a new source root, tools checkout and stage. Git credentials through normal authenticated Git client; never embed them in command or evidence.
~~~powershell
$repo = 'https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas.git'
$src = 'C:\AICOS\ext07r5-source'
$tools = 'C:\AICOS\ext07r5-tools'
$stage = 'C:\AICOS\ext07r5-stage'
git -c core.autocrlf=false clone --no-checkout $repo $src
if ($LASTEXITCODE -ne 0) { throw 'clone HOLD' }
git -C $src -c core.autocrlf=false checkout --detach ba20cd64eba0f09390818c294ae8894fab9a3acf
if ($LASTEXITCODE -ne 0) { throw 'checkout HOLD' }
git -c core.autocrlf=false clone --branch planning/w5-ext-07r5-acceptance-transfer --single-branch $repo $tools
if ($LASTEXITCODE -ne 0) { throw 'tools clone HOLD' }
$r3 = "$tools\candidates\W5-EXT-07R3\integration"
py -3 -B "$tools\candidates\W5-EXT-07\verify_ext07.py" --root $src
if ($LASTEXITCODE -ne 0) { throw 'source HOLD' }
git -C $src fetch origin
if ($LASTEXITCODE -ne 0) { throw 'fetch HOLD' }
# Enumerate all relevant live owner refs, include W5-I/J, D4/D5, ORG06/07/08, UI/Office, Unified.
# Example only; expand to current active owner refs before execution.
py -3 -B "$r3\collect_preflight.py" --repo $src --output C:\AICOS\ext07r5-preflight --ref refs/remotes/origin/integration/unified-u3a-product-acceptance --ref refs/remotes/origin/workstream/w5-j-regression-acceptance --ref refs/remotes/origin/planning/org-08-office-runtime-readback --ref refs/remotes/origin/planning/0229-d4-r6-canonical-readiness
if ($LASTEXITCODE -ne 0) { throw 'preflight HOLD' }
# Inspect all manual rows and ownership. Do not merge. Set $lock to the verified historical raw lock.
$lock = 'C:\aios\premium-a0d\stage\product\ai-company-os-frontend\package-lock.json'
if (!(Test-Path -LiteralPath $lock)) { throw 'LOCK_MISSING HOLD' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $lock).Hash.ToLowerInvariant() -ne '036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88') { throw 'LOCK_HASH HOLD' }
py -3 -B "$r3\w8_ext07r3.py" audit --repo $src
if ($LASTEXITCODE -ne 0) { throw 'audit HOLD' }
py -3 -B "$r3\w8_ext07r3.py" prepare --repo $src --stage $stage --npm-lock $lock
if ($LASTEXITCODE -ne 0) { throw 'prepare HOLD' }
# STOP: inspect fresh REVIEW.json and actual wheel/lock provenance. Only after reviewed approval:
$approve = '<reviewed REVIEW.json SHA-256>'
py -3 -B "$r3\w8_ext07r3.py" install --repo $src --stage $stage --approve $approve
if ($LASTEXITCODE -ne 0) { throw 'install HOLD' }
py -3 -B "$r3\w8_ext07r3.py" test --repo $src --stage $stage --approve $approve
if ($LASTEXITCODE -ne 0) { throw 'test HOLD' }
py -3 -B "$r3\w8_ext07r3.py" smoke --repo $src --stage $stage --approve $approve --chromium '<reviewed Chrome executable>' --frontend-port 17420 --backend-port 17421
if ($LASTEXITCODE -ne 0) { throw 'smoke HOLD' }
~~~
Retain raw logs, reviewed hashes, original DB hashes, W8 and EXT07R3 browser reports and actual screenshots. Local tool tests never prove product browser acceptance. If a pin fails, preserve stage, stop, diagnose rather than repin. Rollback: return to exact EXT06 separate branch; no DB migration or product change. Current gate 2/7; source-only transfer is tracked separately from post-build isolated accepted delivery. Independent 0/10 HOLD.
