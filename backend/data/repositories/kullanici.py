"""Kullanıcı, oturum ve rol değişikliği repository'leri (Hafta 5)."""

import sqlite3
from typing import Optional

from backend.models import Kullanici, Oturum, RolDegisikligi

from .temel import TemelRepository


def kullanici_adi_anahtari(kullanici_adi: str) -> str:
    """Kullanıcı adı karşılaştırma anahtarı.

    SQLite'ın COLLATE NOCASE'i yalnızca İngilizce harfleri eşler: Türkçe klavyede
    "katkat_İhsan" (büyük İ) veya "ıhsan" yazan kullanıcı "katkat_ihsan" hesabını
    bulamıyordu. Kullanıcı adında İ, I, ı ve i aynı kabul edilir; büyük/küçük harf
    ve baştaki/sondaki boşluk fark etmez.
    """
    for harf in "İIı":
        kullanici_adi = kullanici_adi.replace(harf, "i")
    return kullanici_adi.strip().lower()


class KullaniciRepository(TemelRepository[Kullanici]):
    tablo, varlik, siralama = "kullanici", Kullanici, "ad_soyad"

    def kullanici_adi_ile_getir(self, kullanici_adi: str) -> Optional[Kullanici]:
        # Kullanıcı tablosu küçük olduğu için karşılaştırma Python'da, Türkçe'ye uygun yapılır
        aranan = kullanici_adi_anahtari(kullanici_adi)
        return next((k for k in self.listele() if kullanici_adi_anahtari(k.kullanici_adi) == aranan), None)


class OturumRepository(TemelRepository[Oturum]):
    tablo, varlik, siralama = "oturum", Oturum, "olusturma DESC"

    def token_hash_ile_getir(self, token_hash: str) -> Optional[Oturum]:
        sonuc = self._sorgula("SELECT * FROM oturum WHERE token_hash = ?", (token_hash,))
        return sonuc[0] if sonuc else None

    def kullanicinin_acik_oturumlarini_kapat(self, kullanici_id: int, zaman: str) -> int:
        imlec = self.baglanti.execute(
            "UPDATE oturum SET cikis_zamani = ? WHERE kullanici_id = ? AND cikis_zamani IS NULL",
            (zaman, kullanici_id),
        )
        return imlec.rowcount


class RolDegisikligiRepository(TemelRepository[RolDegisikligi]):
    """Kayıtlar yalnızca eklenir; güncelleme/silme iş katmanında kullanılmaz."""

    tablo, varlik, siralama = "rol_degisikligi", RolDegisikligi, "tarih DESC, id DESC"

    def gecmis(self, limit: int = 50) -> list[sqlite3.Row]:
        """Son rol değişiklikleri; kullanıcı ve depo adlarıyla (JOIN)."""
        return self.baglanti.execute(
            """
            SELECT r.tarih, k.kullanici_adi, r.eski_rol, r.yeni_rol,
                   ed.ad AS eski_depo, yd.ad AS yeni_depo, d.kullanici_adi AS degistiren
            FROM rol_degisikligi r
            JOIN kullanici k  ON k.id = r.kullanici_id
            JOIN kullanici d  ON d.id = r.degistiren_id
            LEFT JOIN depo ed ON ed.id = r.eski_depo_id
            LEFT JOIN depo yd ON yd.id = r.yeni_depo_id
            ORDER BY r.tarih DESC, r.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
