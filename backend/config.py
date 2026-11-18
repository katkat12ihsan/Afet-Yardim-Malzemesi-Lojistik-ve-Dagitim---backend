"""Uygulama ayarları.

Gizli bilgiler (API anahtarları vb.) asla koda yazılmaz; ortam değişkeninden
ya da depoya yüklenmeyen .env dosyasından okunur (bkz. .env.example).

Öncelik sırası (Hafta 9):  1) ortam değişkeni   2) .env dosyası   3) varsayılan
.env dosyası proje klasöründe değil, veri klasöründe aranır:
    C:\\Users\\<kullanıcı>\\AfetLojistik\\.env
Böylece anahtar hiçbir depo klasörüne girmez; yanlışlıkla commit'lenemez
(.gitignore'daki .env satırı ikinci güvencedir).
"""

import os
from pathlib import Path
from typing import Optional


def env_dosyasi_oku(yol: Path) -> dict[str, str]:
    """Basit .env okuyucu (ek paket gerekmez): ANAHTAR=değer satırları.

    Boş satır ve # ile başlayan satır atlanır; değerin etrafındaki tırnaklar
    kaldırılır. Dosya yoksa ya da okunamıyorsa boş sözlük döner (uygulama
    anahtarsız da çalışır).
    """
    degerler: dict[str, str] = {}
    try:
        satirlar = yol.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return degerler
    for satir in satirlar:
        satir = satir.strip()
        if not satir or satir.startswith("#") or "=" not in satir:
            continue
        anahtar, deger = satir.split("=", 1)
        deger = deger.strip()
        if len(deger) >= 2 and deger[0] == deger[-1] and deger[0] in "\"'":
            deger = deger[1:-1]
        degerler[anahtar.strip()] = deger
    return degerler


UYGULAMA_ADI = "Afet Yardım Malzemesi Lojistik ve Dağıtım"
SURUM = "0.7.0 (Hafta 9 - harita/rota API)"

# Backend ayrı bir paket olarak (pip ile) kurulabildiği için veritabanı proje
# klasöründe değil, kullanıcının ev klasöründe tutulur. Böylece frontend hangi
# klasörden çalıştırılırsa çalıştırılsın aynı veritabanını kullanır.
#   Windows: C:\Users\<kullanıcı>\AfetLojistik     Linux/macOS: ~/AfetLojistik
# AppData kullanılmaz: Windows, paket olarak kurulmuş uygulamaların (ör. Microsoft
# Store uygulamaları) içinden çalışan programların AppData'ya yazdıklarını gizlice
# paketin kendi klasörüne yönlendirir; aynı bilgisayarda iki farklı veritabanı oluşur.
# AFET_VERI_KLASORU veya AFET_DB_YOLU ortam değişkeniyle değiştirilebilir.
_VARSAYILAN_VERI_KLASORU = Path.home() / "AfetLojistik"
VERI_KLASORU = Path(os.getenv("AFET_VERI_KLASORU") or _VARSAYILAN_VERI_KLASORU)
VERITABANI_YOLU = Path(os.getenv("AFET_DB_YOLU") or VERI_KLASORU / "afet_lojistik.db")
ENV_DOSYASI = VERI_KLASORU / ".env"
_ENV = env_dosyasi_oku(ENV_DOSYASI)


def ayar(ad: str, varsayilan: str = "") -> str:
    """Önce ortam değişkeni, sonra veri klasöründeki .env, sonra varsayılan."""
    deger: Optional[str] = os.getenv(ad)
    if not deger:
        deger = _ENV.get(ad, "")
    return deger or varsayilan

# Kimlik doğrulama (Hafta 5)
PAROLA_ITERASYON = 600_000          # PBKDF2 tur sayısı (OWASP 2023 önerisi); testlerde düşürülür
PAROLA_MIN_UZUNLUK = 8
OTURUM_SURESI_SAAT = 8              # bir vardiya; süre dolunca yeniden giriş gerekir
MAKS_BASARISIZ_GIRIS = 5
KILIT_SURESI_DAKIKA = 5

# Hafta 9 - Harita/rota servisi: OpenRouteService (https://openrouteservice.org)
# Anahtar ücretsiz hesapla alınır; yoksa uygulama kuş uçuşu tahminle çalışır.
HARITA_API_ANAHTARI = ayar("HARITA_API_ANAHTARI")
HARITA_ZAMAN_ASIMI_SN = float(ayar("HARITA_ZAMAN_ASIMI_SN", "6"))   # yanıt gelmezse en fazla bu kadar beklenir
HARITA_DAKIKALIK_ISTEK = int(ayar("HARITA_DAKIKALIK_ISTEK", "30"))  # istemci tarafı hız sınırı (servis: 40/dk)
ROTA_ONBELLEK_GUN = 7               # aynı depo-nokta rotası bu kadar gün yeniden sorulmaz

# Hafta 10'da kullanılacak
LLM_API_ANAHTARI = ayar("LLM_API_ANAHTARI")
