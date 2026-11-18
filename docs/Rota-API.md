# Rota / Dağıtım Planı — Harita/Rota API Entegrasyonu (Hafta 9)

**Amaç:** Bir dağıtımın deposundan ihtiyaç noktasına **karayolu mesafesini, süresini ve rotasını** harici bir harita servisinden almak; servis yoksa ya da hata verirse uygulamanın çalışmaya devam etmesi.

| Parça | Dosya | Görev |
|---|---|---|
| Entegrasyon (dış servis) | `backend/entegrasyon/harita_api.py` | REST isteği, yanıtı ayrıştırma, hataları tek türe çevirme, hız sınırı |
| İş katmanı | `backend/services/rota_servisi.py` | Yetki, önbellek, servis hatasında kuş uçuşu tahmine geri dönüş |
| Veri | `007_rota_onbellek.sql`, `repositories/rota.py` | Servisten gelen rotaların önbelleği |
| Ayar | `backend/config.py`, `.env.example` | Anahtar ortam değişkeninden ya da depo dışındaki `.env`'den |
| Arayüz | frontend `frontend/rota_sayfasi.py` | Dağıtım listesi, mesafe/süre, Canvas'ta rota çizimi, uyarı |
| Test | `tests/test_rota.py` (22), frontend `test_arayuz.py` | Her hata türü, önbellek, geri dönüş, anahtar saklama |

## 1. Servis seçimi

| Seçenek | Anahtar | Ücretsiz sınır | Neden seçilmedi / seçildi |
|---|---|---|---|
| **OpenRouteService (ORS)** | Var (ücretsiz hesap) | 40 istek/dk, 2000/gün | **Seçildi.** OpenStreetMap verisi, REST + JSON (GeoJSON), anahtarlı kimlik doğrulama ve hız sınırı var; ders kapsamındaki konuların hepsi gerçek olarak uygulanıyor. |
| OSRM genel demo sunucusu | Yok | Kullanım politikası: yoğun kullanım yasak | Anahtar yok: "anahtarı ortam değişkeninde saklama" çalışılamaz; demo sunucusu üretim için değil. |
| Google Directions API | Var | Kredi kartı ile faturalandırma | Ödeme bilgisi gerekiyor; ders projesi için uygun değil. |

## 2. REST isteği ve yanıtı

```
POST https://api.openrouteservice.org/v2/directions/driving-car/geojson
Authorization: <API anahtarı>
Content-Type: application/json

{"coordinates": [[40.4983, 38.8853], [40.3497, 39.3097]]}      <- [BOYLAM, ENLEM] sırası!
```

```json
{"features": [{
   "properties": {"summary": {"distance": 61234.5, "duration": 3120.4}},
   "geometry":   {"coordinates": [[40.4983, 38.8853], [40.45, 39.10], ...]}}]}
```

- **Kimlik doğrulama:** Anahtar `Authorization` **başlığında** gönderilir. ORS anahtarı URL'de de (`?api_key=`) kabul ediyor, ama URL'ler sunucu kayıtlarında, vekil sunucularda ve hata mesajlarında görünür; bu yüzden başlık kullanıldı.
- **Ayrıştırma (`yaniti_ayristir`):** `features[0].properties.summary` → mesafe (metre → km) ve süre (saniye → dakika); `geometry.coordinates` → rota noktaları, `[boylam, enlem]`'den uygulamanın kullandığı `(enlem, boylam)` sırasına çevrilir. Beklenen alan yoksa, sayı değilse, eksiyse ya da geometride 2'den az nokta varsa `YANIT_BOZUK`.
- **Neden ek paket yok?** `urllib.request` + `json` (standart kütüphane) yeterli; projenin "yalnızca standart kütüphane" ilkesi korunuyor, exe de büyümüyor.

## 3. Hata yönetimi

Tüm hatalar `HaritaApiHatasi(tur, ayrinti, durum_kodu)`'na çevrilir. İş katmanı hiçbirinde uygulamayı durdurmaz: **kuş uçuşu tahmin** gösterir ve nedenini ekrana yazar.

| Durum | Nasıl anlaşılır | `tur` | Ne olur |
|---|---|---|---|
| Anahtar tanımlı değil | `HARITA_API_ANAHTARI` boş | `anahtar_yok` | Servise **hiç gidilmez**; tahmin. Sayfanın üstünde turuncu uyarı. |
| Anahtar geçersiz | HTTP 401 / 403 | `anahtar_gecersiz` | Tahmin; aynı oturumda **bir daha denenmez** (her tıklamada reddedilen istek gönderilmesin). |
| Hız sınırı | HTTP 429 | `hiz_siniri` | Tahmin; **60 saniye** servise istek gönderilmez. |
| İstemci tarafı sınır | Son 60 sn'de 30 istek | `hiz_siniri` | İstek **hiç gönderilmez** (servisin 40/dk sınırına yaklaşmadan durulur). |
| Zaman aşımı | `TimeoutError` (varsayılan 6 sn) | `zaman_asimi` | Tahmin; arayüz en fazla 6 sn bekler. |
| Bağlantı yok | `URLError`, `OSError` | `baglanti` | Tahmin (afet bölgesinde internet kesintisi gerçek bir durum). |
| Rota yok | HTTP 404 (ORS kodu 2010) | `rota_bulunamadi` | Tahmin (ör. noktanın yakınında karayolu yok). |
| Servis hatası | HTTP 5xx, diğer | `servis_hatasi` | Tahmin. |
| Bozuk yanıt | JSON değil / alan eksik | `yanit_bozuk` | Tahmin. |

Hata ekrana Türkçe ve sade bir cümleyle çıkar ("Harita servisi zamanında yanıt vermedi. Kuş uçuşu tahmin gösteriliyor."). Teknik ayrıntı (`ayrinti`: servisin hata mesajı) yalnızca uyarı kaydına (`logging`) yazılır. **Anahtar hiçbir mesaja, kayda ya da `repr`'e girmez** (test: `test_anahtar_loglara_ve_mesajlara_sizmaz`).

**Kuş uçuşu tahmin:** Haversine mesafesi × 1,3 (karayolu kuş uçuşu çizgiden her zaman uzundur; %30 kaba bir varsayımdır), süre = mesafe / 50 km/sa. Ekranda kesikli turuncu düz çizgi ve "Kaynak: Tahmini (kuş uçuşu × 1,3)" yazar; gerçek rotayla karıştırılmaz.

## 4. Önbellek ve hız sınırı (rate limit)

- Depolar ve ihtiyaç noktaları yer değiştirmez; aynı depo → nokta rotası **7 gün** önbellekte tutulur (`rota_onbellek`). İkinci kez açıldığında servise gidilmez: hız sınırı harcanmaz, internetsiz de görünür.
- Önbellek kaydı, hesaplandığı andaki koordinatları da saklar. Depo ya da nokta koordinatı değişirse kayıt eşleşmez, rota yeniden sorulur.
- **Yalnızca servisten gelen** rota saklanır; tahmin saklanmaz (servis düzelince gerçek rota alınsın).
- Rota listesi açılırken servise istek gönderilmez (yalnızca önbellek). Servis, kullanıcı bir dağıtımı seçtiğinde ya da "Yeniden Hesapla"ya bastığında çağrılır.
- **Eşleştirme önerisi neden hâlâ kuş uçuşu?** Öneri her talep seçiminde bütün depoları sıralar: depo sayısı kadar istek demektir. Sıralama için kuş uçuşu yeterli; gerçek rota yalnızca planlanan, yani yola çıkacak dağıtım için sorulur.

## 5. API anahtarı nerede, nasıl saklanıyor?

Öncelik sırası (`config.ayar`): **ortam değişkeni → veri klasöründeki `.env` → varsayılan (boş)**.

```bat
setx HARITA_API_ANAHTARI "anahtariniz"
```
ya da `C:\Users\<kullanıcı>\AfetLojistik\.env` dosyasına:
```
HARITA_API_ANAHTARI=anahtariniz
```

- `.env` proje klasöründe **değil**, veri klasöründe aranır: hiçbir deponun içinde olmadığı için yanlışlıkla commit'lenemez. Proje klasörüne konsa bile `.gitignore`'daki `.env` satırı depoya almaz.
- Depoda yalnızca boş şablon var: `.env.example` (test: `test_anahtar_depoda_yok`).
- `.env` okuyucu kendi yazdığımız 20 satırlık bir fonksiyon (`env_dosyasi_oku`): `#` yorum, boş satır, tırnaklı değer.
- Anahtar alma: openrouteservice.org'da ücretsiz hesap → Dashboard → "Request a token" (Free plan).

## 6. Test yaklaşımı

Testler gerçek servise **gitmez**: anahtar, internet ve hız sınırı gerekmez, her çalıştırmada aynı sonucu verir. `OrsIstemcisi`'ne sahte bir *gönderici* fonksiyonu verilir (bağımlılık enjeksiyonu) ve servisin her yanıtı taklit edilir: 200, 403, 429, 404, 500, 502, bozuk JSON, zaman aşımı, bağlantı hatası. Saat de sahtedir: "60 saniye bekle" kuralı beklemeden denenir.

Gerçek ağ katmanı da denenir: test, bilgisayarın içinde (`127.0.0.1`) küçük bir HTTP sunucusu açar; bir uç yanıt vermeden bekler (**gerçek zaman aşımı**), diğeri 403 döner (`urllib`'in `HTTPError`'ı doğru çevriliyor mu?).

Gerçek ORS sunucusuyla elle denendi: geçersiz anahtar → `403 "Access to this API has been disallowed"` → `anahtar_gecersiz`; 1 ms zaman aşımı → `zaman_asimi`.
