# 5. Öğrenci Öz Değerlendirme Formu

| Öğrenci | Numara | Proje (Kod/Ad) | Tarih |
|---|---|---|---|
| İhsan Katkat | 251161036 | P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım | 09.10.2026 |

---

## Hafta 3

**Bu hafta tamamladığım işler:**
Projenin temelini attım. Python'u ve Git'i kurdum, projeyi backend ve frontend diye iki ana klasöre böldüm. ER diyagramını ve mimari şemayı çıkardım, GitHub'da depoyu açtım. Uygulama şu an boş da olsa açılıyor, menüden modüllere tıklanınca hangi hafta yapılacağı yazıyor.

**Yeni öğrendiğim kavram/teknoloji:**
Katmanlı mimariyi daha önce sadece adıyla biliyordum. Arayüzün veritabanını hiç bilmemesi gerektiğini ve her şeyin servis üzerinden gitmesinin nedenini bu hafta anladım. N-N ilişkinin neden ara tabloyla çözüldüğünü de bağış–malzeme örneğinde oturttum.

**Yapay zekâdan nerede ve nasıl yararlandım:**
Mimari, klasör yapısı ve ER diyagramı için Claude'dan öneri aldım; iskelet kodu da büyük ölçüde onunla yazıldı. Teknolojiyi (Python masaüstü) ve depoyu frontend/backend olarak ayırmayı ben istedim. Ayrıntılar AI günlüğünde (Kayıt 1–3).

**En çok zorlandığım nokta ve nasıl aştım:**
Bilgisayarımda hiçbir geliştirme aracı kurulu değildi, Git'i de ilk kez kurdum. GitHub'a yüklerken kullanıcı adını yanlış girdiğim için depo bulunamadı hatası aldım. Doğru kullanıcı adını yazınca sorun çözüldü.

**Kendi kodumu açıklama düzeyim (1–5) ve gerekçesi:** 3
Klasör yapısını ve ER'deki ilişkileri anlatabiliyorum. Tkinter tarafındaki bazı ayrıntıları (pack, Treeview ayarları) henüz tam oturtmadım.

**Bir sonraki adım için planım:**
ER diyagramını veritabanına dökmek, tabloları ve kısıtları kurmak.

---

## Hafta 4

**Bu hafta tamamladığım işler:**
Veritabanını kurdum: 11 tablo, yabancı anahtarlar, CHECK ve UNIQUE kısıtları, indeksler. Örnek verilerle doldurdum, her tablo için ekle/getir/güncelle/sil işlemlerini yazdım. Ana panelde artık veritabanından gelen sayılar görünüyor.

**Yeni öğrendiğim kavram/teknoloji:**
Migration mantığı, ON DELETE RESTRICT ile CASCADE farkı, transaction (ya hep ya hiç) ve parametreli sorgunun SQL injection'ı nasıl engellediği. SQLite'ta yabancı anahtar kontrolünün varsayılan olarak kapalı olması beni şaşırttı.

**Yapay zekâdan nerede ve nasıl yararlandım:**
Şema, repository sınıfları, örnek veri ve testler Claude ile yazıldı. Sonuçları demo komutunu çalıştırarak kontrol ettim; kısıtların gerçekten hata verdiğini gördüm. Ayrıntılar AI günlüğünde (Kayıt 4–6).

**En çok zorlandığım nokta ve nasıl aştım:**
Ortak repository sınıfının (TemelRepository) tüm tablolar için nasıl tek kodla çalıştığını anlamak biraz zaman aldı. Sözlü hazırlık notlarından ve kodu satır satır okuyarak çözmeye çalışıyorum.

**Kendi kodumu açıklama düzeyim (1–5) ve gerekçesi:** 3
SQL kısmını ve kısıtları rahat anlatıyorum. TemelRepository'deki tip dönüşümü kısmını daha çok çalışmam gerekiyor.

**Bir sonraki adım için planım:**
Kullanıcı kaydı, giriş ve rol bazlı yetkilendirme.

---

## Hafta 5

**Bu hafta tamamladığım işler:**
Kayıt ve giriş ekranlarını ekledim. Parolalar tuzlanıp hash'lenerek saklanıyor; 5 yanlış denemede hesap 5 dakika kilitleniyor. Üç rol var: Yönetici, Kurum ve Depo. Her rol yalnızca kendi modüllerini açabiliyor. Yetki kontrolü sadece arayüzde değil, backend'de de yapılıyor.

**Yeni öğrendiğim kavram/teknoloji:**
Kimlik doğrulama ile yetkilendirmenin farkı, hash ile şifreleme arasındaki fark, salt'ın ne işe yaradığı, oturum token'ı ve neden token'ın veritabanında düz saklanmadığı.

**Yapay zekâdan nerede ve nasıl yararlandım:**
Güvenli parola saklama yöntemlerini (PBKDF2) ve yaygın güvenlik açıklarını Claude'a sordum; kimlik servisi ve giriş ekranı onunla birlikte yazıldı. Testlerle düz metin parola kalmadığını ve yetkisiz erişimin engellendiğini doğruladım. Ayrıntılar AI günlüğünde (Kayıt 7–9).

**En çok zorlandığım nokta ve nasıl aştım:**
Giriş penceresinden ana pencereye geçiş ve çıkış yapınca tekrar giriş ekranına dönme akışı. main.py'deki döngüyle çözüldü.

**Kendi kodumu açıklama düzeyim (1–5) ve gerekçesi:** 3
Hash, salt ve rol kontrolünü anlatabiliyorum. Hesap kilitleme ve oturum süresi kısmını tekrar etmem lazım.

**Bir sonraki adım için planım:**
Envanter modülü: malzeme ve kategori ekranları, depoya giriş-çıkış, stok seviyesi.

---

## Hafta 6

**Bu hafta tamamladığım işler:**
Envanter modülünü bitirdim. Depoya giriş, çıkış, sayım düzeltmesi ve kritik seviye artık ekrandan yapılabiliyor. Her işlem hareket geçmişine düşüyor; kim yaptı, ne zaman yaptı, neden yaptı görünüyor. Depo görevlisi sadece kendi deposunu görüyor. Malzeme ve kategori ekleme yalnızca yöneticide.

**Yeni öğrendiğim kavram/teknoloji:**
Anlık stok ile hareket geçmişini ayrı tutmanın mantığı, iki kaydı tek transaction'da yazmak, iş kuralı ile basit doğrulama arasındaki fark. Bir de Python'un Türkçe "I/ı" harfini yanlış küçülttüğünü öğrendim.

**Yapay zekâdan nerede ve nasıl yararlandım:**
Veri modeli, iş kuralları, testler ve ekran Claude ile yazıldı. Kuralları afet deposu senaryosuna göre birlikte seçtik (örneğin battaniye kesirli olamaz). Ekranı kendi hesaplarımla açıp denedim. Ayrıntılar AI günlüğünde (Kayıt 10–12).

**En çok zorlandığım nokta ve nasıl aştım:**
Eski veritabanındaki stokların hareket kaydı yoktu ve "stok = hareket toplamı" kuralı bozuluyordu. Migration'a açılış hareketi ekleyerek çözdük.

**Kendi kodumu açıklama düzeyim (1–5) ve gerekçesi:** 3
Stok çıkışının adım adım nasıl çalıştığını ve neden tek transaction olduğunu anlatabiliyorum. Ekran kodundaki pencere ve sekme ayrıntılarına daha çok çalışmam lazım.

**Bir sonraki adım için planım:**
Bağış girişi ve ihtiyaç eşleştirme. Bağışlar stoğa envanterin giriş yolundan girecek.

---

## Hafta 7

**Bu hafta tamamladığım işler:**
Bağış girişi ve ihtiyaç eşleştirmeyi bitirdim. Bağışçı ve kalemler girilince malzeme depoya stok olarak giriyor. İhtiyaç sayfasında talepler öncelik sırasıyla geliyor; seçince en yakın depodan başlayan bir öneri çıkıyor. Stok yetmezse ne kadar eksik kaldığını gösteriyor. Dağıtımlar Planlandı → Yolda → Teslim edildi diye ilerliyor, talebin durumu da kendiliğinden güncelleniyor.

**Yeni öğrendiğim kavram/teknoloji:**
Türetilmiş veri (talep durumunu saklamak yerine hesaplamak), rezerve stok, iki koordinat arası mesafe (Haversine) ve bir modülün başka bir modülün servisini kendi transaction'ı içinde kullanması.

**Yapay zekâdan nerede ve nasıl yararlandım:**
Veri modeli, iş kuralları, testler ve ekranlar Claude ile yazıldı. "Stok ne zaman düşmeli?", "talep durumu elle mi tutulmalı?" gibi kararları birlikte tartışıp verdik. Ekranları gerçek verinin kopyasında denedim. Ayrıntılar AI günlüğünde (Kayıt 14–16).

**En çok zorlandığım nokta ve nasıl aştım:**
Bir bağışın birden çok kalemi stoğa eklerken Envanter her kalemi ayrı kaydediyordu; bir kalem hatalı olsa öncekiler kalırdı. Envanter'e transaction açmayan bir yol ekleyip bağışın tamamını tek transaction'da yaptık.

**Kendi kodumu açıklama düzeyim (1–5) ve gerekçesi:** 3
Eşleştirme önerisinin adımlarını, fazla/eksik kurallarını ve stoğun neden "Yolda"da düştüğünü anlatabiliyorum. Ekran kodundaki öneri tablosunun güncellenme ayrıntılarına daha çok çalışmam lazım.

**Bir sonraki adım için planım:**
Vize haftası: modülleri uçtan uca deneyip hataları gidermek, ara sürümü etiketlemek, demo senaryosunu hazırlamak.
