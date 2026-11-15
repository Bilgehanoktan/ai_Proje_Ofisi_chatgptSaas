# EDS-W1-0167A — UI tasarım eki
Statü: A0 tasarım adayı; yeni DOC-REV numarası tahsis edilmedi. Ana mimari değişmedi.
Referans: `Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas` / `recovery/0167-r11-local-mvp` / kaynak entegrasyon commit `f716591be84188d792f8a95ea3995a956208b51d`. R11 handover/CURRENT.md, NEXT_STEP.md, kök ve frontend AGENTS.md okunmuştur.

## Tasarım hedefi ve sınır
Next.js 15.5.9, React 19.1.4, Phaser 3.90.0, TypeScript 5.9.3 pinleri korunur. Yeni paket kurulmadı. Ember V29 yalnız görsel hedef; satın alma ya da kopyalama yok. EDS, 13 mevcut menüyü ve dört çekirdek rolü koruyan merkezi token sistemi önerisidir. Orijinal 8×8 izometrik çizim kavramsaldır; gerçek snapshot ve R11 demo geometrisiyle eşleştirilmez; oda/kat geometrisi kararı değildir. Kat 2 rezervdir; ajan yoktur. 55 OfficeV0 alanında hiçbir değişiklik/ratifikasyon yoktur.

## Güven sınırı
Ürün UI'sı yalnız backend projection tüketir. null → —, stale/unknown → canlı görünüm durur; JOIN_HOLD korunur. QA ≠ IV ≠ release. Policy ve W-A epoch bilinmiyorsa ALLOW yok. Görsel etkileşimler yalnız yerel durumdur, hiçbir komut/harcama/dispatch/release yok. Önizleme CSP ile ağ erişimini kapatır, veri depolamaz. Bağımsız güvenlik kabulü yoktur.

## Fazlar
- EDS-01: R11 paket, dashboard, office scene, UI katalog, snapshot, AGENTS statik incelendi. Bağımlılık sürümü/lisans/güvenlik incelemesi bekler.
- EDS-02: Açık/koyu tema ve tipografi, renk, radius, motion, focus tokenları tasarım adayı.
- EDS-03: Navigasyon, menü araması, ortak kart ve duyarlı kabuk HTML tasarım adayı.
- EDS-04: CEO paneli, null KPI, kaynak ve güven sınırı kartları tasarım adayı.
- EDS-05: İki kat, dört rol şablonu, rezerv istasyon, kavramsal izometrik çizim tasarım adayı. Phaser sahnesi değişmedi.
- EDS-06–10: Ajan ekranı detayları, gerçek DAG görselleştirmesi, diğer modüller, Storybook/Playwright ve API kabulü bekler; prototip katalog görünümü bu fazları tamamlamaz.

## Bağımlılık adayları
Tailwind, shadcn/ui, Motion, Lucide, Recharts, React Flow, TanStack Table, Storybook, Playwright: mevcut manifestte yok; paket seçimi ve sürüm pinleri onaylanmadı, hiçbir paket indirilmedi. İlk entegrasyon için CSS tokenları ve mevcut React bileşenleriyle en küçük dilim önerilir. React Flow varsa yalnız backend kanonik planını görselleştirir. UI animasyonu Phaser ajan yürütmesi değildir.

## Entegrasyon planı
1. R11 commit/manifest yeniden kontrol; yürürlükteki T01 ve dar kaynak kapsamı/PRE bağımsız koşulları çözülür.
2. EDS-02 CSS tokenları + layout kabuğu; mevcut fixture/route ve fallback aynı kalır.
3. EDS-03/04 Dashboard, MetricsStrip, SnapshotStrip, OperationPanel; mevcut 13 navigasyon ve yedi rol sekmesi korunur.
4. EDS-05 OfficePanel ve görsel asset yaklaşımı; kanonik olmayan koordinatlar ayrılır; empty floor, scene failure ve reduced-motion korunur.
5. Ayrı DEV/TEST izni ile dependency lock, typecheck, build, browser, erişilebilirlik ve screenshot regressions; sonuçlar kanıt dizinine.
6. Kontrollü repo aktarımı, katalog, manifest, rollback ve devir; gerçek kabul ayrı.

## Paralel işler
W2 55/20 owner eşlemesi ve projection freshness; W3/W4 terminal/reconciliation, R03 T1; W6 bağımsız key custody; W7 settlement; W8 test oracle ve dependency lock. Bunlar bu UI turunda değiştirilmedi. 0167 → 0168 yerel MVP kritik yolu korunur.
