"""Veritabanı kurulum komutu.

    python -m backend.data.kurulum                 # migration'ları uygula
    python -m backend.data.kurulum --ornek-veri    # + boşsa sentetik veriyi yükle
    python -m backend.data.kurulum --sifirla --ornek-veri   # veritabanını silip baştan kur
"""

import argparse

from backend import config
from backend.data.database import baglanti_ac, islem, migrasyonlari_uygula
from backend.data.ornek_veri import ornek_veri_yukle


def main() -> None:
    ayrac = argparse.ArgumentParser(description="Veritabanını kurar.")
    ayrac.add_argument("--ornek-veri", action="store_true", help="sentetik örnek veriyi yükle")
    ayrac.add_argument("--sifirla", action="store_true", help="mevcut veritabanı dosyasını sil")
    secenekler = ayrac.parse_args()

    if secenekler.sifirla and config.VERITABANI_YOLU.exists():
        config.VERITABANI_YOLU.unlink()
        print(f"Silindi: {config.VERITABANI_YOLU}")

    baglanti = baglanti_ac()
    try:
        uygulananlar = migrasyonlari_uygula(baglanti)
        print("Uygulanan migration:", ", ".join(uygulananlar) if uygulananlar else "yok (şema güncel)")

        if secenekler.ornek_veri:
            with islem(baglanti):
                yuklendi = ornek_veri_yukle(baglanti)
            print("Örnek veri yüklendi." if yuklendi else "Veritabanı dolu, örnek veri atlandı.")
    finally:
        baglanti.close()
    print(f"Veritabanı: {config.VERITABANI_YOLU}")


if __name__ == "__main__":
    main()
