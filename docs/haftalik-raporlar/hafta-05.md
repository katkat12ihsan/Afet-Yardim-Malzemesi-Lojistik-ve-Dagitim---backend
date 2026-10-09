# Hafta 5 İlerleme Raporu — Kullanıcı Yönetimi ve Kimlik Doğrulama

**Öğrenci:** İhsan Katkat · 251161036
**Proje:** P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım
**Geliştirilen modül:** Kimlik doğrulama ve kullanıcı/rol
**Dal:** `hafta-05` (main'e birleştirildi)

## Yapılan teknik çalışmalar

| Görev (yönergeden) | Durum | Kanıt |
|---|---|---|
| Kayıt/giriş akışı | ✅ | `frontend/giris_penceresi.py` (giriş + kayıt formu), `KimlikServisi.kayit_ol / giris_yap` |
| Parola hash'leme | ✅ | `backend/guvenlik.py` — PBKDF2-SHA256, 600.000 tur, kullanıcı başına rastgele tuz |
| Oturum/token yönetimi | ✅ | `oturum` tablosu; token'ın yalnızca SHA-256 özeti saklanır; 8 saat süre; çıkışta kapatılır |
| Rol tabanlı erişim (depo/kurum) | ✅ | `backend/services/yetki.py` — Yönetici / Kurum / Depo; backend'de kontrol |

**Backend:**
- `002_kullanici.sql` migration'ı: `kullanici` ve `oturum` tabloları, kısıtlar ve indeksler.
- `KullaniciRepository` ve `OturumRepository`.
- `KimlikServisi`: kayıt, giriş, oturum doğrulama, çıkış, modül erişimi ve yalnızca Yönetici'nin görebildiği kullanıcı listesi.
- Hata sınıfları ve hesap kilitleme (5 hatalı denemede 5 dakika).
- `OzetServisi` artık geçerli oturum istiyor.

**Frontend:**
- Giriş/kayıt penceresi.
- Ana pencerede kullanıcı adı, rol ve "Çıkış Yap" düğmesi.
- Yetkisiz modüller menüde "(kilitli)" görünüyor; tıklanınca "Erişim engellendi" sayfası açılıyor.
- Kullanıcılar sayfası (yalnızca Yönetici).
- Panelde modül başına "Erişim" sütunu.
- Akış: çıkış → giriş ekranı → tekrar giriş.

**Testler:** 19 yeni test (`tests/test_kimlik.py`). Toplam 38 test, hepsi geçiyor.

**Teslim — kısa güvenlik notu:** [docs/Guvenlik-Notu.md](../Guvenlik-Notu.md)

## Haftalık kontrol kriterleri

- [x] Parola düz metin saklanmıyor (`test_parola_duz_metin_saklanmaz`, `test_ayni_parola_farkli_tuz_farkli_hash`)
- [x] Yetkisiz erişim engelleniyor (`YetkiTestleri`, ekran: `hafta-05-depo-yetkisiz-erisim.png`)
- [x] Oturum/token doğru yönetiliyor (çıkış sonrası, süre dolunca ve uydurma token'la erişim reddediliyor)

## Gösterilecek ilerleme (demo sırası)

1. `python -m backend.data.kurulum --sifirla --ornek-veri` → 002 migration'ı, test kullanıcıları (yonetici / kurum1 / depo1)
2. `python main.py`
   1. Yanlış parola ile giriş → "Kullanıcı adı veya parola hatalı."
   2. "Kayıt ol" ile yeni Kurum hesabı aç, giriş yap.
   3. `depo1` ile giriş: kilitli modüle tıkla → "Erişim engellendi".
   4. `yonetici` ile giriş: Kullanıcılar sayfası.
   5. Çıkış Yap → giriş ekranına dönüş.
3. Veritabanında parolanın hash'li olduğunu göster: `SELECT kullanici_adi, parola_hash FROM kullanici;`
4. `python -m unittest` → 38 test OK

## Karşılaşılan sorunlar ve çözümler

- **Sorun:** Örnek veri aracı parola hash'i için iş katmanına bağımlı oluyordu (veri → iş, yanlış yön).
  **Çözüm:** `guvenlik.py` `backend/` seviyesine ortak yardımcı olarak taşındı.
- **Sorun:** 600.000 turluk PBKDF2 testleri yavaşlatıyordu.
  **Çözüm:** Tur sayısı hash metninin içinde saklanıyor (`pbkdf2_sha256$600000$...`). Testler daha düşük turla çalışıyor ve doğrulama, kayıttaki tur sayısını kullanıyor.
- **Sorun:** SQLite'ta bool tipi yok.
  **Çözüm:** `aktif` alanı 0/1 olarak saklanıyor, `TemelRepository` okurken bool'a çeviriyor.

## Gelecek hafta (Hafta 6)

Çekirdek Modül A — Envanter Yönetimi:
- malzeme ve kategori ekranları,
- depoya giriş/çıkış (transaction ile stok güncelleme),
- stok seviyesi ve kritik stok uyarısı,
- Depo rolü yalnızca kendi deposunu görecek.

## Ekran görüntüleri

- `docs/ekran-goruntuleri/hafta-05-giris-hatali.png`
- `docs/ekran-goruntuleri/hafta-05-depo-yetkisiz-erisim.png`
- `docs/ekran-goruntuleri/hafta-05-yonetici-kullanicilar.png`

## Yapay zekâ kullanımı özeti

Güvenli parola saklama, oturum yönetimi ve OWASP açıkları için Claude'dan araştırma ve kod önerisi alındı. Doğrulama testlerle yapıldı. Ayrıntı: [AI kullanım günlüğü](../ai-kullanim-gunlugu.md) (Kayıt 7–9).
