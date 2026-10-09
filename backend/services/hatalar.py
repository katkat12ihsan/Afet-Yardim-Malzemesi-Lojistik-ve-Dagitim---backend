"""İş katmanı hata sınıfları. Frontend bu hataları yakalayıp kullanıcıya mesaj gösterir."""


class IsKuraliHatasi(Exception):
    """Tüm iş katmanı hatalarının temel sınıfı."""


class DogrulamaHatasi(IsKuraliHatasi):
    """Girilen veri kurallara uymuyor (zayıf parola, boş alan, alınmış kullanıcı adı...)."""


class GecersizGiris(IsKuraliHatasi):
    """Kullanıcı adı veya parola hatalı.

    Hangisinin hatalı olduğu bilerek söylenmez: aksi halde saldırgan önce
    geçerli kullanıcı adlarını bulup sonra yalnızca parolaya odaklanabilir.
    """

    def __init__(self) -> None:
        super().__init__("Kullanıcı adı veya parola hatalı.")


class HesapKilitli(IsKuraliHatasi):
    """Çok sayıda başarısız denemeden sonra hesap geçici olarak kilitlendi."""


class OturumGecersiz(IsKuraliHatasi):
    """Oturum yok, süresi dolmuş ya da çıkış yapılmış -> yeniden giriş gerekir."""


class YetkisizErisim(IsKuraliHatasi):
    """Kullanıcının rolü bu işlem için yetkili değil."""
