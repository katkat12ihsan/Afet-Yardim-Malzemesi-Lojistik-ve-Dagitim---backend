# Hafta 9 İlerleme Raporu — Harici API Entegrasyonu: Harita / Rota

**Öğrenci:** İhsan Katkat · 251161036
**Proje:** P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım
**Geliştirilen modül:** Harita ve rota entegrasyonu (Rota / Dağıtım Planı)
**Sürüm:** `v0.7.0` (iki depoda da etiketli) · **Dal:** `hafta-09` (iki depoda da; main'e birleştirildi)

## Yapılan teknik çalışmalar

| Görev (yönergeden) | Durum | Kanıt |
|---|---|---|
| Harita/rota API | ✅ | `backend/entegrasyon/harita_api.py`: OpenRouteService REST istemcisi (`POST /v2/directions/driving-car/geojson`), anahtar `Authorization` başlığında, yanıtın ayrıştırılması ve doğrulanması. |
| Mesafe/rota hesabı | ✅ | `backend/services/rota_servisi.py`: dağıtımın deposundan ihtiyaç noktasına karayolu km, süre ve rota çizgisi; 7 günlük önbellek (`007_rota_onbellek.sql`). Frontend `rota_sayfasi.py`: liste, mesafe/süre, Canvas'ta çizim. |
| Hata yönetimi | ✅ | 9 hata türü (anahtar yok/geçersiz, hız sınırı, zaman aşımı, bağlantı, rota yok, servis hatası, bozuk yanıt); hepsinde uygulama durmaz, kuş uçuşu × 1,3 tahmin ve nedeni gösterilir. İstemci tarafı hız sınırı (30/dk), 429 sonrası 60 sn bekleme, 6 sn zaman aşımı. |
| Anahtarı ortam değişkeninde saklamak | ✅ | `config.ayar`: ortam değişkeni → depo dışındaki `~/AfetLojistik/.env`; depoda yalnızca boş `.env.example`; anahtar URL'de, hata mesajında ve logda yok (testli). |

**Hata yönetimi özeti:**

| Durum | Ne olur |
|---|---|
| Anahtar tanımlı değil | Servise hiç gidilmez; tahmin; sayfanın üstünde turuncu uyarı |
| 401/403 geçersiz anahtar | Tahmin; aynı oturumda bir daha denenmez |
| 429 hız sınırı / istemci sınırı | Tahmin; 60 sn istek gönderilmez / istek hiç gönderilmez |
| Zaman aşımı (6 sn), bağlantı yok | Tahmin; arayüz en fazla 6 sn bekler |
| 404 rota yok, 5xx, bozuk JSON | Tahmin |

**Testler:** Backend 134 test (22 yeni, `tests/test_rota.py`), frontend 6 arayüz testi. Testler gerçek servise gitmez: sahte gönderici ve sahte saatle her yanıt türü; yerel HTTP sunucusuyla gerçek zaman aşımı ve 403. Hepsi geçiyor ([test çıktısı](../ekran-goruntuleri/hafta-09-test-ciktisi.txt)). Gerçek ORS sunucusuyla elle: geçersiz anahtar → 403 → `anahtar_gecersiz`.

**Teslim edilen çıktılar:** çalışan API entegrasyonu · hata yönetimi · [modül belgesi](../Rota-API.md) · güncel [AI kullanım günlüğü](../ai-kullanim-gunlugu.md) (Kayıt 20–21).

## Haftalık kontrol kriterleri

- [x] API anahtarı depoda değil: ortam değişkeni ya da depo dışındaki `.env`; `.env.example` boş; `test_anahtar_depoda_yok`, `test_anahtar_loglara_ve_mesajlara_sizmaz`.
- [x] Hatalar yönetiliyor: 9 hata türü, her biri test edildi; hiçbirinde uygulama durmuyor (Şekil 1).
- [x] Entegrasyon doğru: istek biçimi (koordinat sırası [boylam, enlem], başlık), birim çevirisi (m → km, sn → dk) ve ayrıştırma testli; gerçek sunucuya karşı 403 doğru işlendi. Geçerli anahtarla canlı rota denemesi anahtar tanımlanınca yapılacak.

## Gösterilecek ilerleme (demo)

1. Anahtar tanımlı değilken: `kurum1` → Rota / Dağıtım Planı → üstte turuncu "API anahtarı tanımlı değil" uyarısı.
2. Dağıtım #4 (Genç Ara Depo → Adaklı Konteyner Kent) seçilir → **69,7 km · 1 sa 24 dk**, "Kaynak: Tahmini (kuş uçuşu × 1,3)", kesikli turuncu çizgi (Şekil 1).
3. Anahtar tanımlanınca (`setx HARITA_API_ANAHTARI ...`, uygulama yeniden açılır): aynı dağıtım → karayolu km/süre, mavi rota çizgisi, "Kaynak: Harita servisi"; ikinci seçimde "önbellek".
4. Ana Panel: Rota / Dağıtım Planı **Hazır** (Şekil 2).
5. Terminal: `python -m unittest` → 134 test OK; `tests/test_rota.py` hata türleri.

## Karşılaşılan sorunlar ve çözümler

| Sorun | Çözüm |
|---|---|
| ORS koordinatı [boylam, enlem] sırasıyla istiyor; uygulamada her yerde (enlem, boylam). Ters gönderilince nokta Bingöl yerine Giresun civarına düşer. | Çeviri yalnızca istemcide, tek yerde yapılıyor; istek gövdesi testle sabitlendi. |
| Gerçek servisle hata durumlarını (429, 500, zaman aşımı) istendiği an üretmek mümkün değil; testler kotayı harcar ve internete bağlı olur. | İstemciye sahte "gönderici" ve sahte saat verildi (bağımlılık enjeksiyonu); gerçek ağ yolu için bilgisayarın içinde yanıt vermeyen küçük bir HTTP sunucusu açıldı. |
| Kapalı porta bağlanma testi Windows'ta 2 sn yeniden deneme yüzünden "bağlantı hatası" yerine "zaman aşımı" veriyordu. | İşletim sistemine bağlı test kaldırıldı; bağlantı hatası sahte gönderiyle deneniyor. |
| Hafta 8'de `.env` okumak için python-dotenv planlanmıştı. | Ek bağımlılık yerine 20 satırlık kendi okuyucumuz; `.env` proje klasöründe değil veri klasöründe aranıyor (depoya giremez). |
| Rota listesi açılırken her satır için servis çağrılırsa hız sınırı dolar, sayfa yavaş açılır. | Liste yalnızca önbellekten; servis yalnızca seçilen dağıtım için. Eşleştirme sıralaması bilerek kuş uçuşu kaldı. |

## Gelecek hafta (Hafta 10)

- Yapay zekâ bileşeni: ihtiyaç önceliği, nüfus, bekleme süresi ve stok verisine göre dağıtım önceliği ve rota önerisi.
- İstem (prompt) tasarımı, çıktının doğrulanması (geçersiz/boş çıktıda kural tabanlı öneriye geri dönüş), AI günlüğünde istem ve çıktının belgelenmesi.
- Anahtar: `LLM_API_ANAHTARI` (aynı `config.ayar` yolu); LLM'e kişisel veri gönderilmez.

## Ekran görüntüleri

- Şekil 1 — `docs/ekran-goruntuleri/hafta-09-rota-tahmini.png`: Rota sayfası, anahtar yokken kuş uçuşu tahmin ve uyarı
- Şekil 2 — `docs/ekran-goruntuleri/hafta-09-ana-panel-rota-hazir.png`: panelde Rota / Dağıtım Planı "Hazır"
- `docs/ekran-goruntuleri/hafta-09-test-ciktisi.txt`: iki deponun test çıktısı

## Yapay zekâ kullanımı özeti

OpenRouteService API belgesini çözümlemek (istek/yanıt biçimi, hata kodları, hız sınırı) ve örnek yanıtı incelemek için Claude kullanıldı; istemci, rota servisi, sayfa ve testler birlikte yazıldı. Servis seçimini, anahtarın başlıkta ve depo dışındaki `.env`'de durmasını, tahminin önbelleğe yazılmamasını ve eşleştirmenin kuş uçuşu kalmasını gerekçesiyle ben seçtim. Ayrıntı: [AI kullanım günlüğü](../ai-kullanim-gunlugu.md) (Kayıt 20–21).

## Ekler — commit bağlantıları

**Backend** — dal: [hafta-09](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/tree/hafta-09) · etiket: [v0.7.0](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/tree/v0.7.0)

- [ca9d043](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/ca9d043) backend: API anahtarı ortam değişkeni ya da veri klasöründeki .env dosyasından; harita ayarları
- [ee8db3a](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/ee8db3a) backend: OpenRouteService rota istemcisi - REST, zaman aşımı, hata türleri, hız sınırı
- [66dc151](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/66dc151) backend: migration 007 rota önbelleği, RotaOnbellekRepository
- [41a6e5d](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/41a6e5d) backend: RotaServisi - dağıtım rotası, önbellek, servis hatasında kuş uçuşu tahmine geri dönüş; Rota modülü Hazır
- [72b8772](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/72b8772) test: harita API ve rota servisi (22 test; sahte gönderici + yerel sunucuyla gerçek zaman aşımı)
- [47d8dab](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/47d8dab) docs: .env.example - anahtar ortam değişkeni ya da veri klasöründeki .env; harita ayarları
- [40714e6](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/40714e6) backend: sürüm 0.7.0
- [43c99c5](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/43c99c5) docs: Rota-API, CHANGELOG 0.7.0, mimari entegrasyon katmanı, ER 007, README
- [1444e76](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/commit/1444e76) docs: hafta 9 sözlü hazırlık, AI günlüğü (Kayıt 20-21), formlar, öz değerlendirme, ekran görüntüleri, test çıktısı

**Frontend** — dal: [hafta-09](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/tree/hafta-09) · etiket: [v0.7.0](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/tree/v0.7.0)

- [8934384](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/8934384) frontend: Rota / Dağıtım Planı sayfası - karayolu mesafesi, süre, Canvas'ta rota çizimi, tahmin uyarısı
- [a0f3938](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/a0f3938) frontend: Rota menüsü kendi sayfasını açar; main.py RotaServisi oluşturur
- [cb345f5](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/cb345f5) test: arayüzde rota sayfası (seçim -> rota çizimi, anahtarsız tahmin uyarısı); panelde Rota Hazır
- [fb0e6a5](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/fb0e6a5) chore: backend v0.7.0'a sabitlendi (harita/rota API)
- [29bd83d](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/commit/29bd83d) docs: CHANGELOG 0.7.0, README hafta 9 - rota sayfası, API anahtarı
