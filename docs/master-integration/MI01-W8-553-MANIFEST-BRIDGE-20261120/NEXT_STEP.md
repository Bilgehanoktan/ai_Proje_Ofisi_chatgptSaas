# Next validated gate

MI-01 owner: inspect `review/mi01-w8-553-manifest-bridge-20261120` commit `ebee7053f55e9c3dd1c70053a2c3244929723906` on source 553 `a80932b6d5e99667889dfaa25b682feb267c6cba` before any use. The bridge is only a manifest-binding compatibility candidate.

1. Independently obtain exact 553 file archive + fingerprint with source owner; confirm old W8 harness and all unchanged 552 manifest records.
2. Exact W8 original `audit` using reviewed bridge; output not yet captured.
3. Original W8 `prepare` create `python.lock`, `REVIEW.json`, hash each wheel; no transient unreviewed locks.
4. Obtain dependency owner supply-chain review/approval (S03-S06); otherwise stop.
5. Then original `install` → `test`/Next production build/TS → `smoke`/native Chromium and 52 captures, collect reproducible logs. No new CI/PR workflow scope without approval.
6. Only then reopen isolated source promotion review PR14 and downstream PG/IAM/IV gates; no production activation before acceptance.

Nothing on C04-C08 is called PASS here.
