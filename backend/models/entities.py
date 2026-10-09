"""Varlık (entity) katmanı.

ER diyagramındaki (docs/ER-Diyagrami.md) her tablo burada bir dataclass ile
temsil edilir. Bu sınıflar hiçbir katmana bağımlı değildir; veri erişim,
iş ve arayüz katmanları bu sınıfları ortak "dil" olarak kullanır.

Not: id alanları veritabanına kaydedilene kadar None kalır (Hafta 4).
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Durum / seviye sabitleri
# ---------------------------------------------------------------------------

class OncelikSeviyesi(Enum):
    DUSUK = 1
    ORTA = 2
    YUKSEK = 3
    KRITIK = 4


class TalepDurumu(Enum):
    BEKLIYOR = "Bekliyor"
    KISMEN_KARSILANDI = "Kısmen karşılandı"
    KARSILANDI = "Karşılandı"
    IPTAL = "İptal"


class DagitimDurumu(Enum):
    PLANLANDI = "Planlandı"
    YOLDA = "Yolda"
    TESLIM_EDILDI = "Teslim edildi"
    IPTAL = "İptal"


class Rol(Enum):
    YONETICI = "Yönetici"   # tüm modüller + kullanıcı yönetimi
    KURUM = "Kurum"         # yardım kuruluşu koordinatörü: ihtiyaç, dağıtım, rapor
    DEPO = "Depo"           # depo görevlisi: envanter, bağış girişi (kendi deposu)


# ---------------------------------------------------------------------------
# Temel tanım tabloları
# ---------------------------------------------------------------------------

@dataclass
class Kategori:
    ad: str                                  # Gıda, Barınma, Hijyen, Sağlık ...
    id: Optional[int] = None


@dataclass
class Malzeme:
    kategori_id: int                         # FK -> Kategori
    ad: str
    birim: str                               # adet, koli, kg, litre
    aciklama: str = ""
    id: Optional[int] = None


@dataclass
class Depo:
    ad: str
    il: str
    ilce: str
    adres: str = ""
    enlem: Optional[float] = None            # Hafta 9: harita/rota
    boylam: Optional[float] = None
    id: Optional[int] = None


@dataclass
class IhtiyacNoktasi:
    ad: str                                  # Çadır kent, okul, mahalle merkezi
    il: str
    ilce: str
    adres: str = ""
    enlem: Optional[float] = None
    boylam: Optional[float] = None
    nufus_tahmini: int = 0
    oncelik: OncelikSeviyesi = OncelikSeviyesi.ORTA
    id: Optional[int] = None


@dataclass
class Bagisci:
    ad: str                                  # Kişi ya da kurum (sentetik veri!)
    tur: str = "Bireysel"                    # Bireysel / Kurumsal
    telefon: str = ""
    eposta: str = ""
    id: Optional[int] = None


# ---------------------------------------------------------------------------
# Bağış (giriş) tarafı
# ---------------------------------------------------------------------------

@dataclass
class Bagis:
    bagisci_id: int                          # FK -> Bagisci
    depo_id: int                             # FK -> Depo (teslim alınan depo)
    tarih: datetime
    aciklama: str = ""
    id: Optional[int] = None


@dataclass
class BagisKalemi:
    """Bagis <-> Malzeme N-N ilişkisinin ara tablosu."""
    bagis_id: int                            # FK -> Bagis
    malzeme_id: int                          # FK -> Malzeme
    miktar: float
    son_kullanma_tarihi: Optional[date] = None
    id: Optional[int] = None


@dataclass
class Stok:
    """Depo <-> Malzeme N-N ilişkisi: hangi depoda hangi malzemeden ne kadar var.

    Birincil anahtar (depo_id, malzeme_id) bileşik anahtardır.
    """
    depo_id: int                             # PK, FK -> Depo
    malzeme_id: int                          # PK, FK -> Malzeme
    miktar: float = 0
    kritik_seviye: float = 0                 # Hafta 6: stok uyarısı


# ---------------------------------------------------------------------------
# İhtiyaç ve dağıtım (çıkış) tarafı
# ---------------------------------------------------------------------------

@dataclass
class IhtiyacTalebi:
    ihtiyac_noktasi_id: int                  # FK -> IhtiyacNoktasi
    malzeme_id: int                          # FK -> Malzeme
    miktar: float
    talep_tarihi: datetime
    durum: TalepDurumu = TalepDurumu.BEKLIYOR
    id: Optional[int] = None


@dataclass
class Dagitim:
    """Dağıtım kaydı: bir depodan bir ihtiyaç noktasına yapılan sevkiyat."""
    depo_id: int                             # FK -> Depo (çıkış)
    ihtiyac_noktasi_id: int                  # FK -> IhtiyacNoktasi (varış)
    planlanan_tarih: datetime
    teslim_tarihi: Optional[datetime] = None
    durum: DagitimDurumu = DagitimDurumu.PLANLANDI
    arac_plaka: str = ""
    id: Optional[int] = None


@dataclass
class DagitimKalemi:
    """Dagitim <-> Malzeme N-N ilişkisinin ara tablosu."""
    dagitim_id: int                          # FK -> Dagitim
    malzeme_id: int                          # FK -> Malzeme
    miktar: float
    id: Optional[int] = None


# ---------------------------------------------------------------------------
# Kullanıcı ve oturum (Hafta 5)
# ---------------------------------------------------------------------------

@dataclass
class Kullanici:
    kullanici_adi: str
    ad_soyad: str
    parola_hash: str = field(repr=False)     # loglara/ekrana yanlışlıkla basılmasın
    rol: Rol
    depo_id: Optional[int] = None            # FK -> Depo (yalnızca Depo rolü için zorunlu)
    aktif: bool = True
    basarisiz_giris: int = 0
    kilitli_bitis: Optional[datetime] = None
    olusturma_tarihi: datetime = field(default_factory=lambda: datetime.now().replace(microsecond=0))
    son_giris: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class Oturum:
    """Giriş yapan kullanıcının oturumu. Token'ın kendisi değil SHA-256 özeti saklanır."""
    kullanici_id: int                        # FK -> Kullanici
    token_hash: str = field(repr=False)
    olusturma: datetime
    son_kullanma: datetime
    cikis_zamani: Optional[datetime] = None
    id: Optional[int] = None
