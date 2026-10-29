# Hafta 7 Sözlü Sınav Hazırlığı — Bağış Girişi ve İhtiyaç Eşleştirme

## 1) Bağış–ihtiyaç eşleştirmesini nasıl yaptın?
Bağışlar önce depolara stok olarak giriyor. Eşleştirme, bu stok ile ihtiyaç noktalarının taleplerini buluşturuyor:
1. **Sıra:** Açık talepler ihtiyaç noktasının önceliğine göre (Kritik önce), sonra talep tarihine göre listeleniyor.
2. **Kalan:** Seçilen talep için *kalan = talep − karşılanan* hesaplanıyor. Karşılanan, iptal edilmemiş dağıtımlarda bu talebe bağlı kalemlerin toplamı.
3. **Uygun stok:** Her depo için *uygun stok = stok − rezerve* hesaplanıyor. Rezerve, planlanmış ama yola çıkmamış miktar.
4. **Öneri:** Uygun stoğu olan depolar ihtiyaç noktasına **en yakından** başlanarak sıralanıyor (koordinatlardan Haversine ile km) ve kalan dolana kadar dolduruluyor. Adet, koli ve paket birimlerinde tam sayıya yuvarlanıyor.
5. **Onay:** Kullanıcı miktarları değiştirip onaylıyor. Her depo için bir dağıtım ve talebe bağlı bir kalem oluşuyor; talep durumu yeniden hesaplanıyor.

**Neden en yakın depo?** Afet lojistiğinde hız önemli ve yakın depo daha az yakıt harcar. Gerçek yol mesafesi 9. haftada rota API'siyle, yapay zekâ önceliği 10. haftada eklenecek.

## 2) Fazla/eksik durumunu nasıl ele aldın?
- **Fazla gönderim:** Kod buna izin vermiyor.
  - E2: Atamaların toplamı talebin kalanını aşarsa "Fazla gönderim" hatası çıkıyor; bir noktaya ihtiyacından fazlası gitmiyor.
  - E3: Bir depodan, rezerve düşülmüş uygun stoktan fazlası atanamıyor; aynı battaniye iki talebe birden verilemiyor.
- **Eksik stok:** Öneri uygun stoğun tamamını kullanıyor ve **karşılanamayan miktarı** kırmızıyla gösteriyor (örnek: hijyen kiti 100 talep, 90 stok → "10 paket açıkta"). Talep *Kısmen karşılandı* olarak açık kalıyor; yeni bağış gelince tekrar eşleştiriliyor.
- **Genel görünüm:** Stok–Talep Dengesi sekmesi her malzeme için toplam uygun stok ile açık talep kalanını karşılaştırıyor (*Eksik / Dengede / Fazla / Talep yok*). En eksik malzeme en üstte; bağış kampanyası buna göre yönlendirilebiliyor.
- **Bağış tarafında fazla:** Bağış depoya stok olarak giriyor. Henüz talebi olmayan malzeme "Talep yok" olarak görünüyor ve yeni bir talep açılınca kullanılıyor.

## 3) Bu modülün verisini nasıl modelledin?
4. haftadan beri var olan tablolar kullanıldı: bağışçı, bağış, bağış kalemi, ihtiyaç noktası, ihtiyaç talebi, dağıtım, dağıtım kalemi. Bağış ve dağıtım "başlık + kalemler" yapısında, yani fatura mantığı.

Bu hafta tek bir kolon ekledim: **`dagitim_kalemi.ihtiyac_talebi_id`** (005 migration'ı). Bir dağıtım kaleminin hangi talebi karşıladığını bu kolon söylüyor. Böylece karşılanan, kalan ve talep durumu hesaplanabiliyor.

Talep durumu artık **türetilmiş bir veri**: karşılanan 0 ise Bekliyor, kısmi ise Kısmen, tamamı ise Karşılandı. Elle değiştirilmiyor, böylece dağıtımlarla çelişemiyor. Eski veride çelişki vardı (kuru gıda yolda olduğu hâlde talep "Bekliyor" görünüyordu); migration bunu düzeltti.

"Rezerve" ayrı bir tabloda değil, planlanmış dağıtım kalemlerinden hesaplanıyor; aynı bilgiyi iki yerde tutmuyorum.

## 4) Bu modülde hangi iş kuralını neden koydun?
- **B4 — Gıdada son kullanma tarihi zorunlu, süresi geçmiş ürün kabul edilmez:** Afet bölgesine bozuk gıda gitmesi sağlık riski.
- **B8 / E9 — Tek transaction:** Bir bağışın 3 kaleminden biri hatalıysa hiçbiri yazılmıyor; yarım bağış ve tutarsız stok oluşmuyor.
- **E2 — Fazla gönderim yok:** Kıt kaynak; bir noktaya fazlası giderse başka bir nokta eksik kalır.
- **E3 — Rezerve düşülmüş uygun stok:** Planlanmış ama yola çıkmamış malzeme başka talebe verilmesin.
- **E6 — Dağıtımı olan talep iptal edilemez:** Yoksa yolda olan bir sevkiyatın neden yapıldığı belirsizleşir; önce dağıtım iptal ediliyor.
- **E7 — Durum geçişleri:** "Planlandı → Teslim edildi" atlanamıyor; stok "Yolda" adımında düştüğü için o adım atlanırsa stok hiç düşmezdi.

## 5) Bu modülü diğer modüllerle nasıl entegre ettin?
- **Envanter (Hafta 6):** Bağış ve dağıtım stoğu kendi SQL'iyle değiştirmiyor; Envanter'in `stok_hareketi_uygula` metodunu kendi transaction'ının içinden çağırıyor.
  - Böylece K1 (stok eksiye düşmez) ve hareket geçmişi her kaynak için aynı. Hareket geçmişinde "Bağış #7 - ..." ve "Dağıtım #5 -> Karlıova ..." gibi açıklamalar görünüyor.
  - Miktar, birim ve depo sahipliği kuralları da Envanter'den geliyor (`miktari_dogrula`, `depo_sahipligi`); kurallar iki yerde ayrı ayrı yazılmadı.
- **Kimlik/yetki (Hafta 5):** Bağış modülü Yönetici ve Depo'ya (kendi deposu), Eşleştirme ve Dağıtım Yönetici ve Kurum'a açık; kontrol backend'de.
- **Veritabanı (Hafta 4):** Var olan tablolar ve migration sistemi kullanıldı; eski veri silinmedi, 005 ile bağlandı.
- **Panel:** "Bekleyen talep" kartı hesaplanan durumları sayıyor.
- **İki depo:** Kurallar backend paketinde (`BagisServisi`, `EslestirmeServisi`), ekranlar frontend deposunda.

---

## Teorik kavramlar (kısa)
- **Veri modeli:** Başlık–kalem yapısı; türetilmiş veri (talep durumu) ile saklanan veri (dağıtım kalemi) ayrımı.
- **İş kuralı / doğrulama:**
  - Biçim kontrolü: tarih ve telefon biçimi.
  - İş mantığı: fazla gönderim, rezerve, durum geçişleri.
- **Modülerlik:** Her modülün kendi servisi var. Modüller birbirini SQL ile değil **servis metotlarıyla** kullanıyor; stok yalnızca Envanter'den değişiyor.

## Sık yapılan hatalar (bende olmamalı)
| Hata | Bendeki önlem |
|---|---|
| Doğrulamayı atlamak | Her kalem ve atama serviste doğrulanıyor; hata hangi kalemde olduğunu söylüyor |
| Erişim/sahiplik kontrolünü unutmak | Depo görevlisi başka depoya bağış giremiyor, Depo rolü eşleştirme yapamıyor (testli) |
| İlişkili kayıtları yönetmemek | Bağış + kalemler + stok; dağıtım + kalem + stok + talep durumu hep tek transaction |

## Olası ek sorular
- **Neden stok dağıtım planlanınca değil, "Yolda" olunca düşüyor?** Planlanan malzeme hâlâ depoda fiziksel olarak duruyor; sayım yapılsa orada bulunur. Bu yüzden önce *rezerve* ediliyor, depodan çıkınca stoktan düşüyor. İptal edilirse stok hareketi gerekmiyor.
- **Haversine nedir?** Dünya'yı küre kabul ederek iki enlem/boylam arasındaki en kısa yüzey mesafesini veren formül. Yol mesafesi değil, kuş uçuşu.
- **İki kişi aynı anda aynı stoğu atarsa?** SQLite yazmaları sırayla yapar. İkinci kişinin atamasında E3 güncel rezerveyle tekrar kontrol ediliyor; yetmezse hata alıyor.
