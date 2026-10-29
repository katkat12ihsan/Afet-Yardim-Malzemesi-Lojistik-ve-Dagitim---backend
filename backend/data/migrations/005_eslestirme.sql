-- =====================================================================
-- Migration 005 - İhtiyaç eşleştirme (Hafta 7: Çekirdek Modül B)
--
-- Her dağıtım kalemi artık hangi ihtiyaç talebini karşıladığını bilir.
-- Böylece bir talebin "karşılanan" miktarı hesaplanabilir:
--   karşılanan = iptal edilmemiş dağıtımlardaki, bu talebe bağlı kalemlerin toplamı
--   kalan      = talep miktarı - karşılanan
-- ve talep durumu bu sayılardan türetilir:
--   karşılanan = 0            -> Bekliyor
--   0 < karşılanan < miktar   -> Kısmen karşılandı
--   karşılanan >= miktar      -> Karşılandı
-- ('İptal' talepler kullanıcı kararıdır, yeniden hesaplanmaz.)
-- =====================================================================

ALTER TABLE dagitim_kalemi
    ADD COLUMN ihtiyac_talebi_id INTEGER REFERENCES ihtiyac_talebi(id) ON DELETE RESTRICT;

CREATE INDEX idx_dagitim_kalemi_talep ON dagitim_kalemi(ihtiyac_talebi_id);

-- Bu migration'dan önce oluşmuş dağıtım kalemlerini, aynı ihtiyaç noktasının aynı
-- malzeme için açtığı en eski (iptal edilmemiş) talebe bağla.
UPDATE dagitim_kalemi
SET ihtiyac_talebi_id = (
    SELECT t.id
    FROM ihtiyac_talebi t
    JOIN dagitim d ON d.id = dagitim_kalemi.dagitim_id
    WHERE t.ihtiyac_noktasi_id = d.ihtiyac_noktasi_id
      AND t.malzeme_id = dagitim_kalemi.malzeme_id
      AND t.durum <> 'İptal'
    ORDER BY t.talep_tarihi, t.id
    LIMIT 1
)
WHERE ihtiyac_talebi_id IS NULL;

-- Talep durumlarını bağlı dağıtımlardan yeniden hesapla
UPDATE ihtiyac_talebi
SET durum = (
    SELECT CASE
        WHEN k.karsilanan >= ihtiyac_talebi.miktar THEN 'Karşılandı'
        WHEN k.karsilanan > 0                      THEN 'Kısmen karşılandı'
        ELSE 'Bekliyor'
    END
    FROM (SELECT COALESCE(SUM(dk.miktar), 0) AS karsilanan
          FROM dagitim_kalemi dk
          JOIN dagitim d ON d.id = dk.dagitim_id
          WHERE dk.ihtiyac_talebi_id = ihtiyac_talebi.id
            AND d.durum <> 'İptal') AS k
)
WHERE durum <> 'İptal';
