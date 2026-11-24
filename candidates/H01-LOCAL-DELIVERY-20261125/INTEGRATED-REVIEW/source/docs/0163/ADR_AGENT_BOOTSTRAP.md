# ADR-0163 — ajan inceleme bootstrap kaynak dilimi
Durum: OWNER_DIRECTED_SOURCE_CANDIDATE_INTEGRATED; normative acceptance HOLD. 0162F ADR'nin genel güvenlik şartları değişmez. Proje sahibi bu dar sentetik kaynak istisnasını açıkça istemiştir. H01'in talimatı gerçek IV makbuzu olarak kullanılmaz.

## Görev akışı
Orchestrator planlar ve kesin scope oluşturur → Research gereksinim/kaynak karşılaştırır → Engineer sadece izinli source adayını yazar → QA oracle, tip/derleme/test kanıtını ayrı üretir → Security scope, grant, epoch, SoD ve olumsuz koşulları denetler → IV Agent ayrı principal/custody altında kanıtı okur → Policy Gateway uygun yetki yoksa HOLD. Gerçek çalışan bağımsız ajan ortamı henüz mevcut değildir. Aynı asistanın rol bazlı incelemesi gerçek ayrı ajan icrası değildir. Runtime policy evaluator, kimlik, receipt ve durable audit sonraki kontrollü tasarım dilimidir. Her ajan görevini kendi kendine kabul edemez; gerçek güvenlik ve yayın kabulü ayrı kalır.

## UI-04/05
Dashboard owns floor, view, display, selection, panel and detail; layout and entry remount resets. OfficePanel controlled; static assets and independent validated demo geometry; JOIN_HOLD. AgentDetail controlled role template; no actual instance. OperationPanel controlled tabs; no live approval or event. Existing page/facade paths unchanged. No API, DB, schema, event or dependency change. Source-only change: four TSX files, three add + one replace, product manifest metadata. Three exact 0162C bytes, Dashboard three presentation strings changed. Backend 0162-C sources remain quarantined. Existing IV unchanged.

## Stop conditions
Unexpected parent/hash/path, scope expansion, non-synthetic data, live join, missing execution permission, attempt to self-approve, any actual effect: HOLD. No auto grant/retry. The policy JSON is a design record, not a functioning runtime gate. Rollback ordinary revert on isolated branch, never force or revive authority.
