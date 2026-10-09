"""Veri erişim katmanı - veritabanı bağlantısı, transaction ve migration.

Migration: Şema değişiklikleri numaralı .sql dosyaları olarak
(backend/data/migrations/001_..., 002_...) saklanır. Her dosya bir kez
uygulanır ve `sema_surumu` tablosuna yazılır. Böylece veritabanı her
bilgisayarda aynı sırayla, aynı şemaya getirilir; şema da Git'te izlenir.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from backend import config

MIGRASYON_KLASORU = Path(__file__).resolve().parent / "migrations"


def baglanti_ac(yol: Optional[str] = None) -> sqlite3.Connection:
    """SQLite bağlantısı açar; yabancı anahtar kısıtlarını etkinleştirir.

    yol=":memory:" verilirse bellekte geçici veritabanı açılır (testler için).
    """
    if yol is None:
        config.VERI_KLASORU.mkdir(parents=True, exist_ok=True)
        yol = str(config.VERITABANI_YOLU)
    baglanti = sqlite3.connect(yol)
    baglanti.execute("PRAGMA foreign_keys = ON")  # SQLite'ta varsayılan kapalıdır
    baglanti.row_factory = sqlite3.Row
    return baglanti


@contextmanager
def islem(baglanti: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Transaction: blok içindeki tüm yazma işlemleri ya birlikte kaydedilir
    (COMMIT) ya da bir hata olursa hiçbiri kaydedilmez (ROLLBACK).

    Repository metotları kendileri commit etmez; birden çok tabloyu
    etkileyen bir işlem (ör. bağış + kalemleri + stok) tek transaction
    içinde yapılabilsin diye commit kararı çağırana bırakılır.
    """
    try:
        yield baglanti
        baglanti.commit()
    except Exception:
        baglanti.rollback()
        raise


def migrasyonlari_uygula(baglanti: sqlite3.Connection) -> list[str]:
    """Henüz uygulanmamış migration dosyalarını sırayla uygular.

    Döndürür: bu çağrıda uygulanan dosya adları.
    """
    baglanti.execute(
        "CREATE TABLE IF NOT EXISTS sema_surumu ("
        " surum INTEGER PRIMARY KEY,"
        " dosya TEXT NOT NULL,"
        " uygulanma_zamani TEXT NOT NULL)"
    )
    baglanti.commit()
    uygulanmis = {satir["surum"] for satir in baglanti.execute("SELECT surum FROM sema_surumu")}

    uygulananlar = []
    for dosya in sorted(MIGRASYON_KLASORU.glob("*.sql")):
        surum = int(dosya.name.split("_", 1)[0])  # "001_ilk_sema.sql" -> 1
        if surum in uygulanmis:
            continue
        sql = dosya.read_text(encoding="utf-8")
        kayit = (
            "INSERT INTO sema_surumu (surum, dosya, uygulanma_zamani) "
            f"VALUES ({surum}, '{dosya.name}', '{datetime.now().isoformat(timespec='seconds')}');"
        )
        try:
            # Script ve sürüm kaydı tek transaction: yarım kalan migration olmaz
            baglanti.executescript(f"BEGIN;\n{sql}\n{kayit}\nCOMMIT;")
        except sqlite3.Error:
            if baglanti.in_transaction:
                baglanti.rollback()
            raise
        uygulananlar.append(dosya.name)
    return uygulananlar
