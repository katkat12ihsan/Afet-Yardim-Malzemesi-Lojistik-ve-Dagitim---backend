"""Uygulama ayarları.

Gizli bilgiler (API anahtarları vb.) asla koda yazılmaz; ortam değişkeninden
ya da depoya yüklenmeyen .env dosyasından okunur (bkz. .env.example).
"""

import os
from pathlib import Path

UYGULAMA_ADI = "Afet Yardım Malzemesi Lojistik ve Dağıtım"
SURUM = "0.3.0 (Hafta 5 - kimlik doğrulama)"

PROJE_KOKU = Path(__file__).resolve().parent.parent
VERI_KLASORU = PROJE_KOKU / "data"
VERITABANI_YOLU = Path(os.getenv("AFET_DB_YOLU", VERI_KLASORU / "afet_lojistik.db"))

# Kimlik doğrulama (Hafta 5)
PAROLA_ITERASYON = 600_000          # PBKDF2 tur sayısı (OWASP 2023 önerisi); testlerde düşürülür
PAROLA_MIN_UZUNLUK = 8
OTURUM_SURESI_SAAT = 8              # bir vardiya; süre dolunca yeniden giriş gerekir
MAKS_BASARISIZ_GIRIS = 5
KILIT_SURESI_DAKIKA = 5

# Hafta 9 ve 10'da kullanılacak harici servis anahtarları (şimdilik boş)
HARITA_API_ANAHTARI = os.getenv("HARITA_API_ANAHTARI", "")
LLM_API_ANAHTARI = os.getenv("LLM_API_ANAHTARI", "")
