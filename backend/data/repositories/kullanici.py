"""Kullanıcı ve oturum repository'leri (Hafta 5)."""

from typing import Optional

from backend.models import Kullanici, Oturum

from .temel import TemelRepository


class KullaniciRepository(TemelRepository[Kullanici]):
    tablo, varlik, siralama = "kullanici", Kullanici, "ad_soyad"

    def kullanici_adi_ile_getir(self, kullanici_adi: str) -> Optional[Kullanici]:
        # Kolon COLLATE NOCASE tanımlı: büyük/küçük harf duyarsız eşleşir
        sonuc = self._sorgula("SELECT * FROM kullanici WHERE kullanici_adi = ?", (kullanici_adi,))
        return sonuc[0] if sonuc else None


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
