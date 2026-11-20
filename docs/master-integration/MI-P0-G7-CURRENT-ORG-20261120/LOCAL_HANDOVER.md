# AI Company OS — G7 current-ORG runner, isolated handover

Date: 2026-11-20. GitHub draft review PR #24: https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/24

## Scope and authority

Independent, fail-closed run adapter for the seven **original unchanged** G7 tests with current product OperationsStore import precedence. This is **not** original G7 product execution, source promotion, IAM grant, protected PostgreSQL, new CI authorization, or product acceptance. Parent canonical product-dev SHA `254e0188998d0d245bd8ee4eb901aead02951a66`; target PR19 immutable checkout `93e6c84db1a061ee914aa2c1d543620404515c0b`.

## Evidence

This container: Python 3.13.5, SQLite 3.46.1. `python -B -m unittest -v test_verify_current_org_g7` 16/16 PASS (zero fail/skip), `py_compile` PASS. Full private 562 source checkout unavailable via GitHub DNS; original seven methods against current ORG: **0/7 NOT_RUN**. Previous owner CI run #44700495037: historical G2 50 + ORG 15 + historical G7 7 = 72/72 PASS, not rerun. GitHub script/test blobs: `48bc0a7c6582defac61a5e346fd923af200d1d88`, `7313cf0160c006eaa5eb7ebc2381712daa26a14a`.

## Authorized rerun

Keep this runner outside immutable checkout. After the source owner supplies exact trusted 562 checkout and pins dependencies, run:

```
python -B verify_current_org_g7.py --root /absolute/path/to/checkout/93e6c84 --json-out /absolute/path/outside/checkout/report.json
```

Exit 2 = HOLD, do not change pins to force success. Exit 0 requires seven real cases executed without skips, with product-root ORG class. Hash and import roots are validated before execution. No workflow or cloud CI permission is included. Validate raw log and owner approval separately.

## Next / rollback

Next owner: MI-03/MI-04 G7 current-ORG full source run and review, MI-01 W8 C04-C08 on 553, G2/G9 source variant choice, independent PG/issuer/IV separately. Close draft PR24/revert isolated review paths to roll back; no `product-dev`, `main`, source owner PRs, permissions or claims changed. General weighted progress HESAPLANAMADI; Core 12/16, UI 21/40, MVP 0/11, IV 0/7, delta 0 pp.
