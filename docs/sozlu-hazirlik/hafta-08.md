# Hafta 8 Sözlü Sınav Hazırlığı — VİZE: Ara Sürüm, Entegrasyon

> **Temel ilke (kılavuz):** Açıklayamadığım kod başarılı sayılmaz. Değerlendirilen, kodu kimin yazdığı değil, benim ona ne kadar hâkim olduğum.
> Sözlü genişten dara üç aşamada ilerler: **(1) genel kavrayış → (2) modül düzeyi → (3) satır düzeyi ve değiştirme.** Bu belge de aynı sırayla hazırlandı.

---

## Haftanın 5 sorusu

### 1) Şu ana kadarki mimarini özetle. (1 dakikalık cevap)
- **Ne:** Afet bağışlarını depolarda stok olarak tutan, ihtiyaç noktalarının taleplerini en yakın depodan karşılayan ve dağıtımı izleyen bir Python masaüstü uygulaması.
- **Katmanlar:** Sunum (Tkinter, **frontend deposu**) → İş (`backend/services`) → Veri erişim (`backend/data`, repository'ler) → SQLite. Ayrıca varlık katmanı (`backend/models`, dataclass'lar). Bağımlılık tek yönlü: alt katman üstü tanımaz.
- **Modüller:** Kimlik/yetki (H5), Envanter (H6), Bağış ve Eşleştirme/Dağıtım (H7). Her biri bir servis sınıfı.
- **İki depo:** Backend kurulabilir bir paket (`pyproject.toml`); frontend onu `requirements.txt` ile **etiketli sürümden** (`@v0.6.0`) kuruyor.
- **Neden?** Test edilebilirlik: kurallar pencere açmadan test ediliyor (101 test). Sorumluluk ayrımı: SQL yalnızca veri katmanında, kural yalnızca serviste. Arayüz değişse iş kuralları değişmez.
- **Alternatif:** Tek dosyada Tkinter + SQL. Hızlı başlardı ama her ekran kendi kuralını yazardı ve test edilemezdi.

### 2) Hangi modül hangi veriyi nereden alıyor?
| Modül | Yazdığı | Nereden alıyor |
|---|---|---|
| Kimlik | kullanici, oturum, rol_degisikligi | — (herkes ona soruyor: `modul_erisimi(token, modül)`) |
| Envanter | stok, stok_hareketi, malzeme, kategori | Kimlik'ten kullanıcı + rol + depo; dağıtım kalemlerinden **rezerve** (H8) |
| Bağış | bagisci, bagis, bagis_kalemi | Stoğu Envanter'in `stok_hareketi_uygula` metoduyla artırıyor |
| Eşleştirme/Dağıtım | ihtiyac_talebi, dagitim, dagitim_kalemi | Envanter'den stok; depo/nokta koordinatlarından mesafe; "Yolda"da Envanter'den çıkış |
| Panel | — | Talep durumları, kritik stok, modül planı |

**Kural:** Bir modül başka bir modülün tablosunu SQL ile **değiştirmez**, servis metodunu çağırır. Stok yalnızca Envanter'den değişir. Bu yüzden "stok = hareketlerin toplamı" her kaynakta korunuyor.

### 3) En çok zorlandığın entegrasyon neydi, nasıl çözdün?
**Rezerve stok ile Envanter çıkışının çakışması.** Hata ayıklama adımlarım:
1. **Belirti:** Entegrasyon testinde, planlanmış dağıtım "Yola Çıkar" adımında *yetersiz stok* hatası aldı.
2. **Hipotez:** Arada biri stoğu azaltmış olmalı. Eşleştirme rezerveyi hesaba katıyordu ama Envanter'in Stok Çıkışı katmıyordu.
3. **İzole etme:** Kuru gıdadan 180 koli planla, sonra depo görevlisiyle 200 koli çıkış yap. Çıkış kabul edildi (280 → 80). Dağıtım 180 isteyince 80 kaldığı için K1 hatası.
4. **Düzeltme:** `stok_cikisi` artık *serbest = stok − rezerve*'yi aşan çıkışı reddediyor (**K9**). Ekranda **Rezerve** sütunu ve çıkış penceresinde "rezerve 180, serbest 100" bilgisi var.
5. **Doğrulama:** `test_hata1_rezerve_stok_envanterden_cikarilamaz` regresyon testi: 200 reddedilir, 100 kabul edilir, dağıtım yola çıkar, sonunda stok = rezerve = 0.

İkinci hata: **K7** yalnızca stok/hareket tablosuna bakıyordu. Sadece bir talepte geçen malzemenin birimi "adet"ten "paket"e değiştirilebiliyordu; talebin anlamı bozulurdu. Şimdi bağış, talep ve dağıtım kalemlerine de bakıyor (`test_hata2_...`).

### 4) Yapay zekâdan aldığın bir kod parçasını satır satır açıkla.
Aşağıdaki **Aşama 3** bölümünde: `EnvanterServisi.stok_cikisi` (H8 düzeltmesi) ve `stok_hareketi_uygula` (H7 entegrasyon yolu).

### 5) Bir sonraki aşamanın planı nedir?
| Hafta | Plan | Hazır olan ön koşul |
|---|---|---|
| 9 | Harita/rota API: depo → ihtiyaç noktası gerçek yol mesafesi ve süresi; API anahtarı ortam değişkeninde; zaman aşımı/hata durumunda Haversine'e geri dönüş | Koordinatlar, `HARITA_API_ANAHTARI`, "Kısmen" durumdaki Rota modülü |
| 10 | YZ: dağıtım önceliği ve rota önerisi (LLM); kural tabanlı öneriyle karşılaştırma | Öncelik, talep tarihi, stok verisi |
| 11 | Takip: bağıştan teslime izlenebilirlik | Hareket açıklamalarında "Bağış #", "Dağıtım #" bağlantıları |
| 12 | Şeffaflık raporu, kritik stok bildirimi | Stok–Talep Dengesi, kritik seviye |
| 13–15 | Test kapsamı, dokümantasyon, paket, final `v1.0.0` | 106 test, CHANGELOG, etiketleme düzeni |

---

## Aşama 1 — Genel kavrayış: bir işlem hangi modülden hangisine gidiyor?

**Örnek: "Yola Çıkar" düğmesi**
1. `ihtiyac_sayfasi.py`: düğme → `EslestirmeServisi.dagitim_durumu_degistir(token, id, YOLDA)`.
2. `_yetki` → `KimlikServisi.modul_erisimi`: oturum geçerli mi, rol "dagitim" modülüne girebilir mi? Kontrol backend'de; menüdeki kilit yalnızca kolaylık.
3. `GECISLER` sözlüğü: Planlandı → Yolda izinli mi? (E7)
4. `with islem(...)`: her kalem için `EnvanterServisi.stok_hareketi_uygula(..., ÇIKIŞ, -miktar)` → K1 kontrolü, stok güncellenir, hareket yazılır.
5. Dağıtımın durumu kaydedilir, bağlı talebin durumu yeniden hesaplanır (E8).
6. Bir kalem bile başarısız olursa `islem` ROLLBACK yapar: ne durum ne stok değişir.

## Aşama 2 — Modül düzeyi: kararlar ve gerekçeleri

| Karar | Neden | Alternatif ve neden seçmedim |
|---|---|---|
| Stok "Yolda"da düşer, planlamada değil | Planlanan malzeme fiziksel olarak hâlâ depoda; sayımda bulunur | Planlamada düşürmek: sayım ile kayıt tutmazdı, iptalde de sahte iade hareketi gerekirdi |
| Rezerve ayrı tabloda tutulmaz, sorguyla hesaplanır | Aynı bilgi iki yerde olursa çelişebilir | `stok.rezerve` kolonu: daha hızlı ama her durum değişikliğinde iki yeri güncellemek gerekir |
| Talep durumu türetilmiş veri | Dağıtımlarla çelişemez | Elle durum: H7'de çelişki yaşandı (yolda olan kuru gıda "Bekliyor" görünüyordu) |
| Yetki serviste | Arayüzü atlayan biri (ör. test, betik) de kurala takılır | Yalnızca menüyü kilitlemek: kılavuzdaki "sık hata" |
| Tek transaction (`islem`) | Yarım bağış veya yarım dağıtım olmasın | Her kalemi ayrı kaydetmek: hata olunca önceki kalemler kalırdı |
| Etiketli sürüm + `@v0.6.0` pin | Sınavda kurulan kod etiketin aynısı; sonraki haftanın değişikliği vize sürümünü bozmaz | `@main`: her `pip install` en son kodu getirir, vize sürümü tekrar üretilemez |

**Kullanılan kütüphaneler:** `sqlite3` (bağlantı, `execute`, `Row`), `dataclasses` (varlıklar), `hashlib.pbkdf2_hmac` + `secrets` (parola, token), `math` (Haversine, `floor`), `tkinter.ttk` (Treeview, Notebook), `unittest` + `subprocess` (testler).

## Aşama 3 — Satır düzeyi: AI ile yazılan kodu açıklama

### A) `EnvanterServisi.stok_cikisi` — K9 düzeltmesi (`backend/services/envanter_servisi.py`)

```python
def stok_cikisi(self, token, depo_id, malzeme_id, miktar, aciklama=""):
    kullanici = self._kullanici(token)                     # 1
    self._depo_kontrol(kullanici, depo_id)                 # 2
    malzeme = self._malzeme(malzeme_id)                    # 3
    miktar = self._miktar(miktar, malzeme)                 # 4
    stok = self._stoklar.getir(depo_id, malzeme_id)        # 5
    rezerve = DagitimKalemiRepository(self._baglanti).rezerve(depo_id, malzeme_id)   # 6
    serbest = max(round((stok.miktar if stok else 0) - rezerve, 3), 0)               # 7
    if rezerve and miktar > serbest:                       # 8
        raise DogrulamaHatasi(f"... rezerve ... en fazla {serbest:g} ...")           # 9
    return self._hareket_yaz(kullanici, depo_id, malzeme, HareketTuru.CIKIS, -miktar, aciklama)  # 10
```

| Satır | Ne yapar |
|---|---|
| 1 | Token'dan kullanıcıyı bulur, Envanter modülüne yetkisi var mı bakar (Kurum → `YetkisizErisim`). |
| 2 | Depo rolündeyse yalnızca kendi deposu (K5). |
| 3 | Malzeme yoksa hata; varsa birimini öğreniriz (tam sayı kuralı için). |
| 4 | "12,5" gibi metni sayıya çevirir; > 0, ≤ 100.000, adet/koli/paket ise tam sayı (K2, K3). |
| 5 | Depodaki stok satırı; hiç yoksa `None`. |
| 6 | Bu depoda bu malzemeden **Planlandı** durumundaki dağıtımlara ayrılan toplam (SQL `SUM`, `COALESCE` ile boşsa 0). |
| 7 | Serbest miktar. `round(..., 3)`: kesirli kg/litre için kayan nokta hatası (0.30000000004) olmasın. `max(..., 0)`: sayım stoğu rezervenin altına düşürdüyse eksi göstermesin. |
| 8 | Rezerve varsa ve istenen serbesti aşıyorsa... |
| 9 | ...kullanıcının ne yapacağını da söyleyen hata. Pencere kapanmaz, mesaj kırmızı görünür. |
| 10 | Asıl çıkış: transaction içinde stok güncellenir ve hareket yazılır; K1 orada da kontrol edilir. |

**"Bu satırı silsen ne olur?"**

| Değişiklik | Sonuç |
|---|---|
| 6–9 silinir | H8 hatası geri gelir: rezerve stok çıkar, dağıtım "Yolda"da *yetersiz stok* alır. `test_hata1` kırmızı olur. |
| 8'de `rezerve and` silinir | Rezerve yokken de kontrol çalışır. Sonuç aynı; mesaj farklı olur ("…0 rezerve…" yerine K1'in "Yetersiz stok" mesajı daha anlamlı). Bu yüzden koşulda duruyor. |
| 7'de `max(…, 0)` silinir | Sayım 10'a düşürüp rezerve 40 ise serbest −30 görünür; mesaj "en fazla −30 çıkış" der. Davranış yine reddeder ama mesaj saçma olur. |
| 4 ile 5 yer değiştirir | Sonuç değişmez; ancak 4 hatalı girdi için önce hata vermeli ki boşuna sorgu yapılmasın. |
| 10'da `-miktar` yerine `miktar` | Çıkış stoğu artırır; ayrıca veritabanındaki CHECK (çıkış negatif olmalı) INSERT'i reddeder. |

**İzini sür:** Bingöl'de kuru gıda 280, rezerve 180. `stok_cikisi(..., "200")` → miktar 200, serbest 100, 200 > 100 → hata. `"100"` → kabul, stok 180. Sonra dağıtım yola çıkınca 180 − 180 = 0.

**Yeniden yaz (alternatif):** Kontrolü `_hareket_yaz`'ın içine koymak da mümkündü; ama o metodu sayım düzeltmesi de kullanıyor, sayım gerçeği yazar ve engellenmemeli. Bu yüzden kural yalnızca çıkışta.

### B) `EnvanterServisi.stok_hareketi_uygula` — modüllerin ortak stok yolu

```python
stok = self._stoklar.getir(depo_id, malzeme.id) or Stok(depo_id, malzeme.id, 0, 0)   # 1
onceki = stok.miktar                                                                 # 2
sonraki = round(onceki + degisim, 3)                                                 # 3
if sonraki < 0:                                                                      # 4  K1
    raise DogrulamaHatasi("Yetersiz stok: ...")
stok.miktar = sonraki                                                                # 5
self._stoklar.kaydet(stok)                                                           # 6
return self._hareketler.ekle(StokHareketi(depo_id, malzeme.id, tur, degisim, onceki, sonraki, aciklama.strip(), kullanici.id))  # 7
```
- **1:** Depoda bu malzeme hiç yoksa (ilk bağış) sıfır stoklu yeni satır oluşturur. `or` olmasa `None.miktar` hatası olurdu.
- **3–4:** Değişim eksi (çıkış) olabilir; sonuç sıfırın altına inerse reddeder.
- **6–7:** Stok ve hareket aynı transaction'da. **Transaction açmaz**; çağıran (Bağış, Dağıtım) açar. Böylece 3 kalemli bir bağışın tamamı ya da hiçbiri yazılır.
- **Silsen ne olur?** 4 silinirse stok eksiye düşmeye çalışır, veritabanı CHECK'i de reddeder ama mesaj teknik olur. 7 silinirse stok değişir ama geçmiş tutulmaz; "stok = hareket toplamı" testi kırmızı olur.

### C) `EslestirmeServisi.oneri` — kısa izleme
Kiğı'nın 100 paket hijyen kiti talebi: adaylar `uygun_stok > 0` olan depolar. Bağıştan sonra Bingöl 40 (48,9 km), Genç 90 (64,7 km). Mesafeye göre sıralanır. Döngü: Bingöl `min(40, 100) = 40`, kalan 60; Genç `min(90, 60) = 60`, kalan 0. `math.floor` paket kesirli olmasın diye. `sort` satırı silinirse daha uzak depo önce önerilebilir.

---

## Teorik kavramlar
- **Entegrasyon:** Ayrı yazılan modüllerin birlikte doğru çalışması. **Entegrasyon testi** modülleri birlikte dener; birim testi tek bir parçayı dener. Benim hatam iki modülün sınırındaydı ve birim testleri bunu göremezdi.
- **Sürümleme (semantic versioning):** `MAJOR.MINOR.PATCH`. Hafta başına yeni özellik = MINOR (0.5 → 0.6), yalnızca hata düzeltmesi = PATCH (0.4.1, 0.4.2), 1.0.0 = final. Etiket (`git tag -a v0.6.0`) commit'e kalıcı bir ad verir; `git checkout v0.6.0` vize kodunu geri getirir.
- **Regresyon:** Düzeltilmiş bir hatanın sonraki değişiklikle geri gelmesi. Önlem: her düzeltilen hata için o hatayı yeniden üreten bir test.

## Sık yapılan hatalar (bende olmamalı)
| Hata | Bendeki önlem |
|---|---|
| Entegrasyonu son ana bırakmak | H7'den itibaren modüller servis üzerinden bağlandı; H8'de uçtan uca test ve demo |
| Ara sürümü etiketlememek | `v0.6.0` etiketi (iki depo), CHANGELOG, frontend `@v0.6.0`'a sabit |
| Açıklanamayan AI kodu taşımak | Bu belgedeki satır satır açıklamalar; AI günlüğünde her kayıt için "açıklayabiliyor muyum: E" |

## Soru bankası (kılavuz 3.1–3.6) — kısa cevaplar

| Soru | Cevabım |
|---|---|
| En kritik modül hangisi? | **Envanter.** Bağış ve dağıtım stoğu onun yolundan değiştiriyor; orada bir hata her modülü bozar (H8 hatası da oradaydı). |
| ER'de hangi ilişkiler var? | Depo 1–N stok, malzeme 1–N stok (stok, depo–malzeme N–N'in ara tablosu; birincil anahtar `(depo_id, malzeme_id)`). Bağış 1–N kalem, dağıtım 1–N kalem, talep 1–N dağıtım kalemi. |
| Neden indeks? | Sık filtrelenen alanlar: `stok_hareketi(depo_id, malzeme_id)`, talep durumu. Okuma hızlanır, yazma biraz yavaşlar. |
| Referans bütünlüğü? | `FOREIGN KEY` + `PRAGMA foreign_keys=ON`; hareketi olan kullanıcı/malzeme silinemez (RESTRICT), kalemler başlıkla silinir (CASCADE). |
| Parolayı nasıl sakladın? | PBKDF2-SHA256, 600.000 tur, kullanıcıya özel tuz. Düz metin yok; özet tek yönlü. |
| Oturum mu token mı? | Rastgele token; veritabanında yalnızca SHA-256 özeti. 8 saat süre, çıkışta ve rol değişince geçersiz. |
| Yetkisiz erişim? | Her servis metodu `modul_erisimi` ile başlıyor; Depo rolüne ek olarak depo sahipliği. Arayüzde gizlemek yetmez. |
| Hangi senaryoları test ettin? | Mutlu yol (uçtan uca akış) + sınırlar (0, eksi, 100.000 üstü, 2,5 battaniye) + hata durumları (yetersiz stok → rollback, yetkisiz rol, süresi dolmuş oturum). |
| Bir hatayı nasıl ayıkladın? | Belirti → hipotez → izole et → düzelt → doğrula (Soru 3'teki K9 örneği). |
| Commit stratejin? | Küçük ve tek amaçlı: `backend:`, `frontend:`, `test:`, `fix:`, `docs:` önekleri; her hafta ayrı dal, sonra main'e merge; gizli veri yok (`.env` gitignore'da). |
| API / LLM soruları | Henüz yok (H9–H10). Plan: anahtar ortam değişkeninde (`.env.example` hazır), zaman aşımı ve hata olursa Haversine/kural tabanlı öneriye geri dönüş. |

## Kırmızı bayraklara karşı kendi kontrolüm
- Kodda kullanılmayan blok yok; her servis metodu bir ekranda ya da testte kullanılıyor.
- Adlandırma tek üslupta (Türkçe, `snake_case`); sınıflar `...Servisi`, `...Repository`.
- AI günlüğü ile kod tutarlı: Kayıt 17–18 bu haftanın değişikliklerini anlatıyor.
- Hazır ileri desen yok; yalnızca standart kütüphane.
