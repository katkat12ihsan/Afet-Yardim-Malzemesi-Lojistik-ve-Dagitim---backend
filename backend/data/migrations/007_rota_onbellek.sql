-- =====================================================================
-- Migration 007 - Rota önbelleği (Hafta 9: harita/rota API)
--
-- Harita servisinin ücretsiz planında istek sınırı var (dakikada 40, günde 2000).
-- Depolar ve ihtiyaç noktaları yer değiştirmediği için aynı depo -> nokta rotası
-- her açılışta yeniden sorulmaz; servisten gelen sonuç burada saklanır.
--
--   koordinatlar : rota hesaplanırken kullanılan "enlem,boylam;enlem,boylam".
--                  Depo ya da noktanın koordinatı değişirse eşleşmez, rota
--                  yeniden sorulur (eski kayıt kendiliğinden geçersiz olur).
--   geometri     : rota çizgisi, JSON [[enlem, boylam], ...]
--   Yalnızca SERVİSTEN gelen rota saklanır; kuş uçuşu tahmin saklanmaz
--   (servis düzelince gerçek rota alınsın).
-- =====================================================================

CREATE TABLE rota_onbellek (
    depo_id             INTEGER NOT NULL REFERENCES depo(id) ON DELETE CASCADE,
    ihtiyac_noktasi_id  INTEGER NOT NULL REFERENCES ihtiyac_noktasi(id) ON DELETE CASCADE,
    koordinatlar        TEXT    NOT NULL,
    mesafe_km           REAL    NOT NULL CHECK (mesafe_km >= 0),
    sure_dk             REAL    NOT NULL CHECK (sure_dk >= 0),
    geometri            TEXT    NOT NULL,
    tarih               TEXT    NOT NULL,
    PRIMARY KEY (depo_id, ihtiyac_noktasi_id)
);
