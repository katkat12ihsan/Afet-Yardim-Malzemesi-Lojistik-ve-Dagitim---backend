# 1. Risk Analizi

| Öğrenci | Numara | Proje (Kod/Ad) | Tarih |
|---|---|---|---|
| İhsan Katkat | 251161036 | P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım | 09.10.2026 |

**Skor:** Olasılık (1–3) × Etki (1–3). 1–2 düşük, 3–4 orta, 6–9 yüksek risk. Yüksek riskler için mutlaka önlem tanımlanır.

| No | Risk | Kategori | Ol. | Etki | Skor | Önlem / Aksiyon |
|---|---|---|---|---|---|---|
| 1 | Tkinter ile karmaşık ekranlar (tablo, form, harita) beklenenden uzun sürüyor | Teknik | 2 | 3 | **6** | Ortak form/tablo bileşenleri yazmak; harita için hazır `tkintermapview` paketi; kapsamı gerekirse daraltmak |
| 2 | Harita/rota API'sinin limiti, ücreti veya anahtar zorunluluğu (Hafta 9) | Dış | 2 | 2 | 4 | Ücretsiz OSRM/OpenStreetMap; sonuçları önbelleğe almak; API yoksa kuş uçuşu mesafeye düşmek |
| 3 | Yapay zekâ çıktısı hatalı veya anlaşılmadan kullanılıyor | AI/Etik | 2 | 3 | **6** | AI günlüğü; her kodu açıklama; birim testiyle doğrulama |
| 4 | Haftalık teslimlerin birikmesi | Zaman | 3 | 2 | **6** | Haftalık küçük hedefler; hafta içinde erken commit |
| 5 | Stok tutarsızlığı (bağış/dağıtım kaydedilip stok güncellenmemesi) | Teknik | 2 | 3 | **6** | Giriş/çıkış + stok güncellemesi tek transaction; `CHECK (miktar >= 0)`; testler |
| 6 | LLM API'sine kişisel veri gönderilmesi (KVKK) | AI/Etik | 1 | 3 | 3 | Yalnızca sentetik veri; LLM'e sadece malzeme/miktar/öncelik gönderilir, kişi bilgisi gönderilmez |
| 7 | API anahtarının depoya yüklenmesi | Güvenlik | 1 | 3 | 3 | Ortam değişkeni, `.env` `.gitignore`'da, `.env.example` şablonu |
| 8 | Veritabanı dosyasının bozulması / kaybı | Teknik | 1 | 2 | 2 | Şema migration'da, örnek veri komutla yeniden kurulabiliyor; Hafta 14'te yedekleme özelliği |
