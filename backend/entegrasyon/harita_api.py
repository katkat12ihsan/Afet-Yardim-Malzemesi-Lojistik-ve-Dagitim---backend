"""OpenRouteService (ORS) yön/rota API istemcisi (Hafta 9).

Servis: https://openrouteservice.org  ·  Belge: https://openrouteservice.org/dev/#/api-docs
Uç nokta:  POST https://api.openrouteservice.org/v2/directions/driving-car/geojson

REST isteği:
  Başlık  Authorization: <API anahtarı>     (anahtar URL'ye YAZILMAZ: URL'ler sunucu,
          Content-Type: application/json      vekil ve tarayıcı kayıtlarında görünür)
  Gövde   {"coordinates": [[boylam, enlem], [boylam, enlem]]}   <- dikkat: önce BOYLAM

Başarılı yanıt (200, GeoJSON):
  {"features": [{"properties": {"summary": {"distance": 61234.5, "duration": 3120.4}},
                 "geometry": {"coordinates": [[40.49, 38.88], [40.48, 38.90], ...]}}]}
  distance metre, duration saniye; geometri [boylam, enlem] noktaları.

Hata yanıtları (servisin döndürdüğü kodlar):
  401/403 anahtar yok/geçersiz ("Access to this API has been disallowed")
  429     hız sınırı aşıldı (ücretsiz plan: dakikada 40, günde 2000 yön isteği)
  404     rota bulunamadı (ör. noktanın yakınında yol yok; ORS hata kodu 2010)
  5xx     servis tarafı hata

Hepsi `HaritaApiHatasi`na çevrilir; `tur` alanı hatanın türünü söyler ve iş katmanı
buna göre karar verir. Bu dosya yalnızca standart kütüphaneyi kullanır (urllib, json).
"""

import json
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Optional

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"

Koordinat = tuple[float, float]          # (enlem, boylam) - uygulamanın her yerinde bu sıra

# Hata türleri (HaritaApiHatasi.tur)
ANAHTAR_YOK = "anahtar_yok"
ANAHTAR_GECERSIZ = "anahtar_gecersiz"
HIZ_SINIRI = "hiz_siniri"
ZAMAN_ASIMI = "zaman_asimi"
BAGLANTI = "baglanti"
ROTA_YOK = "rota_bulunamadi"
SERVIS_HATASI = "servis_hatasi"
YANIT_BOZUK = "yanit_bozuk"

_MESAJLAR = {
    ANAHTAR_YOK: "Harita API anahtarı tanımlı değil.",
    ANAHTAR_GECERSIZ: "Harita API anahtarı geçersiz ya da yetkisiz.",
    HIZ_SINIRI: "Harita servisinin istek sınırına ulaşıldı; biraz sonra yeniden deneyin.",
    ZAMAN_ASIMI: "Harita servisi zamanında yanıt vermedi.",
    BAGLANTI: "Harita servisine bağlanılamadı (internet bağlantısı?).",
    ROTA_YOK: "Bu iki nokta arasında karayolu rotası bulunamadı.",
    SERVIS_HATASI: "Harita servisinde geçici bir hata oluştu.",
    YANIT_BOZUK: "Harita servisinin yanıtı beklenen biçimde değil.",
}


class HaritaApiHatasi(Exception):
    """Rota alınamadı. `tur`: yukarıdaki sabitlerden biri; `durum_kodu`: HTTP kodu (varsa)."""

    def __init__(self, tur: str, ayrinti: str = "", durum_kodu: Optional[int] = None) -> None:
        self.tur, self.ayrinti, self.durum_kodu = tur, ayrinti, durum_kodu
        super().__init__(_MESAJLAR.get(tur, tur))


@dataclass(frozen=True)
class ApiRotasi:
    mesafe_km: float
    sure_dk: float
    geometri: tuple[Koordinat, ...] = field(default=(), repr=False)


# İstek gönderici: (url, gövde, başlıklar, zaman_aşımı) -> (HTTP kodu, yanıt gövdesi).
# Testlerde gerçek ağ yerine sahte gönderici verilir.
Gonderici = Callable[[str, bytes, dict[str, str], float], tuple[int, bytes]]


def urllib_gonderici(url: str, govde: bytes, basliklar: dict[str, str], zaman_asimi: float) -> tuple[int, bytes]:
    istek = urllib.request.Request(url, data=govde, headers=basliklar, method="POST")
    try:
        with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
            return yanit.status, yanit.read()
    except urllib.error.HTTPError as hata:          # 4xx/5xx: gövdeyi de oku (hata mesajı orada)
        return hata.code, hata.read() or b""


def yaniti_ayristir(govde: bytes) -> ApiRotasi:
    """ORS GeoJSON yanıtını ApiRotasi'na çevirir; beklenmeyen biçimde YANIT_BOZUK."""
    try:
        veri = json.loads(govde.decode("utf-8"))
        ozellik = veri["features"][0]
        ozet = ozellik["properties"]["summary"]
        mesafe_m, sure_s = float(ozet["distance"]), float(ozet["duration"])
        noktalar = tuple((float(enlem), float(boylam))
                         for boylam, enlem, *_ in ozellik["geometry"]["coordinates"])
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as hata:
        raise HaritaApiHatasi(YANIT_BOZUK, type(hata).__name__) from None
    if mesafe_m < 0 or sure_s < 0 or len(noktalar) < 2:
        raise HaritaApiHatasi(YANIT_BOZUK, "eksi değer ya da eksik geometri")
    return ApiRotasi(round(mesafe_m / 1000, 1), round(sure_s / 60, 1), noktalar)


def _hata_ayrintisi(govde: bytes) -> str:
    """Hata yanıtındaki mesaj (log/ekran için). Anahtar hiçbir zaman mesaja eklenmez."""
    try:
        veri = json.loads(govde.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ""
    hata = veri.get("error") if isinstance(veri, dict) else None
    if isinstance(hata, dict):
        return str(hata.get("message", ""))[:200]
    return str(hata or "")[:200]


class OrsIstemcisi:
    """OpenRouteService'e rota soran istemci.

    Hız sınırı iki katmanlı:
      * İstemci tarafı: son 60 saniyedeki istek sayısı `dakikalik_sinir`a ulaştıysa
        servise HİÇ gidilmez (servisi yormadan ve anahtarı kilitletmeden durur).
      * Servis tarafı: 429 gelirse 60 saniye boyunca yeni istek gönderilmez.
    401/403 gelirse anahtar geçersizdir: aynı oturumda tekrar denenmez.
    """

    def __init__(self, anahtar: str, zaman_asimi: float = 6.0, dakikalik_sinir: int = 30,
                 gonderici: Gonderici = urllib_gonderici,
                 saat: Callable[[], float] = time.monotonic) -> None:
        self._anahtar = anahtar.strip()
        self._zaman_asimi = zaman_asimi
        self._sinir = dakikalik_sinir
        self._gonder = gonderici
        self._saat = saat
        self._istek_zamanlari: deque[float] = deque()
        self._bekle_bitis = 0.0
        self._anahtar_reddedildi = False

    @property
    def anahtar_var(self) -> bool:
        return bool(self._anahtar)

    def __repr__(self) -> str:                      # anahtar loglara/hata ekranına sızmasın
        return f"OrsIstemcisi(anahtar={'***' if self._anahtar else 'yok'})"

    def _hiz_kontrolu(self) -> None:
        simdi = self._saat()
        if simdi < self._bekle_bitis:
            raise HaritaApiHatasi(HIZ_SINIRI, f"{int(self._bekle_bitis - simdi) + 1} sn bekleniyor")
        while self._istek_zamanlari and simdi - self._istek_zamanlari[0] >= 60:
            self._istek_zamanlari.popleft()
        if len(self._istek_zamanlari) >= self._sinir:
            raise HaritaApiHatasi(HIZ_SINIRI, f"istemci sınırı: dakikada {self._sinir} istek")
        self._istek_zamanlari.append(simdi)

    def rota(self, baslangic: Koordinat, bitis: Koordinat) -> ApiRotasi:
        """İki nokta (enlem, boylam) arası karayolu rotası. Hata olursa HaritaApiHatasi."""
        if not self._anahtar:
            raise HaritaApiHatasi(ANAHTAR_YOK)
        if self._anahtar_reddedildi:
            raise HaritaApiHatasi(ANAHTAR_GECERSIZ, "bu oturumda reddedildi")
        self._hiz_kontrolu()

        govde = json.dumps({"coordinates": [[baslangic[1], baslangic[0]], [bitis[1], bitis[0]]]}).encode()
        basliklar = {"Authorization": self._anahtar, "Content-Type": "application/json",
                     "Accept": "application/geo+json, application/json",
                     "User-Agent": "AfetLojistik/0.7 (ders projesi)"}
        try:
            kod, yanit = self._gonder(ORS_URL, govde, basliklar, self._zaman_asimi)
        except TimeoutError:                                         # socket.timeout dahil
            raise HaritaApiHatasi(ZAMAN_ASIMI) from None
        except urllib.error.URLError as hata:
            if isinstance(hata.reason, TimeoutError):
                raise HaritaApiHatasi(ZAMAN_ASIMI) from None
            raise HaritaApiHatasi(BAGLANTI, str(hata.reason)[:120]) from None
        except OSError as hata:
            raise HaritaApiHatasi(BAGLANTI, type(hata).__name__) from None

        if kod == 200:
            return yaniti_ayristir(yanit)
        ayrinti = _hata_ayrintisi(yanit)
        if kod in (401, 403):
            self._anahtar_reddedildi = True
            raise HaritaApiHatasi(ANAHTAR_GECERSIZ, ayrinti, kod)
        if kod == 429:
            self._bekle_bitis = self._saat() + 60
            raise HaritaApiHatasi(HIZ_SINIRI, ayrinti, kod)
        if kod == 404:
            raise HaritaApiHatasi(ROTA_YOK, ayrinti, kod)
        raise HaritaApiHatasi(SERVIS_HATASI, ayrinti, kod)
