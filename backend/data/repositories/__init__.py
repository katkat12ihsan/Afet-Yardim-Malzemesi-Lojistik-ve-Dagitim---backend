"""CRUD veri erişim sınıfları (repository deseni)."""

from .kullanici import KullaniciRepository, OturumRepository, RolDegisikligiRepository
from .stok import StokHareketiRepository, StokRepository
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
    "KullaniciRepository", "MalzemeRepository", "OturumRepository", "RolDegisikligiRepository", "StokHareketiRepository",
    "StokRepository",
]
