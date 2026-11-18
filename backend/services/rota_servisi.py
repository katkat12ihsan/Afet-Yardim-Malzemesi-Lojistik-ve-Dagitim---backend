"""İş katmanı - Rota / Dağıtım Planı: harita/rota API entegrasyonu (Hafta 9).

Bir dağıtımın deposundan ihtiyaç noktasına karayolu mesafesi, süresi ve rota çizgisi.

Akış (dagitim_rotasi):
  1. Yetki: "dagitim" modülü (Yönetici, Kurum). Depo ve noktanın koordinatı olmalı.
  2. Önbellek: aynı depo -> nokta rotası son ROTA_ONBELLEK_GUN gün içinde ve aynı
     koordinatlarla alınmışsa servise hiç gidilmez (hız sınırı, hız, internetsiz kullanım).
  3. Harita servisi (OpenRouteService): başarılıysa sonuç önbelleğe yazılır.
  4. Servis hata verirse (anahtar yok/geçersiz, zaman aşımı, bağlantı yok, hız sınırı,
     rota yok, bozuk yanıt) uygulama DURMAZ: kuş uçuşu mesafe x yol katsayısı ile
     TAHMİNİ rota döner ve ekranda neden tahmin gösterildiği yazılır.
     Tahmin önbelleğe yazılmaz: servis düzelince gerçek rota alınır.

Neden eşleştirme önerisi hâlâ kuş uçuşu kullanıyor?
  Öneri her talep seçiminde tüm depoları sıralar (depo sayısı kadar istek). Rota API'si
  yalnızca planlanan dağıtım için, yani gerçekten yola çıkacak araç için sorulur:
  istek sayısı hız sınırının çok altında kalır. Sıralama için kuş uçuşu yeterli.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional

from backend import config
from backend.data.database import islem
from backend.data.repositories import (
    DagitimRepository, DepoRepository, IhtiyacNoktasiRepository, RotaOnbellekRepository,
)
from backend.entegrasyon.harita_api import (
    ANAHTAR_YOK, HaritaApiHatasi, Koordinat, OrsIstemcisi,
)
from backend.models import Kullanici

from .eslestirme_servisi import MODUL_DAGITIM, mesafe_km
from .hatalar import DogrulamaHatasi
from .kimlik_servisi import KimlikServisi

_log = logging.getLogger(__name__)

# Kuş uçuşu tahmin: karayolu kuş uçuşu çizgiden her zaman uzundur; dağlık arazi için
# yaklaşık %30 fazlası kaba bir varsayımdır (gerçek değer rota servisinden gelir).
YOL_KATSAYISI = 1.3
ORTALAMA_HIZ_KMSA = 50.0

KAYNAK_SERVIS = "Harita servisi"
KAYNAK_ONBELLEK = "Harita servisi (önbellek)"
KAYNAK_TAHMIN = "Tahmini (kuş uçuşu × 1,3)"


@dataclass(frozen=True)
class RotaBilgisi:
    dagitim_id: int
    depo: str
    nokta: str
    baslangic: Koordinat
    bitis: Koordinat
    mesafe_km: float
    sure_dk: float
    kaynak: str
    uyari: str = ""                                 # tahmin gösteriliyorsa nedeni
    geometri: tuple[Koordinat, ...] = field(default=(), repr=False)

    @property
    def tahmini(self) -> bool:
        return self.kaynak == KAYNAK_TAHMIN


@dataclass(frozen=True)
class RotaSatiri:
    """Rota sayfasındaki liste satırı (API'ye gidilmez; yalnızca önbellek)."""
    dagitim_id: int
    durum: str
    depo: str
    nokta: str
    kalemler: str
    planlanan_tarih: str
    arac_plaka: str
    mesafe_km: Optional[float]                      # önbellekte yoksa None
    sure_dk: Optional[float]


def sure_yaz(dakika: Optional[float]) -> str:
    """75 -> '1 sa 15 dk', 40 -> '40 dk'."""
    if dakika is None:
        return "-"
    toplam = int(round(dakika))
    saat, dk = divmod(toplam, 60)
    return f"{saat} sa {dk} dk" if saat else f"{dk} dk"


def tahmini_rota(baslangic: Koordinat, bitis: Koordinat) -> tuple[float, float]:
    """(mesafe_km, sure_dk): kuş uçuşu x YOL_KATSAYISI, ORTALAMA_HIZ_KMSA ile süre."""
    kus = mesafe_km(baslangic[0], baslangic[1], bitis[0], bitis[1]) or 0.0
    yol = round(kus * YOL_KATSAYISI, 1)
    return yol, round(yol / ORTALAMA_HIZ_KMSA * 60, 1)


def _koordinat_anahtari(a: Koordinat, b: Koordinat) -> str:
    return f"{a[0]:.5f},{a[1]:.5f};{b[0]:.5f},{b[1]:.5f}"


class RotaServisi:
    def __init__(self, baglanti: sqlite3.Connection, kimlik: KimlikServisi,
                 istemci: Optional[OrsIstemcisi] = None,
                 saat: Callable[[], datetime] = lambda: datetime.now().replace(microsecond=0)) -> None:
        self._baglanti = baglanti
        self._kimlik = kimlik
        self._istemci = istemci or OrsIstemcisi(
            config.HARITA_API_ANAHTARI, config.HARITA_ZAMAN_ASIMI_SN, config.HARITA_DAKIKALIK_ISTEK)
        self._saat = saat
        self._onbellek = RotaOnbellekRepository(baglanti)

    def _yetki(self, token: str) -> Kullanici:
        return self._kimlik.modul_erisimi(token, MODUL_DAGITIM)

    # -------------------------------------------------------------- bilgi
    def servis_durumu(self) -> str:
        """Ekranın üstünde gösterilen tek satır (anahtarın kendisi hiçbir zaman gösterilmez)."""
        if self._istemci.anahtar_var:
            return "Rota servisi: OpenRouteService (API anahtarı tanımlı)"
        return ("Rota servisi: API anahtarı tanımlı değil. Mesafeler kuş uçuşu tahminidir "
                f"(anahtar: HARITA_API_ANAHTARI ortam değişkeni ya da {config.ENV_DOSYASI}).")

    def rota_listesi(self, token: str) -> list[RotaSatiri]:
        """Dağıtımlar + önbellekteki mesafe/süre. Servise istek GÖNDERMEZ (liste hızlı açılsın)."""
        self._yetki(token)
        onbellek = self._onbellek.tumu()
        satirlar = []
        for d in DagitimRepository(self._baglanti).liste():
            o = onbellek.get((d["depo_id"], d["ihtiyac_noktasi_id"]))
            satirlar.append(RotaSatiri(
                d["id"], d["durum"], d["depo"], d["nokta"], (d["kalemler"] or "").replace(".0 ", " "),
                d["planlanan_tarih"], d["arac_plaka"] or "",
                o["mesafe_km"] if o else None, o["sure_dk"] if o else None))
        return satirlar

    # --------------------------------------------------------------- rota
    def dagitim_rotasi(self, token: str, dagitim_id: int, yeniden_sor: bool = False) -> RotaBilgisi:
        """Dağıtımın deposundan ihtiyaç noktasına rota. Servis hatasında tahmini rota döner.

        yeniden_sor=True: önbellek atlanır, servise yeniden sorulur ("Yeniden Hesapla").
        """
        self._yetki(token)
        dagitim = DagitimRepository(self._baglanti).getir(dagitim_id)
        if dagitim is None:
            raise DogrulamaHatasi("Dağıtım bulunamadı.")
        depo = DepoRepository(self._baglanti).getir(dagitim.depo_id)
        nokta = IhtiyacNoktasiRepository(self._baglanti).getir(dagitim.ihtiyac_noktasi_id)
        if None in (depo.enlem, depo.boylam, nokta.enlem, nokta.boylam):
            raise DogrulamaHatasi(f"{depo.ad} ya da {nokta.ad} için koordinat girilmemiş; rota hesaplanamaz.")
        bas, bit = (depo.enlem, depo.boylam), (nokta.enlem, nokta.boylam)
        anahtar = _koordinat_anahtari(bas, bit)
        temel = dict(dagitim_id=dagitim.id, depo=depo.ad, nokta=nokta.ad, baslangic=bas, bitis=bit)

        # 2) önbellek
        kayit = self._onbellek.getir(depo.id, nokta.id)
        if (not yeniden_sor and kayit and kayit["koordinatlar"] == anahtar
                and datetime.fromisoformat(kayit["tarih"]) > self._saat() - timedelta(days=config.ROTA_ONBELLEK_GUN)):
            geometri = tuple((float(e), float(b)) for e, b in json.loads(kayit["geometri"]))
            return RotaBilgisi(**temel, mesafe_km=kayit["mesafe_km"], sure_dk=kayit["sure_dk"],
                               kaynak=KAYNAK_ONBELLEK, geometri=geometri)

        # 3) harita servisi
        try:
            rota = self._istemci.rota(bas, bit)
        except HaritaApiHatasi as hata:
            # 4) geri dönüş: uygulama çalışmaya devam eder, kullanıcı nedenini görür
            if hata.tur != ANAHTAR_YOK:
                _log.warning("Rota alınamadı (dağıtım #%s): %s %s", dagitim.id, hata.tur, hata.ayrinti)
            km, dk = tahmini_rota(bas, bit)
            return RotaBilgisi(**temel, mesafe_km=km, sure_dk=dk, kaynak=KAYNAK_TAHMIN,
                               uyari=f"{hata} Kuş uçuşu tahmin gösteriliyor.", geometri=(bas, bit))

        with islem(self._baglanti):
            self._onbellek.kaydet(depo.id, nokta.id, anahtar, rota.mesafe_km, rota.sure_dk,
                                  json.dumps([list(n) for n in rota.geometri]), self._saat().isoformat())
        return RotaBilgisi(**temel, mesafe_km=rota.mesafe_km, sure_dk=rota.sure_dk,
                           kaynak=KAYNAK_SERVIS, geometri=rota.geometri)
