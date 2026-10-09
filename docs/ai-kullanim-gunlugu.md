# Yapay Zekâ Kullanım Günlüğü (AI Usage Log)

Her kayıt: tarih · araç · istem (prompt) · alınan çıktı · benim yaptığım değişiklik/doğrulama · açıklayabilir miyim (E/H).

> İlke: 'Açıklayabilir mi?' sorusunun cevabı **E** olmayan hiçbir kod parçası teslim edilemez.

---

## Hafta 3 — Kurulum, Mimari ve Veri Modeli

### Kayıt 1 — Mimari ve klasör yapısı
- **Tarih:** 09.10.2026
- **Araç:** Claude (Claude Code)
- **İstem:** "P16 Afet Yardım Malzemesi Lojistik projesi için Python masaüstü uygulamasında katmanlı mimari ve klasör yapısı öner."
- **Çıktı:** Sunum (frontend) / İş (services) / Veri erişim (data) + ortak varlık (models) katmanları; Tkinter + SQLite önerisi.
- **Benim kararım / doğrulamam:** Teknoloji olarak Python masaüstü uygulamasını ben seçtim; AI ilk olarak C#/Node/PHP seçenekleri sundu. Sonra depoyu frontend ve backend diye ikiye ayırmasını istedim. `.gitignore`daki `data/` kuralının `backend/data` paketini de dışarıda bıraktığı fark edildi, `/data/` olarak düzeltildi.
- **Bu kodu açıklayabiliyor muyum? (E/H):** E

### Kayıt 2 — ER diyagramı varlık/ilişki önerisi
- **Tarih:** 09.10.2026
- **Araç:** Claude
- **İstem:** "Malzeme, bağış, ihtiyaç noktası ve dağıtım kaydı varlıkları için ilişkileri ve N-N ara tablolarını öner."
- **Çıktı:** 11 varlık; Bağış–Malzeme, Depo–Malzeme, Dağıtım–Malzeme için ara tablolar (BağışKalemi, Stok, DağıtımKalemi).
- **Benim kararım / doğrulamam:** Önerilen 11 tabloyu PDF'teki dört varlıkla (malzeme, bağış, ihtiyaç noktası, dağıtım kaydı) karşılaştırdım. Kullanıcı tablosunu takvime uygun olarak 5. haftaya bıraktık. Stoğu ayrı tabloda tutma kararını hızlı sorgu ve kritik stok uyarısı için kabul ettim.
- **Bu kodu açıklayabiliyor muyum? (E/H):** E

### Kayıt 3 — İskelet kod
- **Tarih:** 09.10.2026
- **Araç:** Claude
- **İstem:** "Tkinter ile sol menülü, modül yer tutuculu boş ana pencere iskeleti yaz."
- **Çıktı:** `main.py`, `frontend/main_window.py`, `services/modul_servisi.py`, `models/entities.py`, testler.
- **Benim kararım / doğrulamam:** `python main.py` ile pencerenin açıldığını, `python -m unittest` ile 3 testin geçtiğini kontrol ettim.
- **Bu kodu açıklayabiliyor muyum? (E/H):** E

---

## Hafta 4 — Veritabanı Tasarımı ve Veri Erişim Katmanı

### Kayıt 4 — SQL şema ve kısıtlar
- **Tarih:** 09.10.2026
- **Araç:** Claude
- **İstem:** "ER diyagramıma göre SQLite şemasını yaz; FK'lerde RESTRICT/CASCADE seçimini, CHECK kısıtlarını ve indeksleri gerekçeleriyle öner."
- **Çıktı:** `001_ilk_sema.sql` (11 tablo, 15 indeks), migration çalıştırıcısı (`sema_surumu` tablosu).
- **Benim kararım / doğrulamam:** `python -m backend.data.sorgu_ornekleri` çıktısında 5 kısıt ihlalinin reddedildiğini ve bağış silinince kalemlerinin de silindiğini (CASCADE) gördüm. bagis_kalemi ilişkisinin açıklaması Veritabani.md'de.
- **Bu kodu açıklayabiliyor muyum? (E/H):** E

### Kayıt 5 — Repository (CRUD) ve ORM karşılaştırması
- **Tarih:** 09.10.2026
- **Araç:** Claude
- **İstem:** "ORM mi saf SQL mi? Tekrarı azaltan genel bir CRUD repository sınıfı yaz; değerleri parametreli sorguyla gönder."
- **Çıktı:** `TemelRepository` (dataclass alanları = kolonlar, enum/tarih dönüşümü), tablo repository'leri, bileşik anahtarlı `StokRepository` (upsert).
- **Benim kararım / doğrulamam:** ORM yerine saf SQL kullanıldı; böylece sorguları görüp açıklayabiliyorum ve ek paket gerekmiyor. Değerlerin `?` parametresiyle gönderildiğini, SQL metnine eklenmediğini kodda kontrol ettim.
- **Bu kodu açıklayabiliyor muyum? (E/H):** E

### Kayıt 6 — Sentetik veri ve testler
- **Tarih:** 09.10.2026
- **Araç:** Claude
- **İstem:** "KVKK'ya uygun, kendi içinde tutarlı (stok = bağış − dağıtım) sentetik örnek veri ve kısıt testleri yaz."
- **Çıktı:** `ornek_veri.py`, `kurulum.py`, `sorgu_ornekleri.py`, `tests/test_veritabani.py` (16 test).
- **Benim kararım / doğrulamam:** Örnek verideki bağışçı adlarının "Anonim Bağışçı" / "Örnek ... A.Ş.", telefonların 0555 000 00 NN ve e-postaların example.com olduğunu, yani gerçek kişi verisi olmadığını kontrol ettim. 19 testin hepsi geçti.
- **Bu kodu açıklayabiliyor muyum? (E/H):** E

---

## Hafta 5 — Kullanıcı Yönetimi ve Kimlik Doğrulama

### Kayıt 7 — Güvenli parola saklama ve güvenlik açıkları araştırması
- **Tarih:** 09.10.2026
- **Araç:** Claude
- **İstem:** "Python standart kütüphanesiyle güvenli parola saklama nasıl yapılır? bcrypt, PBKDF2 ve düz SHA-256'yı karşılaştır. Kimlik doğrulamada yaygın OWASP açıkları neler?"
- **Çıktı:** PBKDF2-HMAC-SHA256 (600.000 tur, 16 bayt tuz), `compare_digest`, genel hata mesajı, hesap kilitleme önerileri; `backend/guvenlik.py`.
- **Benim kararım / doğrulamam:** bcrypt ek paket gerektirdiği için Python'un kendi `hashlib.pbkdf2_hmac` fonksiyonu seçildi. Testte aynı parolanın iki farklı hash ürettiğini ve veritabanında düz parolanın olmadığını gördüm.
- **Bu kodu açıklayabiliyor muyum? (E/H):** E

### Kayıt 8 — Oturum/token ve rol tabanlı erişim
- **Tarih:** 09.10.2026
- **Araç:** Claude
- **İstem:** "Masaüstü uygulamada oturum/token yönetimi ve Yönetici/Kurum/Depo rolleri için yetkilendirme katmanı tasarla; yetki kontrolü sadece arayüzde olmasın."
- **Çıktı:** `002_kullanici.sql` (kullanici, oturum), `KimlikServisi`, `yetki.py` (rol → modül tablosu), hata sınıfları.
- **Benim kararım / doğrulamam:** JWT yerine veritabanında tutulan oturum seçildi; çıkışta oturum hemen kapatılabiliyor. Rol yetkilerini afet senaryosuna göre belirledim: depo görevlisi stok ve bağış, kurum ihtiyaç ve dağıtım. Testlerde Depo rolünün dağıtım modülüne giremediğini gördüm.
- **Bu kodu açıklayabiliyor muyum? (E/H):** E

### Kayıt 9 — Giriş/kayıt ekranı ve testler
- **Tarih:** 09.10.2026
- **Araç:** Claude
- **İstem:** "Tkinter ile giriş ve kayıt penceresi yaz; çıkış yapınca giriş ekranına dönülsün. Kimlik doğrulama için birim testleri yaz."
- **Çıktı:** `frontend/giris_penceresi.py`, ana pencerede kullanıcı/rol/çıkış ve Kullanıcılar sayfası, `tests/test_kimlik.py` (19 test).
- **Benim kararım / doğrulamam:** Uygulamayı üç test kullanıcısıyla açıp kilitli menüleri ve "Erişim engellendi" sayfasını kontrol ettim (ekran görüntüleri). 38 testin hepsi geçti.
- **Bu kodu açıklayabiliyor muyum? (E/H):** E
