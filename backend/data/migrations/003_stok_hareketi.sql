-- =====================================================================
-- Migration 003 - Stok hareketi (Hafta 6: Envanter Yönetimi)
--
-- `stok` tablosu "şu an ne kadar var?" sorusunu cevaplar.
-- `stok_hareketi` ise "neden bu kadar?" sorusunu: her giriş, çıkış ve sayım
-- düzeltmesi silinmeyen bir satır olarak kaydedilir (denetim izi).
-- Kural: bir depodaki bir malzemenin stoğu = o ikilinin hareketlerinin toplamı.
-- Stok satırı ve hareket satırı her zaman TEK transaction içinde yazılır.
-- =====================================================================

CREATE TABLE stok_hareketi (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    depo_id         INTEGER NOT NULL REFERENCES depo(id)      ON DELETE RESTRICT,
    malzeme_id      INTEGER NOT NULL REFERENCES malzeme(id)   ON DELETE RESTRICT,
    tur             TEXT    NOT NULL CHECK (tur IN ('Açılış', 'Giriş', 'Çıkış', 'Sayım')),
    degisim         REAL    NOT NULL CHECK (degisim <> 0),          -- + giriş, - çıkış
    onceki_miktar   REAL    NOT NULL CHECK (onceki_miktar >= 0),
    sonraki_miktar  REAL    NOT NULL CHECK (sonraki_miktar >= 0),   -- stok eksiye düşemez
    aciklama        TEXT    NOT NULL DEFAULT '',
    -- Hareketi yapan kullanıcı. Geçmişi olan kullanıcı silinemez (pasifleştirilir).
    -- NULL = sistem (ör. açılış devri).
    kullanici_id    INTEGER REFERENCES kullanici(id) ON DELETE RESTRICT,
    tarih           TEXT    NOT NULL,
    -- Tutarlılık kuralları veritabanı seviyesinde:
    CHECK (abs(sonraki_miktar - (onceki_miktar + degisim)) < 0.000001),
    CHECK ((tur IN ('Açılış', 'Giriş') AND degisim > 0)
        OR (tur = 'Çıkış' AND degisim < 0)
        OR  tur = 'Sayım')
);

CREATE INDEX idx_hareket_depo_malzeme ON stok_hareketi(depo_id, malzeme_id, tarih);
CREATE INDEX idx_hareket_malzeme      ON stok_hareketi(malzeme_id);
CREATE INDEX idx_hareket_kullanici    ON stok_hareketi(kullanici_id);

-- Bu migration'dan önce oluşmuş stoklar için açılış hareketi (devir):
-- böylece "stok = hareketlerin toplamı" kuralı mevcut veritabanlarında da sağlanır.
INSERT INTO stok_hareketi (depo_id, malzeme_id, tur, degisim, onceki_miktar, sonraki_miktar,
                           aciklama, kullanici_id, tarih)
SELECT depo_id, malzeme_id, 'Açılış', miktar, 0, miktar,
       'Hafta 6 öncesi stok devri', NULL, strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime')
FROM stok
WHERE miktar > 0;
