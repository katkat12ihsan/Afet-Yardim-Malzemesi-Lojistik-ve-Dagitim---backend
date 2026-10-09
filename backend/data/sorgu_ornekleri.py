"""Hafta 4 demosu: şema + örnek veriyle çalışan temel sorgular ve kısıtlar.

    python -m backend.data.sorgu_ornekleri

Veritabanına kalıcı hiçbir değişiklik yapmaz: CRUD ve kısıt denemeleri
bir transaction içinde yapılıp sonunda geri alınır (ROLLBACK).
"""

import sqlite3
from datetime import datetime

from backend.data.database import baglanti_ac, migrasyonlari_uygula
from backend.data.repositories import (
    BagisKalemiRepository, BagisRepository, DepoRepository, IhtiyacTalebiRepository,
    KategoriRepository, MalzemeRepository, StokRepository,
)
from backend.models import BagisKalemi, IhtiyacTalebi, Malzeme

TABLOLAR = ["kategori", "malzeme", "depo", "ihtiyac_noktasi", "bagisci", "bagis",
            "bagis_kalemi", "stok", "ihtiyac_talebi", "dagitim", "dagitim_kalemi"]


def baslik(metin: str) -> None:
    print(f"\n=== {metin} " + "=" * max(0, 66 - len(metin)))


def dene(aciklama: str, islev) -> None:
    """Bir kısıt ihlalini dener; veritabanının reddettiğini gösterir."""
    try:
        islev()
        print(f"  [!] {aciklama}: KABUL EDİLDİ (beklenmiyordu)")
    except sqlite3.IntegrityError as hata:
        print(f"  [OK] {aciklama}: reddedildi -> {hata}")


def main() -> None:
    baglanti = baglanti_ac()
    migrasyonlari_uygula(baglanti)

    baslik("1) Tablo kayıt sayıları")
    for tablo in TABLOLAR:
        print(f"  {tablo:<16} {baglanti.execute(f'SELECT COUNT(*) FROM {tablo}').fetchone()[0]:>4}")
    if KategoriRepository(baglanti).sayi() == 0:
        print("\nVeritabanı boş. Önce: python -m backend.data.kurulum --ornek-veri")
        return

    baslik("2) Merkez depo stokları (JOIN: stok + malzeme + kategori)")
    merkez = DepoRepository(baglanti).listele()[0]
    print(f"  Depo: {merkez.ad}")
    for s in StokRepository(baglanti).depo_stoklari(merkez.id):
        print(f"  {s['kategori']:<8} {s['malzeme']:<22} {s['miktar']:>7.0f} {s['birim']}")

    baslik("3) Bekleyen talepler - önceliğe göre (JOIN + WHERE + ORDER BY)")
    for t in IhtiyacTalebiRepository(baglanti).bekleyenler_oncelik_sirali():
        print(f"  öncelik {t['oncelik']}  {t['nokta']:<26} {t['malzeme']:<20} "
              f"{t['miktar']:>5.0f} {t['birim']:<6} {t['durum']}")

    baslik("4) Kritik seviyenin altındaki stoklar")
    for s in StokRepository(baglanti).kritik_stoklar() or []:
        print(f"  {s['depo']:<30} {s['malzeme']:<20} {s['miktar']:.0f} < {s['kritik_seviye']:.0f}")

    baslik("5) GROUP BY: kategori bazında toplam bağış")
    for satir in baglanti.execute(
        """SELECT k.ad, COUNT(*) AS kalem, SUM(bk.miktar) AS toplam
           FROM bagis_kalemi bk JOIN malzeme m ON m.id = bk.malzeme_id
           JOIN kategori k ON k.id = m.kategori_id
           GROUP BY k.ad ORDER BY toplam DESC"""):
        print(f"  {satir['ad']:<8} {satir['kalem']:>2} kalem  toplam {satir['toplam']:>6.0f}")

    # ---- Bu noktadan sonrası geri alınacak ----
    baslik("6) CRUD (sonunda ROLLBACK yapılır)")
    malzeme_repo = MalzemeRepository(baglanti)
    ilk_kategori = KategoriRepository(baglanti).listele()[0]
    yeni = malzeme_repo.ekle(Malzeme(ilk_kategori.id, "Deneme Malzemesi", "adet"))
    print(f"  CREATE  -> id={yeni.id}")
    print(f"  READ    -> {malzeme_repo.getir(yeni.id)}")
    yeni.aciklama = "güncellendi"
    print(f"  UPDATE  -> {malzeme_repo.guncelle(yeni)}  aciklama={malzeme_repo.getir(yeni.id).aciklama!r}")
    print(f"  DELETE  -> {malzeme_repo.sil(yeni.id)}  tekrar okuma: {malzeme_repo.getir(yeni.id)}")

    baslik("7) Kısıtlar çalışıyor mu?")
    ilk_malzeme = malzeme_repo.listele()[0]
    ilk_bagis = BagisRepository(baglanti).listele()[0]
    dene("Olmayan malzemeye bağış kalemi (FOREIGN KEY)",
         lambda: BagisKalemiRepository(baglanti).ekle(BagisKalemi(ilk_bagis.id, 99999, 5)))
    dene("Negatif miktarlı talep (CHECK miktar > 0)",
         lambda: IhtiyacTalebiRepository(baglanti).ekle(
             IhtiyacTalebi(1, ilk_malzeme.id, -10, datetime.now())))
    dene("Aynı adla ikinci kategori (UNIQUE)",
         lambda: baglanti.execute("INSERT INTO kategori (ad) VALUES (?)", (ilk_kategori.ad,)))
    dene("Stoğu olan malzemeyi silmek (ON DELETE RESTRICT)",
         lambda: malzeme_repo.sil(StokRepository(baglanti).listele()[0].malzeme_id))
    dene("Teslim tarihi olmadan 'Teslim edildi' (tablo CHECK)",
         lambda: baglanti.execute(
             "INSERT INTO dagitim (depo_id, ihtiyac_noktasi_id, planlanan_tarih, durum) "
             "VALUES (1, 1, '2026-10-09T08:00', 'Teslim edildi')"))

    kalem_once = baglanti.execute("SELECT COUNT(*) FROM bagis_kalemi WHERE bagis_id = ?",
                                  (ilk_bagis.id,)).fetchone()[0]
    BagisRepository(baglanti).sil(ilk_bagis.id)
    kalem_sonra = baglanti.execute("SELECT COUNT(*) FROM bagis_kalemi WHERE bagis_id = ?",
                                   (ilk_bagis.id,)).fetchone()[0]
    print(f"  [OK] Bağış silinince kalemleri de silindi (ON DELETE CASCADE): {kalem_once} -> {kalem_sonra}")

    baglanti.rollback()
    print("\nDemo değişiklikleri geri alındı (ROLLBACK); veritabanı değişmedi.")
    baglanti.close()


if __name__ == "__main__":
    main()
