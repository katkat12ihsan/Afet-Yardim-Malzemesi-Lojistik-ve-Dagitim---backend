"""Uygulama ayarları.

Gizli bilgiler (API anahtarları vb.) asla koda yazılmaz; ortam değişkeninden
ya da depoya yüklenmeyen .env dosyasından okunur (bkz. .env.example).
"""

import os
from pathlib import Path

UYGULAMA_ADI = "Afet Yardım Malzemesi Lojistik ve Dağıtım"
SURUM = "0.2.0 (Hafta 4 - veritabanı)"

PROJE_KOKU = Path(__file__).resolve().parent.parent
VERI_KLASORU = PROJE_KOKU / "data"
VERITABANI_YOLU = Path(os.getenv("AFET_DB_YOLU", VERI_KLASORU / "afet_lojistik.db"))

# Hafta 9 ve 10'da kullanılacak harici servis anahtarları (şimdilik boş)
HARITA_API_ANAHTARI = os.getenv("HARITA_API_ANAHTARI", "")
LLM_API_ANAHTARI = os.getenv("LLM_API_ANAHTARI", "")
