# W8 gerçek yürütme kapısı — 20.11.2026

## Amaç, kaynak ve teknik gerçeklik

Kullanıcı dört işlemi sırasıyla istedi: W8 özgün build/browser; sahiplerce onaylanmış G2/G9/Office/proxy kaynaklarını tek ürüne entegrasyon; bağımsız root/issuer/sink ve korumalı PostgreSQL negatifleri; 11 MVP kabul koşulu. **Bu çalışma tamamlama iddiası değildir**; yürütme başlatma girişimlerinin gerçek kanıtlarını ve engelleri aynı sürümlü kaynakta korur.

Referans: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, 553 dosya, 552 manifest, blob `27b4eb5816265d4e6e6d2458acb6220db7dd0c76`. Aktif tek-yazıcı sahipleri: W8 PR20, G2/G9 PR19, Office PR22, Proxy PR26, dört-proxy aday PR29, G7 gerçek ORG PR24, release denetimi PR25, security PR10. Hiçbirine kaynak müdahalesi yapılmadı.

## Gerçek deneme ve arıza teşhisi

| Denenen adım | Fiili sonuç | Sınır |
| --- | --- | --- |
| `git ls-remote https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas.git 254e0188...` | **Exit 128**, `Could not resolve host: github.com` | Kanonik 553 checkout **elde edilemedi** |
| `node -v`, `npm -v`, `python --version` | Node 22.16.0, npm 10.9.2, Python 3.13.5 | Yalnız ortam envanteri |
| `chromium --version` | Chromium 144.0.7559.96 | Tarayıcı mevcut, uygulama/build yok |
| `npm cache ls` seçili `next/react/typescript` pinleri | Eşleşen çıktı yok | Tam npm bağımlılık/tedarik incelemesi değil |
| `psql`, `postgres`, `pg_ctl` | Yürütülebilir dosyalar yok | Korumalı PG testi yapılamadı |
| Kullanıcının eski arşivleri | 29 ve 107 üst seviye kayıt; güncel kök W8/manifest yok | 0155 sürümü 553 yerine **kullanılamaz** |

İndirilemeyen kaynak nedeniyle özgün W8 **C04–C08 NOT_RUN**, native browser **NOT_RUN**. İndirme sırasında hata almak build/test FAIL anlamına da gelmez; bu bir önkoşul **BLOCKED** durumudur. Verilen JSON’da gerçek komut/exit/stderr saklanır. Yerel çıktı SHA-256: `4109f233223bbd4c67af9170297c2bb60e660e0a8058a4a139f8ef4b4af3679e`. GitHub'daki `EVIDENCE.json`, yerel dosyanın birebir kopyası değil, kaynaklı teknik özetidir.

## Mimari, kod ve bağımlılık kataloğu

- Ürün: `product/ai-company-os-frontend/package.json` (Git blob `55a6d296ee20daad2cd36f4552f9feb3f4440ba3`); Next.js 15.5.29, React/ReactDOM 19.1.10, TypeScript 5.9.3. Bunlar inceleme pinleri, kurulup çalıştırılmadı.
- W8: PR20 `tests/integration/w8_unified_u3.py` Git blob `b4043035e75c5a18b7b19a9f18eecfef8e8fe677`; `w8_frozen_npm.py` `257ba8f110508ff30ad03212111cfe8e2299d801`; sabit npm lock `4cd33f437df85d7e74c7946a0999f76adf2e31fe`. Mevcut 19/19 sentetik test, orijinal prepare/install değildir.
- G2/G9: PR19 562/561 ve mevcut 72/72 sentetik D0 CI; bağımsız yetki/kök onayı, korumalı PG ve orijinal mevcut-ORG G7 yeniden niteliklendirme açık.
- Office/proxy: PR22, PR26, PR29 ayrı aday/sahip incelemeleri; `app/api/demo/*/route.ts` kaynak değişiklikleri üzerinde tek ürün kabulü henüz yok.
- Sınıf/fonksiyon/API/DB/event/dependency değişikliği **bu tur 0**. Hiçbir yeni kaynak üretim ya da git workflow değişikliği yapılmadı.

## Sıra ve kabul koşulu

1. **MI01 sahibi** ağ erişimli, izinli izole host'ta 553 tam checkout ile Git/source SHA ve kilitli wheel/npm bağımlılıklarını karşılaştırmalı. C04 gerçek `prepare`; C05 ayrı tedarik/lisans kontrolü. Sonrasında C06/C07/C08 orijinal W8 build+native Chromium raporları ve logları gerekir. Mevcut dar CI istisnası PR4/PR6, otomatik 553 W8 kapsamı vermez.
2. **MI04/MI05/proxy sahipleri** kaynak ve güven sözleşmesi onayından sonra hedef sürümün **gerçek tek manifestini** üretmeli, W8 pinini yalnız o kaynak ağacı üzerinden gözden geçirip tüm regresyon/build/browserı yeniden çalıştırmalı. İlgili PR'ların `draft/HOLD` durumu izin değildir.
3. **Bağımsız güvenlik operatörü** seçilen A mimarisinin issuer, consumed claim ve sink fencing güvenini gerçek ayrı otoriteyle doğrulamalı; izinli PostgreSQL RLS, korumalı COMMIT, restore/replay negatiflerini çalıştırmalı.
4. **MVP** 11 kriter, yalnız bu bütünleşik ve güvenlikten geçen kaynakta test edilerek kabul edilebilir. Şu anda **0/11**.

## İlerleme, kayıt, bakım ve geri dönüş

Ağırlık `15/35/20/20/10`, kriter paydaları `0/10` onaylı; genel geliştirme oranı **HESAPLANAMADI**. Operasyonel W8 3/8; Core 12/16; UI 21/40; MVP 0/11; bağımsız IV 0/7; önceki→şimdi delta 0. Eski testler yeniden sayılmaz.

Sadece işin ortam engeli test edildi; `main`, `product-dev`, workflow, kimlik/grant, production ve müşteri verilerine dokunulmadı. Geri dönüş: yalnız merkezî bu kanıt dosyasını ve ilgili progress işaretini normal revert ile geri al. Arıza giderme: ağ çözümlemesi + tam kaynak SHA doğrulanmadan arşivden veya eksik wheelhouse'dan C04 başlatma; tedarik/lisans onaylanmadan C05'e PASS verme. Bir sonraki sorumlu aksiyon W8 sahibinin **gerçek çalışma ortamında aynı özgün komutu çalıştırmasıdır**, yeni plan/yardımcı PR değildir.

Devir: `EVIDENCE.json`, önkoşul ortam çıktıları; mevcut onay sınırları ve kaynak sahipliği korunur.
