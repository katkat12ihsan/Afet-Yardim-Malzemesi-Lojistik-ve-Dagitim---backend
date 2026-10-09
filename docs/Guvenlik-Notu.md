# Güvenlik Notu — Kimlik Doğrulama ve Yetkilendirme (Hafta 5)

## Özet

| Konu | Uygulama | Dosya |
|---|---|---|
| Parola saklama | PBKDF2-HMAC-SHA256, 600.000 tur, kullanıcı başına 16 baytlık rastgele tuz. Düz metin parola hiçbir yerde saklanmaz. | `backend/guvenlik.py` |
| Parola politikası | En az 8 karakter, en az bir harf ve bir rakam; iki kez girilip eşleşmeli | `guvenlik.parola_kurallarini_kontrol_et` |
| Parola karşılaştırma | `hmac.compare_digest` (sabit süreli; zamanlama saldırısına karşı) | `guvenlik.parola_dogrula` |
| Hatalı giriş mesajı | Kullanıcı adı mı parola mı yanlış, söylenmez: "Kullanıcı adı veya parola hatalı." Olmayan kullanıcıda da sahte hash doğrulanır, yanıt süresi farkı oluşmaz | `kimlik_servisi.giris_yap` |
| Kaba kuvvet koruması | 5 hatalı denemede hesap 5 dakika kilitlenir; kilitliyken doğru parola da reddedilir | `kimlik_servisi.giris_yap` |
| Oturum | Girişte 32 baytlık rastgele token üretilir; veritabanına yalnızca SHA-256 özeti yazılır. Süre 8 saat; çıkışta oturum kapatılır | `oturum` tablosu, `oturum_dogrula` |
| Yetkilendirme (RBAC) | Rol → modül tablosu; her sayfa açılışında ve korumalı servis çağrısında **backend'de** kontrol | `backend/services/yetki.py` |
| Rol kısıtları | Yönetici kayıt ekranından açılamaz (yalnızca sistemde hiç kullanıcı yokken ilk hesap); Depo rolü bir depoya bağlı olmak zorunda (veritabanı CHECK) | `kayit_ol`, `002_kullanici.sql` |
| Hassas alanların sızması | `Kullanici.parola_hash` ve `Oturum.token_hash` `repr` dışında tutulur (log/print'te görünmez); Kullanıcılar sayfasında gösterilmez | `models/entities.py` |
| SQL injection | Tüm değerler `?` parametresiyle gönderilir | `repositories/temel.py` |
| Gizli bilgiler | API anahtarları ortam değişkeninde; `.env` ve veritabanı dosyası `.gitignore`'da | `config.py`, `.gitignore` |

## Rol – modül yetki tablosu

| Modül | Yönetici | Kurum | Depo |
|---|:-:|:-:|:-:|
| Ana Panel | ✔ | ✔ | ✔ |
| Envanter Yönetimi | ✔ | – | ✔ |
| Bağış Girişi | ✔ | – | ✔ |
| İhtiyaç Eşleştirme | ✔ | ✔ | – |
| Rota / Dağıtım Planı | ✔ | ✔ | – |
| Yapay Zekâ Önerisi | ✔ | ✔ | – |
| Takip | ✔ | ✔ | ✔ |
| Şeffaflık Raporu | ✔ | ✔ | – |
| Kullanıcılar | ✔ | – | – |

## Neden yetki kontrolü yalnızca arayüzde değil?

Menüde yetkisiz modüller "(kilitli)" olarak soluk gösterilir; bu yalnızca kullanım kolaylığıdır. Asıl karar `KimlikServisi.modul_erisimi(token, modul)` ve `kullanicilari_listele(token)` gibi backend metotlarında verilir. Arayüz değiştirilse ya da başka bir istemci (ileride web arayüzü) yazılsa bile yetkisiz işlem çalışmaz. Testler bunu arayüz olmadan doğrular (`tests/test_kimlik.py → YetkiTestleri`).

## OWASP Top 10 ile ilişki

| OWASP (2021) | Bu projedeki önlem |
|---|---|
| A01 Broken Access Control | Backend RBAC, her işlemde oturum + rol kontrolü |
| A02 Cryptographic Failures | PBKDF2 + tuz; token özeti; düz metin parola yok |
| A03 Injection | Parametreli sorgular |
| A07 Identification and Authentication Failures | Parola politikası, hesap kilitleme, genel hata mesajı, oturum süresi ve çıkış |

## Bilinen sınırlamalar / sonraki adımlar

- Kayıt olan Kurum/Depo hesapları hemen aktif olur. Gerçek kullanımda Yönetici onayı (`aktif = 0` ile başlayıp onaylanınca 1) eklenmeli.
- Parola değiştirme / sıfırlama ekranı henüz yok.
- Depo görevlisinin yalnızca **kendi deposunun** kayıtlarını görmesi (satır düzeyi yetki) Hafta 6–7'de envanter ve bağış modülleriyle birlikte uygulanacak; `kullanici.depo_id` bunun için şimdiden tutuluyor.
- Test kullanıcılarının parolaları `backend/data/ornek_veri.py` içinde açıktır; yalnızca yerel demo içindir.
