# ORG-10R1 — Controlled local run

Download exact ORG-10 source archive (not this delta): https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/archive/5c7eb6b148e6e96247682653ff70dccc4a7ba823.zip . Do not extract. Use ordinary non-elevated Windows PowerShell, separate existing ORG-only Python venv with psycopg and psycopg-binary 3.3.9, independently reviewed local PostgreSQL 17.12 distribution (bin/lib/share), no live data. Check actual 55436 ownership with D4/ORG owner. Prior PG clusters/ports remain untouched. Use exact launcher SHA256 below; do not accept changed bytes.

Launcher SHA256: abe425aacb89ee32edb1b89875302556ad25e37ce7b956b43e4503a22c16cbda

Preflight (read-only):
```
& $Py -E -s -B -X utf8 $Runner --archive $Archive --pg-bin $Pg --manifest C:\AIOS\ORG10_RUNTIME_REVIEW_01.json
```
Requires new manifest path. Output exact archive count and RUNTIME_FINGERPRINT. No DB starts. Compare manifest entries against independently reviewed installation/wheel evidence; use this manifest SHA256 as reviewed fingerprint only after actual external review. Do not substitute freshly observed hash for independent review. Review port ownership, source/profile and fresh stage/evidence. No installation or downloads by launcher.

Execution only after review:
```
& $Py -E -s -B -X utf8 $Runner --archive $Archive --pg-bin $Pg --manifest C:\AIOS\ORG10_RUNTIME_REVIEW_01.json --stage C:\AIOS\org10-disposable-01 --evidence C:\AIOS\ORG10_EVIDENCE_01 --reviewed-fingerprint $ReviewedHash --execute-disposable
```
Initdb: choose new admin password, repeat; ORG10 admin password: same. Bootstrap: four distinct synthetic role passwords; repeat as prompted. Owner runner: enter matching role passwords in order. Never paste credentials into chat or commands. No product authority.

On success verify exit 0, 31 checks, supplemental 48 MAINTAIN probes zero granted, exact tree/fingerprint post-check, server stopped, `COMPLETE_REPORT_UNATTESTED`. Send original `pg_report.json`, `launch_report.json` and their SHA256, sanitized bootstrap/start/stop evidence; no credentials, private paths or raw server.log. On failure no automatic retry, preserve stage/evidence and inspect. Do not stop unidentified cluster or delete prior DB. Manual stop requires positively verified data directory, cluster, port, process and admin connection. Do not use 55433/55434/55435. Independent custody, IAM, Core join, product and Office remain HOLD.
