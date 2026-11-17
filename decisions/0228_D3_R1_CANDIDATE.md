# 0228-D3-R1 candidate decision record
Status: design/source candidate, not new CEO approval or canonical decision.
- Choose a dedicated branch and fixture namespace; preserve D1/D2 and all original DDL pins.
- Bind tenant tuple to database-authenticated session_user, require current_user=session_user; deny GUC as sole identity.
- Use separate NOLOGIN owner and separate runtime logins; explicit policies, scoped mutable columns, append-only rows.
- Use new disposable database and port 55433; no shared cluster, no permanent passwords, no main merge, no CI.
- Fixed synthetic scope is a proof fixture, not production entitlement or IAM contract.
- Pending review: bootstrap/credential handling, actual PostgreSQL results, company-stream/T1 binding, independent authority and canonical policy.
