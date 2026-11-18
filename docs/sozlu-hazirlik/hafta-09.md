# Hafta 9 Sözlü Sınav Hazırlığı — Harici API Entegrasyonu: Harita / Rota

> **Temel ilke (kılavuz):** Açıklayamadığım kod başarılı sayılmaz.
> Sıra: **(1) genel kavrayış → (2) modül düzeyi → (3) satır düzeyi ve değiştirme.** Ayrıntılı modül belgesi: [Rota-API.md](../Rota-API.md)

---

## Haftanın 5 sorusu

### 1) Rotayı nasıl hesaplattın?
- **Servis:** OpenRouteService (OpenStreetMap verisi), REST. `POST .../v2/directions/driving-car/geojson`.
- **İstek:** Gövdede iki koordinat `{"coordinates": [[boylam, enlem], [boylam, enlem]]}`. Dikkat: ORS **önce boylamı** ister, bizim uygulamada her yerde (enlem, boylam) var; çeviriyi istemci yapıyor.
- **Kimlik doğrulama:** Anahtar `Authorization` başlığında.
- **Akış:** Rota sayfasında dağıtım seçilir → `RotaServisi.dagitim_rotasi` → önbellekte varsa oradan, yoksa `OrsIstemcisi.rota` → sonuç önbelleğe yazılır → ekranda km, süre ve Canvas'ta rota çizgisi.
- **Neden ORS?** Ücretsiz ama anahtarlı ve hız sınırlı: dersin konuları (kimlik doğrulama, rate limit) gerçekten uygulanıyor. Google ödeme bilgisi istiyor; OSRM demo sunucusunda anahtar yok.

### 2) Rota alınamazsa ne yapıyorsun?
- Uygulama **durmaz**: kuş uçuşu mesafe (Haversine) × 1,3 yol katsayısı, süre = mesafe / 50 km/sa ile **tahmini** rota döner.
- Ekranda turuncu, kesikli düz çizgi; "Kaynak: Tahmini (kuş uçuşu × 1,3)" ve nedeni ("Harita servisi zamanında yanıt vermedi. Kuş uçuşu tahmin gösteriliyor.").
- Tahmin **önbelleğe yazılmaz**: servis düzelince gerçek rota alınsın.
- Neden? Afet bölgesinde internet kesilebilir; dağıtım planı harita servisine bağımlı kalmamalı.

### 3) API anahtarını nasıl ve nerede sakladın?
- **Kodda yok, depoda yok.** `config.ayar("HARITA_API_ANAHTARI")`: önce **ortam değişkeni**, yoksa `C:\Users\<kullanıcı>\AfetLojistik\.env`.
- `.env` bilerek **proje klasöründe değil**, veri klasöründe: hiçbir depo klasörünün içinde değil, yanlışlıkla commit'lenemez. `.gitignore`'da `.env` satırı da var (ikinci güvence).
- Depoda yalnızca boş şablon `.env.example`. Test: `test_anahtar_depoda_yok`.
- Anahtar URL'ye değil başlığa konuyor; `repr(istemci)` → `anahtar=***`; hata mesajlarına girmiyor (test: `test_anahtar_loglara_ve_mesajlara_sizmaz`).

### 4) API çağrısı başarısızsa ne oluyor?
Her hata `HaritaApiHatasi`'na çevriliyor, `tur` alanına göre karar veriliyor:

| Ne oldu | Tür | Ek davranış |
|---|---|---|
| Anahtar yok | `anahtar_yok` | Servise hiç gidilmez |
| 401/403 | `anahtar_gecersiz` | O oturumda bir daha denenmez |
| 429 | `hiz_siniri` | 60 sn istek gönderilmez |
| 30 istek/dk doldu | `hiz_siniri` | İstek hiç gönderilmez (istemci tarafı sınır) |
| 6 sn yanıt yok | `zaman_asimi` | — |
| İnternet yok | `baglanti` | — |
| 404 | `rota_bulunamadi` | — |
| 5xx | `servis_hatasi` | — |
| JSON bozuk/eksik | `yanit_bozuk` | — |

Hepsinde sonuç aynı: tahmini rota + kullanıcıya sade bir cümle. Teknik ayrıntı `logging` ile uyarı kaydına.

### 5) Yanıtı nasıl ayrıştırdın?
`yaniti_ayristir(govde)`: `json.loads` → `features[0]["properties"]["summary"]` → `distance` (metre) ve `duration` (saniye) → km'ye ve dakikaya çevrilip 1 basamağa yuvarlanır. `geometry.coordinates` → her nokta `[boylam, enlem]`'den `(enlem, boylam)`'a çevrilir. JSON değilse, alan eksikse, sayı değilse, eksiyse ya da 2'den az nokta varsa `YANIT_BOZUK`. Yani **yanıta güvenmiyorum, doğruluyorum**.

---

## Aşama 1 — Genel kavrayış: bir rota isteğinin yolculuğu

1. `rota_sayfasi.py`: kullanıcı tablodan dağıtım seçer (`<<TreeviewSelect>>`) → `RotaServisi.dagitim_rotasi(token, id)`. İmleç "bekle" olur.
2. `_yetki` → `KimlikServisi.modul_erisimi(token, "dagitim")`: Yönetici ve Kurum girebilir, Depo giremez.
3. Dağıtımın deposu ve ihtiyaç noktası okunur; koordinat yoksa `DogrulamaHatasi`.
4. **Önbellek:** aynı koordinatlarla 7 günden yeni kayıt varsa → `KAYNAK_ONBELLEK`, servise gidilmez.
5. **Servis:** `OrsIstemcisi.rota` → anahtar kontrolü → hız kontrolü → `urllib` POST (6 sn zaman aşımı) → HTTP kodu → ayrıştırma.
6. Başarılı: önbelleğe yazılır (`islem` transaction) → `KAYNAK_SERVIS`. Hata: `HaritaApiHatasi` yakalanır → tahmin + uyarı.
7. Arayüz: km/süre, kaynak, uyarı, Canvas'ta çizim; tabloda Mesafe/Süre sütunu güncellenir.

**Katmanlar:** Arayüz HTTP bilmez → İş katmanı (`rota_servisi`) karar verir → Entegrasyon katmanı (`harita_api`) yalnızca dış servisle konuşur → Veri katmanı önbelleği yazar.

## Aşama 2 — Modül düzeyi: kararlar ve gerekçeleri

| Karar | Neden | Alternatif ve neden seçmedim |
|---|---|---|
| Ayrı `backend/entegrasyon/` katmanı | Dış servis değişirse (ör. ORS → başka servis) yalnızca bu dosya değişir; iş kuralı etkilenmez | HTTP kodunu servisin içine yazmak: test etmek ve değiştirmek zorlaşırdı |
| `urllib` (standart kütüphane) | Ek paket yok, exe büyümez; tek bir POST isteği için yeterli | `requests`: daha rahat ama yeni bağımlılık |
| Anahtar başlıkta | URL'ler kayıtlarda görünür | `?api_key=...`: ORS kabul ediyor ama sızma riski |
| Önbellek (7 gün, koordinatla) | Hız sınırı, hız, internetsiz görüntüleme | Her seferinde sormak: 40/dk sınırı çabuk dolar |
| Tahmini önbelleğe yazmamak | Servis düzelince gerçek değer gelsin | Yazmak: 7 gün boyunca yanlış (tahmini) değer görünürdü |
| Geçersiz anahtarı oturumda bir kez denemek | Her tıklamada reddedilecek istek göndermemek | Her seferinde denemek: gereksiz trafik |
| Liste açılırken servise gitmemek | 20 dağıtım = 20 istek olurdu; sayfa yavaş açılırdı | Tüm satırları hesaplamak |
| Eşleştirme sıralaması kuş uçuşu | Her öneri depo sayısı kadar istek demek | Yol mesafesiyle sıralamak: hız sınırı |
| Sahte gönderici ile test | Anahtar/internet gerekmez, her hata türü denenebilir, her seferinde aynı sonuç | Gerçek servisle test: kotayı harcar, internete bağlı, hata durumları üretilemez |
| Harita karosu yok, Canvas çizimi | Ek paket ve tile sunucusu (yine dış servis) gerekmez | `tkintermapview`: güzel ama Pillow/requests bağımlılığı ve karo indirme |

**Kullanılan kütüphaneler:** `urllib.request` (Request, urlopen, timeout), `urllib.error` (HTTPError, URLError), `json`, `time.monotonic` (saat geri alınsa da çalışan süre ölçümü), `collections.deque` (kayan pencere), `logging`, `tkinter.Canvas`, testte `http.server` + `threading` (yerel sunucu), `unittest.mock`.

## Aşama 3 — Satır düzeyi

### A) `OrsIstemcisi.rota` (`backend/entegrasyon/harita_api.py`)

```python
if not self._anahtar:                                   # 1
    raise HaritaApiHatasi(ANAHTAR_YOK)
if self._anahtar_reddedildi:                            # 2
    raise HaritaApiHatasi(ANAHTAR_GECERSIZ, "bu oturumda reddedildi")
self._hiz_kontrolu()                                    # 3
govde = json.dumps({"coordinates": [[baslangic[1], baslangic[0]], [bitis[1], bitis[0]]]}).encode()   # 4
basliklar = {"Authorization": self._anahtar, "Content-Type": "application/json", ...}            # 5
try:
    kod, yanit = self._gonder(ORS_URL, govde, basliklar, self._zaman_asimi)                       # 6
except TimeoutError:                                    # 7
    raise HaritaApiHatasi(ZAMAN_ASIMI) from None
except urllib.error.URLError as hata:                   # 8
    if isinstance(hata.reason, TimeoutError): raise HaritaApiHatasi(ZAMAN_ASIMI) from None
    raise HaritaApiHatasi(BAGLANTI, str(hata.reason)[:120]) from None
except OSError as hata:                                 # 9
    raise HaritaApiHatasi(BAGLANTI, type(hata).__name__) from None
if kod == 200: return yaniti_ayristir(yanit)            # 10
if kod in (401, 403): self._anahtar_reddedildi = True; raise ...ANAHTAR_GECERSIZ   # 11
if kod == 429: self._bekle_bitis = self._saat() + 60; raise ...HIZ_SINIRI          # 12
if kod == 404: raise ...ROTA_YOK                        # 13
raise ...SERVIS_HATASI                                  # 14
```

| Satır | Ne yapar |
|---|---|
| 1 | Anahtar boşsa ağa hiç çıkmadan hata: gereksiz istek ve bekleme yok. |
| 2 | Bu oturumda servis anahtarı reddettiyse tekrar denemez. |
| 3 | Kayan pencere: son 60 sn'deki istekler `deque`'de; 30'a ulaştıysa ya da 429 sonrası bekleme sürüyorsa hata, istek gönderilmez. |
| 4 | Gövde: ORS [boylam, enlem] ister; `baslangic` bizde (enlem, boylam), bu yüzden `[1], [0]`. `.encode()` → bayt (HTTP gövdesi bayttır). |
| 5 | Anahtar başlıkta, URL'de değil. |
| 6 | Asıl istek. `self._gonder` gerçek uygulamada `urllib_gonderici`, testte sahte fonksiyon. `zaman_asimi` = 6 sn. |
| 7 | Yanıt süresi aşıldı. Python 3.10'dan beri `socket.timeout` = `TimeoutError`. |
| 8 | `urlopen` bağlantı kurarken zaman aşımını `URLError(reason=timeout)` içinde verebiliyor; ikisini ayırıyorum. Diğerleri: DNS bulunamadı, bağlantı reddedildi → `BAGLANTI`. |
| 9 | Kalan ağ hataları (ör. bağlantı koptu). **Sıra önemli:** `URLError` ve `TimeoutError` da `OSError`'ın alt sınıfı; genel olanı önce yazsam özel olanlar hiç yakalanmazdı. |
| 10 | Başarılı: ayrıştırma ve doğrulama. |
| 11–14 | HTTP koduna göre tür. 4xx/5xx gövdesi `urllib_gonderici`'de `HTTPError`'dan okunur ve kod olarak döner. |

`from None`: kullanıcıya/loglara iç içe teknik traceback zinciri değil, tek ve anlamlı hata gider.

**"Bu satırı silsen ne olur?"**

| Değişiklik | Sonuç |
|---|---|
| 4'te `[1], [0]` yerine `[0], [1]` | Enlem ile boylam yer değişir → Bingöl Merkez (38,89 K, 40,50 D) yerine 40,50 K, 38,89 D'ye, yani Giresun civarına düşer; ORS yanlış bir rota ya da 404 verir. `test_istek_bicimi_ve_yanit_ayristirma` kırmızı. |
| 6'da `zaman_asimi` verilmezse | `urlopen` varsayılanı sınırsız bekleyebilir → arayüz donar. Kılavuzdaki "zaman aşımını yönetmemek" hatası. |
| 9 en üste taşınırsa | Zaman aşımı da `BAGLANTI` olur; mesaj yanlış. |
| 11'de bayrak kaldırılırsa | Geçersiz anahtarla her seçimde servise istek gider. `test_gecersiz_anahtar_bir_kez_denenir` kırmızı. |
| 3 silinirse | Hızlı tıklamada 40/dk aşılır, servis 429 verir, anahtar geçici olarak kısıtlanabilir. |

### B) `RotaServisi.dagitim_rotasi` — geri dönüş (fallback)

```python
try:
    rota = self._istemci.rota(bas, bit)
except HaritaApiHatasi as hata:
    if hata.tur != ANAHTAR_YOK:
        _log.warning("Rota alınamadı (dağıtım #%s): %s %s", dagitim.id, hata.tur, hata.ayrinti)
    km, dk = tahmini_rota(bas, bit)
    return RotaBilgisi(**temel, mesafe_km=km, sure_dk=dk, kaynak=KAYNAK_TAHMIN,
                       uyari=f"{hata} Kuş uçuşu tahmin gösteriliyor.", geometri=(bas, bit))
with islem(self._baglanti):
    self._onbellek.kaydet(...)
```
- Yalnızca `HaritaApiHatasi` yakalanır; programlama hatası (ör. `TypeError`) yutulmaz, testte görünür.
- Anahtar yoksa uyarı kaydı yazılmaz: bu bir hata değil, bilinen bir yapılandırma.
- `geometri=(bas, bit)`: düz çizgi; arayüz `tahmini` ise kesikli turuncu çizer.
- Önbelleğe yazma `return`'den sonra değil, yalnızca başarılı yolda.

**İzini sür:** Anahtar yok, dağıtım #4 Genç Ara Depo → Adaklı Konteyner Kent. Haversine ≈ 53,6 km × 1,3 = **69,7 km**; 69,7 / 50 × 60 = **83,6 dk ≈ 1 sa 24 dk**. Ekrandaki değer bu (Şekil 1).

---

## Teorik kavramlar
- **REST:** Kaynaklara HTTP yöntemleriyle (GET, POST…) erişilen, durumsuz (her istek kendi bilgisini taşır) servis yaklaşımı. Yanıt genellikle JSON; sonuç HTTP durum koduyla bildirilir (200, 4xx istemci hatası, 5xx sunucu hatası).
- **API kimlik doğrulama:** Servisin "kim istiyor?" sorusu. Burada API anahtarı (başlıkta). Anahtar bir paroladır: kodda, depoda, URL'de, logda olmamalı.
- **Rate limit (hız sınırı):** Servisin birim zamanda kabul ettiği istek sayısı (ORS ücretsiz: 40/dk, 2000/gün). Aşılınca 429. Önlem: önbellek, istemci tarafı sınır, 429 sonrası bekleme.
- **Zaman aşımı:** Yanıt için beklenecek en uzun süre. Yoksa program sonsuza dek bekleyebilir.
- **Hata yönetimi / zarif bozulma (graceful degradation):** Bir parça çalışmazsa sistemin tamamen durması yerine daha az iyi ama çalışan bir yola (tahmin) geçmesi.
- **Bağımlılık enjeksiyonu:** `OrsIstemcisi(..., gonderici=...)`: nesnenin ihtiyaç duyduğu parça dışarıdan verilir; testte sahtesi takılır.

## Sık yapılan hatalar (bende olmamalı)
| Hata | Bendeki önlem |
|---|---|
| Anahtarı koda gömmek | Ortam değişkeni / depo dışı `.env`; `.env.example` boş; test |
| Hataları yakalamamak | 9 hata türü, her biri için test; hepsinde tahmine geri dönüş |
| Zaman aşımını yönetmemek | 6 sn (ayarlanabilir); yerel sunucuyla gerçek zaman aşımı testi |

## Soru bankası — kısa cevaplar
| Soru | Cevabım |
|---|---|
| GET yerine neden POST? | ORS'un GeoJSON rota ucu POST; ayrıca GET'te koordinatlar ve anahtar URL'ye girerdi. |
| `time.time()` yerine neden `time.monotonic()`? | Bilgisayarın saati elle ya da otomatik değişse bile geri gitmez; süre ölçmek için doğru saat. |
| Önbellek neden koordinatı saklıyor? | Depo taşınırsa eski rota geçersiz olmalı; koordinat değişince kayıt eşleşmez, yeniden sorulur. |
| Testlerde neden gerçek servis yok? | Kotayı harcar, internet ister, 429/500/zaman aşımı istendiğinde üretilemez, sonuç değişebilir. Gerçek servisle elle de denedim: geçersiz anahtar → 403 doğru işlendi. |
| Arayüz donuyor mu? | En fazla zaman aşımı kadar (6 sn) ve bekle imleci gösteriliyor; önbellekteki rota anında. İleride istek ayrı iş parçacığında yapılabilir. |
| Bu veri kişisel mi? | Hayır: yalnızca depo ve ihtiyaç noktası koordinatları gidiyor; kişi bilgisi gönderilmiyor. |
