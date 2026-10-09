"""Hafta 5 - kimlik doğrulama, oturum ve yetkilendirme testleri."""

import unittest
from datetime import datetime, timedelta

from backend import config, guvenlik
from backend.data.database import baglanti_ac, islem, migrasyonlari_uygula
from backend.data.ornek_veri import ornek_veri_yukle
from backend.data.repositories import DepoRepository, KullaniciRepository, OturumRepository
from backend.models import Rol
from backend.services.hatalar import (
    DogrulamaHatasi, GecersizGiris, HesapKilitli, OturumGecersiz, YetkisizErisim,
)
from backend.services.kimlik_servisi import KimlikServisi
from backend.services.ozet_servisi import OzetServisi

PAROLA = "Guvenli123"


class KimlikTesti(unittest.TestCase):
    def setUp(self):
        self._eski_iterasyon = config.PAROLA_ITERASYON
        config.PAROLA_ITERASYON = 1_000       # testler hızlı çalışsın
        self.db = baglanti_ac(":memory:")
        migrasyonlari_uygula(self.db)
        with islem(self.db):
            ornek_veri_yukle(self.db)
        self.kimlik = KimlikServisi(self.db)
        self.depo_id = DepoRepository(self.db).listele()[0].id
        # İlk kullanıcı Yönetici olabilir
        self.kimlik.kayit_ol("yonetici", "Test Yönetici", PAROLA, PAROLA, Rol.YONETICI)

    def tearDown(self):
        self.db.close()
        config.PAROLA_ITERASYON = self._eski_iterasyon

    def kayit(self, kadi="kurum1", rol=Rol.KURUM, depo_id=None, parola=PAROLA):
        return self.kimlik.kayit_ol(kadi, "Test Kişi", parola, parola, rol, depo_id)


class ParolaGuvenligiTestleri(KimlikTesti):
    def test_parola_duz_metin_saklanmaz(self):
        k = self.kayit()
        satir = self.db.execute("SELECT parola_hash FROM kullanici WHERE id = ?", (k.id,)).fetchone()
        self.assertNotIn(PAROLA, satir[0])
        self.assertTrue(satir[0].startswith("pbkdf2_sha256$"))

    def test_ayni_parola_farkli_tuz_farkli_hash(self):
        self.assertNotEqual(guvenlik.parola_hashle(PAROLA), guvenlik.parola_hashle(PAROLA))

    def test_parola_dogrulama(self):
        h = guvenlik.parola_hashle(PAROLA)
        self.assertTrue(guvenlik.parola_dogrula(PAROLA, h))
        self.assertFalse(guvenlik.parola_dogrula("Yanlis123", h))

    def test_parola_hash_ekrana_basilmaz(self):
        self.assertNotIn("pbkdf2", repr(self.kayit()))


class KayitTestleri(KimlikTesti):
    def test_zayif_parola_reddedilir(self):
        for zayif in ("kisa1", "sadeceharf", "12345678"):
            with self.assertRaises(DogrulamaHatasi):
                self.kayit(kadi=f"k{len(zayif)}{zayif[:2]}", parola=zayif)

    def test_parolalar_eslesmeli(self):
        with self.assertRaises(DogrulamaHatasi):
            self.kimlik.kayit_ol("kisi1", "Kişi", PAROLA, PAROLA + "x", Rol.KURUM)

    def test_kullanici_adi_buyuk_kucuk_harf_duyarsiz_benzersiz(self):
        self.kayit(kadi="ali")
        with self.assertRaises(DogrulamaHatasi):
            self.kayit(kadi="ALI")

    def test_ikinci_yonetici_kayit_ekranindan_acilamaz(self):
        with self.assertRaises(DogrulamaHatasi):
            self.kayit(kadi="yonetici2", rol=Rol.YONETICI)

    def test_depo_rolu_depo_secmeli(self):
        with self.assertRaises(DogrulamaHatasi):
            self.kayit(kadi="depo1", rol=Rol.DEPO)
        self.assertEqual(self.kayit(kadi="depo1", rol=Rol.DEPO, depo_id=self.depo_id).depo_id, self.depo_id)


class GirisVeOturumTestleri(KimlikTesti):
    def test_basarili_giris_token_doner_ve_token_duz_saklanmaz(self):
        token = self.kimlik.giris_yap("yonetici", PAROLA)
        self.assertGreater(len(token), 30)
        hashler = [s[0] for s in self.db.execute("SELECT token_hash FROM oturum")]
        self.assertNotIn(token, hashler)
        self.assertIn(guvenlik.token_ozeti(token), hashler)
        self.assertEqual(self.kimlik.oturum_dogrula(token).kullanici_adi, "yonetici")

    def test_yanlis_parola_ve_olmayan_kullanici_ayni_mesaj(self):
        with self.assertRaises(GecersizGiris) as a:
            self.kimlik.giris_yap("yonetici", "Yanlis123")
        with self.assertRaises(GecersizGiris) as b:
            self.kimlik.giris_yap("olmayan", "Yanlis123")
        self.assertEqual(str(a.exception), str(b.exception))

    def test_bes_hatali_denemede_hesap_kilitlenir(self):
        for _ in range(config.MAKS_BASARISIZ_GIRIS - 1):
            with self.assertRaises(GecersizGiris):
                self.kimlik.giris_yap("yonetici", "Yanlis123")
        with self.assertRaises(HesapKilitli):
            self.kimlik.giris_yap("yonetici", "Yanlis123")
        with self.assertRaises(HesapKilitli):   # doğru parola da kilitliyken reddedilir
            self.kimlik.giris_yap("yonetici", PAROLA)

    def test_cikis_sonrasi_token_gecersiz(self):
        token = self.kimlik.giris_yap("yonetici", PAROLA)
        self.kimlik.cikis_yap(token)
        with self.assertRaises(OturumGecersiz):
            self.kimlik.oturum_dogrula(token)

    def test_suresi_dolan_oturum_gecersiz(self):
        token = self.kimlik.giris_yap("yonetici", PAROLA)
        gecmis = (datetime.now() - timedelta(minutes=1)).isoformat(timespec="seconds")
        baslangic = (datetime.now() - timedelta(hours=9)).isoformat(timespec="seconds")
        self.db.execute("UPDATE oturum SET olusturma = ?, son_kullanma = ?", (baslangic, gecmis))
        with self.assertRaises(OturumGecersiz):
            self.kimlik.oturum_dogrula(token)

    def test_uydurma_token_gecersiz(self):
        with self.assertRaises(OturumGecersiz):
            self.kimlik.oturum_dogrula("uydurma-token")


class YetkiTestleri(KimlikTesti):
    def giris(self, kadi, rol, depo_id=None):
        self.kayit(kadi=kadi, rol=rol, depo_id=depo_id)
        return self.kimlik.giris_yap(kadi, PAROLA)

    def test_depo_gorevlisi_dagitim_modulune_giremez(self):
        token = self.giris("depo1", Rol.DEPO, self.depo_id)
        self.kimlik.modul_erisimi(token, "envanter")
        with self.assertRaises(YetkisizErisim):
            self.kimlik.modul_erisimi(token, "dagitim")

    def test_kurum_envanter_modulune_giremez(self):
        token = self.giris("kurum1", Rol.KURUM)
        self.kimlik.modul_erisimi(token, "ihtiyac")
        with self.assertRaises(YetkisizErisim):
            self.kimlik.modul_erisimi(token, "envanter")

    def test_kullanici_listesi_yalnizca_yonetici(self):
        kurum = self.giris("kurum1", Rol.KURUM)
        with self.assertRaises(YetkisizErisim):   # backend uç noktası korumalı
            self.kimlik.kullanicilari_listele(kurum)
        yonetici = self.kimlik.giris_yap("yonetici", PAROLA)
        self.assertEqual(len(self.kimlik.kullanicilari_listele(yonetici)), 2)

    def test_oturumsuz_panel_ozeti_alinamaz(self):
        with self.assertRaises(OturumGecersiz):
            OzetServisi(self.db, self.kimlik).panel_ozeti(None)


if __name__ == "__main__":
    unittest.main()
