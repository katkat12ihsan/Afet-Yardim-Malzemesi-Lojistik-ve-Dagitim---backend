"""Hafta 6 - Envanter Yönetimi testleri (iş kuralları K1-K8, bkz. envanter_servisi.py)."""

import sqlite3
import unittest

from backend import config
from backend.data.database import baglanti_ac, islem, migrasyonlari_uygula
from backend.data.ornek_veri import ornek_veri_yukle
from backend.data.repositories import (
    DepoRepository, MalzemeRepository, StokHareketiRepository, StokRepository,
)
from backend.models import Rol
from backend.services.envanter_servisi import EnvanterServisi
from backend.services.hatalar import DogrulamaHatasi, YetkisizErisim
from backend.services.kimlik_servisi import KimlikServisi
from backend.services.ozet_servisi import OzetServisi

PAROLA = "Guvenli123"


class EnvanterTesti(unittest.TestCase):
    def setUp(self):
        self.addCleanup(setattr, config, "PAROLA_ITERASYON", config.PAROLA_ITERASYON)
        config.PAROLA_ITERASYON = 1_000
        self.db = baglanti_ac(":memory:")
        self.addCleanup(self.db.close)
        migrasyonlari_uygula(self.db)
        with islem(self.db):
            ornek_veri_yukle(self.db)
        self.kimlik = KimlikServisi(self.db)
        self.env = EnvanterServisi(self.db, self.kimlik)
        depolar = DepoRepository(self.db).listele()            # ada göre: Bingöl, Genç, Solhan
        self.merkez, self.genc = depolar[0].id, depolar[1].id
        malzemeler = {m.ad: m for m in MalzemeRepository(self.db).listele()}
        self.battaniye = malzemeler["Battaniye"].id             # adet
        self.konserve = malzemeler["Konserve"].id               # koli
        self.kategori_id = malzemeler["Battaniye"].kategori_id

        self.kimlik.kayit_ol("yonetici", "Yönetici", PAROLA, PAROLA, Rol.YONETICI)
        self.kimlik.kayit_ol("depo_merkez", "Merkez Görevlisi", PAROLA, PAROLA, Rol.DEPO, self.merkez)
        self.kimlik.kayit_ol("kurum1", "Kurum", PAROLA, PAROLA, Rol.KURUM)
        self.yonetici = self.kimlik.giris_yap("yonetici", PAROLA)
        self.depocu = self.kimlik.giris_yap("depo_merkez", PAROLA)
        self.kurum = self.kimlik.giris_yap("kurum1", PAROLA)

    def miktar(self, depo_id, malzeme_id):
        stok = StokRepository(self.db).getir(depo_id, malzeme_id)
        return stok.miktar if stok else 0

    def tutarli_mi(self, depo_id, malzeme_id):
        return abs(self.miktar(depo_id, malzeme_id)
                   - StokHareketiRepository(self.db).toplam_degisim(depo_id, malzeme_id)) < 1e-9


class StokHareketiTestleri(EnvanterTesti):
    def test_giris_stogu_artirir_ve_hareket_kaydeder(self):
        once = self.miktar(self.merkez, self.battaniye)
        h = self.env.stok_girisi(self.depocu, self.merkez, self.battaniye, 50, "Yeni bağış")
        self.assertEqual(self.miktar(self.merkez, self.battaniye), once + 50)
        self.assertEqual((h.onceki_miktar, h.sonraki_miktar, h.degisim), (once, once + 50, 50))
        gecmis = self.env.hareket_gecmisi(self.depocu, self.merkez, self.battaniye)
        self.assertEqual(gecmis[0]["tur"], "Giriş")
        self.assertEqual(gecmis[0]["kullanici"], "depo_merkez")

    def test_cikis_stogu_azaltir(self):
        once = self.miktar(self.merkez, self.battaniye)
        self.env.stok_cikisi(self.depocu, self.merkez, self.battaniye, "20", "Sevkiyat")
        self.assertEqual(self.miktar(self.merkez, self.battaniye), once - 20)

    def test_K1_stok_eksiye_dusemez_ve_hicbir_sey_yazilmaz(self):
        once = self.miktar(self.merkez, self.battaniye)
        hareket_sayisi = StokHareketiRepository(self.db).sayi()
        with self.assertRaises(DogrulamaHatasi) as h:
            self.env.stok_cikisi(self.depocu, self.merkez, self.battaniye, once + 1)
        self.assertIn("Yetersiz stok", str(h.exception))
        self.assertEqual(self.miktar(self.merkez, self.battaniye), once)
        self.assertEqual(StokHareketiRepository(self.db).sayi(), hareket_sayisi)

    def test_K2_adet_birimi_kesirli_olamaz(self):
        with self.assertRaises(DogrulamaHatasi):
            self.env.stok_girisi(self.depocu, self.merkez, self.battaniye, "2,5")

    def test_K3_sifir_negatif_ve_metin_miktar_reddedilir(self):
        for gecersiz in (0, -5, "abc", "", 10_000_000):
            with self.assertRaises(DogrulamaHatasi):
                self.env.stok_girisi(self.depocu, self.merkez, self.battaniye, gecersiz)

    def test_K4_sayim_aciklama_zorunlu_ve_fark_kaydedilir(self):
        once = self.miktar(self.merkez, self.konserve)
        with self.assertRaises(DogrulamaHatasi):
            self.env.sayim_duzeltmesi(self.depocu, self.merkez, self.konserve, once - 3, "")
        h = self.env.sayim_duzeltmesi(self.depocu, self.merkez, self.konserve, once - 3,
                                      "3 koli hasarlı, imha edildi")
        self.assertEqual(h.degisim, -3)
        self.assertEqual(self.miktar(self.merkez, self.konserve), once - 3)

    def test_ilk_giris_stok_satiri_olusturur(self):
        self.assertEqual(self.miktar(self.genc, self.konserve), 0)
        yonetici_h = self.env.stok_girisi(self.yonetici, self.genc, self.konserve, 10)
        self.assertEqual(yonetici_h.onceki_miktar, 0)
        self.assertEqual(self.miktar(self.genc, self.konserve), 10)

    def test_K8_stok_her_zaman_hareketlerin_toplamina_esit(self):
        self.env.stok_girisi(self.depocu, self.merkez, self.battaniye, 30)
        self.env.stok_cikisi(self.depocu, self.merkez, self.battaniye, 12)
        self.env.sayim_duzeltmesi(self.depocu, self.merkez, self.battaniye, 100, "Yıl sonu sayımı")
        for stok in StokRepository(self.db).listele():          # örnek verideki tüm stoklar dahil
            self.assertTrue(self.tutarli_mi(stok.depo_id, stok.malzeme_id), stok)

    def test_hareket_tablosu_tutarsiz_kaydi_reddeder(self):
        with self.assertRaises(sqlite3.IntegrityError):          # sonraki != önceki + değişim
            self.db.execute(
                "INSERT INTO stok_hareketi (depo_id, malzeme_id, tur, degisim, onceki_miktar,"
                " sonraki_miktar, tarih) VALUES (?, ?, 'Giriş', 5, 10, 99, '2026-10-21T10:00:00')",
                (self.merkez, self.battaniye))


class YetkiVeSahiplikTestleri(EnvanterTesti):
    def test_K5_depo_gorevlisi_baska_depoya_dokunamaz(self):
        with self.assertRaises(YetkisizErisim):
            self.env.stok_listesi(self.depocu, self.genc)
        with self.assertRaises(YetkisizErisim):
            self.env.stok_girisi(self.depocu, self.genc, self.battaniye, 5)
        self.assertEqual([d.id for d in self.env.erisilebilir_depolar(self.depocu)], [self.merkez])

    def test_kurum_rolu_envantere_giremez(self):
        with self.assertRaises(YetkisizErisim):
            self.env.stok_listesi(self.kurum, self.merkez)

    def test_K6_tanimlari_yalnizca_yonetici_degistirir(self):
        with self.assertRaises(YetkisizErisim):
            self.env.malzeme_ekle(self.depocu, self.kategori_id, "Su arıtma tableti", "paket")
        m = self.env.malzeme_ekle(self.yonetici, self.kategori_id, "Su arıtma tableti", "paket")
        self.assertIsNotNone(m.id)

    def test_yonetici_tum_depolari_gorur(self):
        self.assertEqual(len(self.env.erisilebilir_depolar(self.yonetici)), 3)


class TanimTestleri(EnvanterTesti):
    def test_ayni_adli_malzeme_ve_kategori_eklenemez(self):
        with self.assertRaises(DogrulamaHatasi):
            self.env.malzeme_ekle(self.yonetici, self.kategori_id, "battaniye", "adet")
        for ayni in ("  gıda ", "GIDA", "BATTANİYE"):              # Türkçe I/ı, İ/i
            with self.assertRaises(DogrulamaHatasi):
                if ayni == "BATTANİYE":
                    self.env.malzeme_ekle(self.yonetici, self.kategori_id, ayni, "adet")
                else:
                    self.env.kategori_ekle(self.yonetici, ayni)

    def test_gecersiz_birim_reddedilir(self):
        with self.assertRaises(DogrulamaHatasi):
            self.env.malzeme_ekle(self.yonetici, self.kategori_id, "Jeneratör", "ton")

    def test_K7_stogu_olan_malzeme_silinemez_birimi_degismez(self):
        with self.assertRaises(DogrulamaHatasi):
            self.env.malzeme_sil(self.yonetici, self.battaniye)
        with self.assertRaises(DogrulamaHatasi):
            self.env.malzeme_guncelle(self.yonetici, self.battaniye, self.kategori_id,
                                      "Battaniye", "kg")
        guncel = self.env.malzeme_guncelle(self.yonetici, self.battaniye, self.kategori_id,
                                           "Battaniye (yün)", "adet", "Kışlık")
        self.assertEqual(guncel.ad, "Battaniye (yün)")

    def test_kullanilmayan_malzeme_silinir_dolu_kategori_silinemez(self):
        m = self.env.malzeme_ekle(self.yonetici, self.kategori_id, "Deneme Malzemesi", "adet")
        self.env.malzeme_sil(self.yonetici, m.id)
        self.assertIsNone(MalzemeRepository(self.db).getir(m.id))
        with self.assertRaises(DogrulamaHatasi):
            self.env.kategori_sil(self.yonetici, self.kategori_id)


class StokSeviyesiTestleri(EnvanterTesti):
    def test_kritik_seviye_ve_durum(self):
        satir = next(s for s in self.env.stok_listesi(self.depocu, self.merkez)
                     if s.malzeme_id == self.konserve)
        self.env.kritik_seviye_ayarla(self.depocu, self.merkez, self.konserve, satir.miktar + 1)
        satir = next(s for s in self.env.stok_listesi(self.depocu, self.merkez, sadece_kritik=True)
                     if s.malzeme_id == self.konserve)
        self.assertEqual(satir.durum, "Kritik")
        with self.assertRaises(DogrulamaHatasi):
            self.env.kritik_seviye_ayarla(self.depocu, self.merkez, self.konserve, -1)

    def test_stok_listesi_tum_malzemeleri_icerir_ve_filtrelenir(self):
        tumu = self.env.stok_listesi(self.yonetici, self.genc)
        self.assertEqual(len(tumu), MalzemeRepository(self.db).sayi())   # stoksuzlar 0 ile
        aranan = self.env.stok_listesi(self.yonetici, self.genc, arama="İÇME")
        self.assertEqual([s.malzeme for s in aranan], ["İçme suyu (5 L)"])

    def test_panel_kritik_sayisi_depo_gorevlisinin_deposuyla_sinirli(self):
        tum = OzetServisi(self.db, self.kimlik).panel_ozeti(self.yonetici).kritik_stok
        kendi = OzetServisi(self.db, self.kimlik).panel_ozeti(self.depocu).kritik_stok
        self.assertEqual(kendi, len(self.env.kritik_stoklar(self.depocu)))
        self.assertLessEqual(kendi, tum)


class SiralamaTesti(EnvanterTesti):
    def test_turkce_alfabe_sirasi(self):
        adlar = [m.ad for m in self.env.malzemeler(self.yonetici)]
        self.assertLess(adlar.index("Çadır (4 kişilik)"), adlar.index("Hijyen kiti"))
        self.assertLess(adlar.index("İçme suyu (5 L)"), adlar.index("Konserve"))
        self.assertLess(adlar.index("Hijyen kiti"), adlar.index("İçme suyu (5 L)"))   # ı < i


class MigrasyonTesti(unittest.TestCase):
    def test_003_mevcut_stoklar_icin_acilis_hareketi_olusturur(self):
        """Hafta 5'te kurulmuş bir veritabanı 003'ü aldığında stok = hareket toplamı olmalı."""
        db = baglanti_ac(":memory:")
        self.addCleanup(db.close)
        migrasyonlari_uygula(db)
        with islem(db):
            ornek_veri_yukle(db)
            db.execute("DELETE FROM stok_hareketi")              # 003 öncesi durumu taklit et
            db.execute("DELETE FROM sema_surumu WHERE surum = 3")
            db.execute("DROP TABLE stok_hareketi")
        self.assertEqual(migrasyonlari_uygula(db), ["003_stok_hareketi.sql"])
        hareketler = StokHareketiRepository(db)
        for stok in StokRepository(db).listele():
            self.assertAlmostEqual(stok.miktar, hareketler.toplam_degisim(stok.depo_id, stok.malzeme_id))


if __name__ == "__main__":
    unittest.main()
