"""Hafta 5 - kimlik doğrulama, oturum ve yetkilendirme testleri (+ parola sıfırlama)."""

import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from backend import config, guvenlik
from backend.data import database
from backend.data.database import baglanti_ac, islem, migrasyonlari_uygula
from backend.data.ornek_veri import ornek_veri_yukle
from backend.data.repositories import DepoRepository, KullaniciRepository, OturumRepository
from backend.models import Rol
from backend.services.hatalar import (
    DogrulamaHatasi, GecersizGiris, HesapKilitli, OturumGecersiz, ParolaDegistirilmeli, YetkisizErisim,
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
        for ayni in ("ALI", "alı", "ALİ"):                  # Türkçe I/ı/İ aynı kullanıcı adı
            with self.assertRaises(DogrulamaHatasi):
                self.kayit(kadi=ayni)

    def test_turkce_klavyeyle_yazilan_kullanici_adiyla_giris(self):
        """Hata kaydı: 'katkat_ihsan' hesabına Türkçe klavyede 'Katkat_İhsan' yazınca girilemiyordu."""
        self.kayit(kadi="katkat_ihsan")
        for yazim in ("katkat_ihsan", "Katkat_İhsan", "KATKAT_İHSAN", "KATKAT_IHSAN", "katkat_ıhsan", " katkat_ihsan "):
            token = self.kimlik.giris_yap(yazim, PAROLA)
            self.assertEqual(self.kimlik.oturum_dogrula(token).kullanici_adi, "katkat_ihsan", yazim)

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


class RolDuzenlemeTestleri(KimlikTesti):
    """Kullanıcılar sayfası: rolü düzenle."""

    def setUp(self):
        super().setUp()
        self.yonetici = self.kimlik.giris_yap("yonetici", PAROLA)
        self.kurum = self.kayit(kadi="kurum1")

    def test_yonetici_rol_degistirir_ve_gecmise_yazilir(self):
        k = self.kimlik.rol_degistir(self.yonetici, self.kurum.id, Rol.DEPO, self.depo_id)
        self.assertEqual((k.rol, k.depo_id), (Rol.DEPO, self.depo_id))
        kayit = self.kimlik.rol_gecmisi(self.yonetici)[0]
        self.assertEqual((kayit["kullanici_adi"], kayit["eski_rol"], kayit["yeni_rol"], kayit["degistiren"]),
                         ("kurum1", "Kurum", "Depo", "yonetici"))

    def test_yonetici_disindaki_rol_degistiremez(self):
        kurum_token = self.kimlik.giris_yap("kurum1", PAROLA)
        diger = self.kayit(kadi="kurum2")
        with self.assertRaises(YetkisizErisim):
            self.kimlik.rol_degistir(kurum_token, diger.id, Rol.YONETICI)

    def test_kendi_rolunu_degistiremez(self):
        kendisi = self.kimlik.oturum_dogrula(self.yonetici)
        with self.assertRaises(YetkisizErisim):
            self.kimlik.rol_degistir(self.yonetici, kendisi.id, Rol.KURUM)

    def test_depo_rolu_icin_depo_zorunlu_diger_rollerde_depo_bosalir(self):
        with self.assertRaises(DogrulamaHatasi):
            self.kimlik.rol_degistir(self.yonetici, self.kurum.id, Rol.DEPO)
        self.kimlik.rol_degistir(self.yonetici, self.kurum.id, Rol.DEPO, self.depo_id)
        k = self.kimlik.rol_degistir(self.yonetici, self.kurum.id, Rol.YONETICI, self.depo_id)
        self.assertIsNone(k.depo_id)

    def test_degisiklik_yoksa_hata_ve_kayit_yok(self):
        with self.assertRaises(DogrulamaHatasi):
            self.kimlik.rol_degistir(self.yonetici, self.kurum.id, Rol.KURUM)
        self.assertEqual(self.kimlik.rol_gecmisi(self.yonetici), [])

    def test_rolu_degisenin_acik_oturumu_kapanir(self):
        kurum_token = self.kimlik.giris_yap("kurum1", PAROLA)
        self.kimlik.rol_degistir(self.yonetici, self.kurum.id, Rol.YONETICI)
        with self.assertRaises(OturumGecersiz):
            self.kimlik.oturum_dogrula(kurum_token)
        yeni = self.kimlik.giris_yap("kurum1", PAROLA)          # yeni rolle tekrar giriş
        self.assertEqual(self.kimlik.oturum_dogrula(yeni).rol, Rol.YONETICI)

    def test_gecmis_tablosu_kendi_kendine_kaydi_reddeder(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO rol_degisikligi (kullanici_id, eski_rol, yeni_rol, degistiren_id, tarih)"
                            " VALUES (1, 'Kurum', 'Yönetici', 1, '2026-10-23T10:00:00')")


class ParolaSifirlamaTestleri(KimlikTesti):
    """Şifremi unuttum yerine: Yönetici parolayı sıfırlar, kullanıcı ilk girişte yeni parola belirler."""

    YENI = "YeniParola9"

    def setUp(self):
        super().setUp()
        self.yonetici = self.kimlik.giris_yap("yonetici", PAROLA)
        self.kurum = self.kayit(kadi="kurum1")

    def sifirla(self):
        return self.kimlik.parola_sifirla(self.yonetici, self.kurum.id)

    def test_gecici_parola_kurallara_uyar_ve_duz_saklanmaz(self):
        gecici = self.sifirla()
        self.assertFalse(guvenlik.parola_kurallarini_kontrol_et(gecici))
        self.assertFalse(set(gecici) & set("0O1lI"))          # karıştırılan karakter yok
        k = KullaniciRepository(self.db).getir(self.kurum.id)
        self.assertNotIn(gecici, k.parola_hash)
        self.assertTrue(guvenlik.parola_dogrula(gecici, k.parola_hash))
        self.assertTrue(k.parola_degistirmeli)
        self.assertNotEqual(gecici, self.sifirla())            # her seferinde farklı

    def test_eski_parola_artik_gecmez(self):
        self.sifirla()
        with self.assertRaises(GecersizGiris):
            self.kimlik.giris_yap("kurum1", PAROLA)

    def test_gecici_parolayla_oturum_acilmaz(self):
        gecici = self.sifirla()
        with self.assertRaises(ParolaDegistirilmeli):
            self.kimlik.giris_yap("kurum1", gecici)
        acik = self.db.execute("SELECT COUNT(*) FROM oturum WHERE kullanici_id = ? AND cikis_zamani IS NULL",
                               (self.kurum.id,)).fetchone()[0]
        self.assertEqual(acik, 0)

    def test_yeni_parola_belirlenince_giris_yapilir(self):
        gecici = self.sifirla()
        token = self.kimlik.parola_yenile("kurum1", gecici, self.YENI, self.YENI)
        self.assertEqual(self.kimlik.oturum_dogrula(token).kullanici_adi, "kurum1")
        self.assertFalse(KullaniciRepository(self.db).getir(self.kurum.id).parola_degistirmeli)
        self.kimlik.giris_yap("kurum1", self.YENI)               # artık normal giriş
        with self.assertRaises(GecersizGiris):                   # geçici parola tek kullanımlık
            self.kimlik.giris_yap("kurum1", gecici)

    def test_yeni_parola_kurallari(self):
        gecici = self.sifirla()
        for yeni, tekrar in (("kisa1", "kisa1"), ("SadeceHarf", "SadeceHarf"),
                             (self.YENI, "Baska12345"), (gecici, gecici)):
            with self.subTest(yeni=yeni), self.assertRaises(DogrulamaHatasi):
                self.kimlik.parola_yenile("kurum1", gecici, yeni, tekrar)
        self.assertTrue(KullaniciRepository(self.db).getir(self.kurum.id).parola_degistirmeli)

    def test_yanlis_gecici_parola_kilit_sayacina_girer(self):
        self.sifirla()
        for _ in range(config.MAKS_BASARISIZ_GIRIS - 1):
            with self.assertRaises(GecersizGiris):
                self.kimlik.parola_yenile("kurum1", "Tahmin1234", self.YENI, self.YENI)
        with self.assertRaises(HesapKilitli):
            self.kimlik.parola_yenile("kurum1", "Tahmin1234", self.YENI, self.YENI)

    def test_sifirlanmamis_hesapta_parola_yenile_calismaz(self):
        with self.assertRaises(DogrulamaHatasi):
            self.kimlik.parola_yenile("kurum1", PAROLA, self.YENI, self.YENI)

    def test_yalnizca_yonetici_ve_kendi_parolasini_sifirlayamaz(self):
        kurum_token = self.kimlik.giris_yap("kurum1", PAROLA)
        diger = self.kayit(kadi="kurum2")
        with self.assertRaises(YetkisizErisim):
            self.kimlik.parola_sifirla(kurum_token, diger.id)
        kendisi = self.kimlik.oturum_dogrula(self.yonetici)
        with self.assertRaises(YetkisizErisim):
            self.kimlik.parola_sifirla(self.yonetici, kendisi.id)
        with self.assertRaises(DogrulamaHatasi):
            self.kimlik.parola_sifirla(self.yonetici, 9999)

    def test_sifirlama_acik_oturumu_kapatir_ve_kilidi_acar(self):
        kurum_token = self.kimlik.giris_yap("kurum1", PAROLA)
        for _ in range(config.MAKS_BASARISIZ_GIRIS):
            with self.assertRaises((GecersizGiris, HesapKilitli)):
                self.kimlik.giris_yap("kurum1", "Yanlis123")
        gecici = self.sifirla()
        with self.assertRaises(OturumGecersiz):
            self.kimlik.oturum_dogrula(kurum_token)
        with self.assertRaises(ParolaDegistirilmeli):            # kilit kalktı: HesapKilitli değil
            self.kimlik.giris_yap("kurum1", gecici)

    def test_sifirlama_gecmise_yazilir(self):
        self.sifirla()
        kayit = self.kimlik.parola_sifirlama_gecmisi(self.yonetici)[0]
        self.assertEqual((kayit["kullanici_adi"], kayit["sifirlayan"]), ("kurum1", "yonetici"))
        with self.assertRaises(sqlite3.IntegrityError):          # kendi kendine kayıt DB'de de yasak
            self.db.execute("INSERT INTO parola_sifirlama (kullanici_id, sifirlayan_id, tarih)"
                            " VALUES (1, 1, '2026-11-17T10:00:00')")


class Migrasyon006Testi(unittest.TestCase):
    def test_mevcut_kullanicilar_korunur_ve_parola_degistirmeli_degildir(self):
        """005'e kadar kurulu bir veritabanına 006 uygulanınca hesaplar aynen girebilir."""
        db = baglanti_ac(":memory:")
        asil_klasor = database.MIGRASYON_KLASORU
        with tempfile.TemporaryDirectory() as gecici:
            for dosya in asil_klasor.glob("00[1-5]_*.sql"):      # 006 öncesini taklit et
                shutil.copy(dosya, gecici)
            database.MIGRASYON_KLASORU = Path(gecici)
            try:
                migrasyonlari_uygula(db)
            finally:
                database.MIGRASYON_KLASORU = asil_klasor
        db.execute("INSERT INTO kullanici (kullanici_adi, ad_soyad, parola_hash, rol, olusturma_tarihi)"
                   " VALUES ('eski', 'Eski Hesap', 'pbkdf2_sha256$1$00$00', 'Kurum', '2026-10-01T09:00:00')")
        db.commit()

        self.assertEqual(migrasyonlari_uygula(db)[0], "006_parola_sifirlama.sql")   # 006 ve sonrası
        k = KullaniciRepository(db).kullanici_adi_ile_getir("eski")
        self.assertEqual(k.ad_soyad, "Eski Hesap")
        self.assertFalse(k.parola_degistirmeli)
        db.close()


if __name__ == "__main__":
    unittest.main()
