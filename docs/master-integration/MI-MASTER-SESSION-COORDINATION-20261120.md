# AI Company OS — Master Integration / sohbet sorumluluğu ve çakışma denetimi
**Tarih:** 2026-11-20  
**Durum:** COORDINATION_ONLY / OWNER_REVIEW_HOLD / NO_PRODUCT_PROMOTION  
**Kaynak:** planning/master-integration-governance @ 0ff231e0794ebe14aade13c40e0e89bc215fb58a (başlangıç referansı)  
**Ortak ürün:** integration/product-dev @ 8a3b05aadd32b214f3f8988fc9c793f853fbe3d0 (505 ürün kaynağı / 504 manifest kaydı).

## Karar / yetki
Kullanıcı, bu sohbeti **Master Integration & Release Management** için koordinasyon hattı olarak kullanmayı kabul etti. Bu yalnız kaynak/kanıt/sahiplik uzlaştırma, görev kuyruğu, entegrasyon hazırlığı ve devir yönetimi talimatıdır. Doğrudan ürüne merge, otomatik CI veya geniş CI izni, gerçek IAM/grant, dış etki, harcama, main/PROD, bağımsız IV kabulü vermez. Mevcut H01 PR #4 / PR #6 dar CI istisnaları değişmez. Güvenlikte D-03/D-04 **Option A** yalnızca seçilmiş mimari yöndür.

## Aktif iş sahipleri ve tekrar iş önleme
| Kayıt | Sahip iş | GitHub incelemesi | Bu sohbetin sınırı |
|---|---|---|---|
| PR #7 | MI-505→539 kaynak farkı, manifest/kanıt uzlaştırması | draft; source 1a8bb515486d907eab98d8a5a928c0c300158684 | Aynı 49 yolu yeniden analiz eden ayrı görev açma; owner kararlarını ve merkezi kayıt çatışmasını koordine et |
| CTL-01 | ORG/G9 `durable_ops.py` 41 satır additive fark ve 539→553 manifest | governance @ 0ff231e; owner HOLD | 14 ürün yolunu veya G9 fonksiyonlarını yeniden yazma |
| PR #8 | GATE02 A1 bağımsız yetki root/issuer/custody/restore/sink sahip incelemesi | draft; 0e477fa71e56b4504fde1db173f8633028265440 | Mimari A kararını tekrar açma; issuer/grant/PG kabulü olduğunu iddia etme |
| PR #6 | Özgün Core–OperationsStore 10 sentetik SQLite testi | draft; 4c0f88e08450ba9ad0e51640737531a432afd383 | 10 test yeniden üretilmez; owner provenance ve strict PG ayrı |
| PR #5 | Core–OperationsStore statik audit/pozitif test devri | draft; review-only | PR6 ile çakışan testi yeniden geliştirme |
| PR #4 | MI-10 sınırlı D0 CI / SSE tanılama | draft; f98da5ab0cef72e87b15878499baceeb15909005 | Yeni workflow/izin üretme; tam W8 ve özgün native U3 ayrı |

## Çakışma ve kaynak pin değerlendirmesi
1. **Aynı dosya yazarı riski:** PR #7 ve PR #8 aynı `progress/MASTER_INTEGRATION_CURRENT.json` dosyasını değiştiriyor. PR #7 ayrıca `progress/MASTER_INTEGRATION_PARTIAL_PROGRESS.json` dosyasını düzenliyor. Kaynak sahipleri ayrı; mevcut governance HEAD korunarak tek-yazıcı sıralamasıyla değişiklikleri *cherry-pick yerine içerik bazlı* gözden geçirmek gerekli. Draft PR'ların hiçbiri otomatik merge edilmeyecek.
2. **505→539:** Ortak aday @ `4035d1a884362dae56a60d91358ea6e8e7dc0cdd` (539 / 538 manifest). Önceki GitHub karşılaştırmasında 505 tabanından 49 `product/` yol farkı görüldü. Bu değişiklikler kabul edilmiş ürün aktarımı değildir; PR7 kaynak/owner kanıtı kullanılacak.
3. **539→553:** Core/ORG adayı @ `d6b82dc412b7bb0f048ece2fd43fe83f6627cc59` (553 / 552 manifest). CTL-01 readback: 14 yeni ürün yolu, eski 538 manifest girdisi aynen korunmuş, kaynak manifesti değiştirilmiş. `durable_ops.py` özgün G9 referansına göre 41 yeni satır içerir; G9/ORG sahibi onayı ve bağımlılık testleri açık.
4. **Test:** PR6 son GitHub run #44623379375 SUCCESS, aynı özgün 10 sentetik testin tekrarı; yeni benzersiz test sayısı 0. PR4 run #44620987573 3/3 SUCCESS; 17/17 SSE tazelik QA, tanısal build/browser kapsamı; tam kaynak W8 zinciri ve native U3 kabulü açık. Tekrarlar % veya kabul arttırmaz.

## Kilitli entegrasyon sırası / mevcut görevler
| Sıra | Kapı | Mevcut sahip | Kapanış için beklenen |
|---|---|---|---|
| 1 | Kaynak uzlaştırma ve çakışma | PR7 + CTL01 + Core/ORG/W8 sahipleri | 49 yolun sahip kararı; 14 ek dosyanın exact pin/dependency review; iki PR'nin merkezi JSON değişikliklerinin tek-yazıcı uzlaştırması |
| 2 | MI01 / W8 | Unified / MI01 / MI10 | özgün tam prepare-install-test-smoke, frozen lock/wheelhouse fingerprint ve native U3 browser kanıtı |
| 3 | GATE02 / A1 güvenlik kökeni | PR8 + D4/IAM/ORG/MI02/MI03 | bağımsız root/issuer/member/role/assignment/custody ve restore/sink kararları; 0/8 IV negatif kabul henüz NOT_RUN |
| 4 | GATE01/03/04 & PostgreSQL | MI02/03/04 + Memory sahibi | G2/G9/0214 özgün testler, strict PG/RLS/fencing ve restore zinciri; sentetik D0 yerine geçmez |
| 5 | Kanonik ürün aktarma kararı | Master Integration + yetkili ürün sahibi | tek base/head SHA, manifest/pin, API/DB/symbol, tam W8, owner yazılı onayı, rollback; izinli ayrı transfer; **şu anda HOLD** |

## Geliştirme, ürün kabulü, teknik katalog
- Ölçüm standardı: tasarım **%15**, kaynak **%35**, fonksiyonel **%20**, entegrasyon **%20**, nihai kabul **%10**. 10 kapsam grubunun onaylı paydası olmadığından genel geliştirme **HESAPLANAMADI** (önceki/güncel/delta = null).
- Bu tur: **ürün kodu 0**, yeni ürün test koşumu 0, yeni kanonik kabul 0, ilerleme artışı 0. Core **12/16 (%75)**; UI **21/40 (%52,5)**; birleşik MVP **0/11 (%0)**; bağımsız güvenlik kabulü **0/7** (ayrı kapsam). MI03 kayıtlı geliştirme **%42,5**, MI08 **%45**; bu turda değişmedi.
- Yeni sınıf/fonksiyon/API/DB/event/dependency yok. G9/ORG değişikliklerinin katalog/bağımlılık sorumluluğu CTL-01 mevcut kaydında; bu doküman yalnız **merkezi sahiplik, kanıt, iş sırası ve devir** indeksidir. Design Master ve 8 fazlı ürün planı değiştirilmedi.
- Önceki hat kaynakları, commitleri ve kararları korunmuştur; kaynak transferi veya ürün manifesti yazımı yapılmadı.

## Arıza teşhisi, geri dönüş ve sonraki tur
- Olası hata: GitHub draft PR'larında merkezi JSON içeriğinin eski revizyonunun üzerine yazılması. **Teşhis:** base/head ve her JSON'un revizyonunu karşılaştır; `git diff` düzeyinde anahtar kayıplarını kontrol et. **Yöntem:** aynı merkezi yol için tek yazıcı, owner onayından sonra mevcut HEAD'e elle yapısal uzlaştırma; eşleşmeyen kaynak pinlerinde HOLD.
- Kanıt çakışması: Aynı 10/10 veya 42/42 tekrarı yeni test ve kabul olarak sayma; gerçek PostgreSQL veya IV yerine D0 kullanma.
- **Rollback:** Bu governance-belge ekinin normal revert'i; değiştirilen kaynak/ana dal yok. Force push, PR auto-merge, source overwrite yok.
- **Bir sonraki merkezi görev:** PR7 ve PR8 dosya/anahtar çakışmasının owner-inceleme kararını topla; 505→539→553 sahiplik imzalarını ve MI01 W8 eksik kanıtlarını tek geçiş matrisi altında izle. Uygun ürün aktarımı için ayrı yetki ve sahip incelemesi şarttır.

**Bağlantılar:** [PR #7](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/7) · [PR #8](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/8) · [PR #6](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/6) · [PR #4](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/4).
