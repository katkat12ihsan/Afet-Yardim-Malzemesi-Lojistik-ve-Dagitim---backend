# Hafta 5 Sözlü Sınav Hazırlığı

## 1) Parolayı neden hash'liyoruz, tuz (salt) nedir?
Veritabanı çalınırsa parolalar okunamasın diye. Hash tek yönlüdür: `parola → özet` hesaplanır ama özetten parola geri çıkarılamaz. Girişte kullanıcının yazdığı parolayı aynı yöntemle tekrar hash'leyip kayıttaki özetle karşılaştırırım (`guvenlik.parola_dogrula`). Şifreleme ise anahtarla geri çözülebilir; parolayı geri görmeye ihtiyacım olmadığı için hash kullanıyorum.

**Tuz:** Her kullanıcı için üretilen 16 baytlık rastgele değer; parolayla birlikte hash'lenir ve hash'in yanında saklanır (`pbkdf2_sha256$600000$<tuz>$<özet>`). Faydası:
1. Aynı parolayı kullanan iki kişinin hash'i farklı olur (testi var).
2. Önceden hesaplanmış "rainbow table" tabloları işe yaramaz.

**Neden düz SHA-256 değil de PBKDF2?** SHA-256 çok hızlı, saldırgan saniyede milyarlarca deneme yapabilir. PBKDF2 işlemi 600.000 tur tekrarlayıp her denemeyi yavaşlatıyor.

## 2) Oturum ve token farkı nedir?
**Oturum (session):** Sunucu/uygulama tarafında tutulan "bu kullanıcı giriş yaptı" kaydı; benim projemde `oturum` tablosu (kim, ne zaman açtı, ne zaman bitecek, çıkış yaptı mı).

**Token:** Kullanıcıya verilen, oturumu temsil eden rastgele anahtar. Girişte `secrets.token_urlsafe(32)` ile üretiliyor. Arayüz bunu bellekte tutup her işlemde servise veriyor.

Veritabanında token'ın kendisi değil SHA-256 özeti var; veritabanı ele geçse bile geçerli token elde edilemez.

**JWT farkı:** JWT'de bilgiler token'ın içinde imzalı olarak taşınır, sunucu kayıt tutmaz ("stateless"); süresi dolmadan iptal etmek zordur. Ben masaüstü uygulamada çıkışta oturumu hemen kapatabilmek için sunucu taraflı oturum + rastgele token kullandım.

## 3) Rol tabanlı erişimi nasıl uyguladın?
Üç rol var: Yönetici, Kurum, Depo. `yetki.py` içindeki `ROL_YETKILERI` sözlüğü her rolün açabileceği modülleri tutuyor (ör. Depo: panel, envanter, bağış, takip). Her sayfa açılmadan önce arayüz `kimlik.modul_erisimi(token, modul)` çağırıyor. Bu metot önce oturumu doğruluyor, sonra `yetki_gerekli` ile rolü kontrol ediyor; yetki yoksa `YetkisizErisim` fırlatıyor.

**En önemli nokta:** kontrol backend'de. Menüde kilitli göstermek sadece kolaylık. Örneğin `kullanicilari_listele(token)` metodu Yönetici değilse hata veriyor; arayüzü atlasan bile veri gelmiyor (`test_kullanici_listesi_yalnizca_yonetici`).

**Ek kurallar:**
- Yönetici kayıt ekranından açılamıyor; sadece sistemde hiç kullanıcı yokken ilk hesap Yönetici olabiliyor.
- Depo rolü bir depoya bağlı olmak zorunda; bu, veritabanında CHECK kısıtıyla da garanti altında.

## 4) Başarısız giriş denemesinde ne oluyor?
1. Mesaj her zaman "Kullanıcı adı veya parola hatalı." Hangisinin yanlış olduğunu söylemiyorum; yoksa saldırgan önce geçerli kullanıcı adlarını bulur.
2. Kullanıcı yoksa bile sahte bir hash'le doğrulama yapıyorum ki yanıt süresinden de anlaşılmasın.
3. `basarisiz_giris` sayacı artıyor. 5'e ulaşınca `kilitli_bitis` = şimdi + 5 dakika olarak ayarlanıyor ve sayaç sıfırlanıyor. Kilitliyken doğru parola da kabul edilmiyor.
4. Başarılı girişte sayaç sıfırlanıyor, `son_giris` güncelleniyor.
5. Parola alanı her hatadan sonra temizleniyor.

## 5) Yetkisiz kullanıcı korumalı sayfaya giderse ne olur?
- **Giriş yapmamışsa ya da oturumu bitmişse:** `OturumGecersiz` → "Oturum süresi doldu, lütfen yeniden giriş yapın" uyarısı → giriş ekranına dönüş.
- **Giriş yapmış ama rolü yetkili değilse:** `YetkisizErisim` → içerik yüklenmeden "Erişim engellendi: 'Depo' rolünün bu bölüme erişim yetkisi yok" sayfası (ekran görüntüsü `hafta-05-depo-yetkisiz-erisim.png`).

Her iki durumda da veri servisten hiç dönmüyor; kontrol veriden önce yapılıyor.

---

## Teorik kavramlar (kısa)
- **Kimlik doğrulama (authentication):** "Sen kimsin?" → kullanıcı adı + parola ile giriş.
- **Yetkilendirme (authorization):** "Bunu yapmaya iznin var mı?" → rol kontrolü.
- **Hash ve salt:** Tek yönlü özet; kullanıcı başına rastgele tuz.
- **JWT / oturum:** İmzalı, sunucuda kaydı olmayan token (JWT) ya da sunucuda kaydı tutulan oturum (benim tercihim).
- **OWASP temel açıkları:**
  - A01 Bozuk Erişim Kontrolü → backend RBAC.
  - A02 Kriptografik Hatalar → PBKDF2 + tuz.
  - A03 Enjeksiyon → parametreli sorgu.
  - A07 Kimlik Doğrulama Hataları → kilitleme, parola politikası, genel hata mesajı, oturum süresi.

## Sık yapılan hatalar (bende olmamalı)
| Hata | Bendeki durum |
|---|---|
| Parolayı düz metin saklamak | PBKDF2 hash |
| Yetkilendirmeyi yalnızca arayüzde yapmak | Backend'de `modul_erisimi` / `yetki_gerekli` |
| Oturum süresini yönetmemek | 8 saat süre + çıkışta kapatma |

## Olası ek sorular
- **Token'ı neden veritabanında hash'liyorsun ama PBKDF2 ile değil?** Token zaten 32 bayt rastgele; tahmin edilecek bir şey yok. Tek tur SHA-256 yeterli. Parolalar ise insan seçtiği için tahmin edilebilir, onları yavaşlatmak gerekiyor.
- **`compare_digest` neden?** Normal `==` ilk farklı karakterde durur. Süre farkından özet tahmin edilebilir. `compare_digest` her zaman aynı sürede karşılaştırır.
- **Parola hash'i neden `repr`'de yok?** Hata ayıklarken `print(kullanici)` yapılırsa hash log'a düşmesin diye `field(repr=False)`.
