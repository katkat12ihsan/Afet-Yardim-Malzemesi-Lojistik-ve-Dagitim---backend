"""İş katmanı - İhtiyaç Eşleştirme ve dağıtım durumu (Hafta 7, Çekirdek Modül B - 2. kısım).

Kavramlar:
  karşılanan  = iptal edilmemiş dağıtımlarda bu talebe bağlı kalemlerin toplamı
  kalan       = talep miktarı - karşılanan
  rezerve     = bir depodan planlanmış ama henüz yola çıkmamış miktar
  uygun stok  = depodaki stok - rezerve   (aynı malzeme iki talebe birden verilmesin)

Eşleştirme önerisi: Talebin kalanı için uygun stoğu olan depolar, ihtiyaç noktasına
EN YAKIN olandan başlanarak (koordinatlardan kuş uçuşu km) sırayla kullanılır.
Hafta 9'da gerçek yol mesafesi (rota API), Hafta 10'da yapay zekâ önceliği eklenecek.

Dağıtım yaşam döngüsü (durum güncelleme):
  Planlandı --yola çık--> Yolda --teslim et--> Teslim edildi
      |                     |
      +----- iptal ---------+--> İptal   (Yolda'dan iptalde malzeme depoya iade girer)
  Stok depodan "Yolda" olunca düşer (Envanter'in Çıkış yolu, K1 kontrolüyle).

İş kuralları (tests/test_eslestirme.py):
  E1  Kapalı (Karşılandı/İptal) talebe eşleştirme yapılamaz.
  E2  Fazla gönderim yok: atamaların toplamı talebin kalanını aşamaz.
  E3  Bir depodan atanan miktar o deponun uygun stoğunu (stok - rezerve) aşamaz.
  E4  Miktar envanter kurallarına uyar (birime göre tam sayı, > 0).
  E5  Aynı ihtiyaç noktası aynı malzeme için ikinci açık talep açamaz (çifte sayım olmasın).
  E6  Dağıtımı (planlanmış ya da yolda) olan talep iptal edilemez; önce dağıtım iptal edilir.
  E7  Dağıtım durumları yalnızca yukarıdaki geçişlerle değişir.
  E8  Talep durumu her değişiklikte dağıtımlardan yeniden hesaplanır
      (0 -> Bekliyor, kısmi -> Kısmen karşılandı, tamamı -> Karşılandı).
  E9  Her işlem (dağıtım + kalemler + stok hareketi + talep durumu) tek transaction.
"""

import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from backend.data.database import islem
from backend.data.repositories import (
    DagitimKalemiRepository, DagitimRepository, DepoRepository, IhtiyacNoktasiRepository,
    IhtiyacTalebiRepository, MalzemeRepository, StokRepository,
)
from backend.models import (
    Dagitim, DagitimDurumu, DagitimKalemi, HareketTuru, IhtiyacNoktasi, IhtiyacTalebi,
    Kullanici, Malzeme, TalepDurumu,
)

from .envanter_servisi import TAMSAYI_BIRIMLER, EnvanterServisi, Sayi, tr_sirala
from .hatalar import DogrulamaHatasi
from .kimlik_servisi import KimlikServisi

MODUL_IHTIYAC, MODUL_DAGITIM = "ihtiyac", "dagitim"
ACIK_DURUMLAR = (TalepDurumu.BEKLIYOR, TalepDurumu.KISMEN_KARSILANDI)
GECISLER = {   # E7
    DagitimDurumu.PLANLANDI: {DagitimDurumu.YOLDA, DagitimDurumu.IPTAL},
    DagitimDurumu.YOLDA: {DagitimDurumu.TESLIM_EDILDI, DagitimDurumu.IPTAL},
    DagitimDurumu.TESLIM_EDILDI: set(),
    DagitimDurumu.IPTAL: set(),
}


def mesafe_km(enlem1, boylam1, enlem2, boylam2) -> Optional[float]:
    """İki koordinat arası kuş uçuşu mesafe (Haversine). Koordinat yoksa None."""
    if None in (enlem1, boylam1, enlem2, boylam2):
        return None
    r = 6371.0
    f1, f2 = math.radians(enlem1), math.radians(enlem2)
    df, dl = math.radians(enlem2 - enlem1), math.radians(boylam2 - boylam1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 1)


def talep_durumu(miktar: float, karsilanan: float) -> TalepDurumu:
    """E8: talep durumu karşılanan miktardan türetilir."""
    if karsilanan <= 0:
        return TalepDurumu.BEKLIYOR
    if karsilanan < miktar:
        return TalepDurumu.KISMEN_KARSILANDI
    return TalepDurumu.KARSILANDI


@dataclass(frozen=True)
class TalepBilgisi:
    id: int
    nokta_id: int
    nokta: str
    oncelik: int
    malzeme_id: int
    malzeme: str
    birim: str
    miktar: float
    karsilanan: float
    durum: str
    talep_tarihi: str

    @property
    def kalan(self) -> float:
        return max(round(self.miktar - self.karsilanan, 3), 0)


@dataclass(frozen=True)
class OneriSatiri:
    depo_id: int
    depo: str
    uygun_stok: float
    mesafe_km: Optional[float]
    miktar: float                       # bu depodan önerilen miktar


@dataclass(frozen=True)
class EslestirmeOnerisi:
    talep: TalepBilgisi
    satirlar: list[OneriSatiri]         # yalnızca miktar > 0 olanlar; en yakın önce
    adaylar: list[OneriSatiri]          # uygun stoğu olan tüm depolar (bilgi için)

    @property
    def karsilanamayan(self) -> float:
        """Eksik: tüm depoların uygun stoğu yetmiyorsa açıkta kalan miktar."""
        return max(round(self.talep.kalan - sum(s.miktar for s in self.satirlar), 3), 0)


@dataclass(frozen=True)
class DengeSatiri:
    malzeme_id: int
    malzeme: str
    birim: str
    uygun_stok: float
    acik_talep: float

    @property
    def fark(self) -> float:
        return round(self.uygun_stok - self.acik_talep, 3)

    @property
    def durum(self) -> str:
        if self.fark < 0:
            return "Eksik"
        if self.fark > 0 and self.acik_talep == 0:
            return "Talep yok"
        return "Fazla" if self.fark > 0 else "Dengede"


class EslestirmeServisi:
    def __init__(self, baglanti: sqlite3.Connection, kimlik: KimlikServisi,
                 envanter: EnvanterServisi) -> None:
        self._baglanti = baglanti
        self._kimlik = kimlik
        self._envanter = envanter
        self._talepler = IhtiyacTalebiRepository(baglanti)
        self._dagitimlar = DagitimRepository(baglanti)
        self._dkalemler = DagitimKalemiRepository(baglanti)
        self._depolar = DepoRepository(baglanti)
        self._noktalar = IhtiyacNoktasiRepository(baglanti)

    def _yetki(self, token: str, modul: str = MODUL_IHTIYAC) -> Kullanici:
        return self._kimlik.modul_erisimi(token, modul)

    # ============================================================ okuma
    def ihtiyac_noktalari(self, token: str) -> list[IhtiyacNoktasi]:
        self._yetki(token)
        return self._noktalar.listele()                 # öncelik sırasıyla

    def malzemeler(self, token: str) -> list[Malzeme]:
        self._yetki(token)
        return sorted(MalzemeRepository(self._baglanti).listele(), key=lambda m: tr_sirala(m.ad))

    @staticmethod
    def _bilgi(s: sqlite3.Row) -> TalepBilgisi:
        return TalepBilgisi(s["id"], s["ihtiyac_noktasi_id"], s["nokta"], s["oncelik"], s["malzeme_id"],
                            s["malzeme"], s["birim"], s["miktar"], s["karsilanan"], s["durum"],
                            s["talep_tarihi"])

    def talepler(self, token: str, sadece_acik: bool = True) -> list[TalepBilgisi]:
        self._yetki(token)
        return [self._bilgi(s) for s in self._talepler.durum_listesi(sadece_acik)]

    def _talep_bilgisi(self, talep_id: int) -> TalepBilgisi:
        bilgi = next((t for t in map(self._bilgi, self._talepler.durum_listesi(False)) if t.id == talep_id), None)
        if bilgi is None:
            raise DogrulamaHatasi("Talep bulunamadı.")
        return bilgi

    def uygun_stok(self, depo_id: int, malzeme_id: int) -> float:
        stok = StokRepository(self._baglanti).getir(depo_id, malzeme_id)
        return max(round((stok.miktar if stok else 0) - self._dkalemler.rezerve(depo_id, malzeme_id), 3), 0)

    def oneri(self, token: str, talep_id: int) -> EslestirmeOnerisi:
        """Kalan miktar için en yakın depodan başlayarak öneri (fazla gönderim yok)."""
        self._yetki(token)
        talep = self._talep_bilgisi(talep_id)
        nokta = self._noktalar.getir(talep.nokta_id)
        malzeme = self._envanter.malzeme_getir(talep.malzeme_id)
        adaylar = []
        for depo in self._depolar.listele():
            uygun = self.uygun_stok(depo.id, talep.malzeme_id)
            if uygun > 0:
                adaylar.append((depo, uygun, mesafe_km(depo.enlem, depo.boylam, nokta.enlem, nokta.boylam)))
        adaylar.sort(key=lambda a: (a[2] is None, a[2] or 0))    # en yakın önce, koordinatsız en sona

        acik = talep.durum in [d.value for d in ACIK_DURUMLAR]
        kalan = talep.kalan if acik else 0             # kapalı talebe öneri yapılmaz
        satirlar, tum = [], []
        for depo, uygun, km in adaylar:
            miktar = min(uygun, kalan)
            if malzeme.birim in TAMSAYI_BIRIMLER:          # 2,5 battaniye önerilmez
                miktar = math.floor(miktar)
            satir = OneriSatiri(depo.id, depo.ad, uygun, km, miktar)
            tum.append(satir)
            if miktar > 0:
                satirlar.append(satir)
                kalan = round(kalan - miktar, 3)
        return EslestirmeOnerisi(talep, satirlar, tum)

    def stok_talep_dengesi(self, token: str) -> list[DengeSatiri]:
        """Fazla/eksik görünümü: her malzeme için toplam uygun stok ile açık taleplerin kalanı."""
        self._yetki(token)
        acik = {}
        for t in self.talepler(token, sadece_acik=True):
            acik[t.malzeme_id] = acik.get(t.malzeme_id, 0) + t.kalan
        satirlar = []
        for m in MalzemeRepository(self._baglanti).listele():
            uygun = sum(self.uygun_stok(d.id, m.id) for d in self._depolar.listele())
            if uygun or acik.get(m.id):
                satirlar.append(DengeSatiri(m.id, m.ad, m.birim, round(uygun, 3), round(acik.get(m.id, 0), 3)))
        return sorted(satirlar, key=lambda s: (s.fark, tr_sirala(s.malzeme)))     # en eksik önce

    def dagitim_listesi(self, token: str) -> list[sqlite3.Row]:
        self._yetki(token, MODUL_DAGITIM)
        return self._dagitimlar.liste()

    # ========================================================= yardımcı
    def _talep_durumunu_guncelle(self, talep_id: int) -> None:     # E8 (transaction içinde)
        talep = self._talepler.getir(talep_id)
        if talep is None or talep.durum is TalepDurumu.IPTAL:
            return
        yeni = talep_durumu(talep.miktar, self._talepler.karsilanan(talep_id))
        if yeni is not talep.durum:
            talep.durum = yeni
            self._talepler.guncelle(talep)

    @staticmethod
    def _plaka(plaka: str) -> str:
        plaka = " ".join(plaka.upper().split())
        if plaka and not re.fullmatch(r"\d{2} ?[A-ZÇĞİÖŞÜ]{1,3} ?\d{2,4}", plaka):
            raise DogrulamaHatasi("Araç plakası 12 ABC 123 biçiminde olmalı.")
        return plaka

    # ============================================================ yazma
    def talep_ekle(self, token: str, nokta_id: int, malzeme_id: int, miktar: Sayi) -> IhtiyacTalebi:
        self._yetki(token)
        if self._noktalar.getir(nokta_id) is None:
            raise DogrulamaHatasi("İhtiyaç noktası bulunamadı.")
        malzeme = self._envanter.malzeme_getir(malzeme_id)
        miktar = self._envanter.miktari_dogrula(miktar, malzeme)                     # E4
        for t in self.talepler(token, sadece_acik=True):                              # E5
            if t.nokta_id == nokta_id and t.malzeme_id == malzeme_id:
                raise DogrulamaHatasi(f"Bu noktanın {malzeme.ad} için açık bir talebi zaten var "
                                      f"(#{t.id}, kalan {t.kalan:g} {t.birim}).")
        with islem(self._baglanti):
            return self._talepler.ekle(IhtiyacTalebi(nokta_id, malzeme_id, miktar,
                                                     datetime.now().replace(microsecond=0)))

    def talep_iptal(self, token: str, talep_id: int) -> None:
        self._yetki(token)
        talep = self._talepler.getir(talep_id)
        if talep is None:
            raise DogrulamaHatasi("Talep bulunamadı.")
        if talep.durum is TalepDurumu.IPTAL:
            raise DogrulamaHatasi("Talep zaten iptal edilmiş.")
        if self._talepler.karsilanan(talep_id) > 0:                                   # E6
            raise DogrulamaHatasi("Bu talebe bağlı dağıtım var; önce dağıtımı iptal edin.")
        talep.durum = TalepDurumu.IPTAL
        with islem(self._baglanti):
            self._talepler.guncelle(talep)

    def eslestir(self, token: str, talep_id: int, atamalar: list[tuple[int, Sayi]],
                 arac_plaka: str = "", planlanan_tarih: Optional[datetime] = None) -> list[Dagitim]:
        """Talebi depolardan karşılayan dağıtım(lar)ı planlar: her depo için bir dağıtım."""
        self._yetki(token)
        talep = self._talep_bilgisi(talep_id)
        if talep.durum not in [d.value for d in ACIK_DURUMLAR]:                       # E1
            raise DogrulamaHatasi(f"Talep '{talep.durum}' durumunda; eşleştirme yapılamaz.")
        malzeme = self._envanter.malzeme_getir(talep.malzeme_id)
        plaka = self._plaka(arac_plaka)

        toplam, dogrulanan, depolar = 0.0, [], set()
        for depo_id, miktar in atamalar:
            depo = self._depolar.getir(depo_id)
            if depo is None:
                raise DogrulamaHatasi("Depo bulunamadı.")
            if depo_id in depolar:
                raise DogrulamaHatasi(f"{depo.ad} iki kez seçilmiş; miktarı tek satırda toplayın.")
            depolar.add(depo_id)
            miktar = self._envanter.miktari_dogrula(miktar, malzeme, f"{depo.ad} miktarı")   # E4
            uygun = self.uygun_stok(depo_id, malzeme.id)
            if miktar > uygun:                                                        # E3
                raise DogrulamaHatasi(f"{depo.ad}: uygun stok {uygun:g} {malzeme.birim} "
                                      f"(rezerve düşülmüş), {miktar:g} istendi.")
            toplam += miktar
            dogrulanan.append((depo, miktar))
        if not dogrulanan:
            raise DogrulamaHatasi("En az bir depodan miktar atayın.")
        if round(toplam, 3) > talep.kalan:                                            # E2
            raise DogrulamaHatasi(f"Fazla gönderim: talebin kalanı {talep.kalan:g} {malzeme.birim}, "
                                  f"toplam {toplam:g} atandı.")

        tarih = (planlanan_tarih or datetime.now()).replace(microsecond=0)
        olusan = []
        with islem(self._baglanti):                                                   # E9
            for depo, miktar in dogrulanan:
                dagitim = self._dagitimlar.ekle(Dagitim(depo.id, talep.nokta_id, tarih, arac_plaka=plaka))
                self._dkalemler.ekle(DagitimKalemi(dagitim.id, malzeme.id, miktar, talep.id))
                olusan.append(dagitim)
            self._talep_durumunu_guncelle(talep.id)
        return olusan

    def dagitim_durumu_degistir(self, token: str, dagitim_id: int, yeni: DagitimDurumu) -> Dagitim:
        kullanici = self._yetki(token, MODUL_DAGITIM)
        dagitim = self._dagitimlar.getir(dagitim_id)
        if dagitim is None:
            raise DogrulamaHatasi("Dağıtım bulunamadı.")
        if yeni not in GECISLER[dagitim.durum]:                                       # E7
            raise DogrulamaHatasi(f"'{dagitim.durum.value}' durumundaki dağıtım "
                                  f"'{yeni.value}' yapılamaz.")
        nokta = self._noktalar.getir(dagitim.ihtiyac_noktasi_id)
        kalemler = self._dkalemler.dagitimin_kalemleri(dagitim_id)
        eski = dagitim.durum
        with islem(self._baglanti):                                                   # E9
            for k in kalemler:
                malzeme = self._envanter.malzeme_getir(k.malzeme_id)
                if yeni is DagitimDurumu.YOLDA:            # stok depodan şimdi düşer (K1 ile)
                    self._envanter.stok_hareketi_uygula(kullanici, dagitim.depo_id, malzeme, HareketTuru.CIKIS,
                                                        -k.miktar, f"Dağıtım #{dagitim.id} -> {nokta.ad}")
                elif yeni is DagitimDurumu.IPTAL and eski is DagitimDurumu.YOLDA:   # yoldan dönen iade
                    self._envanter.stok_hareketi_uygula(kullanici, dagitim.depo_id, malzeme, HareketTuru.GIRIS,
                                                        k.miktar, f"Dağıtım #{dagitim.id} iptal - depoya iade")
            dagitim.durum = yeni
            if yeni is DagitimDurumu.TESLIM_EDILDI:
                dagitim.teslim_tarihi = datetime.now().replace(microsecond=0)
            self._dagitimlar.guncelle(dagitim)
            for talep_id in {k.ihtiyac_talebi_id for k in kalemler if k.ihtiyac_talebi_id}:
                self._talep_durumunu_guncelle(talep_id)                                # E8
        return dagitim
