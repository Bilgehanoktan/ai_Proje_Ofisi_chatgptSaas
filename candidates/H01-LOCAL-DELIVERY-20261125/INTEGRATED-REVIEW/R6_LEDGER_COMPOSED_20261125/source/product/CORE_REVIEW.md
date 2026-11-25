# Draft.3 — çekirdek inceleme, NOT_RUN
Kaynak: v140 (v135 hedef, UI-03/05/06/07/08, BE-03/04, D07/D14/D15, T1/W-A/PEP, IV); v138 ve v139 sınırları değişmez. Bu dosya tasarım oracle'ıdır; gerçek TEST sonucu değildir.

| ID | İncelenecek örnek | Beklenen (çalıştırılmadı) |
|---|---|---|
| C3-01 | Kat/oda sınır ihlali veya çakışma | ROOM_OVERLAP_OR_BOUNDS |
| C3-02 | Aynı istasyon konumu veya gerçek instance | STATION_INVALID |
| C3-03 | Koridor rotası (2,0) → (2,5) | 6 nokta, yalnız walkable |
| C3-04 | Kapalı başlangıç/hedef | route = null |
| C3-05 | Avatar instance yok | RESERVED |
| C3-06 | Bilinmeyen/stale avatar, sahte proof | UNKNOWN/UNVERIFIED; asla VERIFIED |
| C3-07 | Örnek DAG | plan; draft+research; merge; qa; iv; release (6 dalga) |
| C3-08 | Eksik dependency | DEPENDENCY_MISSING |
| C3-09 | Döngü | DAG_CYCLE |
| C3-10 | QA/IV atlama, üretici yan dalı | QA_OR_PRODUCER_BYPASS / IV_BOUNDARY_MISSING / RELEASE_BYPASS |
| C3-11 | Geçerli örnek plan | her task HOLD, admission DENY, run_id null |
| C3-12 | Üç örnek UI olayı | SAMPLE, last_seq=3, floor-2; verified=false |
| C3-13 | Birebir duplicate | DUPLICATE_IGNORED |
| C3-14 | Aynı ID farklı içerik / aynı sıra farklı ID | EVENT_ID_CONFLICT / SEQUENCE_CONFLICT; RESYNC_REQUIRED |
| C3-15 | Sıra boşluğu / yanlış tenant / yanlış revizyon | RESYNC_REQUIRED; sonraki olaylar SNAPSHOT_REQUIRED |
| C3-16 | Yanlış istasyon/kat | PAYLOAD_INVALID |
| C3-17 | Sahte grant, epoch, lease, budget | DENY; dispatch_allowed=false; provider_called=false |
| C3-18 | DisabledT1.commit | PermissionError; fiziksel DB yok |
| C3-19 | GET /demo/v1/core/preview | sample ve iki türetilmiş read-model; response şeması inceleme |
| C3-20 | Frontend gap örneği | sıra 2 atlanıp 3 görülürse RESYNC_REQUIRED; seçim gizlenir |
| C3-21 | Phaser kat/zoom değişimi | önceki game destroy; render ve kaynak tüketimi inceleme |
| C3-22 | Offline HTML | CSP; dış fetch yok; etkileşim ve klavye inceleme |

## Açık üretim sınırları
- DAG, yalnız RESEARCH örneği; görev lifecycle, scheduling, retry, concurrency, gerçek agent grant yok. QA ve IV rol etiketleri bağımsız güven kökü kanıtı değildir.
- Event Store: değişmez tuple ve yerel örnek replay. Global ordering, gerçek DB lock, transactional CAS, idempotency fence, outbox, audit, SSE, restore veya W-A implementasyonu değildir. DisabledT1 dışında gerçek writer yok. Üretim T1 tek local transaction; dış provider etkisi transaction dışında ve UNKNOWN reconciliation ayrı.
- Security: deny-only fonksiyon, gerçek PDP/PEP veya güvenlik kabulü değildir; sahte referanslar hiçbir zaman allow oluşturmaz. API gerçek auth/tenant isolation sağlamaz; sadece sabit demo. Gerçek service bind/hosting yetkisiz.
- Office: 6×6 kat layout, 4 oda + 4 rezerv, ikinci kat boş. BFS görsel yürüyüş hücrelerinde; gerçek kapı/duvar/çok katlı transfer grafı ve sprite animasyonu yok. SVG ve Phaser farklı görsel adaylar. Ajan yok; avatar projection kısıtlı; IV proof doğrulama yok.
- FE, fixture ile çalışacak şekilde taslak; event paneli backend algoritmasının çalıştırılmış sonucu değil. Response schema hazır, hiçbir schema validator çalıştırılmadı. Canonical KS/NS değil.
- Bütün C3 oracle'ları taslak; NEG-01..30, UX-01..24 veya F0/F3 yerine geçmez.
