"""Rol tabanlı erişim kontrolü (RBAC).

Kimlik doğrulama "Sen kimsin?" sorusudur (giriş). Yetkilendirme ise
"Bunu yapmaya iznin var mı?" sorusudur (bu dosya).

Kural: Yetki kontrolü YALNIZCA arayüzde yapılmaz. Menüde düğmeyi gizlemek
kullanım kolaylığıdır; asıl kontrol backend servislerinde `yetki_gerekli`
ile yapılır. Böylece arayüz atlansa bile yetkisiz işlem çalışmaz.
"""

from backend.models import Kullanici, Rol

from .hatalar import YetkisizErisim

TUM_MODULLER = frozenset({
    "panel", "envanter", "bagis", "ihtiyac", "dagitim", "oneri", "takip", "rapor",
    "kullanicilar",
})

ROL_YETKILERI: dict[Rol, frozenset[str]] = {
    Rol.YONETICI: TUM_MODULLER,
    # Yardım kuruluşu koordinatörü: ihtiyaçları ve dağıtımı planlar, raporları görür
    Rol.KURUM: frozenset({"panel", "ihtiyac", "dagitim", "oneri", "takip", "rapor"}),
    # Depo görevlisi: kendi deposunun stok ve bağış girişini yapar, sevkiyatı takip eder
    Rol.DEPO: frozenset({"panel", "envanter", "bagis", "takip"}),
}


def erisebilir_mi(kullanici: Kullanici, modul: str) -> bool:
    return modul in ROL_YETKILERI.get(kullanici.rol, frozenset())


def yetki_gerekli(kullanici: Kullanici, modul: str) -> None:
    """Yetki yoksa YetkisizErisim fırlatır. Servis metotlarının başında çağrılır."""
    if not erisebilir_mi(kullanici, modul):
        raise YetkisizErisim(
            f"'{kullanici.rol.value}' rolünün bu bölüme erişim yetkisi yok."
        )
