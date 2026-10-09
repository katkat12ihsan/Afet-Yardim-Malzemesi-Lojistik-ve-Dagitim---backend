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
