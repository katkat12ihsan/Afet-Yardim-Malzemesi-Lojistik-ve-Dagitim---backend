"""CRUD veri erişim sınıfları (repository deseni)."""

from .kullanici import (
    KullaniciRepository, OturumRepository, ParolaSifirlamaRepository, RolDegisikligiRepository,
)
from .rota import RotaOnbellekRepository
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
    "KullaniciRepository", "MalzemeRepository", "OturumRepository", "ParolaSifirlamaRepository", "RolDegisikligiRepository", "RotaOnbellekRepository", "StokHareketiRepository",
    "StokRepository",
]
