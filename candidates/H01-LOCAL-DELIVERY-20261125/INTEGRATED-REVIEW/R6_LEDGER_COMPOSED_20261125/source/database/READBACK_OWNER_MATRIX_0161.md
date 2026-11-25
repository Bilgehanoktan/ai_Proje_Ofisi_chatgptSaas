# R03/R01 sahiplik boşlukları — HOLD
4 fiziksel tablo: state_mutations, idempotency_fences, transactional_outbox, audit_ledger. 5 eş-tutarlı readback: beşinci UNKNOWN; 7 mantıksal varlık fiziksel tablo değildir. 0161 sentetik admission zarfı bu sayıları değiştirmez.
|İnceleme alanı|Sahiplik adayı|Kanıt|Durum|
|---|---|---|---|
|head CAS / mutation|Runtime + Data|canonical head readback/lock|HOLD|
|admission / lease|Runtime + Security|issuer/lease/fence/epoch|HOLD|
|budget|Finance + Data|limit revision/settlement receipt|HOLD|
|fence/outbox/audit|Data + Runtime + Security|same local tx and authoritative readback|HOLD|
|fifth physical mapping|Data + Runtime|owner-ratified schema/readback|UNKNOWN|
Role names are design candidates, not real appointments. No SQL, migration, DB, writes or acceptance. [R03](../docs/0158/R03_T1_PHYSICAL_MAPPING_0157.md).
