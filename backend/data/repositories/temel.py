"""Ortak CRUD repository sınıfı.

Her tablo için aynı dört işlem (Create, Read, Update, Delete) tekrar
yazılmasın diye temel sınıf, dataclass alan adlarını tablo kolon adı
olarak kullanır (models/entities.py'deki alan adları = tablo kolonları).

Güvenlik: Tablo ve kolon adları koddaki sabitlerden gelir; kullanıcıdan
gelen DEĞERLER her zaman "?" parametresiyle gönderilir. Değerler SQL
metnine asla birleştirilmediği için SQL injection yapılamaz.
"""

import sqlite3
from dataclasses import fields
from datetime import date, datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar, Union, get_args, get_origin, get_type_hints

T = TypeVar("T")


def db_degeri(deger: Any) -> Any:
    """Python değerini SQLite'a yazılabilir hale getirir."""
    if isinstance(deger, Enum):
        return deger.value
    if isinstance(deger, (datetime, date)):
        return deger.isoformat()
    return deger


def python_degeri(deger: Any, tip: Any) -> Any:
    """SQLite'tan gelen değeri dataclass alanının tipine çevirir."""
    if deger is None:
        return None
    if get_origin(tip) is Union:  # Optional[X] -> X
        tip = next(t for t in get_args(tip) if t is not type(None))
    if isinstance(tip, type):
        if issubclass(tip, Enum):
            return tip(deger)
        if issubclass(tip, datetime):
            return datetime.fromisoformat(deger)
        if issubclass(tip, date):
            return date.fromisoformat(deger)
    return deger


class TemelRepository(Generic[T]):
    """Tek kolonlu `id` birincil anahtarı olan tablolar için CRUD."""

    tablo: str = ""
    varlik: type = object
    siralama: str = "id"

    def __init__(self, baglanti: sqlite3.Connection) -> None:
        self.baglanti = baglanti
        self._tipler = get_type_hints(self.varlik)
        self._kolonlar = [f.name for f in fields(self.varlik) if f.name != "id"]

    # ------------------------------------------------------------ yardımcı
    def _nesneye(self, satir: sqlite3.Row) -> T:
        degerler = {ad: python_degeri(satir[ad], self._tipler[ad]) for ad in satir.keys()}
        return self.varlik(**degerler)

    def _sorgula(self, sql: str, parametreler: tuple = ()) -> list[T]:
        return [self._nesneye(s) for s in self.baglanti.execute(sql, parametreler)]

    # ------------------------------------------------------------- CREATE
    def ekle(self, nesne: T) -> T:
        kolonlar = ", ".join(self._kolonlar)
        yer_tutucular = ", ".join("?" for _ in self._kolonlar)
        degerler = tuple(db_degeri(getattr(nesne, k)) for k in self._kolonlar)
        imlec = self.baglanti.execute(
            f"INSERT INTO {self.tablo} ({kolonlar}) VALUES ({yer_tutucular})", degerler
        )
        nesne.id = imlec.lastrowid
        return nesne

    # --------------------------------------------------------------- READ
    def getir(self, kimlik: int) -> Optional[T]:
        satir = self.baglanti.execute(
            f"SELECT * FROM {self.tablo} WHERE id = ?", (kimlik,)
        ).fetchone()
        return self._nesneye(satir) if satir else None

    def listele(self) -> list[T]:
        return self._sorgula(f"SELECT * FROM {self.tablo} ORDER BY {self.siralama}")

    def sayi(self) -> int:
        return self.baglanti.execute(f"SELECT COUNT(*) FROM {self.tablo}").fetchone()[0]

    # ------------------------------------------------------------- UPDATE
    def guncelle(self, nesne: T) -> bool:
        if nesne.id is None:
            raise ValueError("Kaydedilmemiş nesne güncellenemez (id yok).")
        atamalar = ", ".join(f"{k} = ?" for k in self._kolonlar)
        degerler = tuple(db_degeri(getattr(nesne, k)) for k in self._kolonlar)
        imlec = self.baglanti.execute(
            f"UPDATE {self.tablo} SET {atamalar} WHERE id = ?", (*degerler, nesne.id)
        )
        return imlec.rowcount == 1

    # ------------------------------------------------------------- DELETE
    def sil(self, kimlik: int) -> bool:
        imlec = self.baglanti.execute(f"DELETE FROM {self.tablo} WHERE id = ?", (kimlik,))
        return imlec.rowcount == 1
