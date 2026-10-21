# Hafta 6 Sözlü Sınav Hazırlığı — Envanter Yönetimi

## 1) Envanteri nasıl modelledin?
İki tablo var:
- **`stok`**: Hangi depoda hangi malzemeden şu an ne kadar olduğu. Anahtar `(depo_id, malzeme_id)` ikilisi, yani bir depoda bir malzemenin tek satırı olabilir. Kritik seviye de burada.
- **`stok_hareketi`**: Stoğu değiştiren her işlemin kaydı (giriş, çıkış, sayım, açılış).

Malzeme tanımı (`malzeme` → `kategori`) depodan bağımsız; bütün depolar aynı kataloğu kullanıyor. Envanter ekranında depoda hiç olmayan malzemeler de 0 miktarla görünüyor (LEFT JOIN). Böylece yeni bir malzemenin ilk girişi de oradan yapılabiliyor.

## 2) Stok hareketini nasıl kaydettin?
Her hareket `stok_hareketi` tablosuna yeni bir satır olarak ekleniyor ve hiç silinmiyor. Satırda şunlar var: tür, değişim (+/−), önceki miktar, sonraki miktar, açıklama, işlemi yapan kullanıcı ve tarih. Böylece "bu malzeme neden 80?" sorusunun cevabı hep kayıtlı.

Kritik nokta: stok güncellemesi ve hareket kaydı **aynı transaction** içinde yazılıyor (`_hareket_yaz` → `with islem():`). Biri başarısız olursa ikisi de geri alınıyor; bu yüzden "stok = hareketlerin toplamı" her zaman doğru kalıyor (`test_K8_...`). Ayrıca veritabanı kendisi de kontrol ediyor: `sonraki = önceki + değişim` değilse ya da çıkışın değişimi pozitifse kaydı reddediyor.

Hafta 6'dan önceki stoklar için migration bir "Açılış" hareketi yazıyor. Böylece kural eski veride de bozulmuyor.

## 3) Bu modülün verisini nasıl modelledin?
- **Varlıklar:** `StokHareketi` (dataclass) ve `HareketTuru` (enum: Açılış, Giriş, Çıkış, Sayım).
- **Veritabanında:** `CHECK` kısıtlarıyla tür ve işaret uyumu, sonraki miktarın eksi olmaması ve `sonraki = önceki + değişim` eşitliği.
- **İlişkiler:** Depo, malzeme ve kullanıcıya yabancı anahtarlarla bağlı, hepsi `RESTRICT`. Geçmişi olan malzeme, depo ya da kullanıcı silinemiyor, çünkü denetim kaydı bozulmamalı.
- **İndeks:** `(depo_id, malzeme_id, tarih)` üzerinde. Hareket geçmişi ekranı tam olarak bu üç alana göre filtreleyip sıralıyor.

**Ekranda gösterilen durum hesaplanıyor, saklanmıyor:** miktar 0 ise "Tükendi", kritik seviyenin altındaysa "Kritik", değilse "Normal" (`StokSatiri.durum`).

## 4) Bu modülde hangi iş kuralını neden koydun?
En önemlileri (tamamı `docs/Envanter.md` dosyasında, K1–K8):
- **K1 — Stok eksiye düşemez:** Olmayan malzeme dağıtılamaz. Servis "Yetersiz stok: depoda 148 koli var, 500 istendi" diyor. Veritabanı da `CHECK (miktar >= 0)` ile engelliyor.
- **K2 — Birime göre tam sayı:** 2,5 battaniye olmaz ama 2,5 kg olur.
- **K4 — Sayımda açıklama zorunlu:** Fark neden oluştu (hasar, kayıp, sayım hatası)? Belgelenmezse hesap verilemez.
- **K5 — Sahiplik:** Depo görevlisi yalnızca kendi deposunu görebiliyor ve değiştirebiliyor. Bu, PDF'teki "erişim/sahiplik kontrolünü unutmak" hatasına karşı.
- **K7 — Geçmişi olan malzemenin birimi değişmez:** "koli" → "adet" yapılırsa eski 150 koli kaydı 150 adet gibi okunur, rapor bozulur.

Kuralların hepsi **backend'de** (`EnvanterServisi`); arayüz yalnızca hatayı gösteriyor. Bu yüzden her kural pencere açmadan test edilebiliyor.

## 5) Bu modülü diğer modüllerle nasıl entegre ettin?
- **Hafta 5 ile:**
  - Her metot `modul_erisimi(token, "envanter")` ile başlıyor: oturum geçerli mi, rol yetkili mi? Kurum rolü envantere giremiyor.
  - `kullanici.depo_id` sahiplik kontrolünde kullanılıyor.
  - Hareketlere işlemi yapan kullanıcı kaydediliyor.
- **Hafta 4 ile:** Mevcut `stok`, `malzeme` ve `kategori` tabloları ve repository'leri kullanıldı. Yeni tablo `003` migration'ıyla geldi; eski veri silinmedi.
- **Ana panel:** Kritik stok kartı Depo görevlisi için yalnızca kendi deposunu sayıyor.
- **Hafta 7'ye hazırlık:** Bağış kaydı stoğu kendi başına değiştirmeyecek; Envanter'in giriş yolunu (`_hareket_yaz`) çağıracak. Dağıtım da çıkış yolunu kullanacak. Böylece stok tek bir yerden ve aynı kurallarla değişecek.

**İki depo açısından:** Kurallar backend paketinde, ekran frontend deposunda. Frontend yalnızca `EnvanterServisi`'ni çağırıyor.

---

## Teorik kavramlar (kısa)
- **Veri modeli:** Tablolar, alanlar ve ilişkiler. Burada anlık durum (`stok`) ile hareket geçmişi (`stok_hareketi`) ayrı tutuluyor.
- **İş kuralı / doğrulama:** Doğrulama, verinin biçimce doğru olup olmadığına bakar (sayı mı, boş mu?). İş kuralı, işlemin mantıkça doğru olup olmadığına bakar (stok yeterli mi, bu depo senin mi?). İkisi de serviste; kritik olanlar ayrıca veritabanında.
- **Modülerlik:** Her modül kendi servisinde (`EnvanterServisi`). Diğer modüller stoğu doğrudan SQL ile değil bu servisin yoluyla değiştiriyor.

## Sık yapılan hatalar (bende olmamalı)
| Hata | Bendeki önlem |
|---|---|
| Doğrulamayı atlamak | Miktar, birim, açıklama ve stok yeterliliği serviste ve veritabanında kontrol ediliyor |
| Erişim/sahiplik kontrolünü unutmak | Rol (K6) ve depo sahipliği (K5) backend'de; testleri var |
| İlişkili kayıtları yönetmemek | Stok + hareket tek transaction'da (K8); geçmişi olan malzeme silinmiyor (K7) |

## Olası ek sorular
- **Stoğu neden hareketlerden hesaplamıyorsun, ayrı tutuyorsun?** Her ekranda binlerce hareketi toplamak yavaş olur. Ayrı tutup aynı transaction'da güncelliyorum, eşitliği de testle doğruluyorum.
- **İki kişi aynı anda çıkış yaparsa?** SQLite yazma işlemlerini sırayla yapar. İkinci işlem güncel miktarı okur ve yetersizse K1 devreye girer. Çok kullanıcılı sunucu sürümünde `UPDATE ... WHERE miktar >= ?` gibi atomik bir güncelleme kullanırdım.
- **Neden `lower()` değil de `tr_kucuk()`?** Python'un `lower()` fonksiyonu "I"yı "i" yapar, oysa Türkçede "ı" olmalı. Yoksa "GIDA" ile "Gıda" farklı sayılırdı; bu hatayı testte yakaladım.
