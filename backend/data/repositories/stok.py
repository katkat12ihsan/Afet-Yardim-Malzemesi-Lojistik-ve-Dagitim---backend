"""Stok repository'si.

Stok tablosunun birincil anahtarı bileşiktir: (depo_id, malzeme_id).
Bu yüzden `id` kullanan TemelRepository yerine ayrı yazıldı.
"""

import sqlite3
from typing import Optional

from backend.models import Stok


class StokRepository:
    def __init__(self, baglanti: sqlite3.Connection) -> None:
        self.baglanti = baglanti

    @staticmethod
    def _nesneye(satir: sqlite3.Row) -> Stok:
        return Stok(satir["depo_id"], satir["malzeme_id"], satir["miktar"], satir["kritik_seviye"])

    # CREATE + UPDATE (upsert): satır yoksa ekler, varsa günceller
    def kaydet(self, stok: Stok) -> None:
        self.baglanti.execute(
            """
            INSERT INTO stok (depo_id, malzeme_id, miktar, kritik_seviye)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (depo_id, malzeme_id)
            DO UPDATE SET miktar = excluded.miktar, kritik_seviye = excluded.kritik_seviye
            """,
            (stok.depo_id, stok.malzeme_id, stok.miktar, stok.kritik_seviye),
        )

    # READ
    def getir(self, depo_id: int, malzeme_id: int) -> Optional[Stok]:
        satir = self.baglanti.execute(
            "SELECT * FROM stok WHERE depo_id = ? AND malzeme_id = ?", (depo_id, malzeme_id)
        ).fetchone()
        return self._nesneye(satir) if satir else None

    def listele(self) -> list[Stok]:
        return [self._nesneye(s) for s in
                self.baglanti.execute("SELECT * FROM stok ORDER BY depo_id, malzeme_id")]

    def sayi(self) -> int:
        return self.baglanti.execute("SELECT COUNT(*) FROM stok").fetchone()[0]

    def depo_stoklari(self, depo_id: int) -> list[sqlite3.Row]:
        """Bir deponun stokları; malzeme ve kategori adlarıyla (JOIN)."""
        return self.baglanti.execute(
            """
            SELECT m.ad AS malzeme, k.ad AS kategori, s.miktar, m.birim, s.kritik_seviye
            FROM stok s
            JOIN malzeme m  ON m.id = s.malzeme_id
            JOIN kategori k ON k.id = m.kategori_id
            WHERE s.depo_id = ?
            ORDER BY k.ad, m.ad
            """,
            (depo_id,),
        ).fetchall()

    def kritik_stoklar(self) -> list[sqlite3.Row]:
        """Miktarı kritik seviyenin altına düşmüş stoklar (Hafta 6 uyarıları için)."""
        return self.baglanti.execute(
            """
            SELECT d.ad AS depo, m.ad AS malzeme, s.miktar, s.kritik_seviye, m.birim
            FROM stok s
            JOIN depo d    ON d.id = s.depo_id
            JOIN malzeme m ON m.id = s.malzeme_id
            WHERE s.miktar < s.kritik_seviye
            ORDER BY d.ad, m.ad
            """
        ).fetchall()

    # DELETE
    def sil(self, depo_id: int, malzeme_id: int) -> bool:
        imlec = self.baglanti.execute(
            "DELETE FROM stok WHERE depo_id = ? AND malzeme_id = ?", (depo_id, malzeme_id)
        )
        return imlec.rowcount == 1
