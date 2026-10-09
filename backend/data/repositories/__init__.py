"""CRUD veri erişim sınıfları (repository deseni)."""

from .stok import StokRepository
from .varliklar import (
    BagisciRepository,
    BagisKalemiRepository,
    BagisRepository,
    DagitimKalemiRepository,
    DagitimRepository,
    DepoRepository,
    IhtiyacNoktasiRepository,
    IhtiyacTalebiRepository,
    KategoriRepository,
    MalzemeRepository,
)

__all__ = [
    "BagisciRepository", "BagisKalemiRepository", "BagisRepository",
    "DagitimKalemiRepository", "DagitimRepository", "DepoRepository",
    "IhtiyacNoktasiRepository", "IhtiyacTalebiRepository", "KategoriRepository",
    "MalzemeRepository", "StokRepository",
]
