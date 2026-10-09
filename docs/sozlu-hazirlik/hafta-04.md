# Hafta 4 Sözlü Sınav Hazırlığı

## 1) Bir tabloya neden indeks ekledin/eklemedin?
İndeks, kitabın arkasındaki dizin gibidir: sorgu tüm tabloyu satır satır taramak yerine aranan değere doğrudan gider. **Ekledim:** FK kolonlarına (`bagis_kalemi.malzeme_id` vb.) çünkü SQLite bunları otomatik indekslemiyor; hem JOIN'ler hem de "bu malzemeyi silersem ona bağlı kayıt var mı?" (RESTRICT) kontrolü bu kolonda arama yapıyor. `ihtiyac_talebi.durum` ve `dagitim.durum`'a da ekledim çünkü "bekleyen talepler", "yoldaki araçlar" sürekli sorgulanacak. **Eklemedim:** `aciklama`, `telefon` gibi hiç aranmayan kolonlara; her indeks yer kaplıyor ve her INSERT/UPDATE'te güncellenmesi gerektiği için yazmayı yavaşlatıyor. `stok(depo_id)` için ayrı indeks gereksiz, çünkü bileşik PK `(depo_id, malzeme_id)` zaten depo_id ile başlayan bir indeks.

## 2) Yabancı anahtar kısıtı ne işe yarar?
**Referans bütünlüğü** sağlar: bir tablodaki değerin, bağlı olduğu tabloda gerçekten var olmasını garanti eder. Örnek: `bagis_kalemi.malzeme_id = 99999` yazmaya çalışınca, öyle bir malzeme olmadığı için `FOREIGN KEY constraint failed` hatası alınıyor (demoda bölüm 7). Silmede ne olacağını da belirler: `RESTRICT` → stoğu olan malzeme silinemez; `CASCADE` → bağış silinince kalemleri de silinir. SQLite'ta FK kontrolü varsayılan kapalı, ben her bağlantıda `PRAGMA foreign_keys = ON` ile açıyorum.

## 3) N-N ilişkiyi nasıl modelledin?
İlişkisel veritabanında N-N doğrudan tutulamaz; araya bir **ara tablo** koyup iki adet 1-N'ye böldüm. Bir bağışta çok malzeme, bir malzeme çok bağışta → `bagis_kalemi (bagis_id FK, malzeme_id FK, miktar)`. Ara tablo ilişkiye ait bilgiyi de taşıyor (miktar, son kullanma tarihi). Diğerleri: Depo–Malzeme → `stok` (PK bileşik: depo_id + malzeme_id), Dağıtım–Malzeme → `dagitim_kalemi`, İhtiyaç noktası–Malzeme → `ihtiyac_talebi`.

## 4) Migration neden kullanılır?
Şemanın **sürüm kontrolü** içindir. Şema değişiklikleri numaralı dosyalarda (`001_ilk_sema.sql`, gelecek hafta `002_kullanici.sql`) durur ve Git'te izlenir. `sema_surumu` tablosu hangi dosyaların uygulandığını tutar; uygulama açılınca yalnızca eksik olanlar sırayla çalıştırılır. Faydaları: her bilgisayarda aynı şema oluşur, veritabanını silmeden yeni tablo eklenebilir, değişikliğin geçmişi görülür. Her migration tek transaction içinde çalışıyor, hata olursa yarım şema kalmıyor.

## 5) Bir CRUD işleminin SQL'ini açıkla.
`TemelRepository`'de (ör. malzeme için):
- **Create:** `INSERT INTO malzeme (kategori_id, ad, birim, aciklama) VALUES (?, ?, ?, ?)` → `cursor.lastrowid` ile yeni id nesneye yazılır.
- **Read:** `SELECT * FROM malzeme WHERE id = ?` → satır dataclass'a çevrilir.
- **Update:** `UPDATE malzeme SET kategori_id = ?, ad = ?, birim = ?, aciklama = ? WHERE id = ?` → `rowcount == 1` ise başarılı.
- **Delete:** `DELETE FROM malzeme WHERE id = ?`.

`?` **parametreli sorgu**dur: değer SQL metnine birleştirilmez, sürücü ayrı gönderir; bu yüzden kullanıcı `'; DROP TABLE malzeme; --` yazsa bile sadece metin olarak saklanır (SQL injection engellenir). Stok için bileşik anahtar yüzünden upsert kullandım: `INSERT … ON CONFLICT (depo_id, malzeme_id) DO UPDATE SET miktar = excluded.miktar`.

---

## Teorik kavramlar (kısa)
- **DDL** (Data Definition Language): yapıyı tanımlar → `CREATE TABLE`, `CREATE INDEX`, `ALTER`, `DROP`. Migration dosyam DDL.
- **DML** (Data Manipulation Language): veriyi işler → `INSERT`, `SELECT`, `UPDATE`, `DELETE`. Repository'lerim DML.
- **İndeks:** Aramayı hızlandıran ek veri yapısı (B-ağacı); okuma hızlanır, yazma biraz yavaşlar.
- **Referans bütünlüğü:** FK'nin gösterdiği kayıt her zaman var olmalı.
- **Transaction:** Birden çok işlemin "ya hep ya hiç" çalışması (ACID). `with islem(baglanti):` hatasız biterse COMMIT, hata olursa ROLLBACK. Test: aynı blokta 2 kategori eklerken ikincisi UNIQUE'e takılınca ilki de geri alınıyor.

## Sık yapılan hatalar (bende olmamalı)
İlişkisiz/denormalize tablolar → her şey FK ile bağlı, 3NF · Kısıt tanımlamamak → FK, CHECK, UNIQUE, NOT NULL var · Gerçek kişisel veri → yalnızca sentetik veri.

## Demo sırasında sorulabilecek ek sorular
- *Stoğu neden hesaplamak yerine tablo olarak tuttun?* Hızlı okuma ve kritik seviye uyarısı için; tutarlılık her giriş/çıkışın transaction içinde stok güncellemesiyle sağlanacak (Hafta 6-7). `CHECK (miktar >= 0)` fazla çıkışı veritabanında da engelliyor.
- *Repository neden commit etmiyor?* Bağış + kalemler + stok gibi çok tablolu işlemler tek transaction olsun diye commit kararı çağıranda.
- *Neden ORM kullanmadın?* SQL'i görüp açıklayabilmek, ek bağımlılık olmaması; tekrarı TemelRepository ile azalttım.
