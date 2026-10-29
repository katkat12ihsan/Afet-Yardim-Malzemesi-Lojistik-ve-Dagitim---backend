"""İş katmanı - Envanter Yönetimi (Hafta 6, Çekirdek Modül A).

Sorumluluklar:
  * Malzeme/kategori tanımları (yalnızca Yönetici)
  * Depoya giriş, depodan çıkış, sayım düzeltmesi, kritik seviye
  * Stok seviyesi ve kritik stok listesi

İş kuralları (her biri bir test ile doğrulanır, bkz. tests/test_envanter.py):
  K1  Stok hiçbir zaman eksiye düşemez (çıkış mevcut stoğu aşamaz).
  K2  adet/koli/paket birimli malzemede miktar tam sayı olmalı; kg/litre kesirli olabilir.
  K3  Tek harekette miktar 0'dan büyük ve en fazla MAKS_TEK_HAREKET olmalı.
  K4  Sayım düzeltmesinde açıklama zorunlu (neden fark oluştu?).
  K5  Depo görevlisi yalnızca kendi deposunun stoğunu görür/değiştirir (sahiplik).
  K6  Malzeme/kategori tanımlarını yalnızca Yönetici değiştirir (tutarlı katalog).
  K7  Stoğu veya geçmişi olan malzemenin birimi değiştirilemez ve malzeme silinemez.
  K8  Stok güncellemesi ve hareket kaydı tek transaction'dadır; ikisi birlikte yazılır
      ya da hiçbiri yazılmaz. Böylece "stok = hareketlerin toplamı" her zaman doğrudur.
"""

import sqlite3
from dataclasses import dataclass
from typing import Optional, Union

from backend.data.database import islem
from backend.data.repositories import (
    DepoRepository, KategoriRepository, MalzemeRepository, StokHareketiRepository,
    StokRepository,
)
from backend.models import (
    Depo, HareketTuru, Kategori, Kullanici, Malzeme, Rol, Stok, StokHareketi,
)

from .hatalar import DogrulamaHatasi, YetkisizErisim
from .kimlik_servisi import KimlikServisi

GECERLI_BIRIMLER = ("adet", "koli", "paket", "kg", "litre")
TAMSAYI_BIRIMLER = frozenset({"adet", "koli", "paket"})
MAKS_TEK_HAREKET = 100_000
MODUL = "envanter"

Sayi = Union[int, float, str]


def tr_kucuk(metin: str) -> str:
    """Türkçe'ye uygun küçük harf: Python'un lower() fonksiyonu 'I' -> 'i' yapar,
    oysa Türkçede 'I' -> 'ı' ve 'İ' -> 'i' olmalı. Aksi halde 'GIDA' ile 'Gıda'
    farklı sayılır ve aynı kategori iki kez eklenebilirdi."""
    return metin.replace("I", "ı").replace("İ", "i").lower()


_TR_ALFABE = "0123456789aâbcçdefgğhıiîjklmnoöprsştuüûvyz"
_TR_SIRA = {harf: sira for sira, harf in enumerate(_TR_ALFABE)}


def tr_sirala(metin: str) -> tuple:
    """Türkçe alfabe sırası anahtarı: SQLite ve Python varsayılan olarak Ç, İ, Ö, Ş, Ü'yü
    Z'den sonraya koyar ('Çadır' listenin sonuna düşer). Bu anahtar doğru sıralar."""
    return tuple(_TR_SIRA.get(harf, 100 + ord(harf)) for harf in tr_kucuk(metin))


@dataclass(frozen=True)
class StokSatiri:
    malzeme_id: int
    malzeme: str
    kategori_id: int
    kategori: str
    birim: str
    miktar: float
    kritik_seviye: float

    @property
    def durum(self) -> str:
        if self.miktar == 0:
            return "Tükendi"
        if self.miktar < self.kritik_seviye:
            return "Kritik"
        return "Normal"


class EnvanterServisi:
    def __init__(self, baglanti: sqlite3.Connection, kimlik: KimlikServisi) -> None:
        self._baglanti = baglanti
        self._kimlik = kimlik
        self._depolar = DepoRepository(baglanti)
        self._kategoriler = KategoriRepository(baglanti)
        self._malzemeler = MalzemeRepository(baglanti)
        self._stoklar = StokRepository(baglanti)
        self._hareketler = StokHareketiRepository(baglanti)

    # ===================================================== erişim kontrolü
    def _kullanici(self, token: str) -> Kullanici:
        """Oturum geçerli mi + rol envanter modülüne yetkili mi? (Kurum rolü değil)"""
        return self._kimlik.modul_erisimi(token, MODUL)

    def _depo_kontrol(self, kullanici: Kullanici, depo_id: int) -> Depo:
        depo = self._depolar.getir(depo_id)
        if depo is None:
            raise DogrulamaHatasi("Depo bulunamadı.")
        if kullanici.rol is Rol.DEPO and kullanici.depo_id != depo_id:      # K5
            raise YetkisizErisim("Yalnızca kendi deponuzun stoğunu görebilir ve değiştirebilirsiniz.")
        return depo

    @staticmethod
    def _tanim_yetkisi(kullanici: Kullanici) -> None:
        if kullanici.rol is not Rol.YONETICI:                                # K6
            raise YetkisizErisim("Malzeme ve kategori tanımlarını yalnızca Yönetici değiştirebilir.")

    def _malzeme(self, malzeme_id: int) -> Malzeme:
        malzeme = self._malzemeler.getir(malzeme_id)
        if malzeme is None:
            raise DogrulamaHatasi("Malzeme bulunamadı.")
        return malzeme

    # ========================================================= doğrulama
    @staticmethod
    def _sayi(deger: Sayi, alan: str) -> float:
        """Arayüzden gelen '12,5' gibi metinleri de kabul eder (Türkçe ondalık virgül)."""
        if isinstance(deger, str):
            deger = deger.strip().replace(",", ".")
            if not deger:
                raise DogrulamaHatasi(f"{alan} boş olamaz.")
        try:
            return round(float(deger), 3)
        except (TypeError, ValueError):
            raise DogrulamaHatasi(f"{alan} sayı olmalı.") from None

    def _miktar(self, deger: Sayi, malzeme: Malzeme, alan: str = "Miktar",
                sifir_olabilir: bool = False) -> float:
        miktar = self._sayi(deger, alan)
        if miktar < 0 or (miktar == 0 and not sifir_olabilir):                   # K3
            raise DogrulamaHatasi(f"{alan} 0'dan büyük olmalı." if not sifir_olabilir
                                  else f"{alan} negatif olamaz.")
        if miktar > MAKS_TEK_HAREKET:
            raise DogrulamaHatasi(f"{alan} en fazla {MAKS_TEK_HAREKET:,} olabilir.".replace(",", "."))
        if malzeme.birim in TAMSAYI_BIRIMLER and miktar != int(miktar):          # K2
            raise DogrulamaHatasi(f"'{malzeme.birim}' birimli malzemede {alan.lower()} tam sayı olmalı.")
        return miktar

    # ============================ diğer modüller için (Hafta 7: bağış, eşleştirme)
    # Aynı kurallar her modülde aynı kalsın diye doğrulama burada tek yerde durur.
    def malzeme_getir(self, malzeme_id: int) -> Malzeme:
        return self._malzeme(malzeme_id)

    def miktari_dogrula(self, deger: Sayi, malzeme: Malzeme, alan: str = "Miktar") -> float:
        """K2 (birime göre tam sayı) ve K3 (0 < miktar <= 100.000, virgüllü giriş)."""
        return self._miktar(deger, malzeme, alan)

    def depo_sahipligi(self, kullanici: Kullanici, depo_id: int) -> Depo:
        """K5: Depo görevlisi yalnızca kendi deposunda işlem yapar."""
        return self._depo_kontrol(kullanici, depo_id)

    # ============================================================ okuma
    def erisilebilir_depolar(self, token: str) -> list[Depo]:
        kullanici = self._kullanici(token)
        if kullanici.rol is Rol.DEPO:
            return [self._depolar.getir(kullanici.depo_id)]
        return self._depolar.listele()

    def kategoriler(self, token: str) -> list[Kategori]:
        self._kullanici(token)
        return sorted(self._kategoriler.listele(), key=lambda k: tr_sirala(k.ad))

    def malzemeler(self, token: str, kategori_id: Optional[int] = None) -> list[Malzeme]:
        self._kullanici(token)
        liste = (self._malzemeler.listele() if kategori_id is None
                 else self._malzemeler.kategoriye_gore(kategori_id))
        return sorted(liste, key=lambda m: tr_sirala(m.ad))

    def stok_listesi(self, token: str, depo_id: int, kategori_id: Optional[int] = None,
                     arama: str = "", sadece_kritik: bool = False) -> list[StokSatiri]:
        self._depo_kontrol(self._kullanici(token), depo_id)
        arama = tr_kucuk(arama.strip())
        satirlar = [StokSatiri(s["malzeme_id"], s["malzeme"], s["kategori_id"], s["kategori"],
                               s["birim"], s["miktar"], s["kritik_seviye"])
                    for s in self._stoklar.depo_envanteri(depo_id)]
        satirlar.sort(key=lambda s: (tr_sirala(s.kategori), tr_sirala(s.malzeme)))
        return [s for s in satirlar
                if (kategori_id is None or s.kategori_id == kategori_id)
                and (not arama or arama in tr_kucuk(s.malzeme))
                and (not sadece_kritik or s.durum != "Normal")]

    def hareket_gecmisi(self, token: str, depo_id: int, malzeme_id: Optional[int] = None,
                        limit: int = 100) -> list[sqlite3.Row]:
        self._depo_kontrol(self._kullanici(token), depo_id)
        return self._hareketler.gecmis(depo_id, malzeme_id, limit)

    def kritik_stoklar(self, token: str) -> list[sqlite3.Row]:
        kullanici = self._kullanici(token)
        satirlar = self._stoklar.kritik_stoklar()
        if kullanici.rol is Rol.DEPO:
            satirlar = [s for s in satirlar if s["depo_id"] == kullanici.depo_id]
        return satirlar

    # =========================================== tanımlar (Yönetici, K6)
    def kategori_ekle(self, token: str, ad: str) -> Kategori:
        self._tanim_yetkisi(self._kullanici(token))
        ad = " ".join(ad.split())
        if not 2 <= len(ad) <= 40:
            raise DogrulamaHatasi("Kategori adı 2-40 karakter olmalı.")
        if any(tr_kucuk(k.ad) == tr_kucuk(ad) for k in self._kategoriler.listele()):
            raise DogrulamaHatasi(f"'{ad}' kategorisi zaten var.")
        with islem(self._baglanti):
            return self._kategoriler.ekle(Kategori(ad))

    def kategori_sil(self, token: str, kategori_id: int) -> None:
        self._tanim_yetkisi(self._kullanici(token))
        if self._malzemeler.kategoriye_gore(kategori_id):
            raise DogrulamaHatasi("Bu kategoride malzeme var; önce malzemeleri taşıyın veya silin.")
        with islem(self._baglanti):
            if not self._kategoriler.sil(kategori_id):
                raise DogrulamaHatasi("Kategori bulunamadı.")

    def _malzeme_alanlari(self, kategori_id: int, ad: str, birim: str,
                          haric_id: Optional[int] = None) -> str:
        ad = " ".join(ad.split())
        if not 2 <= len(ad) <= 60:
            raise DogrulamaHatasi("Malzeme adı 2-60 karakter olmalı.")
        if self._kategoriler.getir(kategori_id) is None:
            raise DogrulamaHatasi("Geçerli bir kategori seçin.")
        if birim not in GECERLI_BIRIMLER:
            raise DogrulamaHatasi("Birim şunlardan biri olmalı: " + ", ".join(GECERLI_BIRIMLER))
        if any(tr_kucuk(m.ad) == tr_kucuk(ad) and m.id != haric_id
               for m in self._malzemeler.listele()):
            raise DogrulamaHatasi(f"'{ad}' adlı malzeme zaten var.")
        return ad

    def malzeme_ekle(self, token: str, kategori_id: int, ad: str, birim: str,
                     aciklama: str = "") -> Malzeme:
        self._tanim_yetkisi(self._kullanici(token))
        ad = self._malzeme_alanlari(kategori_id, ad, birim)
        with islem(self._baglanti):
            return self._malzemeler.ekle(Malzeme(kategori_id, ad, birim, aciklama.strip()))

    def _malzeme_kullanimda_mi(self, malzeme_id: int) -> bool:
        return self._baglanti.execute(
            "SELECT EXISTS(SELECT 1 FROM stok_hareketi WHERE malzeme_id = ?)"
            " OR EXISTS(SELECT 1 FROM stok WHERE malzeme_id = ? AND miktar > 0)",
            (malzeme_id, malzeme_id),
        ).fetchone()[0] == 1

    def malzeme_guncelle(self, token: str, malzeme_id: int, kategori_id: int, ad: str,
                         birim: str, aciklama: str = "") -> Malzeme:
        self._tanim_yetkisi(self._kullanici(token))
        malzeme = self._malzeme(malzeme_id)
        ad = self._malzeme_alanlari(kategori_id, ad, birim, haric_id=malzeme_id)
        if birim != malzeme.birim and self._malzeme_kullanimda_mi(malzeme_id):    # K7
            raise DogrulamaHatasi("Stoğu veya hareket geçmişi olan malzemenin birimi değiştirilemez; "
                                  "eski miktarların anlamı bozulur.")
        malzeme.kategori_id, malzeme.ad, malzeme.birim, malzeme.aciklama = (
            kategori_id, ad, birim, aciklama.strip())
        with islem(self._baglanti):
            self._malzemeler.guncelle(malzeme)
        return malzeme

    def malzeme_sil(self, token: str, malzeme_id: int) -> None:
        self._tanim_yetkisi(self._kullanici(token))
        self._malzeme(malzeme_id)
        if self._malzeme_kullanimda_mi(malzeme_id):                               # K7
            raise DogrulamaHatasi("Stoğu veya hareket geçmişi olan malzeme silinemez.")
        try:
            with islem(self._baglanti):
                self._baglanti.execute(
                    "DELETE FROM stok WHERE malzeme_id = ? AND miktar = 0", (malzeme_id,))
                self._malzemeler.sil(malzeme_id)
        except sqlite3.IntegrityError:
            # Bağış/talep/dağıtım kalemlerinde kullanılıyorsa veritabanı RESTRICT ile engeller
            raise DogrulamaHatasi("Malzeme bağış, talep veya dağıtım kayıtlarında kullanılıyor; "
                                  "silinemez.") from None

    # ============================================ stok hareketleri (K1-K5, K8)
    def _hareket_yaz(self, kullanici: Kullanici, depo_id: int, malzeme: Malzeme,
                     tur: HareketTuru, degisim: float, aciklama: str) -> StokHareketi:
        with islem(self._baglanti):                                               # K8
            return self.stok_hareketi_uygula(kullanici, depo_id, malzeme, tur, degisim, aciklama)

    def stok_hareketi_uygula(self, kullanici: Kullanici, depo_id: int, malzeme: Malzeme,
                             tur: HareketTuru, degisim: float, aciklama: str) -> StokHareketi:
        """Stok satırını günceller ve hareket kaydını yazar - transaction AÇMADAN.

        Hafta 7 entegrasyonu: Bağış ve Dağıtım modülleri stoğu kendi SQL'leriyle
        değiştirmez; bu metodu kendi transaction'larının içinden çağırır. Böylece
        stok her kaynaktan aynı kurallarla (K1: eksiye düşmez) ve aynı hareket
        kaydıyla değişir; bağışın tamamı ya da hiçbiri yazılır.
        Yetki ve miktar doğrulaması çağıran servisin sorumluluğundadır.
        """
        stok = self._stoklar.getir(depo_id, malzeme.id) or Stok(depo_id, malzeme.id, 0, 0)
        onceki = stok.miktar
        sonraki = round(onceki + degisim, 3)
        if sonraki < 0:                                                           # K1
            raise DogrulamaHatasi(
                f"Yetersiz stok: depoda {onceki:g} {malzeme.birim} {malzeme.ad} var, "
                f"{-degisim:g} {malzeme.birim} çıkış istendi.")
        stok.miktar = sonraki
        self._stoklar.kaydet(stok)
        return self._hareketler.ekle(StokHareketi(
            depo_id, malzeme.id, tur, degisim, onceki, sonraki, aciklama.strip(), kullanici.id))

    def stok_girisi(self, token: str, depo_id: int, malzeme_id: int, miktar: Sayi,
                    aciklama: str = "") -> StokHareketi:
        kullanici = self._kullanici(token)
        self._depo_kontrol(kullanici, depo_id)
        malzeme = self._malzeme(malzeme_id)
        return self._hareket_yaz(kullanici, depo_id, malzeme, HareketTuru.GIRIS,
                                 self._miktar(miktar, malzeme), aciklama)

    def stok_cikisi(self, token: str, depo_id: int, malzeme_id: int, miktar: Sayi,
                    aciklama: str = "") -> StokHareketi:
        kullanici = self._kullanici(token)
        self._depo_kontrol(kullanici, depo_id)
        malzeme = self._malzeme(malzeme_id)
        return self._hareket_yaz(kullanici, depo_id, malzeme, HareketTuru.CIKIS,
                                 -self._miktar(miktar, malzeme), aciklama)

    def sayim_duzeltmesi(self, token: str, depo_id: int, malzeme_id: int, sayilan: Sayi,
                         aciklama: str) -> StokHareketi:
        kullanici = self._kullanici(token)
        self._depo_kontrol(kullanici, depo_id)
        malzeme = self._malzeme(malzeme_id)
        sayilan_miktar = self._miktar(sayilan, malzeme, "Sayılan miktar", sifir_olabilir=True)
        if len(aciklama.strip()) < 5:                                             # K4
            raise DogrulamaHatasi("Sayım düzeltmesinde farkın nedenini açıklayın (en az 5 karakter).")
        mevcut = (self._stoklar.getir(depo_id, malzeme_id) or Stok(depo_id, malzeme_id, 0)).miktar
        fark = round(sayilan_miktar - mevcut, 3)
        if fark == 0:
            raise DogrulamaHatasi("Sayılan miktar sistemdeki miktarla aynı; düzeltme gerekmiyor.")
        return self._hareket_yaz(kullanici, depo_id, malzeme, HareketTuru.SAYIM, fark, aciklama)

    def kritik_seviye_ayarla(self, token: str, depo_id: int, malzeme_id: int,
                             seviye: Sayi) -> None:
        kullanici = self._kullanici(token)
        self._depo_kontrol(kullanici, depo_id)
        malzeme = self._malzeme(malzeme_id)
        seviye = self._miktar(seviye, malzeme, "Kritik seviye", sifir_olabilir=True)
        with islem(self._baglanti):
            stok = self._stoklar.getir(depo_id, malzeme_id) or Stok(depo_id, malzeme_id, 0, 0)
            stok.kritik_seviye = seviye
            self._stoklar.kaydet(stok)
