"""Hafta 7 - Bağış Girişi (B1-B8) ve İhtiyaç Eşleştirme (E1-E9) testleri."""

import unittest
from datetime import date, datetime, timedelta

from backend import config
from backend.data.database import baglanti_ac, islem, migrasyonlari_uygula
from backend.data.ornek_veri import ornek_veri_yukle
from backend.data.repositories import (
    BagisRepository, DepoRepository, IhtiyacNoktasiRepository, MalzemeRepository,
    StokHareketiRepository, StokRepository,
)
from backend.models import DagitimDurumu, Rol, TalepDurumu
from backend.services.bagis_servisi import BagisServisi, KalemGirdisi
from backend.services.envanter_servisi import EnvanterServisi
from backend.services.eslestirme_servisi import EslestirmeServisi, mesafe_km, talep_durumu
from backend.services.hatalar import DogrulamaHatasi, YetkisizErisim
from backend.services.kimlik_servisi import KimlikServisi

PAROLA = "Guvenli123"
GELECEK = (date.today() + timedelta(days=365)).isoformat()


class Hafta7Testi(unittest.TestCase):
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
        self.bagis = BagisServisi(self.db, self.kimlik, self.env)
        self.esl = EslestirmeServisi(self.db, self.kimlik, self.env)
        depolar = {d.ad.split()[0]: d.id for d in DepoRepository(self.db).listele()}
        self.merkez, self.genc, self.solhan = depolar["Bingöl"], depolar["Genç"], depolar["Solhan"]
        self.m = {m.ad: m.id for m in MalzemeRepository(self.db).listele()}
        self.nokta = {n.ad.split()[0]: n.id for n in IhtiyacNoktasiRepository(self.db).listele()}

        self.kimlik.kayit_ol("yonetici", "Yönetici", PAROLA, PAROLA, Rol.YONETICI)
        self.kimlik.kayit_ol("depo_merkez", "Merkez", PAROLA, PAROLA, Rol.DEPO, self.merkez)
        self.kimlik.kayit_ol("kurum1", "Kurum", PAROLA, PAROLA, Rol.KURUM)
        self.yonetici = self.kimlik.giris_yap("yonetici", PAROLA)
        self.depocu = self.kimlik.giris_yap("depo_merkez", PAROLA)
        self.kurum = self.kimlik.giris_yap("kurum1", PAROLA)

    def stok(self, depo_id, malzeme_adi):
        s = StokRepository(self.db).getir(depo_id, self.m[malzeme_adi])
        return s.miktar if s else 0

    def tutarli(self):
        hareket = StokHareketiRepository(self.db)
        return all(abs(s.miktar - hareket.toplam_degisim(s.depo_id, s.malzeme_id)) < 1e-9
                   for s in StokRepository(self.db).listele())

    def talep(self, nokta, malzeme):
        return next(t for t in self.esl.talepler(self.kurum, sadece_acik=False)
                    if t.nokta_id == self.nokta[nokta] and t.malzeme == malzeme and t.durum != "İptal")


# ======================================================================== BAĞIŞ
class BagisTestleri(Hafta7Testi):
    def kaydet(self, kalemler, token=None, depo=None, **ek):
        ek.setdefault("yeni_bagisci", {"ad": "Anonim Bağışçı 9", "tur": "Bireysel"})
        return self.bagis.bagis_kaydet(token or self.depocu, depo or self.merkez, kalemler, **ek)

    def test_bagis_stogu_artirir_ve_hareket_bagisi_gosterir(self):
        once = self.stok(self.merkez, "Battaniye")
        b = self.kaydet([KalemGirdisi(self.m["Battaniye"], 40),
                         KalemGirdisi(self.m["Kuru gıda kolisi"], "25", GELECEK)])
        self.assertEqual(self.stok(self.merkez, "Battaniye"), once + 40)
        gecmis = self.env.hareket_gecmisi(self.depocu, self.merkez, self.m["Battaniye"])
        self.assertEqual((gecmis[0]["tur"], gecmis[0]["aciklama"]), ("Giriş", f"Bağış #{b.id} - Anonim Bağışçı 9"))
        self.assertEqual(len(self.bagis.bagis_detayi(self.depocu, b.id)), 2)
        self.assertTrue(self.tutarli())

    def test_B1_kalemsiz_bagis_olmaz(self):
        with self.assertRaises(DogrulamaHatasi):
            self.kaydet([])

    def test_B2_miktar_envanter_kurallarina_uyar(self):
        with self.assertRaises(DogrulamaHatasi):                 # adet kesirli olamaz
            self.kaydet([KalemGirdisi(self.m["Battaniye"], "2,5")])

    def test_B3_ayni_kalem_iki_kez_yazilamaz(self):
        with self.assertRaises(DogrulamaHatasi):
            self.kaydet([KalemGirdisi(self.m["Battaniye"], 5), KalemGirdisi(self.m["Battaniye"], 7)])

    def test_B4_suresi_gecmis_ve_gidada_skt_zorunlu(self):
        with self.assertRaises(DogrulamaHatasi):
            self.kaydet([KalemGirdisi(self.m["Konserve"], 5, "01.01.2020")])
        with self.assertRaises(DogrulamaHatasi):
            self.kaydet([KalemGirdisi(self.m["Konserve"], 5)])
        self.kaydet([KalemGirdisi(self.m["Konserve"], 5, "31.12.2099")])     # GG.AA.YYYY kabul

    def test_B5_depo_gorevlisi_baska_depoya_bagis_giremez_kurum_giremez(self):
        with self.assertRaises(YetkisizErisim):
            self.kaydet([KalemGirdisi(self.m["Battaniye"], 5)], depo=self.genc)
        with self.assertRaises(YetkisizErisim):
            self.kaydet([KalemGirdisi(self.m["Battaniye"], 5)], token=self.kurum)

    def test_B6_bagisci_dogrulama_ve_tekrar(self):
        for hatali in ({"ad": "A"}, {"ad": "Ali Veli", "tur": "Şirket"},
                       {"ad": "Ali Veli", "telefon": "abc"}, {"ad": "Ali Veli", "eposta": "ali@"},
                       {"ad": "ANONİM BAĞIŞÇI 1"}):                      # mevcut (Türkçe büyük harf)
            with self.assertRaises(DogrulamaHatasi, msg=str(hatali)):
                self.kaydet([KalemGirdisi(self.m["Battaniye"], 5)], yeni_bagisci=hatali)
        mevcut = self.bagis.bagiscilar(self.depocu)[0]
        b = self.kaydet([KalemGirdisi(self.m["Battaniye"], 5)], bagisci_id=mevcut.id, yeni_bagisci=None)
        self.assertEqual(BagisRepository(self.db).getir(b.id).bagisci_id, mevcut.id)

    def test_B7_gelecek_tarihli_bagis_olmaz(self):
        with self.assertRaises(DogrulamaHatasi):
            self.kaydet([KalemGirdisi(self.m["Battaniye"], 5)], tarih=datetime.now() + timedelta(days=2))

    def test_B8_bir_kalem_hataliysa_hicbir_sey_yazilmaz(self):
        bagis_sayisi, stok = BagisRepository(self.db).sayi(), self.stok(self.merkez, "Battaniye")
        with self.assertRaises(DogrulamaHatasi):
            self.kaydet([KalemGirdisi(self.m["Battaniye"], 5), KalemGirdisi(self.m["Konserve"], 5)])  # SKT yok
        self.assertEqual((BagisRepository(self.db).sayi(), self.stok(self.merkez, "Battaniye")), (bagis_sayisi, stok))
        self.assertEqual(len([b for b in self.bagis.bagiscilar(self.depocu) if b.ad == "Anonim Bağışçı 9"]), 0)

    def test_depo_gorevlisi_yalnizca_kendi_bagislarini_gorur(self):
        depolar = {r["depo_id"] for r in self.bagis.bagis_listesi(self.depocu)}
        self.assertEqual(depolar, {self.merkez})
        self.assertGreater(len({r["depo_id"] for r in self.bagis.bagis_listesi(self.yonetici)}), 1)


# =================================================================== EŞLEŞTİRME
class EslestirmeTestleri(Hafta7Testi):
    def test_ornek_veri_talep_durumlari_dagitimlarla_tutarli(self):
        for t in self.esl.talepler(self.kurum, sadece_acik=False):
            if t.durum != "İptal":
                self.assertEqual(t.durum, talep_durumu(t.miktar, t.karsilanan).value, t)

    def test_oneri_en_yakin_depodan_baslar_ve_kalani_asmaz(self):
        t = self.talep("Karlıova", "Kuru gıda kolisi")          # 300 talep, 120 yolda -> kalan 180
        o = self.esl.oneri(self.kurum, t.id)
        self.assertEqual(t.kalan, 180)
        self.assertLessEqual(sum(s.miktar for s in o.satirlar), t.kalan)
        km = [s.mesafe_km for s in o.adaylar]
        self.assertEqual(km, sorted(km))                         # en yakın önce

    def test_eksik_durumu_karsilanamayan_miktari_raporlar(self):
        t = self.talep("Karlıova", "Bebek maması")              # 60 talep, toplam stok 40
        o = self.esl.oneri(self.kurum, t.id)
        self.assertEqual((sum(s.miktar for s in o.satirlar), o.karsilanamayan), (40, 20))

    def test_eslestirme_kismen_sonra_tam_karsilar(self):
        t = self.talep("Karlıova", "Bebek maması")
        self.esl.eslestir(self.kurum, t.id, [(self.genc, 40)], "12 abc 123")
        self.assertEqual(self.talep("Karlıova", "Bebek maması").durum, "Kısmen karşılandı")
        self.bagis.bagis_kaydet(self.yonetici, self.genc, [KalemGirdisi(self.m["Bebek maması"], 20, GELECEK)],
                                yeni_bagisci={"ad": "Örnek Market"})
        self.esl.eslestir(self.kurum, t.id, [(self.genc, 20)])
        self.assertEqual(self.talep("Karlıova", "Bebek maması").durum, "Karşılandı")

    def test_E1_kapali_talebe_eslestirme_olmaz(self):
        t = self.talep("Kiğı", "İçme suyu (5 L)")               # Karşılandı
        with self.assertRaises(DogrulamaHatasi):
            self.esl.eslestir(self.kurum, t.id, [(self.merkez, 1)])

    def test_E2_fazla_gonderim_engellenir(self):
        t = self.talep("Karlıova", "Kuru gıda kolisi")          # kalan 180
        with self.assertRaises(DogrulamaHatasi) as h:
            self.bagis.bagis_kaydet(self.yonetici, self.merkez,
                                    [KalemGirdisi(self.m["Kuru gıda kolisi"], 500, GELECEK)],
                                    yeni_bagisci={"ad": "Örnek Gıda Deposu"})
            self.esl.eslestir(self.kurum, t.id, [(self.merkez, 181)])
        self.assertIn("Fazla gönderim", str(h.exception))

    def test_E3_rezerve_dusulmus_uygun_stok_asilamaz(self):
        kuru = self.m["Kuru gıda kolisi"]
        stok_once, uygun_once = self.stok(self.merkez, "Kuru gıda kolisi"), self.esl.uygun_stok(self.merkez, kuru)
        t = self.talep("Karlıova", "Kuru gıda kolisi")
        self.esl.eslestir(self.kurum, t.id, [(self.merkez, 100)])             # 100 koli rezerve
        self.assertEqual(self.esl.uygun_stok(self.merkez, kuru), uygun_once - 100)
        self.assertEqual(self.stok(self.merkez, "Kuru gıda kolisi"), stok_once)   # stok henüz düşmedi
        yeni = self.esl.talep_ekle(self.kurum, self.nokta["Yedisu"], kuru, 5000)
        with self.assertRaises(DogrulamaHatasi) as h:
            self.esl.eslestir(self.kurum, yeni.id, [(self.merkez, uygun_once - 100 + 1)])
        self.assertIn("uygun stok", str(h.exception))

    def test_E5_ayni_nokta_ayni_malzeme_ikinci_acik_talep_olmaz(self):
        with self.assertRaises(DogrulamaHatasi):
            self.esl.talep_ekle(self.kurum, self.nokta["Karlıova"], self.m["Battaniye"], 10)
        yeni = self.esl.talep_ekle(self.kurum, self.nokta["Yedisu"], self.m["Battaniye"], "30")
        self.assertEqual(yeni.durum, TalepDurumu.BEKLIYOR)

    def test_E6_dagitimi_olan_talep_iptal_edilemez(self):
        with self.assertRaises(DogrulamaHatasi):
            self.esl.talep_iptal(self.kurum, self.talep("Karlıova", "Battaniye").id)
        t = self.talep("Kiğı", "Hijyen kiti")
        self.esl.talep_iptal(self.kurum, t.id)
        self.assertNotIn(t.id, [x.id for x in self.esl.talepler(self.kurum)])

    def test_E7_E8_dagitim_yasam_dongusu_stok_ve_talep_durumu(self):
        t = self.talep("Karlıova", "Bebek maması")
        d = self.esl.eslestir(self.kurum, t.id, [(self.genc, 40)])[0]
        with self.assertRaises(DogrulamaHatasi):                 # Planlandı -> Teslim edildi atlanamaz
            self.esl.dagitim_durumu_degistir(self.kurum, d.id, DagitimDurumu.TESLIM_EDILDI)
        once = self.stok(self.genc, "Bebek maması")
        self.esl.dagitim_durumu_degistir(self.kurum, d.id, DagitimDurumu.YOLDA)
        self.assertEqual(self.stok(self.genc, "Bebek maması"), once - 40)     # stok yolda düşer
        self.esl.dagitim_durumu_degistir(self.kurum, d.id, DagitimDurumu.IPTAL)
        self.assertEqual(self.stok(self.genc, "Bebek maması"), once)          # iade
        self.assertEqual(self.talep("Karlıova", "Bebek maması").durum, "Bekliyor")
        self.assertTrue(self.tutarli())

    def test_teslim_edildi_tarih_yazar_ve_son_durumdur(self):
        d = next(r for r in self.esl.dagitim_listesi(self.kurum) if r["durum"] == "Yolda")
        sonuc = self.esl.dagitim_durumu_degistir(self.kurum, d["id"], DagitimDurumu.TESLIM_EDILDI)
        self.assertIsNotNone(sonuc.teslim_tarihi)
        with self.assertRaises(DogrulamaHatasi):
            self.esl.dagitim_durumu_degistir(self.kurum, d["id"], DagitimDurumu.IPTAL)

    def test_yetki_depo_rolu_eslestirme_yapamaz(self):
        with self.assertRaises(YetkisizErisim):
            self.esl.talepler(self.depocu)
        with self.assertRaises(YetkisizErisim):
            self.esl.dagitim_listesi(self.depocu)

    def test_stok_talep_dengesi_fazla_eksik(self):
        denge = {s.malzeme: s for s in self.esl.stok_talep_dengesi(self.kurum)}
        self.assertEqual(denge["Bebek maması"].durum, "Eksik")          # 40 stok < 60 talep
        self.assertEqual(denge["Bebek maması"].fark, -20)
        self.assertEqual(denge["Konserve"].durum, "Talep yok")          # stok var, talep yok

    def test_plaka_bicimi(self):
        t = self.talep("Karlıova", "Bebek maması")
        with self.assertRaises(DogrulamaHatasi):
            self.esl.eslestir(self.kurum, t.id, [(self.genc, 1)], "ABC")

    def test_mesafe_hesabi(self):
        self.assertAlmostEqual(mesafe_km(38.885, 40.498, 39.294, 41.009), 63.0, delta=2)
        self.assertIsNone(mesafe_km(None, 40, 39, 41))


class Migrasyon005Testi(unittest.TestCase):
    def test_eski_dagitimlar_taleplere_baglanir_ve_durumlar_hesaplanir(self):
        db = baglanti_ac(":memory:")
        self.addCleanup(db.close)
        migrasyonlari_uygula(db)
        with islem(db):
            ornek_veri_yukle(db)
            db.execute("UPDATE dagitim_kalemi SET ihtiyac_talebi_id = NULL")   # 005 öncesini taklit et
            db.execute("UPDATE ihtiyac_talebi SET durum = 'Bekliyor' WHERE durum <> 'İptal'")
            db.execute("DROP INDEX idx_dagitim_kalemi_talep")
            db.execute("ALTER TABLE dagitim_kalemi DROP COLUMN ihtiyac_talebi_id")
            db.execute("DELETE FROM sema_surumu WHERE surum = 5")
        self.assertEqual(migrasyonlari_uygula(db), ["005_eslestirme.sql"])
        durum = dict(db.execute(
            "SELECT m.ad, t.durum FROM ihtiyac_talebi t JOIN malzeme m ON m.id = t.malzeme_id "
            "JOIN ihtiyac_noktasi n ON n.id = t.ihtiyac_noktasi_id WHERE n.ad LIKE 'Karlıova%'").fetchall())
        self.assertEqual(durum["Battaniye"], "Kısmen karşılandı")
        self.assertEqual(durum["Bebek maması"], "Bekliyor")


if __name__ == "__main__":
    unittest.main()
