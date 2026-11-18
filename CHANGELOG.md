# Değişiklik Günlüğü — Backend

Sürüm numaraları [anlamsal sürümleme](https://semver.org/lang/tr/) (MAJOR.MINOR.PATCH) kuralına uyar:

- **MINOR** (0.**6**.0): yeni modül ya da geriye uyumlu yeni özellik (her hafta bir artar).
- **PATCH** (0.4.**1**): yalnızca hata düzeltmesi.
- **MAJOR** 0: proje henüz geliştirme aşamasında; 1.0.0 final sürümü (Hafta 15) olacak.

Etiketli sürümler GitHub'da *Tags* altında görünür: `git checkout v0.6.0` o sürümün kodunu açar.
Frontend deposunun kendi değişiklik günlüğü vardır; frontend `requirements.txt` hangi backend sürümünü kullandığını belirtir.

## [0.7.0] — 18.11.2026 · Hafta 9 · Harici API: Harita / Rota (etiket: `v0.7.0`)

Dağıtımın deposundan ihtiyaç noktasına karayolu mesafesi, süresi ve rotası OpenRouteService'ten. Ayrıntı: [docs/Rota-API.md](docs/Rota-API.md).

### Eklenenler
- `backend/entegrasyon/harita_api.py`: `OrsIstemcisi` (REST POST, anahtar `Authorization` başlığında, 6 sn zaman aşımı), `yaniti_ayristir` (GeoJSON → km, dakika, rota noktaları; doğrulama), `HaritaApiHatasi` ve 9 hata türü (anahtar yok/geçersiz, hız sınırı, zaman aşımı, bağlantı, rota yok, servis hatası, bozuk yanıt). İstemci tarafı hız sınırı (dakikada 30) ve 429 sonrası 60 sn bekleme; geçersiz anahtar oturumda bir kez denenir.
- `backend/services/rota_servisi.py`: `RotaServisi.dagitim_rotasi` (yetki, önbellek, servis hatasında kuş uçuşu × 1,3 tahmine geri dönüş ve nedeni), `rota_listesi` (servise gitmez), `servis_durumu`, `sure_yaz`.
- `007_rota_onbellek.sql`, `RotaOnbellekRepository`: servisten gelen rota 7 gün ve aynı koordinatlarla geçerli; tahmin saklanmaz.
- `config.ayar` ve `env_dosyasi_oku`: ayar önce ortam değişkeninden, sonra depo dışındaki `~/AfetLojistik/.env` dosyasından (ek paket yok). `HARITA_ZAMAN_ASIMI_SN`, `HARITA_DAKIKALIK_ISTEK`, `ROTA_ONBELLEK_GUN`.
- `tests/test_rota.py`: 22 test (sahte gönderici ve sahte saatle her hata türü; yerel HTTP sunucusuyla gerçek zaman aşımı ve 403; önbellek; geri dönüş; yetki; anahtarın depoda ve mesajlarda olmaması). Toplam 134.

### Değişenler
- Rota / Dağıtım Planı modülü **Hazır** (`modul_servisi.GUNCEL_HAFTA = 9`).
- `DagitimRepository.liste` ihtiyaç noktası kimliğini de döndürür.
- `.env.example` açıklamaları; `.env` dosyasının otomatik okunması (Hafta 8'de "python-dotenv ile" planlanmıştı; ek bağımlılık yerine 20 satırlık kendi okuyucumuz yazıldı).

## [0.6.1] — 17.11.2026 · Parola sıfırlama (etiket: `v0.6.1`)

"Şifremi unuttum" yerine **Yönetici parola sıfırlaması**. Uygulama internetsiz çalıştığı için e-posta/SMS ile kimlik doğrulanamaz; doğrulamasız bir "yeni parola belirle" ekranı hesabı kullanıcı adını bilen herkese açardı. Kimliği Yönetici doğrular, sistem geçici parola üretir. (Vize sürümü `v0.6.0` değişmedi; 0.4.3'teki rol düzenlemesi gibi iki hafta arası eklenti.)

### Eklenenler
- `006_parola_sifirlama.sql`: `kullanici.parola_degistirmeli` kolonu (varsayılan 0, mevcut hesaplar etkilenmez) ve `parola_sifirlama` denetim tablosu (kim, kimin parolasını, ne zaman; parolanın kendisi tutulmaz; kişi kendi kendini sıfırlayamaz — CHECK).
- `KimlikServisi.parola_sifirla(token, kullanici_id)`: yalnızca Yönetici, kendi parolası hariç. 10 karakterlik rastgele geçici parola (`guvenlik.gecici_parola_uret`, karıştırılan 0/O/1/l/I yok) döner; yalnızca hash'i saklanır. Kullanıcının açık oturumları kapanır, hesap kilidi ve hatalı deneme sayacı sıfırlanır. Tek transaction.
- `KimlikServisi.parola_yenile(kullanici_adi, gecici, yeni, tekrar)`: geçici parolayla **oturum açılmaz** (`giris_yap` → `ParolaDegistirilmeli`); kullanıcı önce kendi parolasını belirler. Geçici parola doğrulaması girişteki kilit/sayaç kurallarına tabidir; yeni parola politikaya uymalı ve geçici paroladan farklı olmalı.
- `KimlikServisi.parola_sifirlama_gecmisi`, `ParolaSifirlamaRepository`, `ParolaDegistirilmeli` hatası.
- 11 test (10 parola sıfırlama + migration 006'nın mevcut veritabanına uygulanması). Toplam 112.

### Değişenler
- `giris_yap` iki adıma ayrıldı: `_kimlik_dogrula` (kilit, sayaç, parola) ve `_oturum_ac`. Parola kuralları kayıt ve yenilemede ortak (`_parola_hatalari`).

## [0.6.0] — 04.11.2026 · Hafta 8 · VİZE ara sürümü (etiket: `v0.6.0`)

Kullanıcı + veritabanı + çekirdek modüller uçtan uca entegre.

### Düzeltilen hatalar (entegrasyon testinde bulundu)
- **Rezerve stok Envanter'den çıkarılabiliyordu.** Planlanmış bir dağıtımın malzemesi depo görevlisi tarafından Stok Çıkışı ile çıkarılabiliyor, dağıtım sonra "Yolda" adımında *yetersiz stok* hatası alıyordu. Yeni kural **K9**: çıkış en fazla *serbest = stok − rezerve* kadar.
- **K7 eksikti.** Malzemenin birimi değişmez/silinemez kuralı yalnızca stok ve hareket kayıtlarına bakıyordu; yalnızca bağışta, talepte ya da dağıtımda geçen bir malzemenin birimi (adet → paket) değiştirilebiliyordu.

### Eklenenler
- Envanter stok listesinde `rezerve` ve `serbest` bilgisi (`StokSatiri.rezerve`, `StokSatiri.serbest`).
- Modül planında durum: *Hazır / Kısmen / Planlandı* (`ModulBilgisi.durum`).
- `tests/test_entegrasyon.py`: uçtan uca senaryo (bağış → talep → eşleştirme → yola çıkış → teslim), rol değişikliğinin tüm modüllere yansıması, transaction geri alma, iki regresyon testi, kurulum ve veritabanı demosunun ayrı süreç olarak çalıştırılması.
- `CHANGELOG.md`, `docs/Demo-Senaryosu.md`, mimari belgesine veri akışı bölümü.

Testler: 101 (94 → 101).

## [0.5.0] — 29.10.2026 · Hafta 7 · Bağış Girişi ve İhtiyaç Eşleştirme
- `005_eslestirme.sql`: dağıtım kalemi → ihtiyaç talebi bağı; talep durumu dağıtımlardan hesaplanır.
- `BagisServisi` (B1–B8): bağış stoğa Envanter'in yolundan, tek transaction'da girer.
- `EslestirmeServisi` (E1–E9): en yakın depo önerisi (Haversine), rezerve stok, fazla gönderim engeli, eksik uyarısı, dağıtım durumları.
- Envanter'e başka modüllerin kullandığı transaction açmayan stok yolu (`stok_hareketi_uygula`).

## [0.4.3] — 23.10.2026 · Rol düzenleme
- `004_rol_degisikligi.sql`, `KimlikServisi.rol_degistir / rol_gecmisi`: yalnızca Yönetici; kişi kendi rolünü değiştiremez; rolü değişenin oturumu kapanır.

## [0.4.2] — 21.10.2026 · Hata düzeltmesi
- Veritabanı AppData yerine ev klasöründe (`C:\Users\<kullanıcı>\AfetLojistik`). Windows paket sanallaştırması aynı bilgisayarda iki ayrı veritabanı oluşturuyor, kullanıcılar giriş yapamıyordu.

## [0.4.1] — 21.10.2026 · Hata düzeltmesi
- Türkçe klavyeyle yazılan kullanıcı adıyla (`İ/ı`) giriş yapılamıyordu.

## [0.4.0] — 21.10.2026 · Hafta 6 · Envanter Yönetimi
- `003_stok_hareketi.sql` (açılış devri ile), `EnvanterServisi` (K1–K8): giriş, çıkış, sayım, kritik seviye, depo sahipliği.

## [0.3.0] — 09.10.2026 · Hafta 5 · Kimlik doğrulama
- `002_kullanici.sql`; PBKDF2 parola hash, oturum token'ı, RBAC (Yönetici/Kurum/Depo), hesap kilitleme.
- 16.10.2026: backend ayrı depoya taşındı, `pyproject.toml` ile kurulabilir paket oldu.

## [0.2.0] — 09.10.2026 · Hafta 4 · Veritabanı
- `001_ilk_sema.sql` (11 tablo, kısıtlar, indeksler), migration çalıştırıcısı, repository'ler, sentetik veri.

## [0.1.0] — 09.10.2026 · Hafta 3 · İskelet
- Katmanlı mimari (models / services / data), ER diyagramı, ayarlar.
