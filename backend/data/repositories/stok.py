"""Stok ve stok hareketi repository'leri.

Stok tablosunun birincil anahtarı bileşiktir: (depo_id, malzeme_id).
Bu yüzden `id` kullanan TemelRepository yerine ayrı yazıldı.
"""

import sqlite3
from typing import Optional

from backend.models import Stok, StokHareketi

from .temel import TemelRepository


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
            SELECT s.malzeme_id, m.ad AS malzeme, m.kategori_id, k.ad AS kategori,
                   s.miktar, m.birim, s.kritik_seviye
            FROM stok s
            JOIN malzeme m  ON m.id = s.malzeme_id
            JOIN kategori k ON k.id = m.kategori_id
            WHERE s.depo_id = ?
            ORDER BY k.ad, m.ad
            """,
            (depo_id,),
        ).fetchall()

    def depo_envanteri(self, depo_id: int) -> list[sqlite3.Row]:
        """Tüm malzemeler + bu depodaki miktarları (LEFT JOIN).

        Depoda hiç stoğu olmayan malzeme de 0 miktarla gelir; böylece yeni bir
        malzemenin ilk girişi de envanter ekranından yapılabilir.
        """
        return self.baglanti.execute(
            """
            SELECT m.id AS malzeme_id, m.ad AS malzeme, m.kategori_id, k.ad AS kategori, m.birim,
                   COALESCE(s.miktar, 0) AS miktar, COALESCE(s.kritik_seviye, 0) AS kritik_seviye
            FROM malzeme m
            JOIN kategori k  ON k.id = m.kategori_id
            LEFT JOIN stok s ON s.malzeme_id = m.id AND s.depo_id = ?
            ORDER BY k.ad, m.ad
            """,
            (depo_id,),
        ).fetchall()

    def kritik_stoklar(self) -> list[sqlite3.Row]:
        """Miktarı kritik seviyenin altına düşmüş stoklar (Hafta 6 uyarıları için)."""
        return self.baglanti.execute(
            """
            SELECT s.depo_id, d.ad AS depo, s.malzeme_id, m.ad AS malzeme, s.miktar,
                   s.kritik_seviye, m.birim
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


class StokHareketiRepository(TemelRepository[StokHareketi]):
    """Hareketler yalnızca eklenir; güncelleme/silme iş katmanında kullanılmaz (denetim izi)."""

    tablo, varlik, siralama = "stok_hareketi", StokHareketi, "tarih DESC, id DESC"

    def gecmis(self, depo_id: int, malzeme_id: Optional[int] = None,
               limit: int = 100) -> list[sqlite3.Row]:
        """Bir deponun son hareketleri; malzeme ve kullanıcı adlarıyla (JOIN)."""
        sql = """
            SELECT h.id, h.tarih, m.ad AS malzeme, m.birim, h.tur, h.degisim,
                   h.onceki_miktar, h.sonraki_miktar, h.aciklama,
                   COALESCE(k.kullanici_adi, 'sistem') AS kullanici
            FROM stok_hareketi h
            JOIN malzeme m        ON m.id = h.malzeme_id
            LEFT JOIN kullanici k ON k.id = h.kullanici_id
            WHERE h.depo_id = ?
        """
        parametreler: tuple = (depo_id,)
        if malzeme_id is not None:
            sql += " AND h.malzeme_id = ?"
            parametreler += (malzeme_id,)
        sql += " ORDER BY h.tarih DESC, h.id DESC LIMIT ?"
        return self.baglanti.execute(sql, parametreler + (limit,)).fetchall()

    def toplam_degisim(self, depo_id: int, malzeme_id: int) -> float:
        """Hareketlerin toplamı; stok tablosundaki miktarla aynı olmalıdır."""
        return self.baglanti.execute(
            "SELECT COALESCE(SUM(degisim), 0) FROM stok_hareketi WHERE depo_id = ? AND malzeme_id = ?",
            (depo_id, malzeme_id),
        ).fetchone()[0]
