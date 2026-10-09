"""Parola ve token güvenliği (yalnızca Python standart kütüphanesi).

backend/ seviyesinde ortak yardımcıdır: hem iş katmanı (kimlik servisi)
hem de örnek veri aracı kullanır; böylece veri katmanı iş katmanına bağımlı olmaz.

Hash vs şifreleme: Şifrelenen veri anahtarla geri çözülebilir; hash tek
yönlüdür, geri çözülemez. Parolayı geri görmeye hiç ihtiyacımız yok, sadece
"girilen parola doğru mu?" diye bakarız -> hash kullanılır.

Neden düz SHA-256 değil de PBKDF2?
  SHA-256 çok hızlıdır; saldırgan saniyede milyarlarca tahmin deneyebilir.
  PBKDF2 hash'i bilerek yüz binlerce tur tekrarlar, her tahmini pahalı yapar.

Tuz (salt): Her parola için rastgele üretilen 16 bayt. Aynı parolayı
kullanan iki kullanıcının hash'i farklı olur; önceden hesaplanmış
"rainbow table" tabloları işe yaramaz.
"""

import hashlib
import hmac
import secrets

from backend import config

ALGORITMA = "pbkdf2_sha256"


def parola_hashle(parola: str) -> str:
    """'pbkdf2_sha256$<iterasyon>$<tuz_hex>$<özet_hex>' biçiminde hash üretir."""
    tuz = secrets.token_bytes(16)
    iterasyon = config.PAROLA_ITERASYON
    ozet = hashlib.pbkdf2_hmac("sha256", parola.encode("utf-8"), tuz, iterasyon)
    return f"{ALGORITMA}${iterasyon}${tuz.hex()}${ozet.hex()}"


def parola_dogrula(parola: str, kayitli_hash: str) -> bool:
    """Girilen parolayı, kayıttaki tuz ve iterasyonla yeniden hash'leyip karşılaştırır."""
    try:
        algoritma, iterasyon, tuz_hex, ozet_hex = kayitli_hash.split("$")
    except ValueError:
        return False
    if algoritma != ALGORITMA:
        return False
    ozet = hashlib.pbkdf2_hmac("sha256", parola.encode("utf-8"),
                               bytes.fromhex(tuz_hex), int(iterasyon))
    # compare_digest: karşılaştırma süresi eşleşen karakter sayısına göre değişmez
    # (zamanlama saldırısına karşı)
    return hmac.compare_digest(ozet.hex(), ozet_hex)


def parola_kurallarini_kontrol_et(parola: str) -> list[str]:
    """Parola politikası. Boş liste = parola uygun."""
    hatalar = []
    if len(parola) < config.PAROLA_MIN_UZUNLUK:
        hatalar.append(f"en az {config.PAROLA_MIN_UZUNLUK} karakter olmalı")
    if not any(c.isalpha() for c in parola):
        hatalar.append("en az bir harf içermeli")
    if not any(c.isdigit() for c in parola):
        hatalar.append("en az bir rakam içermeli")
    return hatalar


def token_uret() -> str:
    """Tahmin edilemez oturum token'ı (32 bayt kriptografik rastgele)."""
    return secrets.token_urlsafe(32)


def token_ozeti(token: str) -> str:
    """Veritabanına token'ın kendisi değil SHA-256 özeti yazılır.

    Token zaten rastgele ve uzun olduğu için burada tek tur SHA-256 yeterli;
    PBKDF2 gibi yavaşlatmaya gerek yok (tahmin edilecek bir parola değil).
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
