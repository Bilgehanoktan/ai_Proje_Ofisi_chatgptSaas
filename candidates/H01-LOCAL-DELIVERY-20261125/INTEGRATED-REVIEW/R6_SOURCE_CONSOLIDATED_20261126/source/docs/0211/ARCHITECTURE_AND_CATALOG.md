# DOC-REV-0211 — D0 intent authority adapter

Baseline `b395d1944877128ab1bb7fa6477fc3188841fe57`, source `b5b83e548f2e03c9e7a8c5a3b1a11b00849e5e1d`; 347 product files including manifest (346 entries). Two product paths added; all previous 344 non-manifest entries retained. Source and test Git blobs match locally tested bytes.

## What / why / how
D-03 external reference drift and D-04 journal/T1 restore remain P0. New opt-in `intent_authority.py`: `RootPin`, `D0IntentAuthority.create/publish/claim_and_fence`, `execute_authority_fenced_transition`. Separate disposable SQLite authority DB stores append-only root history and unique scope/binding/transaction claim. Claim commits before T1; second writer reservation rechecks exact root sequence, then holds cooperating publishers until wrapper returns. Failure consumes claim permanently. Existing 0210 binding digest and intent pin are reused; wrapper does not accept arbitrary latest callback. No default live wiring or migration.

Lock order: authority -> 0210 witness -> memory -> T1; a root publication winning the gap after claim causes HOLD; if authority itself is rolled back, replay remains possible. Historical receipts are not current authority. Real independent witness custody, signed monotonic head, clock, budget/reservation/effect gate and recovery protocol remain open. Do not use this fixture for live execution.

## Evidence
10 actual local component unittest cases: nine expected behavior checks and one deliberately reproduced authority-store restore residual; zero errors/skips. Prior 154 cases not rerun. Original wrapper integration, Company/Terminal, PG13/RLS, core29 and full app build/browser NOT_RUN. No independent acceptance. Previous 23 missing local core files all read back via GitHub and matched their exact lock blobs, but not materialized locally. Historical 32/55 local source result retained; fresh session has no exact full checkout. Direct dependency versions differ from locked pins.

## Maintenance / diagnosis / rollback
Inspect roots and claims on a read-only copy; stale root or duplicate scope means HOLD, never reset/delete claims. Source pin `9c85c1a9ccdfbceabb0e341ce7565c87318aa815`. Use existing 0207 runner from pinned full archive; do not weaken locks. If reverting code, return to pinned 0210 commit, keep all authority/intent/T1 evidence, never restore authority to authorize replay. No canonical API/event/DB migrations or new dependencies. 
