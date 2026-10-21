# Hafta 6 İlerleme Raporu — Çekirdek Modül A: Envanter Yönetimi

**Öğrenci:** İhsan Katkat · 251161036
**Proje:** P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım
**Geliştirilen modül:** Envanter Yönetimi
**Dal:** `hafta-06` (iki depoda da; main'e birleştirildi)

## Yapılan teknik çalışmalar

| Görev (yönergeden) | Durum | Kanıt |
|---|---|---|
| Malzeme/kategori modeli | ✅ | Malzeme Tanımları sekmesi: ekle, güncelle, sil, kategori ekle/sil (yalnızca Yönetici). Ad tekrarı ve birim kontrolü var. |
| Giriş/çıkış | ✅ | `stok_girisi`, `stok_cikisi`, `sayim_duzeltmesi`. Her işlem `stok_hareketi` tablosuna kaydediliyor (003 migration). |
| Stok seviyesi | ✅ | Stok Durumu sekmesi: miktar, kritik seviye, durum (Normal / Kritik / Tükendi), filtreler ve kritik seviye ayarı |

**Backend deposu** (`hafta-06` dalı):
- `003_stok_hareketi.sql`: hareket tablosu, tutarlılık kısıtları, eski stoklar için açılış devri.
- `StokHareketi` ve `HareketTuru` varlıkları; `StokHareketiRepository`; `depo_envanteri` sorgusu.
- `EnvanterServisi`: 8 iş kuralı (K1–K8).
- `OzetServisi`: kritik stok sayısı Depo rolü için yalnızca kendi deposundan.
- Paket sürümü 0.4.0.

**Frontend deposu** (`hafta-06` dalı):
- `frontend/envanter_sayfasi.py`: 3 sekme ve giriş/çıkış/sayım/kritik seviye pencereleri. Hatalar pencerede kırmızı gösteriliyor, pencere kapanmıyor.
- Ana pencere ve `main.py` bağlantısı; oturum bitişinde güvenli kapanış.

**Testler:** 22 yeni test (`tests/test_envanter.py`). Toplam 60 test, hepsi geçiyor.

**Teslim — kısa açıklama:** [docs/Envanter.md](../Envanter.md)

## Haftalık kontrol kriterleri

- [x] Envanter Yönetimi çalışıyor (ekran görüntüleri; `StokHareketiTestleri`)
- [x] Doğrulama/iş kuralları uygulanıyor (K1–K8, her biri testli; ekran: `hafta-06-yetersiz-stok-uyarisi.png`)
- [x] Önceki modüllerle tutarlı:
  - Hafta 4'ün tabloları kullanıldı, yeni tablo migration ile eklendi.
  - Hafta 5'in oturum, rol ve `depo_id` bilgileri kullanıldı.
  - Panel kartı güncellendi.
  - "Stok = hareket toplamı" kuralı eski veride de sağlanıyor (`test_K8_...`, `MigrasyonTesti`).

## Gösterilecek ilerleme (demo sırası)

1. `depo1` ile giriş → Envanter Yönetimi.
   - Depo kutusu kilitli: yalnızca kendi deposu.
   - Kuru gıda kolisi kırmızı (Kritik).
2. Konserve → Stok Çıkışı → 500 → "Yetersiz stok: depoda 148 koli Konserve var…"
3. Battaniye → Stok Girişi → 50 → durum çubuğunda "400 → 450".
4. Sayım Düzeltmesi açıklamasız → hata; açıklamayla → kaydedilir.
5. Hareket Geçmişi sekmesi: kim, ne zaman, ne kadar, neden.
6. `yonetici` ile giriş:
   - Depo seçimi açık (3 depo).
   - Malzeme Tanımları'nda yeni malzeme ekle.
   - Stoğu olan malzemeyi silmeye çalış → engellenir.
7. Backend deposunda `python -m unittest` → 60 test OK.

## Karşılaşılan sorunlar ve çözümler

| Sorun | Çözüm |
|---|---|
| Hafta 5'te kurulmuş veritabanlarında stok var ama hareket yok; "stok = hareket toplamı" kuralı bozulurdu | 003 migration'ı mevcut her stok için "Açılış" hareketi yazıyor. Örnek veri de aynısını yapıyor. Testi var. |
| Python'un `lower()` fonksiyonu "GIDA"yı "gida" yapıyor; aynı kategori ikinci kez eklenebiliyordu (test sırasında bulundu) | Türkçe'ye uygun `tr_kucuk()` karşılaştırması |
| SQLite Türkçe alfabeyi bilmiyor; "Çadır" ve "İçme suyu" listenin sonuna düşüyordu | `tr_sirala()` ile Türkçe alfabe sırası; testi var |
| Kullanıcılar ondalıklı sayıyı virgülle yazıyor ("12,5") | Serviste virgül noktaya çevriliyor |
| Oturum bir işlem sırasında biterse pencere, kod hâlâ çalışırken kapanıyordu | Kapanış `after(0, destroy)` ile o anki olaydan sonraya ertelendi |

## Gelecek hafta (Hafta 7)

Çekirdek Modül B — Bağış Girişi ve İhtiyaç Eşleştirme + entegrasyon.
- Bağış kaydı stoğa Envanter'in "Giriş" yolu ile yansıyacak.
- İhtiyaç talepleri ile depo stokları eşleştirilecek.
- Ara demo.

## Ekran görüntüleri

- `docs/ekran-goruntuleri/hafta-06-envanter-stok-durumu.png`
- `docs/ekran-goruntuleri/hafta-06-yetersiz-stok-uyarisi.png`
- `docs/ekran-goruntuleri/hafta-06-hareket-gecmisi.png`
- `docs/ekran-goruntuleri/hafta-06-malzeme-tanimlari-yonetici.png`

## Yapay zekâ kullanımı özeti

Veri modeli (hareket tablosu), doğrulama örnekleri ve refaktör önerileri için Claude kullanıldı. Doğrulama testlerle yapıldı. Ayrıntı: [AI kullanım günlüğü](../ai-kullanim-gunlugu.md) (Kayıt 10–12).
