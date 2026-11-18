"""Hafta 9 - Harita/rota API entegrasyonu testleri.

Testler gerçek harita servisine GİTMEZ (anahtar gerekmez, internet gerekmez, hız sınırı
harcanmaz): istemciye sahte bir "gönderici" verilir ve servisin döndürebileceği her yanıt
(başarılı, 403, 429, 404, 500, bozuk JSON, zaman aşımı, bağlantı yok) taklit edilir.
Zaman aşımı ve HTTP hata kodları ayrıca bilgisayarın içinde açılan küçük bir sunucuyla
gerçek urllib üzerinden de denenir.
"""

import json
import os
import socket
import tempfile
import threading
import unittest
import urllib.error
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

from backend import config
from backend.data.database import baglanti_ac, islem, migrasyonlari_uygula
from backend.data.ornek_veri import KULLANICILAR, ornek_kullanicilari_yukle, ornek_veri_yukle
from backend.data.repositories import DagitimRepository, DepoRepository, RotaOnbellekRepository
from backend.entegrasyon import harita_api as api
from backend.entegrasyon.harita_api import HaritaApiHatasi, OrsIstemcisi, urllib_gonderici, yaniti_ayristir
from backend.services import rota_servisi as rs
from backend.services.eslestirme_servisi import mesafe_km
from backend.services.hatalar import DogrulamaHatasi, YetkisizErisim
from backend.services.kimlik_servisi import KimlikServisi

ANAHTAR = "test-anahtari-123"
BINGOL, KIGI = (38.8853, 40.4983), (39.3097, 40.3497)


def ors_yaniti(metre=61234.5, saniye=3120.4, noktalar=((40.4983, 38.8853), (40.45, 39.1), (40.3497, 39.3097))):
    """ORS GeoJSON yanıtının taklidi (koordinatlar [boylam, enlem])."""
    return json.dumps({"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"summary": {"distance": metre, "duration": saniye}},
        "geometry": {"type": "LineString", "coordinates": [list(n) for n in noktalar]}}]}).encode()


class SahteGonderici:
    """Sıradaki yanıtı döndürür ya da hatayı fırlatır; gelen istekleri saklar."""

    def __init__(self, *yanitlar):
        self.yanitlar = list(yanitlar)
        self.istekler = []

    def __call__(self, url, govde, basliklar, zaman_asimi):
        self.istekler.append((url, json.loads(govde), basliklar, zaman_asimi))
        yanit = self.yanitlar.pop(0) if len(self.yanitlar) > 1 else self.yanitlar[0]
        if isinstance(yanit, BaseException):
            raise yanit
        return yanit


class SahteSaat:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def istemci(*yanitlar, anahtar=ANAHTAR, sinir=30):
    g, saat = SahteGonderici(*yanitlar), SahteSaat()
    return OrsIstemcisi(anahtar, zaman_asimi=2, dakikalik_sinir=sinir, gonderici=g, saat=saat), g, saat


# =================================================================== API istemcisi
class IstekVeYanitTestleri(unittest.TestCase):
    def test_istek_bicimi_ve_yanit_ayristirma(self):
        ist, g, _ = istemci((200, ors_yaniti()))
        rota = ist.rota(BINGOL, KIGI)
        url, govde, basliklar, zaman_asimi = g.istekler[0]
        self.assertEqual(url, api.ORS_URL)
        self.assertNotIn(ANAHTAR, url)                                    # anahtar URL'de değil
        self.assertEqual(basliklar["Authorization"], ANAHTAR)             # başlıkta
        self.assertEqual(govde["coordinates"], [[40.4983, 38.8853], [40.3497, 39.3097]])   # [boylam, enlem]
        self.assertEqual(zaman_asimi, 2)
        self.assertEqual((rota.mesafe_km, rota.sure_dk), (61.2, 52.0))    # m -> km, sn -> dk
        self.assertEqual(rota.geometri[0], BINGOL)                        # geri (enlem, boylam)
        self.assertEqual(len(rota.geometri), 3)

    def test_bozuk_yanitlar(self):
        bozuklar = [b"<html>bakim</html>", b"{}", b'{"features": []}',
                    json.dumps({"features": [{"properties": {}, "geometry": {}}]}).encode(),
                    ors_yaniti(metre=-5), ors_yaniti(noktalar=((40.0, 38.0),)), b"\xff\xfe"]
        for govde in bozuklar:
            with self.subTest(govde=govde[:30]), self.assertRaises(HaritaApiHatasi) as h:
                yaniti_ayristir(govde)
            self.assertEqual(h.exception.tur, api.YANIT_BOZUK)

    def test_anahtar_loglara_ve_mesajlara_sizmaz(self):
        ist, _, _ = istemci((403, b'{"error": "Access to this API has been disallowed"}'))
        self.assertNotIn(ANAHTAR, repr(ist))
        with self.assertRaises(HaritaApiHatasi) as h:
            ist.rota(BINGOL, KIGI)
        self.assertNotIn(ANAHTAR, str(h.exception) + h.exception.ayrinti)


class HataYonetimiTestleri(unittest.TestCase):
    def hata(self, ist):
        with self.assertRaises(HaritaApiHatasi) as h:
            ist.rota(BINGOL, KIGI)
        return h.exception

    def test_anahtar_yoksa_servise_gidilmez(self):
        ist, g, _ = istemci((200, ors_yaniti()), anahtar="  ")
        self.assertEqual(self.hata(ist).tur, api.ANAHTAR_YOK)
        self.assertEqual(g.istekler, [])

    def test_gecersiz_anahtar_bir_kez_denenir(self):
        ist, g, _ = istemci((403, b'{"error": "Access to this API has been disallowed"}'))
        h = self.hata(ist)
        self.assertEqual((h.tur, h.durum_kodu), (api.ANAHTAR_GECERSIZ, 403))
        self.assertIn("disallowed", h.ayrinti)
        self.assertEqual(self.hata(ist).tur, api.ANAHTAR_GECERSIZ)
        self.assertEqual(len(g.istekler), 1)                              # ikinci kez gönderilmedi

    def test_429_sonrasi_60_saniye_beklenir(self):
        ist, g, saat = istemci((429, b'{"error": "Rate Limit Exceeded"}'), (200, ors_yaniti()))
        self.assertEqual(self.hata(ist).tur, api.HIZ_SINIRI)
        saat.t += 30
        self.assertEqual(self.hata(ist).tur, api.HIZ_SINIRI)              # bekleme sürüyor
        self.assertEqual(len(g.istekler), 1)
        saat.t += 31
        self.assertEqual(ist.rota(BINGOL, KIGI).mesafe_km, 61.2)          # süre doldu
        self.assertEqual(len(g.istekler), 2)

    def test_istemci_tarafi_dakikalik_sinir(self):
        ist, g, saat = istemci((200, ors_yaniti()), sinir=2)
        ist.rota(BINGOL, KIGI)
        ist.rota(BINGOL, KIGI)
        self.assertEqual(self.hata(ist).tur, api.HIZ_SINIRI)
        self.assertEqual(len(g.istekler), 2)                              # 3. istek hiç gönderilmedi
        saat.t += 60
        ist.rota(BINGOL, KIGI)
        self.assertEqual(len(g.istekler), 3)

    def test_zaman_asimi_baglanti_ve_servis_hatalari(self):
        durumlar = [
            (TimeoutError("timed out"), api.ZAMAN_ASIMI),
            (urllib.error.URLError(TimeoutError()), api.ZAMAN_ASIMI),
            (urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed")), api.BAGLANTI),
            (ConnectionResetError(), api.BAGLANTI),
            ((404, b'{"error": {"code": 2010, "message": "Could not find routable point"}}'), api.ROTA_YOK),
            ((500, b"Internal Server Error"), api.SERVIS_HATASI),
            ((502, b""), api.SERVIS_HATASI),
        ]
        for yanit, tur in durumlar:
            with self.subTest(yanit=yanit):
                ist, _, _ = istemci(yanit)
                self.assertEqual(self.hata(ist).tur, tur)

    def test_404_hata_mesaji_ayrintiya_alinir(self):
        ist, _, _ = istemci((404, b'{"error": {"code": 2010, "message": "Could not find routable point"}}'))
        self.assertIn("routable", self.hata(ist).ayrinti)


class _YavasSunucu(BaseHTTPRequestHandler):
    """Yerel test sunucusu: /yavas yanıt vermeden bekler, /yasak 403 döner."""

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/yavas":
            threading.Event().wait(2)
            return
        govde = b'{"error": "Access to this API has been disallowed"}'
        self.send_response(403)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def log_message(self, *_):
        pass


class GercekUrllibTestleri(unittest.TestCase):
    """urllib_gonderici'nin gerçek ağ katmanında zaman aşımı ve HTTP hatasını doğru çevirdiği."""

    @classmethod
    def setUpClass(cls):
        cls.sunucu = HTTPServer(("127.0.0.1", 0), _YavasSunucu)
        cls.sunucu.daemon_threads = True
        threading.Thread(target=cls.sunucu.serve_forever, daemon=True).start()
        cls.kok = f"http://127.0.0.1:{cls.sunucu.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.sunucu.shutdown()
        cls.sunucu.server_close()

    def yerel(self, yol, zaman_asimi):
        gonderici = lambda _url, govde, basliklar, _za: urllib_gonderici(self.kok + yol, govde, basliklar, zaman_asimi)
        return OrsIstemcisi(ANAHTAR, gonderici=gonderici)

    def test_gercek_zaman_asimi(self):
        with self.assertRaises(HaritaApiHatasi) as h:
            self.yerel("/yavas", 0.3).rota(BINGOL, KIGI)
        self.assertEqual(h.exception.tur, api.ZAMAN_ASIMI)

    def test_gercek_http_403(self):
        with self.assertRaises(HaritaApiHatasi) as h:
            self.yerel("/yasak", 3).rota(BINGOL, KIGI)
        self.assertEqual((h.exception.tur, h.exception.durum_kodu), (api.ANAHTAR_GECERSIZ, 403))


# =================================================================== iş katmanı
class RotaServisiTestleri(unittest.TestCase):
    def setUp(self):
        self._eski_iterasyon = config.PAROLA_ITERASYON
        config.PAROLA_ITERASYON = 1_000
        self.db = baglanti_ac(":memory:")
        migrasyonlari_uygula(self.db)
        with islem(self.db):
            ornek_veri_yukle(self.db)
            ornek_kullanicilari_yukle(self.db)
        self.kimlik = KimlikServisi(self.db)
        parola = {k: p for k, _, p, _, _ in KULLANICILAR}
        self.token = self.kimlik.giris_yap("kurum1", parola["kurum1"])
        self.depo_token = self.kimlik.giris_yap("depo1", parola["depo1"])
        self.dagitim = DagitimRepository(self.db).listele()[0]
        self.zaman = datetime(2026, 11, 18, 10, 0)

    def tearDown(self):
        self.db.close()
        config.PAROLA_ITERASYON = self._eski_iterasyon

    def servis(self, *yanitlar, anahtar=ANAHTAR):
        ist, self.g, _ = istemci(*yanitlar, anahtar=anahtar)
        return rs.RotaServisi(self.db, self.kimlik, ist, saat=lambda: self.zaman)

    def onbellek_sayisi(self):
        return len(RotaOnbellekRepository(self.db).tumu())

    def test_servisten_gelen_rota_onbellege_yazilir_ve_tekrar_sorulmaz(self):
        s = self.servis((200, ors_yaniti()))
        r = s.dagitim_rotasi(self.token, self.dagitim.id)
        self.assertEqual((r.kaynak, r.mesafe_km, r.sure_dk, r.uyari), (rs.KAYNAK_SERVIS, 61.2, 52.0, ""))
        self.assertFalse(r.tahmini)
        r2 = s.dagitim_rotasi(self.token, self.dagitim.id)
        self.assertEqual((r2.kaynak, r2.mesafe_km, len(r2.geometri)), (rs.KAYNAK_ONBELLEK, 61.2, 3))
        self.assertEqual(len(self.g.istekler), 1)                         # ikinci kez servise gidilmedi

    def test_yeniden_hesapla_onbellegi_atlar(self):
        s = self.servis((200, ors_yaniti()), (200, ors_yaniti(metre=70000)))
        s.dagitim_rotasi(self.token, self.dagitim.id)
        r = s.dagitim_rotasi(self.token, self.dagitim.id, yeniden_sor=True)
        self.assertEqual((r.kaynak, r.mesafe_km), (rs.KAYNAK_SERVIS, 70.0))
        self.assertEqual(len(self.g.istekler), 2)

    def test_eski_onbellek_ve_degisen_koordinat_yeniden_sorulur(self):
        s = self.servis((200, ors_yaniti()))
        s.dagitim_rotasi(self.token, self.dagitim.id)
        self.zaman += timedelta(days=config.ROTA_ONBELLEK_GUN + 1)        # süresi doldu
        self.assertEqual(s.dagitim_rotasi(self.token, self.dagitim.id).kaynak, rs.KAYNAK_SERVIS)
        depo = DepoRepository(self.db).getir(self.dagitim.depo_id)
        depo.enlem += 0.01                                                # depo taşındı
        with islem(self.db):
            DepoRepository(self.db).guncelle(depo)
        self.assertEqual(s.dagitim_rotasi(self.token, self.dagitim.id).kaynak, rs.KAYNAK_SERVIS)
        self.assertEqual(len(self.g.istekler), 3)
        self.assertEqual(self.onbellek_sayisi(), 1)                       # aynı satır güncellendi

    def test_anahtar_yoksa_kus_ucusu_tahmin(self):
        s = self.servis((200, ors_yaniti()), anahtar="")
        r = s.dagitim_rotasi(self.token, self.dagitim.id)
        kus = mesafe_km(*r.baslangic, *r.bitis)
        self.assertTrue(r.tahmini)
        self.assertAlmostEqual(r.mesafe_km, kus * rs.YOL_KATSAYISI, delta=0.1)
        self.assertAlmostEqual(r.sure_dk, r.mesafe_km / rs.ORTALAMA_HIZ_KMSA * 60, delta=0.1)
        self.assertIn("anahtarı tanımlı değil", r.uyari)
        self.assertEqual(r.geometri, (r.baslangic, r.bitis))              # düz çizgi
        self.assertEqual((self.g.istekler, self.onbellek_sayisi()), ([], 0))
        self.assertIn("tanımlı değil", s.servis_durumu())

    def test_servis_hatasinda_tahmin_doner_ve_onbellege_yazilmaz(self):
        for yanit, mesaj in ((TimeoutError(), "zamanında yanıt vermedi"),
                             ((429, b"{}"), "istek sınırına"),
                             ((500, b""), "geçici bir hata"),
                             ((200, b"bozuk"), "beklenen biçimde değil")):
            with self.subTest(mesaj=mesaj), self.assertLogs("backend.services.rota_servisi", "WARNING"):
                r = self.servis(yanit).dagitim_rotasi(self.token, self.dagitim.id)
                self.assertTrue(r.tahmini)
                self.assertIn(mesaj, r.uyari)
                self.assertIn("Kuş uçuşu tahmin gösteriliyor", r.uyari)
        self.assertEqual(self.onbellek_sayisi(), 0)

    def test_rota_listesi_servise_gitmez_onbellegi_gosterir(self):
        s = self.servis((200, ors_yaniti()))
        once = {r.dagitim_id: r for r in s.rota_listesi(self.token)}
        self.assertIsNone(once[self.dagitim.id].mesafe_km)
        s.dagitim_rotasi(self.token, self.dagitim.id)
        sonra = {r.dagitim_id: r for r in s.rota_listesi(self.token)}
        self.assertEqual((sonra[self.dagitim.id].mesafe_km, sonra[self.dagitim.id].sure_dk), (61.2, 52.0))
        self.assertEqual(len(self.g.istekler), 1)                         # yalnızca dagitim_rotasi

    def test_yetki_ve_dogrulama(self):
        s = self.servis((200, ors_yaniti()))
        with self.assertRaises(YetkisizErisim):                           # Depo rolü rota modülüne giremez
            s.dagitim_rotasi(self.depo_token, self.dagitim.id)
        with self.assertRaises(DogrulamaHatasi):
            s.dagitim_rotasi(self.token, 99999)
        depo = DepoRepository(self.db).getir(self.dagitim.depo_id)
        depo.enlem = None
        with islem(self.db):
            DepoRepository(self.db).guncelle(depo)
        with self.assertRaises(DogrulamaHatasi):
            s.dagitim_rotasi(self.token, self.dagitim.id)
        self.assertEqual(self.g.istekler, [])

    def test_sure_yazimi(self):
        self.assertEqual([rs.sure_yaz(x) for x in (None, 0, 40, 59.6, 75, 120)],
                         ["-", "0 dk", "40 dk", "1 sa 0 dk", "1 sa 15 dk", "2 sa 0 dk"])


# =================================================================== ayarlar
class AnahtarSaklamaTestleri(unittest.TestCase):
    def test_env_dosyasi_okunur(self):
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / ".env"
            yol.write_text("# yorum\n\nHARITA_API_ANAHTARI = \"abc 123\"\nBOS=\nYANLIS SATIR\nX='y'\n",
                           encoding="utf-8")
            self.assertEqual(config.env_dosyasi_oku(yol), {"HARITA_API_ANAHTARI": "abc 123", "BOS": "", "X": "y"})
            self.assertEqual(config.env_dosyasi_oku(Path(d) / "yok.env"), {})

    def test_ortam_degiskeni_env_dosyasindan_once_gelir(self):
        with mock.patch.dict(config._ENV, {"DENEME_AYARI": "dosyadan"}), \
                mock.patch.dict(os.environ, {"DENEME_AYARI": "ortamdan"}):
            self.assertEqual(config.ayar("DENEME_AYARI"), "ortamdan")
        with mock.patch.dict(config._ENV, {"DENEME_AYARI": "dosyadan"}):
            os.environ.pop("DENEME_AYARI", None)
            self.assertEqual(config.ayar("DENEME_AYARI"), "dosyadan")
        self.assertEqual(config.ayar("OLMAYAN_AYAR_XYZ", "varsayilan"), "varsayilan")

    def test_anahtar_depoda_yok(self):
        """Depodaki hiçbir izlenen dosyada gerçek anahtar biçiminde değer yok; .env gitignore'da."""
        kok = Path(__file__).resolve().parent.parent
        self.assertIn(".env", (kok / ".gitignore").read_text(encoding="utf-8").split())
        ornek = config.env_dosyasi_oku(kok / ".env.example")
        self.assertEqual(ornek.get("HARITA_API_ANAHTARI"), "")


if __name__ == "__main__":
    unittest.main()
