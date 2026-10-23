-- =====================================================================
-- Migration 004 - Rol değişikliği geçmişi (Kullanıcılar sayfası: rolü düzenle)
--
-- Bir kullanıcının rolü (ve Depo rolündeyse bağlı deposu) yalnızca Yönetici
-- tarafından değiştirilir. Her değişiklik silinmeyen bir satır olarak tutulur:
-- kim, kimi, ne zaman, hangi rol/depodan hangisine değiştirdi (denetim izi).
-- =====================================================================

CREATE TABLE rol_degisikligi (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_id    INTEGER NOT NULL REFERENCES kullanici(id) ON DELETE RESTRICT,  -- rolü değişen
    eski_rol        TEXT    NOT NULL CHECK (eski_rol IN ('Yönetici', 'Kurum', 'Depo')),
    yeni_rol        TEXT    NOT NULL CHECK (yeni_rol IN ('Yönetici', 'Kurum', 'Depo')),
    eski_depo_id    INTEGER REFERENCES depo(id) ON DELETE RESTRICT,
    yeni_depo_id    INTEGER REFERENCES depo(id) ON DELETE RESTRICT,
    degistiren_id   INTEGER NOT NULL REFERENCES kullanici(id) ON DELETE RESTRICT,  -- işlemi yapan Yönetici
    tarih           TEXT    NOT NULL,
    -- Gerçekten bir değişiklik olmalı; kişi kendi rolünü değiştiremez
    CHECK (eski_rol <> yeni_rol OR COALESCE(eski_depo_id, 0) <> COALESCE(yeni_depo_id, 0)),
    CHECK (kullanici_id <> degistiren_id),
    CHECK (yeni_rol <> 'Depo' OR yeni_depo_id IS NOT NULL)
);

CREATE INDEX idx_rol_degisikligi_kullanici  ON rol_degisikligi(kullanici_id);
CREATE INDEX idx_rol_degisikligi_degistiren ON rol_degisikligi(degistiren_id);
