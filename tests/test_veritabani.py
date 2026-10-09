"""Hafta 4 - veritabanı, kısıt ve CRUD testleri (bellek içi SQLite)."""

import sqlite3
import unittest
from datetime import date, datetime

from backend.data.database import baglanti_ac, islem, migrasyonlari_uygula
from backend.data.ornek_veri import ornek_veri_yukle
from backend.data.repositories import (
    BagisKalemiRepository, BagisRepository, DagitimRepository, IhtiyacNoktasiRepository,
    IhtiyacTalebiRepository, KategoriRepository, MalzemeRepository, StokRepository,
)
from backend.models import (
    BagisKalemi, Dagitim, DagitimDurumu, IhtiyacTalebi, Kategori, Malzeme, OncelikSeviyesi,
    Rol, Stok,
)
from backend import config
from backend.services.kimlik_servisi import KimlikServisi
from backend.services.ozet_servisi import OzetServisi


class VeritabaniTesti(unittest.TestCase):
    def setUp(self):
        self.db = baglanti_ac(":memory:")
        migrasyonlari_uygula(self.db)
        with islem(self.db):
            ornek_veri_yukle(self.db)

    def tearDown(self):
        self.db.close()


class MigrasyonTestleri(VeritabaniTesti):
    def test_migration_tekrar_uygulanmaz(self):
        self.assertEqual(migrasyonlari_uygula(self.db), [])

    def test_tum_tablolar_olustu(self):
        tablolar = {s[0] for s in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for tablo in ("kategori", "malzeme", "depo", "ihtiyac_noktasi", "bagisci", "bagis",
                      "bagis_kalemi", "stok", "ihtiyac_talebi", "dagitim", "dagitim_kalemi",
                      "kullanici", "oturum"):
            self.assertIn(tablo, tablolar)

    def test_yabanci_anahtar_kontrolu_acik(self):
        self.assertEqual(self.db.execute("PRAGMA foreign_keys").fetchone()[0], 1)


class OrnekVeriTestleri(VeritabaniTesti):
    def test_ikinci_yukleme_atlanir(self):
        self.assertFalse(ornek_veri_yukle(self.db))

    def test_stok_eksi_degil_ve_bagislarla_tutarli(self):
        # Hiçbir stok eksi olamaz (CHECK) ve toplam stok <= toplam bağış
        toplam_stok = self.db.execute("SELECT SUM(miktar) FROM stok").fetchone()[0]
        toplam_bagis = self.db.execute("SELECT SUM(miktar) FROM bagis_kalemi").fetchone()[0]
        self.assertLessEqual(toplam_stok, toplam_bagis)


class CrudTestleri(VeritabaniTesti):
    def test_malzeme_crud(self):
        repo = MalzemeRepository(self.db)
        kategori = KategoriRepository(self.db).ekle(Kategori("Test Kategorisi"))
        m = repo.ekle(Malzeme(kategori.id, "Test malzemesi", "adet"))
        self.assertIsNotNone(m.id)
        self.assertEqual(repo.getir(m.id).ad, "Test malzemesi")
        m.birim = "koli"
        self.assertTrue(repo.guncelle(m))
        self.assertEqual(repo.getir(m.id).birim, "koli")
        self.assertTrue(repo.sil(m.id))
        self.assertIsNone(repo.getir(m.id))

    def test_enum_ve_tarih_donusumu(self):
        nokta = IhtiyacNoktasiRepository(self.db).listele()[0]  # öncelik sırasıyla ilk
        self.assertEqual(nokta.oncelik, OncelikSeviyesi.KRITIK)
        kalem = BagisKalemiRepository(self.db).listele()[0]
        self.assertIsInstance(kalem.son_kullanma_tarihi, date)
        dagitim = DagitimRepository(self.db).duruma_gore(DagitimDurumu.TESLIM_EDILDI)[0]
        self.assertIsInstance(dagitim.teslim_tarihi, datetime)

    def test_stok_upsert_bilesik_anahtar(self):
        repo = StokRepository(self.db)
        s = repo.listele()[0]
        repo.kaydet(Stok(s.depo_id, s.malzeme_id, 999, s.kritik_seviye))
        self.assertEqual(repo.getir(s.depo_id, s.malzeme_id).miktar, 999)
        self.assertEqual(repo.sayi(), len(repo.listele()))  # yeni satır eklenmedi


class KisitTestleri(VeritabaniTesti):
    def test_olmayan_malzemeye_kalem_eklenemez(self):
        bagis = BagisRepository(self.db).listele()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            BagisKalemiRepository(self.db).ekle(BagisKalemi(bagis.id, 99999, 1))

    def test_negatif_miktar_reddedilir(self):
        with self.assertRaises(sqlite3.IntegrityError):
            IhtiyacTalebiRepository(self.db).ekle(IhtiyacTalebi(1, 1, -5, datetime.now()))

    def test_stok_eksiye_dusemez(self):
        s = StokRepository(self.db).listele()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            StokRepository(self.db).kaydet(Stok(s.depo_id, s.malzeme_id, -1))

    def test_kullanimdaki_malzeme_silinemez(self):
        s = StokRepository(self.db).listele()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            MalzemeRepository(self.db).sil(s.malzeme_id)

    def test_teslim_edildi_icin_teslim_tarihi_zorunlu(self):
        with self.assertRaises(sqlite3.IntegrityError):
            DagitimRepository(self.db).ekle(
                Dagitim(1, 1, datetime.now(), None, DagitimDurumu.TESLIM_EDILDI))

    def test_bagis_silinince_kalemleri_silinir(self):
        bagis = BagisRepository(self.db).listele()[0]
        BagisRepository(self.db).sil(bagis.id)
        self.assertEqual(BagisKalemiRepository(self.db).bagisin_kalemleri(bagis.id), [])

    def test_hata_olursa_transaction_geri_alinir(self):
        repo = KategoriRepository(self.db)
        once = repo.sayi()
        with self.assertRaises(sqlite3.IntegrityError):
            with islem(self.db):
                repo.ekle(Kategori("Geçici"))
                repo.ekle(Kategori("Gıda"))  # UNIQUE ihlali -> tüm blok geri alınır
        self.assertEqual(repo.sayi(), once)


class OzetServisiTesti(VeritabaniTesti):
    def test_panel_ozeti(self):
        self.addCleanup(setattr, config, "PAROLA_ITERASYON", config.PAROLA_ITERASYON)
        config.PAROLA_ITERASYON = 1_000  # testler hızlı olsun
        kimlik = KimlikServisi(self.db)
        kimlik.kayit_ol("test_yonetici", "Test", "Parola123", "Parola123", Rol.YONETICI)
        token = kimlik.giris_yap("test_yonetici", "Parola123")
        ozet = OzetServisi(self.db, kimlik).panel_ozeti(token)
        self.assertEqual(ozet.depo, 3)
        self.assertEqual(ozet.malzeme_cesidi, 12)
        self.assertGreater(ozet.bekleyen_talep, 0)
        self.assertFalse(ozet.bos_mu)


if __name__ == "__main__":
    unittest.main()
