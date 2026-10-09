"""İş katmanı - kayıt, giriş, oturum ve çıkış (Hafta 5).

Akış:
  kayit_ol  -> kurallar kontrol edilir, parola hash'lenir, kullanıcı kaydedilir
  giris_yap -> kilit kontrolü, parola doğrulama, oturum açılır, token döner
  oturum_dogrula(token) -> her korumalı işlemden önce: token geçerli mi?
  cikis_yap(token) -> oturum kapatılır, token bir daha kullanılamaz

Frontend token'ı yalnızca bellekte tutar (dosyaya yazmaz); her istekte
servise verir. Servis token'ın özetini veritabanında arar.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from backend import config, guvenlik
from backend.data.database import islem
from backend.data.repositories import DepoRepository, KullaniciRepository, OturumRepository
from backend.models import Kullanici, Oturum, Rol

from .hatalar import DogrulamaHatasi, GecersizGiris, HesapKilitli, OturumGecersiz
from .yetki import yetki_gerekli

# Var olmayan kullanıcı adında da parola doğrulaması yapılsın diye sahte hash.
# Böylece "kullanıcı yok" cevabı "parola yanlış" cevabından daha hızlı dönmez
# ve yanıt süresinden geçerli kullanıcı adları tahmin edilemez.
_SAHTE_HASH = None


def _simdi() -> datetime:
    return datetime.now().replace(microsecond=0)


class KimlikServisi:
    def __init__(self, baglanti: sqlite3.Connection) -> None:
        self._baglanti = baglanti
        self._kullanicilar = KullaniciRepository(baglanti)
        self._oturumlar = OturumRepository(baglanti)

    # ---------------------------------------------------------------- KAYIT
    def ilk_kurulum_mu(self) -> bool:
        """Hiç kullanıcı yoksa ilk kaydolan kişi Yönetici olabilir."""
        return self._kullanicilar.sayi() == 0

    def depo_secenekleri(self) -> list[tuple[int, str]]:
        """Kayıt formundaki depo listesi (id, ad). Giriş gerektirmez; gizli bilgi içermez."""
        return [(d.id, d.ad) for d in DepoRepository(self._baglanti).listele()]

    def kayit_ol(self, kullanici_adi: str, ad_soyad: str, parola: str, parola_tekrar: str,
                 rol: Rol, depo_id: Optional[int] = None) -> Kullanici:
        kullanici_adi, ad_soyad = kullanici_adi.strip(), ad_soyad.strip()
        hatalar = []
        if not (3 <= len(kullanici_adi) <= 30) or not kullanici_adi.replace("_", "").replace(".", "").isalnum():
            hatalar.append("Kullanıcı adı 3-30 karakter olmalı; yalnızca harf, rakam, '.' ve '_' içerebilir.")
        if not ad_soyad:
            hatalar.append("Ad soyad boş olamaz.")
        if parola != parola_tekrar:
            hatalar.append("Parolalar eşleşmiyor.")
        kural_hatalari = guvenlik.parola_kurallarini_kontrol_et(parola)
        if kural_hatalari:
            hatalar.append("Parola " + ", ".join(kural_hatalari) + ".")
        if rol is Rol.YONETICI and not self.ilk_kurulum_mu():
            hatalar.append("Yönetici hesabı kayıt ekranından açılamaz.")
        if rol is Rol.DEPO:
            if depo_id is None or DepoRepository(self._baglanti).getir(depo_id) is None:
                hatalar.append("Depo görevlisi için geçerli bir depo seçilmeli.")
        else:
            depo_id = None
        if self._kullanicilar.kullanici_adi_ile_getir(kullanici_adi):
            hatalar.append("Bu kullanıcı adı alınmış.")
        if hatalar:
            raise DogrulamaHatasi("\n".join(hatalar))

        kullanici = Kullanici(kullanici_adi, ad_soyad, guvenlik.parola_hashle(parola), rol, depo_id)
        with islem(self._baglanti):
            return self._kullanicilar.ekle(kullanici)

    # ---------------------------------------------------------------- GİRİŞ
    def giris_yap(self, kullanici_adi: str, parola: str) -> str:
        """Başarılıysa oturum token'ını döndürür (token yalnızca bu an düz görülür)."""
        simdi = _simdi()
        kullanici = self._kullanicilar.kullanici_adi_ile_getir(kullanici_adi.strip())

        if kullanici is None or not kullanici.aktif:
            guvenlik.parola_dogrula(parola, self._sahte_hash())  # süre eşitleme
            raise GecersizGiris()

        if kullanici.kilitli_bitis and kullanici.kilitli_bitis > simdi:
            kalan = int((kullanici.kilitli_bitis - simdi).total_seconds() // 60) + 1
            raise HesapKilitli(f"Çok fazla hatalı deneme. Hesap yaklaşık {kalan} dakika kilitli.")

        if not guvenlik.parola_dogrula(parola, kullanici.parola_hash):
            kullanici.basarisiz_giris += 1
            kilitlendi = kullanici.basarisiz_giris >= config.MAKS_BASARISIZ_GIRIS
            if kilitlendi:
                kullanici.kilitli_bitis = simdi + timedelta(minutes=config.KILIT_SURESI_DAKIKA)
                kullanici.basarisiz_giris = 0
            with islem(self._baglanti):
                self._kullanicilar.guncelle(kullanici)
            if kilitlendi:
                raise HesapKilitli(f"Çok fazla hatalı deneme. Hesap {config.KILIT_SURESI_DAKIKA} dakika kilitlendi.")
            raise GecersizGiris()

        token = guvenlik.token_uret()
        kullanici.basarisiz_giris, kullanici.kilitli_bitis, kullanici.son_giris = 0, None, simdi
        oturum = Oturum(kullanici.id, guvenlik.token_ozeti(token), simdi,
                        simdi + timedelta(hours=config.OTURUM_SURESI_SAAT))
        with islem(self._baglanti):
            self._kullanicilar.guncelle(kullanici)
            self._oturumlar.ekle(oturum)
        return token

    # --------------------------------------------------------------- OTURUM
    def oturum_dogrula(self, token: Optional[str]) -> Kullanici:
        """Token geçerliyse oturum sahibini döndürür; değilse OturumGecersiz."""
        if not token:
            raise OturumGecersiz("Giriş yapılmamış.")
        oturum = self._oturumlar.token_hash_ile_getir(guvenlik.token_ozeti(token))
        if oturum is None or oturum.cikis_zamani is not None:
            raise OturumGecersiz("Oturum kapalı. Lütfen yeniden giriş yapın.")
        if oturum.son_kullanma <= _simdi():
            raise OturumGecersiz("Oturum süresi doldu. Lütfen yeniden giriş yapın.")
        kullanici = self._kullanicilar.getir(oturum.kullanici_id)
        if kullanici is None or not kullanici.aktif:
            raise OturumGecersiz("Hesap devre dışı.")
        return kullanici

    def cikis_yap(self, token: str) -> None:
        oturum = self._oturumlar.token_hash_ile_getir(guvenlik.token_ozeti(token))
        if oturum and oturum.cikis_zamani is None:
            oturum.cikis_zamani = _simdi()
            with islem(self._baglanti):
                self._oturumlar.guncelle(oturum)

    def modul_erisimi(self, token: str, modul: str) -> Kullanici:
        """Bir sayfayı/modülü açmadan önce: oturum geçerli mi + rol yetkili mi?"""
        kullanici = self.oturum_dogrula(token)
        yetki_gerekli(kullanici, modul)
        return kullanici

    # ------------------------------------------------- KORUMALI UÇ (Yönetici)
    def kullanicilari_listele(self, token: str) -> list[Kullanici]:
        """Yalnızca Yönetici. Rol kontrolü backend'de yapılır, arayüze güvenilmez."""
        yetki_gerekli(self.oturum_dogrula(token), "kullanicilar")
        return self._kullanicilar.listele()

    # ------------------------------------------------------------- yardımcı
    @staticmethod
    def _sahte_hash() -> str:
        global _SAHTE_HASH
        if _SAHTE_HASH is None or f"${config.PAROLA_ITERASYON}$" not in _SAHTE_HASH:
            _SAHTE_HASH = guvenlik.parola_hashle(guvenlik.token_uret())
        return _SAHTE_HASH
