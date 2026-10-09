"""Sentetik (uydurma) örnek veri.

KVKK: Hiçbir gerçek kişiye ait veri yoktur. Bağışçı adları "Anonim Bağışçı N",
telefonlar 0555 000 00 NN, e-postalar ayrılmış "example.com" alan adındadır.
Konumlar Bingöl ili ilçe merkezlerinin yaklaşık koordinatlarıdır.

Stok tablosu elle yazılmaz; bağış kalemlerinden teslim edilmiş/yoldaki
dağıtım kalemleri düşülerek hesaplanır. Böylece örnek veri kendi içinde
tutarlı olur (stok = giren - çıkan).
"""

import sqlite3
from collections import defaultdict
from datetime import date, datetime

from backend.models import (
    Bagis, Bagisci, BagisKalemi, Dagitim, DagitimDurumu, DagitimKalemi, Depo,
    IhtiyacNoktasi, IhtiyacTalebi, Kategori, Malzeme, OncelikSeviyesi, Stok, TalepDurumu,
)
from backend.data.repositories import (
    BagisciRepository, BagisKalemiRepository, BagisRepository, DagitimKalemiRepository,
    DagitimRepository, DepoRepository, IhtiyacNoktasiRepository, IhtiyacTalebiRepository,
    KategoriRepository, MalzemeRepository, StokRepository,
)

KATEGORILER = ["Gıda", "Barınma", "Hijyen", "Sağlık", "Giyim"]

# (ad, kategori, birim, kritik seviye)
MALZEMELER = [
    ("Kuru gıda kolisi", "Gıda", "koli", 100),
    ("İçme suyu (5 L)", "Gıda", "adet", 300),
    ("Bebek maması", "Gıda", "paket", 50),
    ("Konserve", "Gıda", "koli", 40),
    ("Çadır (4 kişilik)", "Barınma", "adet", 20),
    ("Battaniye", "Barınma", "adet", 150),
    ("Uyku tulumu", "Barınma", "adet", 60),
    ("Hijyen kiti", "Hijyen", "paket", 80),
    ("Bebek bezi", "Hijyen", "paket", 50),
    ("İlk yardım çantası", "Sağlık", "adet", 15),
    ("Mont (yetişkin)", "Giyim", "adet", 40),
    ("Çocuk giysi seti", "Giyim", "paket", 30),
]

DEPOLAR = [
    Depo("Bingöl Merkez Lojistik Deposu", "Bingöl", "Merkez", "Örnek OSB, 1. Cadde No:1", 38.8853, 40.4983),
    Depo("Genç Ara Depo", "Bingöl", "Genç", "Örnek Mah. Depo Sk. No:2", 38.7514, 40.5603),
    Depo("Solhan Ara Depo", "Bingöl", "Solhan", "Örnek Mah. Ambar Sk. No:3", 38.9683, 41.0533),
]

IHTIYAC_NOKTALARI = [
    IhtiyacNoktasi("Karlıova Çadır Kent", "Bingöl", "Karlıova", "", 39.2944, 41.0094, 1200, OncelikSeviyesi.KRITIK),
    IhtiyacNoktasi("Kiğı Okul Toplanma Alanı", "Bingöl", "Kiğı", "", 39.3097, 40.3497, 450, OncelikSeviyesi.YUKSEK),
    IhtiyacNoktasi("Yedisu Mahalle Merkezi", "Bingöl", "Yedisu", "", 39.4331, 40.5453, 300, OncelikSeviyesi.ORTA),
    IhtiyacNoktasi("Adaklı Konteyner Kent", "Bingöl", "Adaklı", "", 39.2297, 40.4811, 800, OncelikSeviyesi.YUKSEK),
    IhtiyacNoktasi("Yayladere Köy Konağı", "Bingöl", "Yayladere", "", 39.2253, 40.0697, 150, OncelikSeviyesi.DUSUK),
]

BAGISCILAR = [
    Bagisci("Örnek Gıda A.Ş.", "Kurumsal", "0555 000 00 01", "iletisim@ornekgida.example.com"),
    Bagisci("Örnek Tekstil Ltd.", "Kurumsal", "0555 000 00 02", "bagis@ornektekstil.example.com"),
    Bagisci("Anonim Bağışçı 1", "Bireysel", "0555 000 00 03", "bagisci1@example.com"),
    Bagisci("Anonim Bağışçı 2", "Bireysel", "0555 000 00 04", "bagisci2@example.com"),
    Bagisci("Örnek Yardımlaşma Derneği", "Kurumsal", "0555 000 00 05", "dernek@example.com"),
]

# (bağışçı sırası, depo sırası, tarih, açıklama, [(malzeme adı, miktar, son kullanma)])
BAGISLAR = [
    (0, 0, "2026-10-01T10:00", "Kurumsal gıda bağışı", [
        ("Kuru gıda kolisi", 400, "2027-06-30"), ("İçme suyu (5 L)", 1200, "2027-10-01"),
        ("Konserve", 150, "2028-01-01")]),
    (1, 0, "2026-10-01T15:30", "Kışlık giyim ve battaniye", [
        ("Battaniye", 600, None), ("Mont (yetişkin)", 250, None), ("Çocuk giysi seti", 120, None)]),
    (2, 1, "2026-10-02T09:15", "", [
        ("Hijyen kiti", 90, None), ("Bebek bezi", 70, None), ("Bebek maması", 40, "2027-03-01")]),
    (4, 2, "2026-10-02T13:00", "Dernek barınma yardımı", [
        ("Çadır (4 kişilik)", 80, None), ("Uyku tulumu", 200, None), ("Battaniye", 150, None)]),
    (3, 1, "2026-10-03T11:45", "", [
        ("İlk yardım çantası", 25, "2028-12-31"), ("Kuru gıda kolisi", 60, "2027-05-31")]),
    (0, 2, "2026-10-04T08:30", "İkinci gıda sevkiyatı", [
        ("İçme suyu (5 L)", 500, "2027-10-01"), ("Kuru gıda kolisi", 150, "2027-06-30")]),
]

# (nokta sırası, malzeme adı, miktar, tarih, durum)
TALEPLER = [
    (0, "Çadır (4 kişilik)", 60, "2026-10-02T08:00", TalepDurumu.KISMEN_KARSILANDI),
    (0, "Battaniye", 500, "2026-10-02T08:05", TalepDurumu.KISMEN_KARSILANDI),
    (0, "Kuru gıda kolisi", 300, "2026-10-02T08:10", TalepDurumu.BEKLIYOR),
    (0, "Bebek maması", 60, "2026-10-03T09:00", TalepDurumu.BEKLIYOR),
    (1, "İçme suyu (5 L)", 400, "2026-10-03T10:00", TalepDurumu.KARSILANDI),
    (1, "Hijyen kiti", 100, "2026-10-04T10:30", TalepDurumu.BEKLIYOR),
    (2, "Mont (yetişkin)", 80, "2026-10-04T12:00", TalepDurumu.BEKLIYOR),
    (3, "Uyku tulumu", 150, "2026-10-05T09:00", TalepDurumu.BEKLIYOR),
    (3, "İlk yardım çantası", 10, "2026-10-05T09:20", TalepDurumu.BEKLIYOR),
    (4, "Çocuk giysi seti", 25, "2026-10-06T14:00", TalepDurumu.IPTAL),
]

# (depo sırası, nokta sırası, planlanan, teslim, durum, plaka, [(malzeme adı, miktar)])
DAGITIMLAR = [
    (0, 1, "2026-10-04T07:00", "2026-10-04T11:20", DagitimDurumu.TESLIM_EDILDI, "12 ABC 001",
     [("İçme suyu (5 L)", 400)]),
    (2, 0, "2026-10-05T06:30", "2026-10-05T10:05", DagitimDurumu.TESLIM_EDILDI, "12 ABC 002",
     [("Çadır (4 kişilik)", 40), ("Battaniye", 150)]),
    (0, 0, "2026-10-08T07:00", None, DagitimDurumu.YOLDA, "12 ABC 003",
     [("Battaniye", 200), ("Kuru gıda kolisi", 120)]),
    (1, 3, "2026-10-10T08:00", None, DagitimDurumu.PLANLANDI, "12 ABC 004",
     [("İlk yardım çantası", 10)]),
]

# Bu durumlardaki dağıtımların malzemesi depodan çıkmış sayılır
STOKTAN_DUSEN = {DagitimDurumu.YOLDA, DagitimDurumu.TESLIM_EDILDI}


def _zaman(metin: str) -> datetime:
    return datetime.fromisoformat(metin)


def ornek_veri_yukle(baglanti: sqlite3.Connection) -> bool:
    """Veritabanı boşsa örnek veriyi yükler. Yüklediyse True döner.

    Çağıran transaction'ı yönetir (database.islem).
    """
    if KategoriRepository(baglanti).sayi() > 0:
        return False

    kategori_id = {ad: KategoriRepository(baglanti).ekle(Kategori(ad)).id for ad in KATEGORILER}

    malzeme_repo = MalzemeRepository(baglanti)
    malzeme_id, kritik = {}, {}
    for ad, kategori, birim, kritik_seviye in MALZEMELER:
        malzeme_id[ad] = malzeme_repo.ekle(Malzeme(kategori_id[kategori], ad, birim)).id
        kritik[ad] = kritik_seviye

    depo_ids = [DepoRepository(baglanti).ekle(d).id for d in DEPOLAR]
    nokta_ids = [IhtiyacNoktasiRepository(baglanti).ekle(n).id for n in IHTIYAC_NOKTALARI]
    bagisci_ids = [BagisciRepository(baglanti).ekle(b).id for b in BAGISCILAR]

    stok = defaultdict(float)  # (depo_id, malzeme_adı) -> miktar

    bagis_repo, kalem_repo = BagisRepository(baglanti), BagisKalemiRepository(baglanti)
    for bagisci_sira, depo_sira, tarih, aciklama, kalemler in BAGISLAR:
        bagis = bagis_repo.ekle(Bagis(bagisci_ids[bagisci_sira], depo_ids[depo_sira],
                                      _zaman(tarih), aciklama))
        for malzeme_adi, miktar, skt in kalemler:
            kalem_repo.ekle(BagisKalemi(bagis.id, malzeme_id[malzeme_adi], miktar,
                                        date.fromisoformat(skt) if skt else None))
            stok[(depo_ids[depo_sira], malzeme_adi)] += miktar

    talep_repo = IhtiyacTalebiRepository(baglanti)
    for nokta_sira, malzeme_adi, miktar, tarih, durum in TALEPLER:
        talep_repo.ekle(IhtiyacTalebi(nokta_ids[nokta_sira], malzeme_id[malzeme_adi],
                                      miktar, _zaman(tarih), durum))

    dagitim_repo, dk_repo = DagitimRepository(baglanti), DagitimKalemiRepository(baglanti)
    for depo_sira, nokta_sira, planlanan, teslim, durum, plaka, kalemler in DAGITIMLAR:
        dagitim = dagitim_repo.ekle(Dagitim(depo_ids[depo_sira], nokta_ids[nokta_sira],
                                            _zaman(planlanan), _zaman(teslim) if teslim else None,
                                            durum, plaka))
        for malzeme_adi, miktar in kalemler:
            dk_repo.ekle(DagitimKalemi(dagitim.id, malzeme_id[malzeme_adi], miktar))
            if durum in STOKTAN_DUSEN:
                stok[(depo_ids[depo_sira], malzeme_adi)] -= miktar

    stok_repo = StokRepository(baglanti)
    for (depo_id, malzeme_adi), miktar in stok.items():
        # Kritik seviye ana depoda tam, ara depolarda yarı değer
        seviye = kritik[malzeme_adi] if depo_id == depo_ids[0] else kritik[malzeme_adi] / 2
        stok_repo.kaydet(Stok(depo_id, malzeme_id[malzeme_adi], miktar, seviye))

    return True
