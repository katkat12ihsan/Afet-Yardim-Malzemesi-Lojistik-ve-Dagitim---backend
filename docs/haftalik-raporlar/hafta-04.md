# Hafta 4 İlerleme Raporu — Veritabanı Tasarımı ve Veri Erişim Katmanı

**Proje:** P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım
**Geliştirilen modül:** Veritabanı ve veri erişim katmanı (backend)

## Yapılan teknik çalışmalar

| Görev (yönergeden) | Durum | Kanıt |
|---|---|---|
| Tabloların oluşturulması (migration veya script) | ✅ | `backend/data/migrations/001_ilk_sema.sql` + `migrasyonlari_uygula()` (sürüm tablosu, tek transaction) |
| İlişkiler, kısıtlar ve indeksler | ✅ | 11 tablo, PK/FK (RESTRICT/CASCADE), NOT NULL, UNIQUE, CHECK, 15 indeks |
| Örnek/sentetik veriyle doldurma | ✅ | `backend/data/ornek_veri.py`, `python -m backend.data.kurulum --ornek-veri` |
| Temel CRUD veri erişim fonksiyonları | ✅ | `backend/data/repositories/` (TemelRepository + 10 tablo repository'si + StokRepository) |

Ek olarak:
- **Backend:** `OzetServisi` (iş katmanı) panel sayılarını repository'lerden toplar.
- **Frontend:** Ana panelde 5 özet kartı var (malzeme çeşidi, depo, ihtiyaç noktası, bekleyen talep, kritik stok). Frontend veritabanını görmez, servisi kullanır.
- **Testler:** 16 yeni test (migration, CRUD, enum/tarih dönüşümü, upsert, 5 kısıt ihlali, CASCADE, transaction geri alma). Toplam 19 test, hepsi geçiyor.

## Haftalık kontrol kriterleri

- [x] İlişki ve kısıtlar çalışıyor (`sorgu_ornekleri` bölüm 7 + `tests/test_veritabani.py`)
- [x] CRUD işlemleri sorunsuz (`sorgu_ornekleri` bölüm 6 + `CrudTestleri`)
- [x] Sentetik veri KVKK'ya uygun (anonim adlar, 0555 000 00 NN, example.com)

## Gösterilecek ilerleme (demo sırası)

1. `python -m backend.data.kurulum --sifirla --ornek-veri` → migration uygulanır, veri yüklenir
2. `python -m backend.data.sorgu_ornekleri` → kayıt sayıları, JOIN'li stok listesi, öncelikli bekleyen talepler, kritik stok, GROUP BY, CRUD, 5 kısıt ihlalinin reddedilmesi + CASCADE (çıktı: `docs/ekran-goruntuleri/hafta-04-sorgu-ciktisi.txt`)
3. `python main.py` → ana paneldeki özet kartları veritabanından geliyor
4. `python -m unittest` → 19 test OK

## Karşılaşılan sorunlar ve çözümler

- SQLite'ta yabancı anahtar kontrolü varsayılan kapalı → her bağlantıda `PRAGMA foreign_keys = ON`; testte doğrulanıyor.
- `executescript()` kendi başına transaction açmıyor → migration metni `BEGIN; … COMMIT;` ile sarıldı, hata olursa `rollback()`.
- Enum ve tarih alanları SQLite'ta metin/sayı → `TemelRepository` dataclass tip bilgisine bakarak otomatik dönüştürüyor.

## Gelecek hafta (Hafta 5)

Kullanıcı yönetimi ve kimlik doğrulama: `002_kullanici.sql` migration'ı (kullanıcı + rol), parola hash (salt'lı), giriş penceresi (frontend), rol tabanlı erişim (depo / kurum).

## Ekran görüntüleri

- `docs/ekran-goruntuleri/hafta-04-ana-panel.png`
- `docs/ekran-goruntuleri/hafta-04-sorgu-ciktisi.txt`

## Yapay zekâ kullanımı özeti

Claude; mimari/şema önerisi, kod iskeleti ve test senaryoları için kullanıldı. Ayrıntı: [AI kullanım günlüğü](../ai-kullanim-gunlugu.md) (Kayıt 4–6). Önerilerin doğrulaması testler ve demo komutlarıyla yapıldı.

## Ekler — commit bağlantıları

- [60fc2ee](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/60fc2ee) backend: ilk şema migration'ı (11 tablo, FK/CHECK/UNIQUE kısıtları, indeksler) ve migration çalıştırıcısı
- [4b83a2e](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/4b83a2e) backend: CRUD repository'leri (TemelRepository, tablo repository'leri, bileşik anahtarlı StokRepository)
- [1c6f03d](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/1c6f03d) backend: KVKK uyumlu sentetik örnek veri, kurulum komutu ve sorgu/kısıt demosu
- [909a71f](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/909a71f) backend: panel özeti servisi (OzetServisi)
- [faddbbd](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/faddbbd) frontend: ana panelde veritabanı özet kartları; açılışta migration
- [2cbc2e1](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/2cbc2e1) test: veritabanı, CRUD, kısıt ve transaction testleri (16 test)
- [c923b57](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/c923b57) docs: hafta 4 veritabanı belgesi, ilerleme raporu, AI günlüğü, sözlü hazırlık, ekran görüntüleri
