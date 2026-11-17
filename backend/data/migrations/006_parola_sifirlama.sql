-- =====================================================================
-- Migration 006 - Yönetici tarafından parola sıfırlama
--
-- Uygulama internetsiz çalıştığı için "şifremi unuttum" e-posta/SMS ile
-- yapılamaz. Parolasını unutan kullanıcının parolasını Yönetici sıfırlar:
-- sistem tek kullanımlık geçici bir parola üretir, kullanıcı ilk girişte
-- kendi parolasını belirlemek zorundadır.
--
--   kullanici.parola_degistirmeli : 1 ise giriş yapılamaz, önce yeni parola
--                                   belirlenir (oturum açılmaz).
--   parola_sifirlama              : kim, kimin parolasını, ne zaman sıfırladı
--                                   (silinmeyen denetim izi). Parolanın
--                                   kendisi burada da tutulmaz.
-- =====================================================================

ALTER TABLE kullanici
    ADD COLUMN parola_degistirmeli INTEGER NOT NULL DEFAULT 0 CHECK (parola_degistirmeli IN (0, 1));

CREATE TABLE parola_sifirlama (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_id    INTEGER NOT NULL REFERENCES kullanici(id) ON DELETE RESTRICT,  -- parolası sıfırlanan
    sifirlayan_id   INTEGER NOT NULL REFERENCES kullanici(id) ON DELETE RESTRICT,  -- işlemi yapan Yönetici
    tarih           TEXT    NOT NULL,
    CHECK (kullanici_id <> sifirlayan_id)    -- kişi kendi parolasını bu yolla sıfırlayamaz
);

CREATE INDEX idx_parola_sifirlama_kullanici ON parola_sifirlama(kullanici_id);
