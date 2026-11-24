# 0168 — Local MVP parallel direction / source preparation

Parent: 25ef33730a5bc60c92178ff9226dcb496f376fae. R11 product pin f716591be84188d792f8a95ea3995a956208b51d, manifest blob 337d4fa90bd93b2119da4cd7f6eba193e93d18fe.
H01 asks all nine local MVP items to advance in parallel. Record user execution intent, not independent T01/T06 or DEV/TEST grant. Prior 0167 scope excludes install/runtime and expired. Independent gates HOLD; no PROD, CI, main merge, provider calls, spend or canonical DB mutation.

| Task | Evidence/status | Dependencies |
|---|---|---|
| M01 nine sources | DONE_SOURCE; 9/9 quarantine/target Git blob and base64 match; manifest pins match | none |
| M02 integrity tool | DONE_SOURCE; existing scripts/verify_product.py + Prepare-Local.ps1; clean local full tree preflight pending | none |
| M03 isolated DEV | HOLD; explicit narrow scope and applicable independent receipts | M01/M02 |
| M04 Python/Node install | HOLD; parallel install lanes; pins not transitive locked | M03 |
| M05 backend | NOT_RUN; 134 test candidates; six GET and negative 404 | M04-P, TEST |
| M06 frontend | NOT_RUN; tsc/build/browser | M04-N, TEST |
| M07 FE/BE | QUARANTINE_CANDIDATE; local delta contains fixed loopback Next readback proxy and panel; not in product | M05/M06, source approval |
| M08 agent runtime | HOLD; lifecycle inspection and DisabledModelGateway, no actual dispatch | M03/M05, T1/PEP/custody |
| M09 real tasks | HOLD; local model authorization, runtime, FE and evidence | M07/M08 |

New readback: five schemas and four fixtures byte/base64 and blob parity 9/9. No full 141-entry SHA256 recomputation this turn. Actual product source unchanged. Backend app/api/demo.py six GET, static HOLD. Dashboard fixture-only, plan projection offline. Model gateway disabled; trust signature/custody unproven. 
Local delta delivered separately: three quarantined candidates (route.ts, LocalReadbackPanel.tsx, local_mvp_smoke.py), seven smoke cases NOT_RUN, Python AST only. This GitHub branch records the review direction; those local candidate files are not uploaded here. No product change. 134 product and 24 prior quarantine test candidates NOT_RUN. No runtime test/install/build. Current environment Python 3.13.5/Node 22.16.0/npm 10.9.2, not user Windows PC. Dependency locks absent.
Next: isolated DEV/TEST scope/independent PRE -> pristine source archive preflight -> independent Python/Node lock/install -> parallel backend and frontend evidence -> reviewed readback integration -> actual agent runtime only after authority. Keep historical D4/D5 and 55/20 gaps separate.
Source archive: https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/archive/f716591be84188d792f8a95ea3995a956208b51d.zip
