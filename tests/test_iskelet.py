"""İskelet testleri:  python -m unittest"""

import unittest
from datetime import datetime

from backend.models import Dagitim, DagitimDurumu, IhtiyacTalebi, TalepDurumu
from backend.services import modul_servisi


class VarlikTestleri(unittest.TestCase):
    def test_yeni_kayitlarin_varsayilan_durumu(self):
        talep = IhtiyacTalebi(ihtiyac_noktasi_id=1, malzeme_id=1, miktar=50,
                              talep_tarihi=datetime.now())
        dagitim = Dagitim(depo_id=1, ihtiyac_noktasi_id=1, planlanan_tarih=datetime.now())
        self.assertEqual(talep.durum, TalepDurumu.BEKLIYOR)
        self.assertEqual(dagitim.durum, DagitimDurumu.PLANLANDI)
        self.assertIsNone(talep.id)  # Kaydedilmeden id atanmaz


class ModulServisiTestleri(unittest.TestCase):
    def test_modul_anahtarlari_benzersiz(self):
        anahtarlar = [m.anahtar for m in modul_servisi.modulleri_getir()]
        self.assertEqual(len(anahtarlar), len(set(anahtarlar)))

    def test_tanimsiz_modul_hata_verir(self):
        with self.assertRaises(KeyError):
            modul_servisi.modul_bul("yok")


if __name__ == "__main__":
    unittest.main()
