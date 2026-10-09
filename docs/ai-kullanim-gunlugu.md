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