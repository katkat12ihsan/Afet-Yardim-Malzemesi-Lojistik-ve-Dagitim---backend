# ER Diyagramı — P16 Afet Yardım Malzemesi Lojistik ve Dağıtım

Görsel sürüm: [er-diyagrami.svg](er-diyagrami.svg). Fiziksel şema (SQL): [001_ilk_sema.sql](../backend/data/migrations/001_ilk_sema.sql), açıklaması: [Veritabani.md](Veritabani.md). Aşağıdaki Mermaid diyagramı GitHub'da otomatik çizilir.

```mermaid
erDiagram
    KATEGORI ||--o{ MALZEME : "sınıflandırır"
    BAGISCI  ||--o{ BAGIS : "yapar"
    DEPO     ||--o{ BAGIS : "teslim alır"
    BAGIS    ||--|{ BAGIS_KALEMI : "içerir"
    MALZEME  ||--o{ BAGIS_KALEMI : "bağışlanır"
    DEPO     ||--o{ STOK : "barındırır"
    MALZEME  ||--o{ STOK : "stoklanır"
    IHTIYAC_NOKTASI ||--o{ IHTIYAC_TALEBI : "talep eder"
    MALZEME  ||--o{ IHTIYAC_TALEBI : "talep edilir"
    DEPO     ||--o{ DAGITIM : "gönderir"
    IHTIYAC_NOKTASI ||--o{ DAGITIM : "teslim alır"
    DAGITIM  ||--|{ DAGITIM_KALEMI : "içerir"
    DEPO     |o--o{ KULLANICI : "görevlisi (Depo rolü)"
    KULLANICI ||--o{ OTURUM : "açar"
    MALZEME  ||--o{ DAGITIM_KALEMI : "dağıtılır"

    KATEGORI {
        int id PK
        string ad UK
    }
    MALZEME {
        int id PK
        int kategori_id FK
        string ad
        string birim
        string aciklama
    }
    DEPO {
        int id PK
        string ad
        string il
        string ilce
        string adres
        float enlem
        float boylam
    }
    BAGISCI {
        int id PK
        string ad
        string tur
        string telefon
        string eposta
    }
    BAGIS {
        int id PK
        int bagisci_id FK
        int depo_id FK
        datetime tarih
        string aciklama
    }
    BAGIS_KALEMI {
        int id PK
        int bagis_id FK
        int malzeme_id FK
        float miktar
        date son_kullanma_tarihi
    }
    STOK {
        int depo_id PK,FK
        int malzeme_id PK,FK
        float miktar
        float kritik_seviye
    }
    IHTIYAC_NOKTASI {
        int id PK
        string ad
        string il
        string ilce
        string adres
        float enlem
        float boylam
        int nufus_tahmini
        int oncelik
    }
    IHTIYAC_TALEBI {
        int id PK
        int ihtiyac_noktasi_id FK
        int malzeme_id FK
        float miktar
        datetime talep_tarihi
        string durum
    }
    DAGITIM {
        int id PK
        int depo_id FK
        int ihtiyac_noktasi_id FK
        datetime planlanan_tarih
        datetime teslim_tarihi
        string durum
        string arac_plaka
    }
    KULLANICI {
        int id PK
        string kullanici_adi UK
        string ad_soyad
        string parola_hash
        string rol
        int depo_id FK
        bool aktif
        int basarisiz_giris
        datetime kilitli_bitis
        datetime olusturma_tarihi
        datetime son_giris
    }
    OTURUM {
        int id PK
        int kullanici_id FK
        string token_hash UK
        datetime olusturma
        datetime son_kullanma
        datetime cikis_zamani
    }
    DAGITIM_KALEMI {
        int id PK
        int dagitim_id FK
        int malzeme_id FK
        float miktar
    }
```

## Varlıklar

| Varlık | Açıklama | Birincil anahtar |
|---|---|---|
| **Kategori** | Malzeme grubu (Gıda, Barınma, Hijyen, Sağlık…) | `id` |
| **Malzeme** | Dağıtılabilen ürün tanımı (birimiyle: adet, koli, kg…) | `id` |
| **Depo** | Bağışların toplandığı ve dağıtımın çıktığı yer | `id` |
| **Bağışçı** | Bağışı yapan kişi/kurum (yalnızca **sentetik** veri) | `id` |
| **Bağış** | Bir bağışçının bir depoya yaptığı tek teslimat (başlık) | `id` |
| **Bağış Kalemi** | Bağışın içindeki malzeme + miktar satırları | `id` |
| **Stok** | Hangi depoda hangi malzemeden ne kadar olduğu | `(depo_id, malzeme_id)` bileşik |
| **İhtiyaç Noktası** | Yardım ulaştırılacak yer (çadır kent, okul…) | `id` |
| **İhtiyaç Talebi** | Bir noktanın bir malzemeye olan ihtiyacı | `id` |
| **Dağıtım (dağıtım kaydı)** | Depo → ihtiyaç noktası sevkiyatı (başlık) | `id` |
| **Dağıtım Kalemi** | Sevkiyattaki malzeme + miktar satırları | `id` |

## İlişkiler

| İlişki | Tür | Nasıl modellendi |
|---|---|---|
| Kategori – Malzeme | 1-N | `malzeme.kategori_id` FK |
| Bağışçı – Bağış | 1-N | `bagis.bagisci_id` FK |
| Depo – Bağış | 1-N | `bagis.depo_id` FK |
| Bağış – Malzeme | **N-N** | `BAGIS_KALEMI` ara tablosu |
| Depo – Malzeme | **N-N** | `STOK` ara tablosu (bileşik PK) |
| İhtiyaç Noktası – Malzeme | **N-N** | `IHTIYAC_TALEBI` ara tablosu |
| Depo – İhtiyaç Noktası | **N-N** | `DAGITIM` (bir depo birçok noktaya, bir nokta birçok depodan) |
| Dağıtım – Malzeme | **N-N** | `DAGITIM_KALEMI` ara tablosu |

1-1 ilişkiye bu projede gerek yok. Örnek: ileride her depoya tek bir sorumlu kullanıcı atanırsa `Depo – DepoSorumlusu` 1-1 olurdu.

## Normalizasyon (1NF – 3NF)

- **1NF:** Her hücrede tek değer var. Bir bağışta birden çok malzeme olabildiği için malzemeler bağış tablosuna sütun olarak (`malzeme1, malzeme2…`) yazılmadı; ayrı `BAGIS_KALEMI` satırları olarak tutuldu.
- **2NF:** Bileşik anahtarlı `STOK` tablosunda `miktar` ve `kritik_seviye` anahtarın tamamına (depo **ve** malzeme) bağlı. Malzeme adı gibi yalnızca `malzeme_id`'ye bağlı bilgi STOK'ta tutulmuyor.
- **3NF:** Geçişli bağımlılık yok. Örneğin malzemenin kategori adı `MALZEME` içinde tekrar yazılmıyor; `kategori_id` üzerinden `KATEGORI` tablosundan geliyor.

## Tasarım kararları

- **Başlık + kalem yapısı** (Bağış/BağışKalemi, Dağıtım/DağıtımKalemi): fatura mantığı; bir teslimatta birden çok malzeme olabilir. Şeffaflık raporunda (Hafta 11-12) "bu bağış hangi dağıtımla nereye gitti" sorusu bu tablolar üzerinden izlenecek.
- **Stok ayrı tablo:** Stok miktarı her seferinde bağış − dağıtım toplamından da hesaplanabilirdi; ama hızlı sorgu ve kritik seviye uyarısı (Hafta 6) için ayrı tutuldu. Tutarlılık, giriş/çıkış işlemlerinin iş katmanında tek yerden yapılmasıyla sağlanacak.
- **Konum (enlem/boylam)** Depo ve İhtiyaç Noktası'nda tutuldu: Hafta 9 harita/rota API'si ve Hafta 10 yapay zekâ rota önerisi için gerekli.
- **Kullanıcı ve Oturum tabloları** Hafta 5'te `002_kullanici.sql` migration'ı ile eklendi (görsel SVG ilk 11 tabloyu gösterir). Depo rolündeki kullanıcı `depo_id` ile bir depoya bağlıdır; bir kullanıcının birden çok oturumu olabilir (1-N). Ayrıntı: [Guvenlik-Notu.md](Guvenlik-Notu.md).
