"""İş katmanı - ana panel özeti.

Frontend veritabanına doğrudan erişmez; sayıları bu servisten ister.
Hafta 5: özet yalnızca geçerli oturumu olan kullanıcıya verilir.
Hafta 6: Depo görevlisi kritik stok sayısını yalnızca kendi deposu için görür.
"""

import sqlite3
from dataclasses import dataclass

from backend.data.repositories import (
    DepoRepository, IhtiyacNoktasiRepository, IhtiyacTalebiRepository, MalzemeRepository,
    StokRepository,
)

from backend.models import Rol

from .kimlik_servisi import KimlikServisi


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
    def __init__(self, baglanti: sqlite3.Connection, kimlik: KimlikServisi) -> None:
        self._baglanti = baglanti
        self._kimlik = kimlik

    def panel_ozeti(self, token: str) -> PanelOzeti:
        kullanici = self._kimlik.modul_erisimi(token, "panel")
        kritik = StokRepository(self._baglanti).kritik_stoklar()
        if kullanici.rol is Rol.DEPO:
            kritik = [s for s in kritik if s["depo_id"] == kullanici.depo_id]
        return PanelOzeti(
            malzeme_cesidi=MalzemeRepository(self._baglanti).sayi(),
            depo=DepoRepository(self._baglanti).sayi(),
            ihtiyac_noktasi=IhtiyacNoktasiRepository(self._baglanti).sayi(),
            bekleyen_talep=len(IhtiyacTalebiRepository(self._baglanti).bekleyenler_oncelik_sirali()),
            kritik_stok=len(kritik),
        )
