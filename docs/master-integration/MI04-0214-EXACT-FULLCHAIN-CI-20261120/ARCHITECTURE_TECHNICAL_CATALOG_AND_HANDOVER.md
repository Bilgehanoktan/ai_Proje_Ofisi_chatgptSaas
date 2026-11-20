# AI Company OS — MI-04 / Özgün 0214 tam-zincir testi: tamamlanan D0 kanıtı

**Tarih:** 20.11.2026 · **Durum:** `ORIGINAL_0214_D0_10/10_PASS; SECURITY_HOLD` · **Gerçek kanıt:** [GitHub CI #44695937454](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44695937454), job `136152572204`.

## 1. Çakışma kontrolü / gerekçe
Başka iş hatlarında devam eden MI-01/U3B W8 `prepare/install/test/browser`, MI-10 diagnostik CI, MI-07/08 Windows 344 regresyonu, PR #14 ortak adayın `product-dev` incelemesi ve önceden kanıtlanmış ORG 4+11 testleri **yeniden geliştirilmedi veya koşulmadı**. Merkezi görev kuyruğu MI-04 altında 0214 özgün tam-zincir 10 testini `NOT_RUN` gösteriyordu. Yalnız bu boşluk kapatıldı.

## 2. Kaynak, dosya, sınıf ve API kataloğu
Kaynak aynen `integration/mi-common-source-review-01@a80932b6d5e99667889dfaa25b682feb267c6cba`; 553 ürün dosyası ve 552 manifest girdisi. Dört özgün Git blob SHA'sı CI'de karşılaştırıldı. Tüm 552 kaynak girdisinin byte uzunluğu ve SHA-256 değeri ayrıca kontrol edildi: **552/552 PASS**.

- `product/ai-company-os-backend/tests/test_authority_fullchain_0214.py` — blob `4918027e828e8e72273ee4d6a508cac3aa6e9b59`. `FullChainTests` sınıfı; `setUp`, `invoke`, `claims`, `review`, `committed`, `empty` ve 10 özgün test yöntemi.
- `product/ai-company-os-backend/tests/test_transition_mapping_0194.py` — blob `a4a3827ec4267ce275efe52fe5488e1868502c3f`. Özgün `MappingTests`, `SQLiteConnectionShim`, `SQLiteCursorShim` ve D0 mapping; PostgreSQL kilitleme davranışının kanıtı değildir.
- `product/ai-company-os-backend/app/core/transaction/intent_authority.py` — blob `fa47acd32adb309896f762ec50e47bf26641adbb`. `D0IntentAuthority`, `RootPin`, `execute_authority_fenced_transition`; yalnız restore edilebilir yerel D0 root/claim fixture, bağımsız custody/consensus otoritesi değil.
- `app/core/transaction/fenced_transition.py` — `D0IntentJournal`, `intent_pin`; `app/core/agent_runtime/memory_witness.py` — `D0MemoryWitnessStore`, `MemoryWitnessReader`; `app/engines/memory_engine/snapshot_store.py` — `Snapshot`, `create_store`, `publish_snapshot`. Orijinal 0214 testi bu gerçek ürün modüllerini çağırır.
- Bağımlılık: `requirements-history-signatures.txt` Git blob `b704e3dfd92b43d966dd4c023dab1ab576f57141`, `cryptography==46.0.4`; testin geçici GitHub ortamında `cffi==2.0.0`, `pycparser==3.0`; Python 3.13.5, SQLite 3.45.1. Ürün dependency lock'u değiştirilmedi.

**API/DB/event farkları:** 0 yeni HTTP API, 0 yeni kanonik event, 0 SQL migration veya üretim veritabanı işlemi. Test yalnız disposable yerel SQLite `run.authority.sqlite`, `run.intent.sqlite`, `memory.d0.sqlite`, `memory.witness.sqlite` ve özgün 0194 T1 fixture tablolarını kullanır. Yeni bağımsız root veya effect sink uygulaması yoktur.

## 3. Çalıştırılan gerçek 10 test
GitHub `ubuntu-24.04` üzerinde:

```sh
python -B -m unittest discover -s tests -p test_authority_fullchain_0214.py -v
```

**10/10 PASS** · süre 0,710 s · 0 fail · 0 skip. Kapsam:
1. Concurrent claim yalnız bir original COMMIT
2. Süresi bitmiş lease quarantine
3. Özgün wrapper başarılı D0 COMMIT/readback
4. **Tam eski DB + journal + authority restore ile replay residual — yeniden üretildi**
5. Kayıp COMMIT yanıtı sonrası retry engeli
6. Yalnız journal+T1 restore, authority restore edilmeyince replay engeli
7. Claim öncesi revocation
8. T1 öncesi memory revocation/quarantine
9. Root publisher ile COMMIT yarışının yerel kilitlenmesi
10. Yanlış signature key ile COMMIT reddi

**4. testin PASS olması güvenlik açığının bilerek yeniden üretildiği anlamına gelir.** Eski veritabanı + eski yerel otorite birlikte geri yüklenince ikinci COMMIT gerçekleşir; antirollback çözümü bulunmadı. D-03/D-04 A kararı mimaridir; gerçek bağımsız yönetilen monotonic consumed-claim store ve sink-side fencing hâlâ yok.

## 4. Arıza teşhisi, bakım, geri dönüş ve sınırlar
- Eğer SHA256 veya Git blob farklıysa `SOURCE_PIN_HOLD`; test başarısı başka commit'e taşınamaz.
- Source owner `intent_authority.py` G2 varyantı hâlâ ayrışır; G2 özgün 50 ve G9 özgün 7, W8 native full, korumalı PostgreSQL COMMIT/restore, gerçek IAM/ORG issuer ve A 8 bağımsız negatif durum **NOT_RUN/HOLD**.
- Güvenlik: `authoritative=false`, `dispatch_allowed=false`, `commit_allowed=false` ve dış sağlayıcı çağrısı/harcama **DENY** üretim sınırında. Sentetik 0214 testinde tarihsel COMMIT, gerçek yetki değildir.
- Test amaçlı [PR #16](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/16) **UNMERGED CLOSED**; workflow ortak ürüne veya production'a aktarılmadı. Tekrar koşum için kaynak ve pinleri önce yeniden doğrula, ayrı kontrollü test ortamı kullan.
- Geri dönüş: belge commit'inin normal revert'i veya kayıtların kanıt revizyonu; geçmiş test runner/PR ve özgün commit korunur. Consumed claim geçmişini silme/sıfırlama ve fail-open retry yasak.

## 5. İlerleme, kabul ve devir
Bu tur önceki MI-04 `0214 0/10 NOT_RUN` boşluğunu gerçek **10/10 özgün D0 CI** ile kapatır. Bu testler daha önceki 15 ORG ve 10 CoreOps testlerine **çift sayılmaz**. IAM/ORG tarihsel kayıt **%42,5 → %42,5**; yeni 15/35/20/20/10 ağırlıklı global yüzde için tüm sabit paydalar eksik, **HESAPLANAMADI**. Kanonik Core **12/16**, MVP **0/11**, IV **0/7**, A bağımsız güvenlik **0/8**; ürün kabul değişimi **0**.

**Devir:** MI-01/U3B kendi W8 görevini sürdürür; merkezi PR #14 product-dev incelemesi başka hatta ve birleşim HOLD. MI-04'ün sıradaki teknik bağımlılığı G9/G2 kaynak sahipliğinin çözülmesi ve özgün G2/G9 regresyonu; sonra gerçek PostgreSQL, A1 root/issuer/sink, negatif IV. Bu kayıt yeni bir güvenlik yetkisi veya ayrı owner müdahalesi değildir. Makine kanıtı: `EVIDENCE.json`.
