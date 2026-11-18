"""Rota önbelleği repository'si (Hafta 9).

Birincil anahtar iki kolonlu (depo_id, ihtiyac_noktasi_id) olduğu için TemelRepository
(tek kolonlu id) yerine kendi küçük sorgularını kullanır.
"""

import sqlite3
from typing import Optional


class RotaOnbellekRepository:
    def __init__(self, baglanti: sqlite3.Connection) -> None:
        self.baglanti = baglanti

    def getir(self, depo_id: int, nokta_id: int) -> Optional[sqlite3.Row]:
        return self.baglanti.execute(
            "SELECT * FROM rota_onbellek WHERE depo_id = ? AND ihtiyac_noktasi_id = ?",
            (depo_id, nokta_id),
        ).fetchone()

    def tumu(self) -> dict[tuple[int, int], sqlite3.Row]:
        return {(s["depo_id"], s["ihtiyac_noktasi_id"]): s
                for s in self.baglanti.execute("SELECT * FROM rota_onbellek")}

    def kaydet(self, depo_id: int, nokta_id: int, koordinatlar: str, mesafe_km: float,
               sure_dk: float, geometri: str, tarih: str) -> None:
        """Varsa günceller, yoksa ekler (UPSERT)."""
        self.baglanti.execute(
            """
            INSERT INTO rota_onbellek (depo_id, ihtiyac_noktasi_id, koordinatlar, mesafe_km, sure_dk, geometri, tarih)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (depo_id, ihtiyac_noktasi_id) DO UPDATE SET
                koordinatlar = excluded.koordinatlar, mesafe_km = excluded.mesafe_km,
                sure_dk = excluded.sure_dk, geometri = excluded.geometri, tarih = excluded.tarih
            """,
            (depo_id, nokta_id, koordinatlar, mesafe_km, sure_dk, geometri, tarih),
        )
