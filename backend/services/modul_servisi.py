"""İş katmanı - modül planı ve durumu.

Arayüz, hangi modülün hangi haftada geliştirileceğini ve şu anki durumunu
doğrudan bilmez; bu bilgiyi iş katmanından ister. Böylece katmanlar arası
bağımlılık yönü (Arayüz -> İş -> Veri) korunur.

Hafta 8: her modülün durumu (Hazır / Kısmen / Planlandı) eklendi; ana panel
vize ara sürümünde hangi modülün kullanılabilir olduğunu gösterir.
"""

from dataclasses import dataclass

HAZIR, KISMEN, PLANLANDI = "Hazır", "Kısmen", "Planlandı"


@dataclass(frozen=True)
class ModulBilgisi:
    anahtar: str
    ad: str
    hafta: int
    aciklama: str
    durum: str = PLANLANDI


_MODULLER = (
    ModulBilgisi("envanter", "Envanter Yönetimi", 6,
                 "Malzeme/kategori, depo giriş-çıkış, stok seviyesi ve rezerve.", HAZIR),
    ModulBilgisi("bagis", "Bağış Girişi", 7,
                 "Bağışçı ve bağış kalemlerinin kaydı, stoğa yansıtılması.", HAZIR),
    ModulBilgisi("ihtiyac", "İhtiyaç Eşleştirme", 7,
                 "Talepler ile stoğun eşleştirilmesi; fazla/eksik; dağıtım planı.", HAZIR),
    ModulBilgisi("dagitim", "Rota / Dağıtım Planı", 9,
                 "Dağıtım listesi ve durum güncelleme hazır (Hafta 7); harita/rota Hafta 9.", KISMEN),
    ModulBilgisi("oneri", "Yapay Zekâ Önerisi", 10,
                 "İhtiyaç ve stok verisine göre dağıtım önceliği ve rota önerisi."),
    ModulBilgisi("takip", "Takip", 11,
                 "Dağıtım kayıtlarının durum takibi (Planlandı/Yolda/Teslim)."),
    ModulBilgisi("rapor", "Şeffaflık Raporu", 12,
                 "Bağıştan teslime izlenebilir dağıtım raporu ve bildirimler."),
    ModulBilgisi("kullanicilar", "Kullanıcılar", 5,
                 "Kullanıcı listesi, rol düzenleme ve rol geçmişi (yalnızca Yönetici).", HAZIR),
)


def modulleri_getir() -> tuple[ModulBilgisi, ...]:
    return _MODULLER


def modul_bul(anahtar: str) -> ModulBilgisi:
    for modul in _MODULLER:
        if modul.anahtar == anahtar:
            return modul
    raise KeyError(f"Tanımsız modül: {anahtar}")
