# MI-P0 — Merkezi gerçek kanıt / sürüm geçişi engel kontrolü (20.11.2026)
**Durum:** REVIEW ONLY / FAIL-CLOSED / NO RELEASE AUTHORITY. **Hat:** P10 / MI-P0 (entegrasyon ve test kanıt koordinasyonu). **Görev sahibi:** merkezi entegrasyon koordinasyonu. PR #19/#20/#21/#22/#23/#24/#10 sahipleri ve kaynakları değişmedi.

## Başlangıç ve kanonik pin
- Proje kuralları: yüklenen `AI_Company_OS_YENI_PROJE_TALIMATLARI.txt` (14.11.2026) gözden geçirildi. Güncel `docs/master-integration/WORKING_STANDARD.md`, `progress/MASTER_INTEGRATION_CURRENT.json`, ayrı `REPORTING_STANDARD_20261118.md`, Design Master, sekiz faz planı ve devrin geçerli kaynak kayıtları kullanıldı.
- Kaynak: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, ürün **553 dosya** / manifest **552 girdi**, manifest blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`, ürün ağacı `f4cdcf68115917ab69ba6441414539fe32a59369`. Bu dal `main` veya kabul edilmiş ürün **değildir**.
- İlerleme: tüm sistem geliştirme % **HESAPLANAMADI** (10 grubun 0/10 sahip onaylı paydası; 315 taslak aşama yuvası). Tasarım 15 / kaynak 35 / fonksiyonel 20 / entegrasyon 20 / nihai kabul 10. Core **12/16**, UI **21/40**, MVP **0/11**, IV **0/7**, W8 operasyon **3/8** (ürün yüzdesi değil). Bu turda ürün kabul delta **0 yüzde puan**.
- Önceki genel pano R1, yalnız beş PR ve eski PR22 SHA'sını gösteriyordu; bu tarihsel kanıt **saklanır**, R2 ek kesit ile PR23, PR24 ve gerçek başlıklar eklenir.

## Neyi, neden, nerede, nasıl değiştirdik?
| Yer | Ne / neden | Tip |
|---|---|---|
| `scripts/governance/verify_release_readiness.py` | Source, manifest, 10 grup / 24 alan / 11 MVP, sabit PR head, owner ve bağımsız test kapılarında yanlış READY sonucunu fail-closed engelleyen stdlib CLI | **Yeni denetim kodu, ürün kodu değil** |
| `scripts/governance/test_verify_release_readiness.py` | 20 yerel sentetik negatif/pozitif kanıtı ve CLI çıkış kodlarını test eder | **Yeni yerel guard testi** |
| `progress/MI_P0_RELEASE_BLOCKERS_20261120.json` | 7 aktif sahip/QA PR head'i, 9 release kapısı, gerekçeli HOLD/FAIL/NOT_RUN | Kanıt anlık kesiti |
| `progress/PROGRAM_GLOBAL_SNAPSHOT_20261120_R2.json` | R1'i değiştirmeden 23/24 ve yeni 22/21/24 SHA'sını, QA riskini ve 24 alan/11 MVP bağı korur | Türetilmiş pano R2 |
| `docs/master-integration/MI-P0-RELEASE-EVIDENCE-GATE-20261120/LOCAL_UNITTEST.log` | 20 özgün guard testinin gerçek yerel stdout'u | Test kanıtı |
| Bu belge ve `EVIDENCE.json` | Mimari, dosya/simge/API/DB/bağımlılık kataloğu, test kapsamı, bakım/onarım, kaynak pin, devralma, rollback | Teknik katalog/devir |

### Yeni kod teknik kataloğu
- Python stdlib, ağ erişimi **yok**. `audit(current,snapshot,evidence)` saf giriş veri doğrulama; `_object`, `_sha`, `_pairs` kapalı varsayımlı veri doğrulayıcılar; `main(argv)` salt-okunur CLI ve isteğe bağlı rapor JSON çıktı.
- Giriş: `MASTER_INTEGRATION_CURRENT.json`, `PROGRAM_GLOBAL_SNAPSHOT_20261120_R2.json`, `MI_P0_RELEASE_BLOCKERS_20261120.json`. Çıkış: JSON `VERIFIED_HOLD` veya yalnız **ayrı sahip incelemesine uygun** tanısı. `release_approved` her zaman `false`. **Bu araç güvenlik yetkilendirmesi ve bağımsız IV değildir.**
- Karar: CLI varsayılan 0 = dosyalar geçerli biçimde değerlendirildi; **release PASS anlamına gelmez**. `--require-review-eligible` ile engel varsa 2; eksik/stale/şema uyumsuzluğu varsa 3 (fail-closed).
- Ürün dosya/sınıf/fonksiyon/API/HTTP/DB/şema/olay/sözleşme/bağımlılık ve güvenlik politika değişikliği **0**. CI workflow, secret, grant, prod, auto merge, main değişikliği **0**.

## Bilinen kritik negatif bulgular
1. **Office:** PR #22 eski doğrulamada 6/6 local PASS; bağımsız PR #23 aynı eski owner head'de **0/3 yeni negatif FAIL**, `fetch/read/cancel` abort'a rağmen askıda kalabiliyor. PR #22'nin daha yeni SHA'sı için bu üç testin tekrar koşulduğu **kanıtlanmadı**; *en yeni head de başarısız* diye iddia edilmez. Gate: **HOLD**.
2. **G7 / ORG:** PR #19 CI 72/72 D0 başarılı ama G7 tarihsel ORG fikstürünü kullanıyor. PR #24, mevcut `product` OperationsStore'u dayatan runner için 16/16 **helper** PASS; yedi özgün testin mevcut store üzerinde koşumu **0/7 NOT_RUN**. Gate: **HOLD**.
3. **W8:** PR #20 frozen npm yardımcı yerel 19/19; özgün C04 `NOT_RUN`, C05 `HOLD`, C06–08 `NOT_RUN`. Paket zinciri/onay olmadan tam ürüne geçme.
4. **Güvenlik:** PR #10 Option A sadece mimari karar; root/issuer/sink bağımsız owner, PostgreSQL protected COMMIT, restore/idempotency ve IV 0/7 bekliyor.
5. **Manifest:** 553 `27b4eb...` ve PR19 562 `566b721...` birlikte kayıtsız bağlanırsa `U3_MANIFEST_HOLD`; PR #21 manifest guard sahibi, bu araç onun kaynak koduna dokunmaz.

## Gerçek test ve kaynak bütünlüğü
- Yerel `python -B -m unittest -v test_verify_release_readiness` **20/20 PASS**, 0 skip/0 error, `py_compile` PASS. Testler *sentetik input/guard* kapsamındadır; asıl ürün, bağımsız IV, GitHub Actions ya da yeni W8 koşumu **değildir**.
- Kod SHA256 `0753c8cbf6f8baf55cc08f924847f91904110f233ab2d6e8294627db3b1dcb8e`; Git blob `7607846daa12f164e59ba09b8f32304e9a0e281d`.
- Test SHA256 `f4a13c6daf5c1944b2e14f93c8ac9b04644b68f9005411c81801a1b81d107f05`; Git blob `d27965c3fb1563c57b7d5da90e1c3572802c161c`.
- Log SHA256 `7467de59beb905d3201f8271c8dc7210eb62c7aebb6e256b8d34e32ff6530c63`; Git blob `e56c415e566bb50370329fd238a53fb586bc3ccc`. Üçü GitHub geri okumada byte-exact doğrulanır.
- Gerçek GitHub JSON anlık kayıtları ayrıca salt okunur incelendi; **GitHub üzerindeki yeni Python CLI'nin özgün ürün/W8/PG zinciri çalıştırılmadı.** Kanıtı genişletme.

## Tekrarlanabilir kullanım (ağsız)
```bash
python -B -m unittest -v scripts/governance/test_verify_release_readiness.py
python -B scripts/governance/verify_release_readiness.py \
  --current progress/MASTER_INTEGRATION_CURRENT.json \
  --snapshot progress/PROGRAM_GLOBAL_SNAPSHOT_20261120_R2.json \
  --evidence progress/MI_P0_RELEASE_BLOCKERS_20261120.json \
  --require-review-eligible
```
Bu durum için exit **2 / VERIFIED_HOLD** beklenir (gerçek immutable branch'in exact dosyaları ile birleştirilmiş yerel checkout üzerinde çalıştırılmalı). Her kaynak veya owner SHA değişiminde yeniden kanıt toplanmalı; sadece hash'i güncelleyip PASS yazma.

## Hata teşhisi, bakım, genişletme, geri dönüş
- Çıkış 3: Farklı SHA, eksik sahip PR, imzasız/eksik kriter, dosya biçimi veya beklenmeyen durum; önce sahibi/snapshot/manifest commit'i eşleştir ve gerçek kaynağı tekrar çek; geçmişi yeniden yazma.
- Çıkış 2: Kanıt tutarlı fakat gerçek engeller vardır; önce karşılık gelen PR sahibine müdahale gerektiren dar olguyu ilet, diğer PR'a doğrudan commit yapma.
- Yeni ürün SHA veya onaylı yeni kriter tabanı çıktığında kontrollü yeni R3/sürüm; eski 553/315 sabitleri bir owner kararı ve regresyon olmadan otomatik yükseltilmez.
- Rollback: taslak PR'ı kapat veya yalnız altı **yeni izole review yolu** için normal revert. `integration/product-dev`, diğer taslak PR'lar, `main`, API/DB/güvenlik yetkileri korunur.
- Sıradaki gerçek ürün işi: MI-01 C04→C05→C06-C08; MI-05 son PR22 üzerinde bağımsız 3 negatif ve özgün tarayıcı; MI-04 PR24 ile özgün G7 7/7 current ORG; MI-02 bağımsız root/sink ve protected PG/IV. Görev sahipleri zaten aktif, tekrarlama.

**Yürütme/CEO kararı:** Yeni bir H01 güvenlik/deploy/CI onayı varsayılmadı. Sahip onayı eksik maddeler HOLD kalır; yeni karar sorulmadı.
