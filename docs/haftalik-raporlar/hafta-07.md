# Hafta 7 İlerleme Raporu — Çekirdek Modül B: Bağış Girişi ve İhtiyaç Eşleştirme + Entegrasyon

**Öğrenci:** İhsan Katkat · 251161036
**Proje:** P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım
**Geliştirilen modül:** Bağış Girişi ve İhtiyaç Eşleştirme
**Dal:** `hafta-07` (iki depoda da; main'e birleştirildi)

## Yapılan teknik çalışmalar

| Görev (yönergeden) | Durum | Kanıt |
|---|---|---|
| Bağış modeli | ✅ | Bağış Girişi sayfası: bağışçı (mevcut/yeni), depo, kalemler (malzeme, miktar, son kullanma). `BagisServisi` ile 8 kural (B1–B8). Bağış stoğa Envanter'in giriş yolundan girer. |
| İhtiyaç eşleştirme | ✅ | `EslestirmeServisi.oneri / eslestir`: kalan miktar için uygun stok (stok − rezerve), en yakın depodan başlayarak öneri; fazla gönderim engeli; eksik miktar uyarısı; Stok–Talep Dengesi. |
| Durum güncelleme | ✅ | Dağıtım: Planlandı → Yolda (stok düşer) → Teslim edildi; iptalde iade. Talep durumu dağıtımlardan otomatik hesaplanır (005 migration). |

**Backend deposu** (`hafta-07` dalı):
- `005_eslestirme.sql`: dağıtım kalemi → talep bağı; eski dağıtımları taleplere bağlama ve durumları yeniden hesaplama.
- Yeni sorgular: bağış listesi ve detayı, talep + karşılanan, rezerve miktar, dağıtım listesi.
- `BagisServisi` (B1–B8), `EslestirmeServisi` (E1–E9).
- Envanter'e başka modüllerin kullanacağı yollar: `stok_hareketi_uygula`, `miktari_dogrula`, `depo_sahipligi`.
- Örnek veride dağıtımlar taleplere bağlandı; paket sürümü 0.5.0.

**Frontend deposu** (`hafta-07` dalı):
- `bagis_sayfasi.py` (Yeni Bağış, Bağış Geçmişi).
- `ihtiyac_sayfasi.py` (Talepler ve Eşleştirme, Dağıtımlar, Stok–Talep Dengesi).
- Ortak yardımcılar: `ortak.py`.

**Testler:** 26 yeni test (`tests/test_bagis_eslestirme.py`). Toplam 94 test, hepsi geçiyor.

**Teslim — kısa açıklama:** [docs/Bagis-ve-Eslestirme.md](../Bagis-ve-Eslestirme.md)

## Haftalık kontrol kriterleri

- [x] Bağış Girişi ve İhtiyaç Eşleştirme çalışıyor (Şekil 1–6; `BagisTestleri`, `EslestirmeTestleri`)
- [x] Doğrulama/iş kuralları uygulanıyor: B1–B8 ve E1–E9, her biri testli (Şekil 2: gıdada son kullanma tarihi zorunlu; Şekil 4: eksik uyarısı)
- [x] Önceki modüllerle tutarlı:
  - Stok yalnızca Envanter'in yolundan değişiyor; "stok = hareket toplamı" bağış ve dağıtımdan sonra da korunuyor (`test_E7_E8_...`).
  - Yetki ve sahiplik Hafta 5–6 kurallarıyla aynı.
  - Eski dağıtımlar 005 ile taleplere bağlandı (`Migrasyon005Testi`).

## Gösterilecek ilerleme (ara demo sırası)

1. `depo1` ile giriş → Bağış Girişi.
   - Yeni bağışçı + 3 kalem → Kaydet → Envanter'de stok arttı, Hareket Geçmişi'nde "Bağış #no".
   - Konserveyi son kullanma tarihsiz eklemeyi dene → "gıda ürünlerinde son kullanma tarihi zorunlu" (Şekil 2).
2. `kurum1` ile giriş → İhtiyaç Eşleştirme.
   - Talepler öncelik sırasıyla.
   - Hijyen kiti talebini seç → öneri yalnızca Genç Ara Depo'dan 90 paket → "Eksik: 10 paket açıkta kalacak" (Şekil 4).
   - Dağıtımı Planla → talep "Kısmen karşılandı".
3. Fazla gönderim dene: miktarı kalandan fazla yap → "Fazla gönderim" hatası.
4. Dağıtımlar sekmesi: Yola Çıkar → Envanter'de stok düştü; Teslim Edildi → teslim tarihi yazıldı (Şekil 5).
5. Stok–Talep Dengesi: Hijyen kiti "Eksik −10", diğerleri Fazla / Talep yok (Şekil 6).
6. Backend deposunda `python -m unittest` → 94 test OK.

## Karşılaşılan sorunlar ve çözümler

| Sorun | Çözüm |
|---|---|
| Bağış birden çok kalem ve stok girişi içeriyor. Envanter'in giriş metodu kendi transaction'ını açtığı için her kalem ayrı kaydediliyordu; bir kalem hatalı olsa öncekiler kalırdı. | Envanter'e transaction açmayan `stok_hareketi_uygula` eklendi. Bağış servisi tüm işi tek transaction'da yapıyor (B8). Testi var. |
| Talep durumu elle tutuluyordu ve dağıtımlarla çelişebiliyordu. Örnek veride kuru gıdanın 120 kolisi yolda olduğu hâlde talep "Bekliyor" görünüyordu. | Dağıtım kalemi talebe bağlandı. Durum karşılanan miktardan hesaplanıyor. 005 migration'ı mevcut veriyi düzeltiyor. |
| Planlanan ama yola çıkmayan dağıtımlar stoktan düşmediği için aynı malzeme iki talebe birden verilebilirdi. | "Rezerve" kavramı: uygun stok = stok − planlanmış miktar (E3). |
| Örnek veride "eksik" durumu, demo bağışıyla stok arttığı için kayboluyordu. | Eksik örneği için stoğu gerçekten yetmeyen talep (hijyen kiti: 100 talep, 90 stok) kullanıldı. |
| Tablolar ekran ölçeklemesinde (DPI) taşıyordu. | Sütun genişlikleri küçültüldü; dağıtım tarihleri kısa biçimde (gün.ay saat). |

## Gelecek hafta (Hafta 8 — VİZE)

- Modüllerin uçtan uca entegrasyonu ve bilinen hataların giderilmesi.
- Ara sürüm etiketi (Git tag, ör. `v0.5.0`).
- Kısa demo senaryosu; vize sözlüsüne hazırlık.

## Ekran görüntüleri

- `docs/ekran-goruntuleri/hafta-07-yeni-bagis.png`
- `docs/ekran-goruntuleri/hafta-07-bagis-dogrulama-hatasi.png`
- `docs/ekran-goruntuleri/hafta-07-bagis-gecmisi.png`
- `docs/ekran-goruntuleri/hafta-07-eslestirme-onerisi-eksik.png`
- `docs/ekran-goruntuleri/hafta-07-dagitimlar.png`
- `docs/ekran-goruntuleri/hafta-07-stok-talep-dengesi.png`

## Yapay zekâ kullanımı özeti

Bağış ve eşleştirme veri modeli, doğrulama örnekleri ve refaktör önerileri (transaction açmayan stok yolu) için Claude kullanıldı. Doğrulama testlerle ve gerçek veritabanının bir kopyası üzerinde ekranlar denenerek yapıldı. Ayrıntı: [AI kullanım günlüğü](../ai-kullanim-gunlugu.md) (Kayıt 14–16).
