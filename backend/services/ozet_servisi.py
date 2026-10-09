"""İş katmanı - ana panel özeti.

Frontend veritabanına doğrudan erişmez; sayıları bu servisten ister.
"""

import sqlite3
from dataclasses import dataclass

from backend.data.repositories import (
    DepoRepository, IhtiyacNoktasiRepository, IhtiyacTalebiRepository, MalzemeRepository,
    StokRepository,
)


@dataclass(frozen=True)
class PanelOzeti:
    malzeme_cesidi: int
    depo: int
    ihtiyac_noktasi: int
    bekleyen_talep: int
    kritik_stok: int

    @property
    def bos_mu(self) -> bool:
        return self.malzeme_cesidi == 0 and self.depo == 0


class OzetServisi:
    def __init__(self, baglanti: sqlite3.Connection) -> None:
        self._baglanti = baglanti

    def panel_ozeti(self) -> PanelOzeti:
        return PanelOzeti(
            malzeme_cesidi=MalzemeRepository(self._baglanti).sayi(),
            depo=DepoRepository(self._baglanti).sayi(),
            ihtiyac_noktasi=IhtiyacNoktasiRepository(self._baglanti).sayi(),
            bekleyen_talep=len(IhtiyacTalebiRepository(self._baglanti).bekleyenler_oncelik_sirali()),
            kritik_stok=len(StokRepository(self._baglanti).kritik_stoklar()),
        )
