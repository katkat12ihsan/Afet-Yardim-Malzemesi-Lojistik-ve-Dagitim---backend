"""Hafta 8 - Uçtan uca entegrasyon ve regresyon testleri.

Birim testleri tek bir servisi dener; buradaki testler modülleri BİRLİKTE dener:
kullanıcı (Hafta 5) + veritabanı (Hafta 4) + envanter (Hafta 6) + bağış ve eşleştirme (Hafta 7).
"Regresyon" testleri, Hafta 8'de bulunan hataların geri gelmediğini garanti eder.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from backend import config
from backend.data.database import baglanti_ac, islem, migrasyonlari_uygula
from backend.data.ornek_veri import KULLANICILAR, ornek_kullanicilari_yukle, ornek_veri_yukle
from backend.data.repositories import (
    DepoRepository, IhtiyacNoktasiRepository, MalzemeRepository, StokHareketiRepository, StokRepository,
)
from backend.models import DagitimDurumu, Rol
from backend.services.bagis_servisi import BagisServisi, KalemGirdisi
from backend.services.envanter_servisi import EnvanterServisi
from backend.services.eslestirme_servisi import EslestirmeServisi
from backend.services.hatalar import DogrulamaHatasi, OturumGecersiz, YetkisizErisim
from backend.services.kimlik_servisi import KimlikServisi
from backend.services.ozet_servisi import OzetServisi

GELECEK = (date.today() + timedelta(days=200)).isoformat()
PROJE = Path(__file__).resolve().parent.parent


class Sistem(unittest.TestCase):
    """Uygulamanın main.py'de kurduğu servis zincirinin aynısı (bellek içi veritabanıyla)."""

    def setUp(self):
        self.addCleanup(setattr, config, "PAROLA_ITERASYON", config.PAROLA_ITERASYON)
        config.PAROLA_ITERASYON = 1_000
        self.db = baglanti_ac(":memory:")
        self.addCleanup(self.db.close)
        migrasyonlari_uygula(self.db)
        with islem(self.db):
            ornek_veri_yukle(self.db)
            ornek_kullanicilari_yukle(self.db)
        self.kimlik = KimlikServisi(self.db)
        self.env = EnvanterServisi(self.db, self.kimlik)
        self.bagis = BagisServisi(self.db, self.kimlik, self.env)
        self.esl = EslestirmeServisi(self.db, self.kimlik, self.env)
        self.ozet = OzetServisi(self.db, self.kimlik)
        parola = {k: p for k, _, p, _, _ in KULLANICILAR}
        self.giris = lambda kadi: self.kimlik.giris_yap(kadi, parola[kadi])
        self.m = {m.ad: m.id for m in MalzemeRepository(self.db).listele()}
        self.depo = {d.ad.split()[0]: d.id for d in DepoRepository(self.db).listele()}
        self.nokta = {n.ad.split()[0]: n.id for n in IhtiyacNoktasiRepository(self.db).listele()}

    def stok(self, depo, malzeme):
        s = StokRepository(self.db).getir(self.depo[depo], self.m[malzeme])
        return s.miktar if s else 0

    def stok_hareketle_tutarli(self):
        h = StokHareketiRepository(self.db)
        return all(abs(s.miktar - h.toplam_degisim(s.depo_id, s.malzeme_id)) < 1e-9
                   for s in StokRepository(self.db).listele())


class UctanUcaSenaryo(Sistem):
    def test_bagistan_teslime_tam_akis(self):
        """Vize demo senaryosunun kendisi: bağış -> talep -> eşleştirme -> yola çıkış -> teslim."""
        depocu, kurum, yonetici = self.giris("depo1"), self.giris("kurum1"), self.giris("yonetici")
        bekleyen_once = self.ozet.panel_ozeti(yonetici).bekleyen_talep

        # 1) Depo görevlisi kendi deposuna bağış girer -> stok ve hareket geçmişi artar
        stok_once = self.stok("Bingöl", "Hijyen kiti")
        b = self.bagis.bagis_kaydet(depocu, self.depo["Bingöl"], [KalemGirdisi(self.m["Hijyen kiti"], 40)],
                                    yeni_bagisci={"ad": "Örnek Eczane", "tur": "Kurumsal"})
        self.assertEqual(self.stok("Bingöl", "Hijyen kiti"), stok_once + 40)
        self.assertIn(f"Bağış #{b.id}", self.env.hareket_gecmisi(depocu, self.depo["Bingöl"])[0]["aciklama"])

        # 2) Kurum, talebi öneriyle tam karşılar: bağış sayesinde artık eksik yok; en yakın depo önce
        t = next(x for x in self.esl.talepler(kurum) if x.malzeme == "Hijyen kiti")
        o = self.esl.oneri(kurum, t.id)
        self.assertEqual(o.karsilanamayan, 0)
        self.assertEqual(sum(s.miktar for s in o.satirlar), t.kalan)
        km = [s.mesafe_km for s in o.satirlar]
        self.assertEqual(km, sorted(km))
        once = {s.depo_id: StokRepository(self.db).getir(s.depo_id, self.m["Hijyen kiti"]).miktar for s in o.satirlar}
        dagitimlar = self.esl.eslestir(kurum, t.id, [(s.depo_id, s.miktar) for s in o.satirlar], "12 ABC 08")
        self.assertEqual(next(x for x in self.esl.talepler(kurum, False) if x.id == t.id).durum, "Karşılandı")

        # 3) Dağıtımlar yola çıkar (stok o anda düşer) ve teslim edilir
        for d in dagitimlar:
            self.esl.dagitim_durumu_degistir(kurum, d.id, DagitimDurumu.YOLDA)
            self.esl.dagitim_durumu_degistir(kurum, d.id, DagitimDurumu.TESLIM_EDILDI)
        for s in o.satirlar:
            self.assertEqual(StokRepository(self.db).getir(s.depo_id, self.m["Hijyen kiti"]).miktar,
                             once[s.depo_id] - s.miktar)

        # 4) Panel ve tutarlılık: bir talep kapandı, stok = hareketlerin toplamı
        self.assertEqual(self.ozet.panel_ozeti(yonetici).bekleyen_talep, bekleyen_once - 1)
        self.assertTrue(self.stok_hareketle_tutarli())

    def test_rol_degisikligi_tum_modullere_yansir(self):
        """Kullanıcı modülü ile diğer modüller: rol değişince eski oturum kapanır, yeni yetki geçerli olur."""
        yonetici, kurum = self.giris("yonetici"), self.giris("kurum1")
        kurum_id = self.kimlik.oturum_dogrula(kurum).id
        self.kimlik.rol_degistir(yonetici, kurum_id, Rol.DEPO, self.depo["Genç"])
        with self.assertRaises(OturumGecersiz):
            self.esl.talepler(kurum)
        yeni = self.giris("kurum1")
        with self.assertRaises(YetkisizErisim):            # artık Depo: eşleştirme yok
            self.esl.talepler(yeni)
        self.assertEqual([d.id for d in self.env.erisilebilir_depolar(yeni)], [self.depo["Genç"]])

    def test_yola_cikista_stok_yetmezse_hicbir_sey_degismez(self):
        kurum, yonetici = self.giris("kurum1"), self.giris("yonetici")
        t = next(x for x in self.esl.talepler(kurum) if x.malzeme == "Bebek maması")
        d = self.esl.eslestir(kurum, t.id, [(self.depo["Genç"], 40)])[0]
        self.env.sayim_duzeltmesi(yonetici, self.depo["Genç"], self.m["Bebek maması"], 10, "Sayımda 30 eksik çıktı")
        with self.assertRaises(DogrulamaHatasi):
            self.esl.dagitim_durumu_degistir(kurum, d.id, DagitimDurumu.YOLDA)
        self.assertEqual(self.stok("Genç", "Bebek maması"), 10)
        durum = next(r["durum"] for r in self.esl.dagitim_listesi(kurum) if r["id"] == d.id)
        self.assertEqual(durum, "Planlandı")               # transaction geri alındı
        self.assertTrue(self.stok_hareketle_tutarli())


class Regresyon(Sistem):
    def test_hata1_rezerve_stok_envanterden_cikarilamaz(self):
        """Hafta 8 hatası: planlanan dağıtımın stoğu Envanter'den çıkarılabiliyordu, dağıtım yola çıkamıyordu."""
        kurum, depocu = self.giris("kurum1"), self.giris("depo1")
        t = next(x for x in self.esl.talepler(kurum) if x.malzeme == "Kuru gıda kolisi")
        d = self.esl.eslestir(kurum, t.id, [(self.depo["Bingöl"], 180)])[0]      # 280 stoktan 180 rezerve
        with self.assertRaises(DogrulamaHatasi) as h:
            self.env.stok_cikisi(depocu, self.depo["Bingöl"], self.m["Kuru gıda kolisi"], 200)
        self.assertIn("rezerve", str(h.exception))
        self.env.stok_cikisi(depocu, self.depo["Bingöl"], self.m["Kuru gıda kolisi"], 100)   # serbest kısım çıkar
        self.esl.dagitim_durumu_degistir(kurum, d.id, DagitimDurumu.YOLDA)              # artık yola çıkabiliyor
        satir = next(s for s in self.env.stok_listesi(depocu, self.depo["Bingöl"]) if s.malzeme == "Kuru gıda kolisi")
        self.assertEqual((satir.miktar, satir.rezerve, satir.serbest), (0, 0, 0))

    def test_hata2_talepte_gecen_malzemenin_birimi_degismez(self):
        """Hafta 8 hatası: K7 yalnızca stok/hareket bakıyordu; talepte geçen malzemenin birimi değişebiliyordu."""
        yonetici = self.giris("yonetici")
        kategori = MalzemeRepository(self.db).getir(self.m["Hijyen kiti"]).kategori_id
        yeni = self.env.malzeme_ekle(yonetici, kategori, "Diş fırçası", "adet")
        self.esl.talep_ekle(self.giris("kurum1"), self.nokta["Yedisu"], yeni.id, 50)   # yalnızca talepte geçiyor
        with self.assertRaises(DogrulamaHatasi):
            self.env.malzeme_guncelle(yonetici, yeni.id, kategori, "Diş fırçası", "paket")
        with self.assertRaises(DogrulamaHatasi):
            self.env.malzeme_sil(yonetici, yeni.id)


class KomutSatiriTesti(unittest.TestCase):
    """Kurulum ve demo komutları gerçek bir süreç olarak, geçici veritabanında çalışıyor mu?"""

    def calistir(self, *arg, db):
        ortam = dict(os.environ, AFET_DB_YOLU=db, PYTHONIOENCODING="utf-8")
        sonuc = subprocess.run([sys.executable, "-m", *arg], cwd=PROJE, env=ortam,
                               capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(sonuc.returncode, 0, sonuc.stderr)
        return sonuc.stdout

    def test_kurulum_ve_veritabani_demosu(self):
        with tempfile.TemporaryDirectory() as klasor:
            db = str(Path(klasor) / "deneme.db")
            cikti = self.calistir("backend.data.kurulum", "--sifirla", "--ornek-veri", db=db)
            self.assertIn("005_eslestirme.sql", cikti)
            self.assertIn("Test kullanıcıları eklendi", cikti)
            self.assertIn("şema güncel", self.calistir("backend.data.kurulum", db=db))     # migration tekrar yok
            demo = self.calistir("backend.data.sorgu_ornekleri", db=db)
            self.assertNotIn("KABUL EDİLDİ", demo)                                    # tüm kısıtlar reddetti
            self.assertIn("ROLLBACK", demo)


if __name__ == "__main__":
    unittest.main()
