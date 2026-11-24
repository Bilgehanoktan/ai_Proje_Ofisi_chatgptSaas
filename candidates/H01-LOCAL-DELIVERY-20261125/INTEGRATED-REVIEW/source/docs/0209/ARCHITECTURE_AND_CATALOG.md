# DOC-REV-0209 — signed memory witness and ordinary T1

Baseline `f832f00bffa4162b1f31a9bd192a5aedd44986fb`; source `9164fe68b545144953ea138c5d9cde3f12a18e12`. 343 product files, 342 manifest entries; all 337 previous non-manifest product blobs retained. Five product files added; no existing runtime module replaced. No canonical API/event/DB migration or dependency version change.

## What / why / how
`memory_witness.py` stores Ed25519-signed canonical records in a separate disposable SQLite store. Monotonic sequence, previous SHA, scope, policy/witness/recovery epochs, expiry and exact SnapshotPin are verified; external expected latest digest and key pin must originate outside both stores. Append uses CAS and triggers; a staged pending target blocks matching old snapshots and cannot be cleared on absence. Reader is read-only, checks separation, signature chain and exact head twice around joint review. Local fixture key/store are not independent custody; append authorization and publication are not trusted production protocol. If all three trust inputs roll back, a match is possible.

`witnessed_mapping.py` binds the original typed intent, joint digest and witness pin without changing transition digest. Explicit single-use RUNNING -> VERIFYING decorator: original lock -> preimage/lease/clock/latest check -> original role writes -> original exact postimage/write-set -> second witness check before receipt. Generic commit, special/terminal/budget-changing transitions rejected. Original six-role mapper and SQL executed with SQLite shim. No provider call, actual reservation ledger proof, mandatory production effect gate, or independent grant.

## Evidence
138 actual selected cases (98 regressions, 23 signed witness, 10 T1 coordinator/session with stand-in, 7 original SQL mapping on SQLite), zero failures/skips. 44 product files +3 exact DDL locally hashed. 55 core lock paths still match; 19 available locally (+11), 36 absent, 29 tests NOT_RUN. [Evidence](../../tests/evidence/TEST_EVIDENCE_0209.json).

## P0 residuals
D-01: mandatory effect boundary and budget/reservation binding HOLD. D-02: independent key/latest pin custody and trusted clock, production anti-restore protocol HOLD. D-03: deliberate witness append after last check but before COMMIT resulted in committed D0 state; no provider effect. Repeated reads alone cannot prove cross-store atomicity. Need durable intent/pending and authoritative fence at actual effect boundary; UNKNOWN is quarantine, no retry based on absence. Full Company Coordination/Terminal Anchor composition, PG13/RLS and full build/browser remain NOT_RUN.

## Maintenance / rollback
Use manifest `02b7b2cdea8ba2d21c14cc2bda2a4107502ae237`, exact source lock and pinned optional cryptography 46.0.4. Verify witness chain and external pin, reject alias, stale epochs, pending, bad signature, time drift. On precommit mismatch original transaction rolls back; on unknown commit use exact historical readback, no blind retry. Restore outside both witness/memory stores; never use a copied local pin as independent authority. Return to 0208 pinned commit for code rollback. No canonical migrations applied. Main, CI, PROD and live permissions unchanged.
