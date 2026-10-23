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

## Rol düzenleme (Kullanıcılar sayfası)

Yönetici, Kullanıcılar sayfasında bir hesabı seçip **Rolü Düzenle** ile rolünü (Depo rolünde bağlı deposunu da) değiştirebilir. Kurallar backend'de, `KimlikServisi.rol_degistir` içindedir:

| Kural | Neden |
|---|---|
| Yalnızca Yönetici (`yetki_gerekli(..., "kullanicilar")`) | Arayüz atlansa bile yetkisiz rol değişikliği olmasın |
| Kişi **kendi rolünü** değiştiremez | Son Yönetici kendini düşürüp sistemi yöneticisiz bırakamasın; değişikliği her zaman başka biri yapar |
| Depo rolü için geçerli depo zorunlu; diğer rollerde depo boşaltılır | Veritabanındaki `CHECK (rol <> 'Depo' OR depo_id IS NOT NULL)` ile tutarlı |
| Rolü değişen kişinin **açık oturumları kapatılır** | Yetkisi düşen biri eski menüyle çalışmaya devam edemez; yeni rol sonraki girişte geçerli |
| Her değişiklik `rol_degisikligi` tablosuna yazılır (kim, kimi, ne zaman, eski → yeni rol/depo) | Denetim izi; değişiklik ve kayıt tek transaction'da |

Tablo seviyesinde de korunur (`004_rol_degisikligi.sql`): kendi kendine değişiklik kaydı ve değişiklik içermeyen kayıt `CHECK` ile reddedilir. Testler: `tests/test_kimlik.py → RolDuzenlemeTestleri` (7 test).

## Bilinen sınırlamalar / sonraki adımlar

- Kayıt olan Kurum/Depo hesapları hemen aktif olur. Gerçek kullanımda Yönetici onayı (`aktif = 0` ile başlayıp onaylanınca 1) eklenmeli.
- Parola değiştirme / sıfırlama ekranı henüz yok.
- ~~Rol değiştirme ekranı yok~~ → **eklendi** (yukarıdaki "Rol düzenleme" bölümü). Hesabı pasifleştirme (aktif = 0) ekranı henüz yok.
- ~~Depo görevlisinin yalnızca kendi deposunu görmesi~~ → **Hafta 6'da envanterde uygulandı** (satır düzeyi yetki, `EnvanterServisi._depo_kontrol`, kural K5; bkz. [Envanter.md](Envanter.md)). Bağış modülüne Hafta 7'de uygulanacak.
- Test kullanıcılarının parolaları `backend/data/ornek_veri.py` içinde açıktır; yalnızca yerel demo içindir.
