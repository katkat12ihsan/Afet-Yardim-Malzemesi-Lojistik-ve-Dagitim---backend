-- =====================================================================
-- Migration 002 - Kullanıcı, rol ve oturum (Hafta 5)
--
-- Parola ASLA düz metin saklanmaz. parola_hash kolonu şu biçimdedir:
--   pbkdf2_sha256$<iterasyon>$<tuz_hex>$<özet_hex>
-- Tuz (salt) her kullanıcı için rastgele üretilir ve hash ile birlikte
-- saklanır; aynı parolayı kullanan iki kişinin hash'i farklı olur.
--
-- Oturum token'ı da düz saklanmaz; yalnızca SHA-256 özeti tutulur.
-- Veritabanı ele geçirilse bile geçerli bir token elde edilemez.
-- =====================================================================

CREATE TABLE kullanici (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_adi     TEXT    NOT NULL UNIQUE COLLATE NOCASE   -- "Ali" ile "ali" aynı kullanıcı
                      CHECK (length(kullanici_adi) BETWEEN 3 AND 30),
    ad_soyad          TEXT    NOT NULL CHECK (length(trim(ad_soyad)) > 0),
    parola_hash       TEXT    NOT NULL CHECK (parola_hash LIKE 'pbkdf2_sha256$%'),
    rol               TEXT    NOT NULL CHECK (rol IN ('Yönetici', 'Kurum', 'Depo')),
    depo_id           INTEGER REFERENCES depo(id) ON DELETE RESTRICT,
    aktif             INTEGER NOT NULL DEFAULT 1 CHECK (aktif IN (0, 1)),
    basarisiz_giris   INTEGER NOT NULL DEFAULT 0 CHECK (basarisiz_giris >= 0),
    kilitli_bitis     TEXT,                                   -- kaba kuvvet koruması
    olusturma_tarihi  TEXT    NOT NULL,
    son_giris         TEXT,
    -- Depo görevlisi mutlaka bir depoya bağlı olmalı
    CHECK (rol <> 'Depo' OR depo_id IS NOT NULL)
);

CREATE TABLE oturum (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_id   INTEGER NOT NULL REFERENCES kullanici(id) ON DELETE CASCADE,
    token_hash     TEXT    NOT NULL UNIQUE,
    olusturma      TEXT    NOT NULL,
    son_kullanma   TEXT    NOT NULL,
    cikis_zamani   TEXT,                                      -- dolu ise oturum kapatılmış
    CHECK (son_kullanma > olusturma)
);

CREATE INDEX idx_kullanici_depo    ON kullanici(depo_id);
CREATE INDEX idx_oturum_kullanici  ON oturum(kullanici_id);
