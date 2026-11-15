# EDS kabul planı — NOT_RUN
Bu senaryolar gelecek ürün testleri için oracle taslaklarıdır. Hiçbiri çalıştırılmadı.

| ID | Senaryo | Beklenen |
|---|---|---|
| UI-EDS-01 | 13 menü, klavye ve geri dönüş | Doğru görünüm; görünür focus; yetki değişmez |
| UI-EDS-02 | Açık/koyu ve 320/768/1440 px | Okunabilirlik, yatay taşma yok, WCAG kontrast ölçümü |
| UI-EDS-03 | null KPI / unknown epoch | — ve doğrulanmadı; 0, LIVE veya PASS yok |
| UI-EDS-04 | Kat 1 → Kat 2 | Dört rezerv istasyon → boş kat; seçim temizlenir |
| UI-EDS-05 | Snapshot/layout mismatch | JOIN_HOLD; gerçek placement yok |
| UI-EDS-06 | Geometri sahnesi yüklenemez | Statik fallback ve klavye liste |
| UI-EDS-07 | Reduced motion | Görsel animasyon durur; ajan durumu etkilenmez |
| UI-EDS-08 | Rol şablonu / gerçek instance yok | Instance, görev, yetki uydurulmaz |
| UI-EDS-09 | Boş / stale / geçersiz API verisi | Güvenli boş görünüm; LIVE yok |
| UI-EDS-10 | QA → IV → release | Ayrı statüler; UI komut yazmaz |
| UI-EDS-11 | Build / tip / kontrat | Ayrı izinle gerçek sonuç kaydı |
| UI-EDS-12 | Görsel regresyon ve erişilebilirlik | Ayrı izinle tarayıcı ve ölçüm kanıtı |

Önizleme, ürünün gerçek E2E testinin yerine geçmez. Normatif T01, bağımsız kabul, DEV ve TEST kapıları HOLD.
