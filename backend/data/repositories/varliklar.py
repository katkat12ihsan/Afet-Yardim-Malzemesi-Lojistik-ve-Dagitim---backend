"""Tablo başına repository'ler.

Temel CRUD TemelRepository'den gelir; burada yalnızca tabloya özgü
sorgular (JOIN, filtre) yazılır.
"""

import sqlite3
from typing import Optional

from backend.models import (
    Bagis,
    Bagisci,
    BagisKalemi,
    Dagitim,
    DagitimDurumu,
    DagitimKalemi,
    Depo,
    IhtiyacNoktasi,
    IhtiyacTalebi,
    Kategori,
    Malzeme,
    TalepDurumu,
)

from .temel import TemelRepository


class KategoriRepository(TemelRepository[Kategori]):
    tablo, varlik, siralama = "kategori", Kategori, "ad"


class MalzemeRepository(TemelRepository[Malzeme]):
    tablo, varlik, siralama = "malzeme", Malzeme, "ad"

    def kategoriye_gore(self, kategori_id: int) -> list[Malzeme]:
        return self._sorgula(
            "SELECT * FROM malzeme WHERE kategori_id = ? ORDER BY ad", (kategori_id,)
        )


class DepoRepository(TemelRepository[Depo]):
    tablo, varlik, siralama = "depo", Depo, "ad"


class IhtiyacNoktasiRepository(TemelRepository[IhtiyacNoktasi]):
    tablo, varlik = "ihtiyac_noktasi", IhtiyacNoktasi
    siralama = "oncelik DESC, ad"


class BagisciRepository(TemelRepository[Bagisci]):
    tablo, varlik, siralama = "bagisci", Bagisci, "ad"


class BagisRepository(TemelRepository[Bagis]):
    tablo, varlik, siralama = "bagis", Bagis, "tarih DESC"

    def liste(self, depo_id: Optional[int] = None, limit: int = 200) -> list[sqlite3.Row]:
        """Bağışlar; bağışçı, depo adı ve kalem sayısıyla (JOIN + GROUP BY)."""
        return self.baglanti.execute(
            """
            SELECT b.id, b.tarih, b.depo_id, d.ad AS depo, bc.ad AS bagisci, bc.tur, b.aciklama,
                   COUNT(bk.id) AS kalem_sayisi
            FROM bagis b
            JOIN bagisci bc ON bc.id = b.bagisci_id
            JOIN depo d     ON d.id = b.depo_id
            LEFT JOIN bagis_kalemi bk ON bk.bagis_id = b.id
            WHERE (? IS NULL OR b.depo_id = ?)
            GROUP BY b.id
            ORDER BY b.tarih DESC, b.id DESC
            LIMIT ?
            """,
            (depo_id, depo_id, limit),
        ).fetchall()


class BagisKalemiRepository(TemelRepository[BagisKalemi]):
    tablo, varlik = "bagis_kalemi", BagisKalemi

    def bagisin_kalemleri(self, bagis_id: int) -> list[BagisKalemi]:
        return self._sorgula("SELECT * FROM bagis_kalemi WHERE bagis_id = ?", (bagis_id,))

    def detay(self, bagis_id: int) -> list[sqlite3.Row]:
        return self.baglanti.execute(
            """
            SELECT m.ad AS malzeme, k.ad AS kategori, bk.miktar, m.birim, bk.son_kullanma_tarihi
            FROM bagis_kalemi bk
            JOIN malzeme m  ON m.id = bk.malzeme_id
            JOIN kategori k ON k.id = m.kategori_id
            WHERE bk.bagis_id = ?
            ORDER BY bk.id
            """,
            (bagis_id,),
        ).fetchall()


class IhtiyacTalebiRepository(TemelRepository[IhtiyacTalebi]):
    tablo, varlik, siralama = "ihtiyac_talebi", IhtiyacTalebi, "talep_tarihi"

    def bekleyenler_oncelik_sirali(self) -> list[sqlite3.Row]:
        """Karşılanmamış talepler; ihtiyaç noktasının önceliğine göre sıralı (JOIN)."""
        return self.baglanti.execute(
            """
            SELECT t.id, n.ad AS nokta, n.oncelik, m.ad AS malzeme, t.miktar, m.birim,
                   t.durum, t.talep_tarihi
            FROM ihtiyac_talebi t
            JOIN ihtiyac_noktasi n ON n.id = t.ihtiyac_noktasi_id
            JOIN malzeme m         ON m.id = t.malzeme_id
            WHERE t.durum IN (?, ?)
            ORDER BY n.oncelik DESC, t.talep_tarihi
            """,
            (TalepDurumu.BEKLIYOR.value, TalepDurumu.KISMEN_KARSILANDI.value),
        ).fetchall()

    def durum_listesi(self, sadece_acik: bool = True) -> list[sqlite3.Row]:
        """Talepler + karşılanan miktar (Hafta 7).

        karşılanan = iptal edilmemiş dağıtımlarda bu talebe bağlı kalemlerin toplamı.
        Öncelik sırası: ihtiyaç noktasının önceliği (yüksek önce), sonra talep tarihi (eski önce).
        """
        return self.baglanti.execute(
            """
            SELECT t.id, t.ihtiyac_noktasi_id, n.ad AS nokta, n.oncelik, n.enlem, n.boylam,
                   t.malzeme_id, m.ad AS malzeme, m.birim, t.miktar, t.talep_tarihi, t.durum,
                   COALESCE((SELECT SUM(dk.miktar)
                             FROM dagitim_kalemi dk JOIN dagitim d ON d.id = dk.dagitim_id
                             WHERE dk.ihtiyac_talebi_id = t.id AND d.durum <> ?), 0) AS karsilanan
            FROM ihtiyac_talebi t
            JOIN ihtiyac_noktasi n ON n.id = t.ihtiyac_noktasi_id
            JOIN malzeme m         ON m.id = t.malzeme_id
            WHERE (? = 0 OR t.durum IN (?, ?))
            ORDER BY n.oncelik DESC, t.talep_tarihi, t.id
            """,
            (DagitimDurumu.IPTAL.value, 1 if sadece_acik else 0,
             TalepDurumu.BEKLIYOR.value, TalepDurumu.KISMEN_KARSILANDI.value),
        ).fetchall()

    def karsilanan(self, talep_id: int) -> float:
        return self.baglanti.execute(
            """SELECT COALESCE(SUM(dk.miktar), 0)
               FROM dagitim_kalemi dk JOIN dagitim d ON d.id = dk.dagitim_id
               WHERE dk.ihtiyac_talebi_id = ? AND d.durum <> ?""",
            (talep_id, DagitimDurumu.IPTAL.value),
        ).fetchone()[0]


class DagitimRepository(TemelRepository[Dagitim]):
    tablo, varlik, siralama = "dagitim", Dagitim, "planlanan_tarih DESC"

    def duruma_gore(self, durum: DagitimDurumu) -> list[Dagitim]:
        return self._sorgula("SELECT * FROM dagitim WHERE durum = ?", (durum.value,))

    def liste(self, limit: int = 200) -> list[sqlite3.Row]:
        """Dağıtımlar; depo, ihtiyaç noktası ve kalem özetiyle (JOIN + GROUP_CONCAT)."""
        return self.baglanti.execute(
            """
            SELECT g.id, g.durum, g.planlanan_tarih, g.teslim_tarihi, g.arac_plaka,
                   g.depo_id, d.ad AS depo, n.ad AS nokta,
                   GROUP_CONCAT(m.ad || ' ' || dk.miktar || ' ' || m.birim, ', ') AS kalemler
            FROM dagitim g
            JOIN depo d            ON d.id = g.depo_id
            JOIN ihtiyac_noktasi n ON n.id = g.ihtiyac_noktasi_id
            LEFT JOIN dagitim_kalemi dk ON dk.dagitim_id = g.id
            LEFT JOIN malzeme m         ON m.id = dk.malzeme_id
            GROUP BY g.id
            ORDER BY g.planlanan_tarih DESC, g.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


class DagitimKalemiRepository(TemelRepository[DagitimKalemi]):
    tablo, varlik = "dagitim_kalemi", DagitimKalemi

    def dagitimin_kalemleri(self, dagitim_id: int) -> list[DagitimKalemi]:
        return self._sorgula("SELECT * FROM dagitim_kalemi WHERE dagitim_id = ?", (dagitim_id,))

    def rezerve(self, depo_id: int, malzeme_id: int) -> float:
        """Planlanmış ama henüz yola çıkmamış dağıtımlara ayrılan miktar.

        Stok depodan dağıtım "Yolda" olunca düşer; o zamana kadar planlanan miktar
        rezervdir ve başka bir talebe tekrar verilmemelidir.
        """
        return self.baglanti.execute(
            """SELECT COALESCE(SUM(dk.miktar), 0)
               FROM dagitim_kalemi dk JOIN dagitim d ON d.id = dk.dagitim_id
               WHERE d.depo_id = ? AND dk.malzeme_id = ? AND d.durum = ?""",
            (depo_id, malzeme_id, DagitimDurumu.PLANLANDI.value),
        ).fetchone()[0]
