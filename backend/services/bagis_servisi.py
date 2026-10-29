"""İş katmanı - Bağış Girişi (Hafta 7, Çekirdek Modül B - 1. kısım).

Bir bağış = bağışçı + teslim alınan depo + bir veya daha çok kalem
(malzeme, miktar, son kullanma tarihi). Bağış kaydedilince her kalem
stoğa Envanter'in "Giriş" yoluyla girer (EnvanterServisi.stok_hareketi_uygula).
Bağış stoğu kendi SQL'iyle değiştirmez; böylece K1-K8 envanter kuralları ve
hareket geçmişi bağışlar için de aynen geçerlidir.

İş kuralları (tests/test_bagis.py):
  B1  Bağışta en az 1, en fazla 50 kalem olmalı.
  B2  Miktar envanter kurallarına uyar (birime göre tam sayı, 0 < miktar <= 100.000).
  B3  Aynı malzeme aynı son kullanma tarihiyle iki kez yazılamaz (tek satırda toplanmalı).
  B4  Son kullanma tarihi bağış tarihinden önce olamaz (süresi geçmiş ürün kabul edilmez);
      Gıda kategorisinde son kullanma tarihi zorunludur.
  B5  Depo görevlisi yalnızca kendi deposuna bağış girer (envanter K5).
  B6  Bağışçı: mevcut bir kayıt seçilir ya da yenisi eklenir (ad zorunlu; telefon ve
      e-posta isteğe bağlı ama girilirse biçimi doğru olmalı - KVKK: en az veri).
  B7  Bağış tarihi gelecekte olamaz.
  B8  Bağışçı (yeniyse) + bağış + kalemler + stok girişleri + hareketler TEK transaction.
"""

import re
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Union

from backend.data.database import islem
from backend.data.repositories import (
    BagisciRepository, BagisKalemiRepository, BagisRepository, DepoRepository,
    KategoriRepository, MalzemeRepository,
)
from backend.models import Bagis, Bagisci, BagisKalemi, Depo, HareketTuru, Kullanici, Malzeme, Rol

from .envanter_servisi import EnvanterServisi, Sayi, tr_kucuk, tr_sirala
from .hatalar import DogrulamaHatasi, YetkisizErisim
from .kimlik_servisi import KimlikServisi

MODUL = "bagis"
MAKS_KALEM = 50
BAGISCI_TURLERI = ("Bireysel", "Kurumsal")
Tarih = Union[date, str, None]


@dataclass(frozen=True)
class KalemGirdisi:
    """Arayüzden gelen bir bağış satırı (henüz doğrulanmamış)."""
    malzeme_id: int
    miktar: Sayi
    son_kullanma: Tarih = None


def tarih_cevir(deger: Tarih, alan: str = "Son kullanma tarihi") -> Optional[date]:
    """'2027-06-30', '30.06.2027' ya da date nesnesini kabul eder; boşsa None."""
    if deger is None or isinstance(deger, date):
        return deger
    deger = deger.strip()
    if not deger:
        return None
    for bicim in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(deger, bicim).date()
        except ValueError:
            pass
    raise DogrulamaHatasi(f"{alan} GG.AA.YYYY biçiminde olmalı (ör. 30.06.2027).")


class BagisServisi:
    def __init__(self, baglanti: sqlite3.Connection, kimlik: KimlikServisi,
                 envanter: EnvanterServisi) -> None:
        self._baglanti = baglanti
        self._kimlik = kimlik
        self._envanter = envanter
        self._bagiscilar = BagisciRepository(baglanti)
        self._bagislar = BagisRepository(baglanti)
        self._kalemler = BagisKalemiRepository(baglanti)

    def _kullanici(self, token: str) -> Kullanici:
        return self._kimlik.modul_erisimi(token, MODUL)

    # ============================================================ okuma
    def depolar(self, token: str) -> list[Depo]:
        kullanici = self._kullanici(token)
        if kullanici.rol is Rol.DEPO:
            return [DepoRepository(self._baglanti).getir(kullanici.depo_id)]
        return sorted(DepoRepository(self._baglanti).listele(), key=lambda d: tr_sirala(d.ad))

    def bagiscilar(self, token: str) -> list[Bagisci]:
        self._kullanici(token)
        return sorted(self._bagiscilar.listele(), key=lambda b: tr_sirala(b.ad))

    def malzemeler(self, token: str) -> list[Malzeme]:
        self._kullanici(token)
        return sorted(MalzemeRepository(self._baglanti).listele(), key=lambda m: tr_sirala(m.ad))

    def bagis_listesi(self, token: str, limit: int = 200) -> list[sqlite3.Row]:
        kullanici = self._kullanici(token)
        return self._bagislar.liste(kullanici.depo_id if kullanici.rol is Rol.DEPO else None, limit)

    def bagis_detayi(self, token: str, bagis_id: int) -> list[sqlite3.Row]:
        kullanici = self._kullanici(token)
        bagis = self._bagislar.getir(bagis_id)
        if bagis is None:
            raise DogrulamaHatasi("Bağış bulunamadı.")
        if kullanici.rol is Rol.DEPO and bagis.depo_id != kullanici.depo_id:            # B5
            raise YetkisizErisim("Yalnızca kendi deponuzun bağışlarını görebilirsiniz.")
        return self._kalemler.detay(bagis_id)

    # ========================================================= doğrulama
    @staticmethod
    def _bagisci_dogrula(ad: str, tur: str, telefon: str, eposta: str) -> Bagisci:  # B6
        ad = " ".join(ad.split())
        if not 2 <= len(ad) <= 80:
            raise DogrulamaHatasi("Bağışçı adı 2-80 karakter olmalı.")
        if tur not in BAGISCI_TURLERI:
            raise DogrulamaHatasi("Bağışçı türü Bireysel ya da Kurumsal olmalı.")
        telefon = telefon.strip()
        if telefon and not re.fullmatch(r"\+?[0-9 ]{10,16}", telefon):
            raise DogrulamaHatasi("Telefon yalnızca rakam ve boşluk içermeli (ör. 0555 000 00 00).")
        eposta = eposta.strip()
        if eposta and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", eposta):
            raise DogrulamaHatasi("E-posta adresi geçerli değil.")
        return Bagisci(ad, tur, telefon, eposta)

    def _kalemleri_dogrula(self, kalemler: list[KalemGirdisi],
                           bagis_tarihi: date) -> list[tuple[Malzeme, float, Optional[date]]]:
        if not kalemler:                                                                 # B1
            raise DogrulamaHatasi("Bağışa en az bir kalem ekleyin.")
        if len(kalemler) > MAKS_KALEM:
            raise DogrulamaHatasi(f"Bir bağışta en fazla {MAKS_KALEM} kalem olabilir.")
        kategoriler = {k.id: k.ad for k in KategoriRepository(self._baglanti).listele()}
        dogrulanan, gorulen = [], set()
        for sira, kalem in enumerate(kalemler, start=1):
            malzeme = self._envanter.malzeme_getir(kalem.malzeme_id)
            etiket = f"{sira}. kalem ({malzeme.ad})"
            miktar = self._envanter.miktari_dogrula(kalem.miktar, malzeme, f"{etiket} miktarı")  # B2
            skt = tarih_cevir(kalem.son_kullanma, f"{etiket} son kullanma tarihi")
            if skt is not None and skt < bagis_tarihi:                                    # B4
                raise DogrulamaHatasi(f"{etiket}: son kullanma tarihi geçmiş ({skt:%d.%m.%Y}); "
                                      "süresi geçmiş ürün kabul edilemez.")
            if skt is None and tr_kucuk(kategoriler.get(malzeme.kategori_id, "")) == "gıda":
                raise DogrulamaHatasi(f"{etiket}: gıda ürünlerinde son kullanma tarihi zorunlu.")
            anahtar = (malzeme.id, skt)
            if anahtar in gorulen:                                                        # B3
                raise DogrulamaHatasi(f"{etiket}: aynı malzeme aynı son kullanma tarihiyle iki kez "
                                      "yazılmış; miktarları tek satırda toplayın.")
            gorulen.add(anahtar)
            dogrulanan.append((malzeme, miktar, skt))
        return dogrulanan

    # ============================================================ yazma
    def bagis_kaydet(self, token: str, depo_id: int, kalemler: list[KalemGirdisi],
                     bagisci_id: Optional[int] = None, yeni_bagisci: Optional[dict] = None,
                     aciklama: str = "", tarih: Optional[datetime] = None) -> Bagis:
        """Bağışı kaydeder ve kalemleri stoğa ekler. Hepsi ya da hiçbiri (B8)."""
        kullanici = self._kullanici(token)
        depo = self._envanter.depo_sahipligi(kullanici, depo_id)                          # B5
        tarih = (tarih or datetime.now()).replace(microsecond=0)
        if tarih > datetime.now():                                                        # B7
            raise DogrulamaHatasi("Bağış tarihi gelecekte olamaz.")

        if bagisci_id is not None:                                                        # B6
            bagisci = self._bagiscilar.getir(bagisci_id)
            if bagisci is None:
                raise DogrulamaHatasi("Bağışçı bulunamadı.")
        elif yeni_bagisci:
            bagisci = self._bagisci_dogrula(yeni_bagisci.get("ad", ""), yeni_bagisci.get("tur", "Bireysel"),
                                            yeni_bagisci.get("telefon", ""), yeni_bagisci.get("eposta", ""))
            if any(tr_kucuk(b.ad) == tr_kucuk(bagisci.ad) for b in self._bagiscilar.listele()):
                raise DogrulamaHatasi(f"'{bagisci.ad}' adlı bağışçı zaten kayıtlı; listeden seçin.")
        else:
            raise DogrulamaHatasi("Bir bağışçı seçin ya da yeni bağışçı bilgilerini girin.")

        dogrulanan = self._kalemleri_dogrula(kalemler, tarih.date())

        with islem(self._baglanti):                                                       # B8
            if bagisci.id is None:
                self._bagiscilar.ekle(bagisci)
            bagis = self._bagislar.ekle(Bagis(bagisci.id, depo.id, tarih, aciklama.strip()))
            for malzeme, miktar, skt in dogrulanan:
                self._kalemler.ekle(BagisKalemi(bagis.id, malzeme.id, miktar, skt))
                self._envanter.stok_hareketi_uygula(
                    kullanici, depo.id, malzeme, HareketTuru.GIRIS, miktar,
                    f"Bağış #{bagis.id} - {bagisci.ad}")
        return bagis
