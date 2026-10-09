# Yapay Zekâ Kullanım Günlüğü (AI Usage Log)

Her kayıt: araç · istem (prompt) · alınan çıktı · benim yaptığım değişiklik/doğrulama.

---

## Hafta 3 — Kurulum, Mimari ve Veri Modeli

### Kayıt 1 — Mimari ve klasör yapısı
- **Araç:** Claude (Claude Code)
- **İstem:** "P16 Afet Yardım Malzemesi Lojistik projesi için Python masaüstü uygulamasında katmanlı mimari ve klasör yapısı öner."
- **Çıktı:** Sunum (frontend) / İş (services) / Veri erişim (data) + ortak varlık (models) katmanları; Tkinter + SQLite önerisi.
- **Benim kararım / doğrulamam:** _(doldur: ör. "MVC yerine katmanlı mimariyi seçtim çünkü …"; "data paketinin .gitignore'daki `data/` kuralına takıldığını fark edip `/data/` olarak düzelttim" gibi)_

### Kayıt 2 — ER diyagramı varlık/ilişki önerisi
- **Araç:** Claude
- **İstem:** "Malzeme, bağış, ihtiyaç noktası ve dağıtım kaydı varlıkları için ilişkileri ve N-N ara tablolarını öner."
- **Çıktı:** 11 varlık; Bağış–Malzeme, Depo–Malzeme, Dağıtım–Malzeme için ara tablolar (BağışKalemi, Stok, DağıtımKalemi).
- **Benim kararım / doğrulamam:** _(doldur: ör. "Stok miktarını ayrı tabloda tutmaya karar verdim çünkü …"; "1NF–3NF kontrolünü kendim yaptım")_

### Kayıt 3 — İskelet kod
- **Araç:** Claude
- **İstem:** "Tkinter ile sol menülü, modül yer tutuculu boş ana pencere iskeleti yaz."
- **Çıktı:** `main.py`, `frontend/main_window.py`, `services/modul_servisi.py`, `models/entities.py`, testler.
- **Benim kararım / doğrulamam:** _(doldur: uygulamayı çalıştırdım, testleri çalıştırdım; değiştirdiğim yerler …)_

---

## Hafta 4 — Veritabanı Tasarımı ve Veri Erişim Katmanı

### Kayıt 4 — SQL şema ve kısıtlar
- **Araç:** Claude
- **İstem:** "ER diyagramıma göre SQLite şemasını yaz; FK'lerde RESTRICT/CASCADE seçimini, CHECK kısıtlarını ve indeksleri gerekçeleriyle öner."
- **Çıktı:** `001_ilk_sema.sql` (11 tablo, 15 indeks), migration çalıştırıcısı (`sema_surumu` tablosu).
- **Benim kararım / doğrulamam:** _(doldur: ör. "bagis_kalemi ilişkisini ve CASCADE/RESTRICT seçimini kendim açıkladım (Veritabani.md)"; "sorgu_ornekleri ile 5 kısıtın reddedildiğini gördüm")_

### Kayıt 5 — Repository (CRUD) ve ORM karşılaştırması
- **Araç:** Claude
- **İstem:** "ORM mi saf SQL mi? Tekrarı azaltan genel bir CRUD repository sınıfı yaz; değerleri parametreli sorguyla gönder."
- **Çıktı:** `TemelRepository` (dataclass alanları = kolonlar, enum/tarih dönüşümü), tablo repository'leri, bileşik anahtarlı `StokRepository` (upsert).
- **Benim kararım / doğrulamam:** _(doldur: neden saf SQL seçtim; `?` parametresinin SQL injection'ı nasıl önlediğini test ettim mi?)_

### Kayıt 6 — Sentetik veri ve testler
- **Araç:** Claude
- **İstem:** "KVKK'ya uygun, kendi içinde tutarlı (stok = bağış − dağıtım) sentetik örnek veri ve kısıt testleri yaz."
- **Çıktı:** `ornek_veri.py`, `kurulum.py`, `sorgu_ornekleri.py`, `tests/test_veritabani.py` (16 test).
- **Benim kararım / doğrulamam:** _(doldur: verideki ad/telefon/e-postaların gerçek olmadığını kontrol ettim; 19 testin geçtiğini gördüm)_