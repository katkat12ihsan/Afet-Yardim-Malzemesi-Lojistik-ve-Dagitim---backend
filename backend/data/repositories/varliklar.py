"""Tablo başına repository'ler.

Temel CRUD TemelRepository'den gelir; burada yalnızca tabloya özgü
sorgular (JOIN, filtre) yazılır.
"""

import sqlite3

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


class BagisKalemiRepository(TemelRepository[BagisKalemi]):
    tablo, varlik = "bagis_kalemi", BagisKalemi

    def bagisin_kalemleri(self, bagis_id: int) -> list[BagisKalemi]:
        return self._sorgula("SELECT * FROM bagis_kalemi WHERE bagis_id = ?", (bagis_id,))


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


class DagitimRepository(TemelRepository[Dagitim]):
    tablo, varlik, siralama = "dagitim", Dagitim, "planlanan_tarih DESC"

    def duruma_gore(self, durum: DagitimDurumu) -> list[Dagitim]:
        return self._sorgula("SELECT * FROM dagitim WHERE durum = ?", (durum.value,))


class DagitimKalemiRepository(TemelRepository[DagitimKalemi]):
    tablo, varlik = "dagitim_kalemi", DagitimKalemi

    def dagitimin_kalemleri(self, dagitim_id: int) -> list[DagitimKalemi]:
        return self._sorgula("SELECT * FROM dagitim_kalemi WHERE dagitim_id = ?", (dagitim_id,))
