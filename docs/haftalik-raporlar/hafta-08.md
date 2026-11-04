# Hafta 8 İlerleme Raporu — VİZE: Ara Sürüm, Entegrasyon ve Sözlü Hazırlık

**Öğrenci:** İhsan Katkat · 251161036
**Proje:** P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım
**Geliştirilen modül:** Ara sürüm entegrasyonu
**Ara sürüm:** `v0.6.0` (iki depoda da etiketli) · **Dal:** `hafta-08` (iki depoda da; main'e birleştirildi)

## Yapılan teknik çalışmalar

| Görev (yönergeden) | Durum | Kanıt |
|---|---|---|
| Modüllerin uçtan uca entegrasyonu | ✅ | `tests/test_entegrasyon.py`: kullanıcı + veritabanı + envanter + bağış + eşleştirme + dağıtım tek senaryoda. Frontend `tests/test_arayuz.py`: her rol × her sayfa × her sekme. |
| Bilinen hataların giderilmesi | ✅ | 2 entegrasyon hatası (K9 rezerve, K7) düzeltildi, her biri için regresyon testi. Hafta 7'deki 3 bilinen eksik kapatıldı (aşağıda). |
| Ara sürüm etiketleme (Git tag) | ✅ | `v0.6.0`, açıklamalı etiket, iki depoda. `CHANGELOG.md` (semantic versioning). Frontend backend'i `@v0.6.0`'dan kurar. |
| Kısa demo senaryosu hazırlama | ✅ | [Demo-Senaryosu.md](../Demo-Senaryosu.md): 7 dakika, 9 adım, her adımda ne söyleneceği; `demo.bat` ile her seferinde aynı başlangıç verisi. |

**Düzeltilen hatalar:**

| # | Hata | Nasıl bulundu | Düzeltme |
|---|---|---|---|
| 1 | Planlanmış dağıtıma ayrılan (rezerve) stok, Envanter'den Stok Çıkışı ile çıkarılabiliyordu. Dağıtım sonra "Yola Çıkar"da *yetersiz stok* hatası alıyordu. | Uçtan uca senaryo: 180 koli planla → depo görevlisi 200 koli çıkarır → dağıtım yola çıkamaz | Yeni kural **K9**: çıkış en fazla *serbest = stok − rezerve*. Ekranda Rezerve sütunu, çıkış penceresinde "rezerve / serbest" bilgisi. |
| 2 | Yalnızca bir talepte, bağışta ya da dağıtımda geçen malzemenin birimi değiştirilebiliyordu (adet → paket). | Modüller arası veri sahipliği gözden geçirildi | **K7** artık bağış, talep ve dağıtım kalemlerine de bakıyor. |

**Kapatılan bilinen eksikler (Hafta 7 sonu):**
- Panelde modül tablosu yalnızca haftayı gösteriyordu → **Durum** sütunu (Hazır / Kısmen / Planlandı).
- Rota / Dağıtım Planı menüsü "yakında" sayfası açıyordu → artık **Dağıtımlar** sekmesini açıyor (harita Hafta 9).
- Rezerve miktar yalnızca eşleştirme ekranında görünüyordu → Envanter'de de görünüyor.

**Testler:** Backend 101 test (7 yeni), frontend 5 arayüz testi. Hepsi geçiyor ([test çıktısı](../ekran-goruntuleri/hafta-08-test-ciktisi.txt)).

**Teslim edilen çıktılar:** çalışan ara sürüm (etiketli `v0.6.0`) · güncel [AI kullanım günlüğü](../ai-kullanim-gunlugu.md) (Kayıt 17–18) · bu kısa ilerleme raporu.

## Haftalık kontrol kriterleri

- [x] Ara sürüm çalışıyor: `demo.bat` ile temiz kurulum; demo senaryosu baştan sona uygulamada denendi (Şekil 1–4).
- [x] Modüller entegre: tek senaryoda bağış → envanter → eşleştirme → dağıtım → panel (`test_bagistan_teslime_tam_akis`). Rol değişikliği tüm modüllere yansıyor (`test_rol_degisikligi_tum_modullere_yansir`).
- [x] Tüm kodu açıklayabiliyorum: mimari, veri akışı ve AI ile yazılan kod satır satır [sözlü hazırlık](../sozlu-hazirlik/hafta-08.md) belgesinde.

## Gösterilecek ilerleme (vize demosu)

Kullanıcı + veritabanı + çekirdek modüller uçtan uca. Ayrıntılı senaryo: [Demo-Senaryosu.md](../Demo-Senaryosu.md)

1. Yanlış parola → hata; `yonetici` → panel kartları (7 bekleyen talep) ve modül durumları.
2. `kurum1` → Kiğı'nın hijyen kiti talebi: Genç 90 paket, **eksik 10**.
3. `depo1` → 40 paket hijyen kiti bağışı → Envanter ve hareket geçmişi.
4. `kurum1` → öneri artık Bingöl 40 + Genç 60, eksik yok → Dağıtımı Planla → talep Karşılandı.
5. `depo1` → Envanter'de **Rezerve 40**; çıkış denemesi K9 ile reddedilir.
6. `kurum1` → Rota / Dağıtım menüsü → Yola Çıkar → Teslim Edildi; panelde bekleyen talep 7 → 6.
7. Terminal: 101 + 5 test OK; GitHub'da `v0.6.0` etiketi.

## Karşılaşılan sorunlar ve çözümler

| Sorun | Çözüm |
|---|---|
| Her modülün birim testi geçtiği hâlde iki modül birlikte hatalı çalışıyordu (rezerve stok çıkarılabiliyordu). | Belirti → hipotez → izole etme → düzeltme → doğrulama. Senaryo küçültülüp tekrar üretildi, K9 eklendi, regresyon testi yazıldı. |
| İlk entegrasyon testi, önerinin tek depodan geleceğini varsaymıştı ve kırmızıydı. | Kod doğruydu, test yanlıştı. Test öneriden gelen satırlara göre kontrol edecek şekilde düzeltildi. |
| Frontend backend'i `@main`'den kuruyordu; Hafta 9'da yapılan bir değişiklik vize sürümünü değiştirebilirdi. | Backend `v0.6.0` olarak etiketlendi, frontend `requirements.txt` bu etikete sabitlendi. |
| Demo gerçek veritabanında yapılırsa veri kirlenir ve demo bir sonraki denemede farklı sonuç verir. | `demo.bat` ayrı `demo.db` dosyasını her açılışta sıfırlayıp örnek veriyle kurar; gerçek veritabanı dosyasının değişmediği kontrol edildi. |

## Gelecek hafta (Hafta 9)

- Harita/rota API entegrasyonu: depo → ihtiyaç noktası yol mesafesi ve süresi.
- API anahtarı ortam değişkeninde (`HARITA_API_ANAHTARI`); hata/zaman aşımında kuş uçuşu (Haversine) mesafeye geri dönüş.
- Rota / Dağıtım Planı modülünün durumu "Kısmen" → "Hazır".

## Ekran görüntüleri

- Şekil 1 — `docs/ekran-goruntuleri/hafta-08-ana-panel-modul-durumu.png`: panelde modül durumları
- Şekil 2 — `docs/ekran-goruntuleri/hafta-08-dagitim-menusu.png`: Rota / Dağıtım menüsü → Dağıtımlar
- Şekil 3 — `docs/ekran-goruntuleri/hafta-08-envanter-rezerve.png`: Envanter'de Rezerve sütunu
- Şekil 4 — `docs/ekran-goruntuleri/hafta-08-rezerve-cikis-engeli.png`: rezerve stoğa dokunan çıkış reddedilir (K9)
- `docs/ekran-goruntuleri/hafta-08-test-ciktisi.txt`: iki deponun test çıktısı

## Yapay zekâ kullanımı özeti

Entegrasyon hatalarını ayıklamak (uçtan uca test, hatanın yeniden üretilmesi) ve kodu refaktör etmek (modül durumu, dağıtım menüsü, rezerve gösterimi) için Claude kullanıldı. Her değişikliği kendim açıklayabilecek şekilde inceledim; düzeltme yolunu (çıkışı engellemek mi, dağıtımı otomatik azaltmak mı) gerekçesiyle ben seçtim. Ayrıntı: [AI kullanım günlüğü](../ai-kullanim-gunlugu.md) (Kayıt 17–18).

## Ekler — commit bağlantıları

**Backend** — dal: [hafta-08](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/tree/hafta-08) · etiket: [v0.6.0](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/tree/v0.6.0)

- [cb25ae5](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/cb25ae5) fix: rezerve stok envanterden çıkarılamaz (K9); K7 bağış/talep/dağıtımda geçen malzemeyi de korur
- [00b5761](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/00b5761) backend: modül durumu (Hazır/Kısmen/Planlandı) ve sürüm 0.6.0
- [d6867eb](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/d6867eb) test: uçtan uca entegrasyon, regresyon ve komut satırı testleri
- [fd450c0](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/fd450c0) docs: CHANGELOG (semver 0.1.0-0.6.0), vize demo senaryosu, mimariye modüller ve veri akışı, K9
- [04637e1](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/04637e1) docs: hafta 8 sözlü hazırlık, AI günlüğü (Kayıt 17-18), formlar, öz değerlendirme, ekran görüntüleri, test çıktısı, README

**Frontend** — dal: [hafta-08](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/tree/hafta-08) · etiket: [v0.6.0](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/tree/v0.6.0)

- [43932c5](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/43932c5) frontend: envanterde Rezerve sütunu; çıkış penceresinde rezerve/serbest bilgisi
- [e6237ca](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/e6237ca) frontend: panelde modül durumu; Rota/Dağıtım menüsü Dağıtımlar sekmesini açar
- [6f5f215](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/6f5f215) test: arayüz duman testi - her rol, her sayfa, her sekme (5 test)
- [f6d20e1](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/f6d20e1) frontend: demo.bat - gerçek veriye dokunmadan temiz örnek veriyle vize demosu
- [e16dc4f](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/e16dc4f) docs: CHANGELOG (0.1.0-0.6.0), README hafta 8
- [75a5d1a](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/75a5d1a) chore: backend etiketli vize sürümüne sabitlendi (@v0.6.0)
