-- =====================================================================
-- Migration 001 - İlk şema
-- Kaynak: docs/ER-Diyagrami.md (11 tablo)
--
-- Kısıt kuralları (referans bütünlüğü):
--   ON DELETE RESTRICT : Kullanımda olan kayıt silinemez
--                        (ör. stoğu/bağışı olan malzeme silinemez).
--   ON DELETE CASCADE  : "Başlık" silinince "kalemleri" de silinir
--                        (bağış -> bağış kalemleri, dağıtım -> dağıtım kalemleri).
-- SQLite yabancı anahtar kolonlarına otomatik indeks EKLEMEZ;
-- JOIN ve silme kontrolleri hızlı olsun diye FK kolonlarına indeks eklendi.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Tanım tabloları
-- ---------------------------------------------------------------------
CREATE TABLE kategori (
    id  INTEGER PRIMARY KEY AUTOINCREMENT,
    ad  TEXT    NOT NULL UNIQUE CHECK (length(trim(ad)) > 0)
);

CREATE TABLE malzeme (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    kategori_id  INTEGER NOT NULL
                 REFERENCES kategori(id) ON DELETE RESTRICT,
    ad           TEXT    NOT NULL UNIQUE CHECK (length(trim(ad)) > 0),
    birim        TEXT    NOT NULL CHECK (birim IN ('adet', 'koli', 'paket', 'kg', 'litre')),
    aciklama     TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE depo (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ad      TEXT    NOT NULL UNIQUE,
    il      TEXT    NOT NULL,
    ilce    TEXT    NOT NULL,
    adres   TEXT    NOT NULL DEFAULT '',
    enlem   REAL    CHECK (enlem  IS NULL OR enlem  BETWEEN  -90 AND  90),
    boylam  REAL    CHECK (boylam IS NULL OR boylam BETWEEN -180 AND 180)
);

CREATE TABLE ihtiyac_noktasi (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ad             TEXT    NOT NULL,
    il             TEXT    NOT NULL,
    ilce           TEXT    NOT NULL,
    adres          TEXT    NOT NULL DEFAULT '',
    enlem          REAL    CHECK (enlem  IS NULL OR enlem  BETWEEN  -90 AND  90),
    boylam         REAL    CHECK (boylam IS NULL OR boylam BETWEEN -180 AND 180),
    nufus_tahmini  INTEGER NOT NULL DEFAULT 0 CHECK (nufus_tahmini >= 0),
    oncelik        INTEGER NOT NULL DEFAULT 2 CHECK (oncelik BETWEEN 1 AND 4)  -- 1 Düşük .. 4 Kritik
);

CREATE TABLE bagisci (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ad       TEXT    NOT NULL,
    tur      TEXT    NOT NULL DEFAULT 'Bireysel' CHECK (tur IN ('Bireysel', 'Kurumsal')),
    telefon  TEXT    NOT NULL DEFAULT '',
    eposta   TEXT    NOT NULL DEFAULT ''
);

-- ---------------------------------------------------------------------
-- Bağış (giriş) tarafı
-- ---------------------------------------------------------------------
CREATE TABLE bagis (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    bagisci_id  INTEGER NOT NULL REFERENCES bagisci(id) ON DELETE RESTRICT,
    depo_id     INTEGER NOT NULL REFERENCES depo(id)    ON DELETE RESTRICT,
    tarih       TEXT    NOT NULL,                       -- ISO 8601: 2026-10-09T14:30:00
    aciklama    TEXT    NOT NULL DEFAULT ''
);

-- Bağış <-> Malzeme N-N ilişkisinin ara tablosu
CREATE TABLE bagis_kalemi (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    bagis_id             INTEGER NOT NULL REFERENCES bagis(id)   ON DELETE CASCADE,
    malzeme_id           INTEGER NOT NULL REFERENCES malzeme(id) ON DELETE RESTRICT,
    miktar               REAL    NOT NULL CHECK (miktar > 0),
    son_kullanma_tarihi  TEXT                                   -- ISO 8601 tarih, boş olabilir
);

-- Depo <-> Malzeme N-N ilişkisi; bileşik birincil anahtar:
-- bir depoda bir malzemenin yalnızca TEK stok satırı olabilir.
CREATE TABLE stok (
    depo_id        INTEGER NOT NULL REFERENCES depo(id)    ON DELETE RESTRICT,
    malzeme_id     INTEGER NOT NULL REFERENCES malzeme(id) ON DELETE RESTRICT,
    miktar         REAL    NOT NULL DEFAULT 0 CHECK (miktar >= 0),        -- stok eksiye düşemez
    kritik_seviye  REAL    NOT NULL DEFAULT 0 CHECK (kritik_seviye >= 0),
    PRIMARY KEY (depo_id, malzeme_id)
);

-- ---------------------------------------------------------------------
-- İhtiyaç ve dağıtım (çıkış) tarafı
-- ---------------------------------------------------------------------
CREATE TABLE ihtiyac_talebi (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ihtiyac_noktasi_id  INTEGER NOT NULL REFERENCES ihtiyac_noktasi(id) ON DELETE CASCADE,
    malzeme_id          INTEGER NOT NULL REFERENCES malzeme(id)         ON DELETE RESTRICT,
    miktar              REAL    NOT NULL CHECK (miktar > 0),
    talep_tarihi        TEXT    NOT NULL,
    durum               TEXT    NOT NULL DEFAULT 'Bekliyor'
                        CHECK (durum IN ('Bekliyor', 'Kısmen karşılandı', 'Karşılandı', 'İptal'))
);

CREATE TABLE dagitim (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    depo_id             INTEGER NOT NULL REFERENCES depo(id)            ON DELETE RESTRICT,
    ihtiyac_noktasi_id  INTEGER NOT NULL REFERENCES ihtiyac_noktasi(id) ON DELETE RESTRICT,
    planlanan_tarih     TEXT    NOT NULL,
    teslim_tarihi       TEXT,
    durum               TEXT    NOT NULL DEFAULT 'Planlandı'
                        CHECK (durum IN ('Planlandı', 'Yolda', 'Teslim edildi', 'İptal')),
    arac_plaka          TEXT    NOT NULL DEFAULT '',
    -- İş kuralı veritabanı seviyesinde: teslim edilen dağıtımın teslim tarihi olmalı
    CHECK (durum <> 'Teslim edildi' OR teslim_tarihi IS NOT NULL)
);

-- Dağıtım <-> Malzeme N-N ilişkisinin ara tablosu
CREATE TABLE dagitim_kalemi (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    dagitim_id  INTEGER NOT NULL REFERENCES dagitim(id) ON DELETE CASCADE,
    malzeme_id  INTEGER NOT NULL REFERENCES malzeme(id) ON DELETE RESTRICT,
    miktar      REAL    NOT NULL CHECK (miktar > 0)
);

-- ---------------------------------------------------------------------
-- İndeksler
-- ---------------------------------------------------------------------
-- Yabancı anahtar kolonları (JOIN'ler ve RESTRICT/CASCADE kontrolleri için)
CREATE INDEX idx_malzeme_kategori        ON malzeme(kategori_id);
CREATE INDEX idx_bagis_bagisci           ON bagis(bagisci_id);
CREATE INDEX idx_bagis_depo              ON bagis(depo_id);
CREATE INDEX idx_bagis_kalemi_bagis      ON bagis_kalemi(bagis_id);
CREATE INDEX idx_bagis_kalemi_malzeme    ON bagis_kalemi(malzeme_id);
CREATE INDEX idx_stok_malzeme            ON stok(malzeme_id);   -- depo_id zaten PK'nın ilk kolonu
CREATE INDEX idx_talep_nokta             ON ihtiyac_talebi(ihtiyac_noktasi_id);
CREATE INDEX idx_talep_malzeme           ON ihtiyac_talebi(malzeme_id);
CREATE INDEX idx_dagitim_depo            ON dagitim(depo_id);
CREATE INDEX idx_dagitim_nokta           ON dagitim(ihtiyac_noktasi_id);
CREATE INDEX idx_dagitim_kalemi_dagitim  ON dagitim_kalemi(dagitim_id);
CREATE INDEX idx_dagitim_kalemi_malzeme  ON dagitim_kalemi(malzeme_id);

-- Sık filtrelenecek kolonlar (bekleyen talepler, yoldaki dağıtımlar, bölgeye göre arama)
CREATE INDEX idx_talep_durum             ON ihtiyac_talebi(durum);
CREATE INDEX idx_dagitim_durum           ON dagitim(durum);
CREATE INDEX idx_ihtiyac_noktasi_bolge   ON ihtiyac_noktasi(il, ilce);
