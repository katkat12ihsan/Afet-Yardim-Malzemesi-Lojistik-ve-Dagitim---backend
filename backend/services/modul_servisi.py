"""İş katmanı - modül planı.

Arayüz, hangi modülün hangi haftada geliştirileceğini doğrudan bilmez; bu
bilgiyi iş katmanından ister. Böylece katmanlar arası bağımlılık yönü
(Arayüz -> İş -> Veri) iskelet aşamasında da korunmuş olur.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModulBilgisi:
    anahtar: str
    ad: str
    hafta: int
    aciklama: str


_MODULLER = (
    ModulBilgisi("envanter", "Envanter Yönetimi", 6,
                 "Malzeme/kategori, depo giriş-çıkış ve stok seviyesi."),
    ModulBilgisi("bagis", "Bağış Girişi", 7,
                 "Bağışçı ve bağış kalemlerinin kaydı, stoğa yansıtılması."),
    ModulBilgisi("ihtiyac", "İhtiyaç Eşleştirme", 7,
                 "İhtiyaç noktası talepleri ile depodaki stoğun eşleştirilmesi."),
    ModulBilgisi("dagitim", "Rota / Dağıtım Planı", 9,
                 "Harita/rota API ile depo -> ihtiyaç noktası sevkiyat planı."),
    ModulBilgisi("oneri", "Yapay Zekâ Önerisi", 10,
                 "İhtiyaç ve stok verisine göre dağıtım önceliği ve rota önerisi."),
    ModulBilgisi("takip", "Takip", 11,
                 "Dağıtım kayıtlarının durum takibi (Planlandı/Yolda/Teslim)."),
    ModulBilgisi("rapor", "Şeffaflık Raporu", 12,
                 "Bağıştan teslime izlenebilir dağıtım raporu ve bildirimler."),
    ModulBilgisi("kullanicilar", "Kullanıcılar", 5,
                 "Kullanıcı listesi ve rolleri (yalnızca Yönetici)."),
)


def modulleri_getir() -> tuple[ModulBilgisi, ...]:
    return _MODULLER


def modul_bul(anahtar: str) -> ModulBilgisi:
    for modul in _MODULLER:
        if modul.anahtar == anahtar:
            return modul
    raise KeyError(f"Tanımsız modül: {anahtar}")
