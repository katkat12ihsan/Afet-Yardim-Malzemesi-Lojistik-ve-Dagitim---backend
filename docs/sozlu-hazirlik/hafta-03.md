# Hafta 3 Sözlü Sınav Hazırlığı

## 1) Katmanlı mimariyi neden tercih ettin?
Projede 6 modül haftalık olarak eklenecek. Her modülü aynı üç katmana (Sunum → İş → Veri) bölünce kod düzenli kalıyor: arayüz SQL bilmiyor, veritabanı kodu iş kararı vermiyor. Böylece (a) bir katmanı değiştirince diğerleri etkilenmiyor (ör. SQLite → PostgreSQL geçişinde yalnızca `data` değişir), (b) iş kuralları pencere açmadan `unittest` ile test edilebiliyor, (c) hata nerede ise orada aranıyor. Tek dosyada her şeyi yazmak ilk hafta hızlı ama 6. modülde yönetilemez olurdu.

## 2) İlişki türlerini (1-1, 1-N, N-N) örnekle açıkla.
- **1-N:** Bir kategoride çok malzeme var, her malzeme tek kategoriye ait → `malzeme.kategori_id` FK. Bir depo çok dağıtım gönderir → `dagitim.depo_id`.
- **N-N:** Bir bağışta çok malzeme olabilir, bir malzeme çok bağışta yer alır → iki 1-N'ye bölünüp `BAGIS_KALEMI` ara tablosuyla çözüldü (ara tablo `miktar` bilgisini de taşıyor). Aynı şekilde Depo–Malzeme → `STOK`, Dağıtım–Malzeme → `DAGITIM_KALEMI`.
- **1-1:** Projede şimdilik yok. Örnek: her depoya tek bir sorumlu atansaydı Depo–DepoSorumlusu 1-1 olurdu; çoğu zaman aynı tabloda tutulabilir, ayrı tablo ancak isteğe bağlı/gizli bilgi için mantıklı.

## 3) Bu projede hangi varlıklar birincil anahtar taşıyor ve neden?
Tüm varlıklar kendi `id` (otomatik artan tamsayı, vekil anahtar) PK'sına sahip; çünkü ad/adres gibi alanlar değişebilir veya tekrar edebilir (iki depo aynı adı taşıyabilir). İstisna **STOK**: PK bileşik `(depo_id, malzeme_id)` — bir depoda bir malzemeden yalnızca tek stok satırı olmalı, bileşik anahtar bu kuralı veritabanı seviyesinde garanti ediyor. Ara tablolardaki `bagis_id`, `malzeme_id` gibi alanlar FK; referans bütünlüğünü sağlıyor (olmayan bir malzemeye bağış kalemi eklenemez).

## 4) Klasör yapını hangi mantıkla kurdun?
Depo önce ikiye ayrılıyor: **`frontend/`** (Tkinter pencereleri, yani kullanıcının gördüğü kısım) ve **`backend/`** (arayüzden bağımsız çekirdek). Backend içinde her katman ayrı paket: `services` (iş kuralları), `data` (SQLite erişimi), `models` (ER tablolarının dataclass karşılığı, herkesin ortak dili). `main.py` yalnızca pencereyi başlatır. Frontend backend'i çağırır, backend frontend'i asla import etmez; böylece ileride arayüz web'e taşınsa backend aynen kalır. `tests` kodu, `docs` belgeleri ayrı tutar. `config.py` ayarları tek yerde toplar; gizli anahtarlar ortam değişkeninden okunur. Bağımlılık tek yönlü: `frontend` → `backend/services` → `backend/data`; ör. ana panel modül listesini doğrudan değil `modul_servisi` üzerinden alıyor.

## 5) .gitignore neden gereklidir, neler eklenmemeli?
Depoya yalnızca kaynak kod ve belgeler girmeli. `.gitignore` şunları dışarıda tutar: `__pycache__/` ve `*.pyc` (Python'un ürettiği derlenmiş dosyalar, her makinede yeniden oluşur), `.venv/` (sanal ortam, `requirements.txt`'den yeniden kurulur, yüzlerce MB), `.env` (API anahtarı/parola — gizli bilgi depoya girerse herkes görür), `*.db` (yerel veritabanı, kişisel/test verisi içerebilir), `build/ dist/`, editör klasörleri. Dikkat: `data/` yazınca `afet_lojistik/data` paketi de dışlanıyordu, `/data/` ile yalnızca kök klasörü hedefledim.

---

## Teorik kavramlar (kısa)
- **Katmanlı mimari:** Sorumlulukların sunum / iş / veri katmanlarına ayrılması.
- **ER modeli:** Varlık (tablo), nitelik (sütun), ilişki (FK).
- **PK:** Satırı benzersiz tanımlar, boş olamaz. **FK:** Başka tablonun PK'sına referans, referans bütünlüğü sağlar.
- **1NF:** Hücrede tek değer, tekrar eden sütun grubu yok. **2NF:** 1NF + bileşik anahtarlı tabloda kısmi bağımlılık yok. **3NF:** 2NF + geçişli bağımlılık yok (anahtar olmayan sütun başka anahtar olmayan sütuna bağlı değil).
- **Sürüm kontrolü (Git):** commit = anlık görüntü; küçük, açıklayıcı commit'ler; push ile GitHub'a gönderme.

## Sık yapılan hatalar (bende olmamalı)
Her şeyi tek katmanda toplamak · ilişki/anahtarları eksik tasarlamak · depoya gereksiz/gizli dosya yüklemek.
