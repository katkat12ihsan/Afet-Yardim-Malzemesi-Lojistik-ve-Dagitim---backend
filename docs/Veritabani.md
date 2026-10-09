# Veritabanı Tasarımı ve Veri Erişim Katmanı (Hafta 4)

Veritabanı: **SQLite** (`data/afet_lojistik.db`, depoya yüklenmez). Şema: [backend/data/migrations/001_ilk_sema.sql](../backend/data/migrations/001_ilk_sema.sql) — ER diyagramındaki 11 tablonun birebir karşılığı.

## Kurulum

```bash
python -m backend.data.kurulum --ornek-veri            # şema + sentetik veri
python -m backend.data.kurulum --sifirla --ornek-veri  # sıfırdan kur
python -m backend.data.sorgu_ornekleri                 # demo: sorgular + kısıt denemeleri
python -m unittest                                     # 19 test
```

## Migration

Şema değişiklikleri numaralı SQL dosyalarıdır (`001_ilk_sema.sql`, ileride `002_kullanici.sql` …). `migrasyonlari_uygula()`:

1. `sema_surumu` tablosunu oluşturur (yoksa),
2. henüz uygulanmamış dosyaları numara sırasıyla çalıştırır,
3. her dosyayı ve sürüm kaydını **tek transaction** içinde yapar → yarım kalan migration olmaz.

Uygulama her açılışta (`main.py`) bunu çağırır; şema güncelse hiçbir şey yapmaz. Faydası: şema Git'te izlenir, her bilgisayarda veritabanı aynı adımlarla aynı hale gelir, Hafta 5'teki kullanıcı tablosu yeni bir dosya olarak eklenir (eski veri silinmez).

## Kısıtlar

| Kısıt | Nerede | Ne sağlar |
|---|---|---|
| `PRIMARY KEY` | Her tabloda `id`; `stok`'ta bileşik `(depo_id, malzeme_id)` | Satırı benzersiz tanımlar; bir depoda bir malzemenin tek stok satırı olur |
| `FOREIGN KEY ... ON DELETE RESTRICT` | `malzeme.kategori_id`, `bagis.depo_id`, `stok.malzeme_id` … | Kullanımdaki kayıt silinemez (stoğu/bağışı olan malzeme silinemez) |
| `FOREIGN KEY ... ON DELETE CASCADE` | `bagis_kalemi.bagis_id`, `dagitim_kalemi.dagitim_id`, `ihtiyac_talebi.ihtiyac_noktasi_id` | Başlık silinince kalemleri de silinir, sahipsiz satır kalmaz |
| `NOT NULL` | Zorunlu alanlar | Eksik veri girilemez |
| `UNIQUE` | `kategori.ad`, `malzeme.ad`, `depo.ad` | Aynı adla iki kayıt olmaz |
| `CHECK (miktar > 0)` | Bağış/dağıtım kalemi, talep | Sıfır/eksi miktar girilemez |
| `CHECK (miktar >= 0)` | `stok` | Stok eksiye düşemez (fazla dağıtım veritabanında da engellenir) |
| `CHECK (... IN (...))` | `birim`, `durum`, `tur` | Yalnızca tanımlı değerler |
| `CHECK (oncelik BETWEEN 1 AND 4)`, enlem/boylam aralıkları | `ihtiyac_noktasi`, `depo` | Geçersiz öncelik/koordinat girilemez |
| Tablo `CHECK` | `dagitim` | "Teslim edildi" durumundaki dağıtımın teslim tarihi olmak zorunda |

> SQLite'ta yabancı anahtar kontrolü **varsayılan olarak kapalıdır**; `baglanti_ac()` her bağlantıda `PRAGMA foreign_keys = ON` çalıştırır.

### Elle yazılıp açıklanan ilişki + kısıt örneği

```sql
CREATE TABLE bagis_kalemi (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    bagis_id    INTEGER NOT NULL REFERENCES bagis(id)   ON DELETE CASCADE,
    malzeme_id  INTEGER NOT NULL REFERENCES malzeme(id) ON DELETE RESTRICT,
    miktar      REAL    NOT NULL CHECK (miktar > 0),
    ...
);
```

- Bağış ile malzeme arasında **N-N** ilişki var; `bagis_kalemi` bu ilişkiyi iki adet 1-N'ye böler ve ilişkiye ait bilgiyi (`miktar`) taşır.
- `bagis_id` → **CASCADE**: kalem bağışın parçasıdır, bağış yoksa kalemin anlamı yoktur.
- `malzeme_id` → **RESTRICT**: malzeme tanımı silinirse geçmiş bağış kayıtları anlamsızlaşır (şeffaflık raporu bozulur), bu yüzden silme engellenir.
- `CHECK (miktar > 0)`: 0 veya eksi bağış iş mantığına aykırıdır; kural arayüzde de olacak ama veritabanı son savunma hattıdır.

## İndeksler

- **FK kolonları** (`idx_bagis_depo`, `idx_stok_malzeme` …): SQLite FK kolonlarına otomatik indeks koymaz. JOIN sorguları ve RESTRICT/CASCADE kontrolleri (silinen satıra bağlı kayıt var mı?) bu indekslerle tüm tabloyu taramadan yapılır.
- **Filtre kolonları**: `ihtiyac_talebi(durum)`, `dagitim(durum)`, `ihtiyac_noktasi(il, ilce)` — "bekleyen talepler", "yoldaki dağıtımlar", "bölgeye göre" sorguları sık çalışacak.
- **Eklenmeyenler:** `aciklama`, `telefon` gibi kolonlar aranmadığı için indekslenmedi. Her indeks diskte yer kaplar ve her INSERT/UPDATE'i yavaşlatır.
- `stok(depo_id)` için ayrı indeks yok: bileşik PK `(depo_id, malzeme_id)` zaten `depo_id` ile başlayan bir indekstir.

## ORM mi saf SQL mi?

**Saf SQL + repository deseni** seçildi (`sqlite3` standart kütüphanesi):

| | Saf SQL (seçilen) | ORM (SQLAlchemy vb.) |
|---|---|---|
| Öğrenme | SQL'in kendisi görülür, sözlüde açıklanabilir | Arka planda üretilen SQL gizlidir |
| Bağımlılık | Yok (Python ile gelir) | Ek paket |
| Kod miktarı | Ortak CRUD `TemelRepository`'de bir kez yazıldı | Daha az |
| Veritabanı değiştirme | Repository'ler değişir | Çoğunlukla ayar değişikliği |

Tekrarı azaltmak için `TemelRepository`, dataclass alan adlarını kolon adı olarak kullanarak ekle/getir/listele/güncelle/sil işlemlerini tek yerde yapar. Tabloya özel sorgular (JOIN, filtre) alt sınıflarda yazılır. Değerler **her zaman `?` parametresiyle** gönderilir (SQL injection'a karşı).

## Transaction

Repository metotları commit etmez. Birden çok tabloya yazan işlemler `with islem(baglanti):` bloğunda yapılır: blok hatasız biterse `COMMIT`, hata olursa `ROLLBACK`. Örnek: Hafta 7'de "bağış kaydet" = bağış satırı + kalemleri + stok artışı; biri başarısız olursa hiçbiri kaydedilmez.

## Sentetik veri (KVKK)

`backend/data/ornek_veri.py`: 5 kategori, 12 malzeme, 3 depo, 5 ihtiyaç noktası, 5 bağışçı, 6 bağış (16 kalem), 10 talep, 4 dağıtım. Bağışçılar "Anonim Bağışçı N" / "Örnek … A.Ş.", telefonlar `0555 000 00 NN`, e-postalar `example.com`. **Gerçek kişisel veri yoktur.** Stok, bağışlardan çıkmış dağıtımlar düşülerek hesaplanır (stok = giren − çıkan), böylece veri tutarlıdır.
