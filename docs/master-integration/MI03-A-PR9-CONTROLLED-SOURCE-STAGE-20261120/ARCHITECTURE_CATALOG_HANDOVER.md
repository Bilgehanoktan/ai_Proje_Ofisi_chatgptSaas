# MI03-A / PR #9 — kontrollü entegrasyon kaynak incelemesi ve devir
**20 Kasım 2026.** A tasarım yönü sabittir; bu kayıt gerçek bağımsız root/claim/effect sink uygulaması veya ürün kabulü değildir.

## Ne ve neden
Önceden hazırlanmış ORG/Core/OperationsStore D0 kaynaklarını yeniden üretmek yerine, 539 ürün dosyalı `integration/mi-common-source-review-01@59c0fc505ca286e681ed0965ee317eadf571a806` ile 553 dosyalı `integration/mi03-gate03-org-runtime-closure-01@d6b82dc412b7bb0f048ece2fd43fe83f6627cc59` arasında [taslak PR #9](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/9) açıldı. PR kendi başına birleştirme değildir. `integration/product-dev@8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` ve main değişmedi.

## Nasıl doğrulandı
- 538/538 eski manifest yol/bayt/hash kayıtları aynı; 14 yeni yol, 0 mevcut yol değişikliği, 0 silme. 12 sahip modülü/SQL ve 2 test.
- 14 dosya canlı GitHub kaynağından UTF-8 okunup SHA-256 algoritması (bilinen abc test vektörü ile kontrol edilerek) ve bayt boyutu yeniden hesaplandı: **14/14 MATCH**. Tam liste SOURCE_INTEGRITY.json dosyasında.
- G9 `durable_ops.py` kaynak sürümü 162 satır, aday 203 satırdır. Gerçek satır farkı **41 ek / 0 silme**, G9'ın 162 satırı aynı sıra ve içerikle korunuyor; ek `initialize_assignment_ops`, `record_assignment_review` ve `assignment_review` yalnız D0 içindir. Teknik *additive* olması sahip kararının yerini tutmaz.
- G2 `intent_authority.py` ile ortak D0 arasında 3 eski satırın değişmesi ve IAM ekleri var; bu PR dosyayı değiştirmiyor. Kök otoriteye yükseltme YASAK.

## Kaynak sınırları / arıza teşhisi
1. ORG/Core/G9 sahibi `durable_ops.py` ad alanı, mevcut 162 satırın koruması ve D0 extension uygunluğuna karar verir. Uyumsuzlukta kaynak ayrışması; otomatik merge yok.
2. IAM/Authority sahibi G2 sınıfı ve başka RootPin/claim çağrılarını tek sürüme bağlar; D0IntentAuthority bağımsız root değildir.
3. 4 özgün paketleme/import smoke **NOT_RUN**. SQL 11/11 PASS ve PR6 Core 10/10 PASS **önceki, farklı koşumlardır**. Gerçek G2 50, G9 7, Memory–T1 10, strict PG, W8 ve IV kapıları ayrı açık.
4. `assignment_review` içindeki `ACCEPTED_D0` etiketinin yetki veya yürütme karşılığı yoktur. Bağımsız issuer/claim root/sink, quorum, credential ve restore alanı bulunmuyor. Eski DB+pin restore açığı açık: HOLD.
5. Ürün kaynak sahipleri onay verdikten sonra salt okunur byte/pin diff, temiz exact stage, 4 smoke, 11 SQL regresyonu, G2/G9/0214 ve W8 zinciri; bağımsız A1 custody incelemesi ve 8 negatif test ayrı yetkilendirme/kabul.

## Mimari/teknik katalog
- Mevcut `org_model`, `staffing`, `operations`, `persistence`, `durable_ops`, `assignment_lifecycle`, `org_core_bridge` modülleri yeniden üretilmedi; kaynak adayı olarak PR'a taşındı.
- Yeni HTTP API, PG migration, gerçek runtime grant, kanonik event yayınlama, dış effect sink veya bağımlılık kurulumu **0**. SQLite D0 `op_notice` HOLD korunur.
- A sözleşmeleri `IndependentRootSnapshotV1`, `ConsumedIntentClaimV1`, `SinkFenceAcceptanceV1` **tasarım arayüzüdür**; kodla etkinleştirilmedi.
- Ayrıntılar: `TECHNICAL_CATALOG.json`, `SOURCE_INTEGRITY.json`, `progress/MI03_A_PR9_SOURCE_STAGE_20261120.json`.

## Devir, kabul ve geri dönüş
Önceki/güncel IAM/ORG **%42,5 → %42,5**, fark **0 puan**. Genel geliştirme oranı HESAPLANAMADI. Core 12/16, MVP 0/11, IV 0/7, A bağımsız negatif 0/8 NOT_RUN; hiçbir kabul artışı yok. PR #9 draft, sahip kararı/HOLD. Geri dönüş: PR kapatma veya ileride onaylı birleşim gerçekleşirse normal revert; `product-dev`, `main` ve diğer owner branch geçmişleri korunur. Tüketilmiş claim sıfırlama yapılmaz.

**Tek yazıcı notu:** PR #7/#8 döneminde `progress/MASTER_INTEGRATION_CURRENT.json` ortak yolunda paralel sahiplik uyuşmazlığı kayıtlıdır. Bu tur yalnız güncel GitHub HEAD üzerinden CAS ile atomik bir merkezi kayıt ekler; geçmiş kuyruk/karar/veri silinmez ve mevcut sahiplik tek tarafa aktarılmaz.
