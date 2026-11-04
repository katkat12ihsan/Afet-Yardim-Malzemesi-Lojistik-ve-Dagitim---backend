# Vize Demo Senaryosu (Hafta 8 · sürüm `v0.6.0`)

**Hedef:** Kullanıcı + veritabanı + çekirdek modüllerin uçtan uca çalıştığını yaklaşık **7 dakikada** göstermek.
**Hikâye:** Kiğı Okul Toplanma Alanı 100 paket hijyen kiti istiyor ama depolarda yalnızca 90 paket var. Bir bağış geliyor, talep tam karşılanıyor, malzeme yola çıkıp teslim ediliyor. Bu sırada her modül bir öncekinin verisini kullanıyor.

Aynı akış otomatik test olarak da var: `tests/test_entegrasyon.py` → `test_bagistan_teslime_tam_akis`.

## Hazırlık (sınavdan önce, 1 dakika)

1. Frontend klasöründe **`demo.bat`**'a çift tıkla.
   - Ayrı bir demo veritabanını (`%USERPROFILE%\AfetLojistik\demo.db`) sıfırlayıp örnek veriyle kurar. Gerçek veritabanı (`afet_lojistik.db`) değişmez.
   - Her açılışta aynı başlangıç verisi olduğu için demo her seferinde aynı sonucu verir.
2. Test hesapları: `yonetici`, `kurum1`, `depo1`. Parolalar backend deposunda `backend/data/ornek_veri.py` → `KULLANICILAR`.
3. Yanında açık olsun: VS Code'da backend deposu (kod sorulursa) ve bir terminal (testler için).

## Adımlar

| # | Süre | Kim | Ne yapılır | Ne söylenir |
|---|---|---|---|---|
| 1 | 0:30 | — | Giriş ekranında yanlış parola dene → "Kullanıcı adı veya parola hatalı." | "Parolalar PBKDF2 ile özetlenip saklanıyor. Kullanıcı adı mı parola mı yanlış, söylemiyorum; 5 hatalı denemede hesap 5 dakika kilitleniyor." (Hafta 5) |
| 2 | 1:00 | `yonetici` | Ana Panel: özet kartları (**7 bekleyen talep**) ve modül tablosu (Hazır / Kısmen / Planlandı). Kullanıcılar sayfasına kısaca göz at. | "Kartlar doğrudan veritabanından sayılıyor. Tablo, hangi modülün hangi haftada bittiğini gösteriyor. Rota modülü *Kısmen*: dağıtım listesi hazır, harita 9. haftada." |
| 3 | 0:45 | `kurum1` | İhtiyaç Eşleştirme → Kiğı'nın **Hijyen kiti** talebini seç. Öneri: Genç Ara Depo 90 paket, **"Eksik: 10 paket"**. Planlamadan çık. | "Öneri, uygun stoğu olan depoları ihtiyaç noktasına en yakından başlayarak dolduruyor. Stok yetmediği için 10 paketin açıkta kalacağını söylüyor." (Hafta 7) |
| 4 | 1:00 | `depo1` | Menüde İhtiyaç ve Kullanıcılar **kilitli**. Bağış Girişi → yeni bağışçı "Örnek Eczane", Hijyen kiti **40 paket** → Kaydet. Envanter'de Hijyen kiti 40; Hareket Geçmişi'nde "Bağış #…". | "Depo görevlisi yalnızca kendi deposunu görüyor; yetki kontrolü backend'de. Bağış, stoğu kendi SQL'iyle değil Envanter'in yolundan artırıyor; bu yüzden hareket geçmişine düşüyor." (Hafta 5–7) |
| 5 | 1:00 | `kurum1` | Aynı talep: öneri artık **Bingöl 40 (48,9 km) + Genç 60 (64,7 km)**, eksik yok. Plaka yaz → **Dağıtımı Planla** → talep "Karşılandı". | "Bağış veriyi değiştirdi, eşleştirme bunu hemen gördü: önce en yakın depo, Bingöl. Talebin durumu elle değil, dağıtımlardan hesaplanıyor." |
| 6 | 1:00 | `depo1` | Envanter: Hijyen kiti satırında **Rezerve 40**. Stok Çıkışı → 10 paket → **"planlanmış dağıtımlara ayrılmış (rezerve)…"** hatası. | "Bu, vize haftasında entegrasyon testiyle bulduğum hata. Önce bu çıkış yapılabiliyordu ve dağıtım yola çıkamıyordu. Şimdi K9 kuralı engelliyor; regresyon testi var." (Hafta 8) |
| 7 | 0:45 | `kurum1` | Rota / Dağıtım Planı menüsü → Dağıtımlar sekmesi açılır. İki dağıtım: **Yola Çıkar** → **Teslim Edildi**. | "Stok planlamada değil, malzeme depodan çıkınca, yani *Yolda* adımında düşüyor. Stok yetmezse durum değişikliği dahil hiçbir şey kaydedilmiyor (transaction)." |
| 8 | 0:30 | `yonetici` | Ana Panel: bekleyen talep **7 → 6**. Envanter (Bingöl): Hijyen kiti 0, hareket geçmişinde "Dağıtım #…". | "Uçtan uca: kullanıcı → bağış → envanter → eşleştirme → dağıtım → panel. Her modül veriyi bir önceki modülün servisinden alıyor." |
| 9 | 0:30 | — | Terminal: backend'de `python -m unittest` → **101 test OK**; frontend'de 5 arayüz testi. GitHub'da `v0.6.0` etiketi ve CHANGELOG. | "Ara sürüm etiketli: `v0.6.0`. Frontend backend'i bu etiketten kuruyor, yani gösterdiğim kod etiketli sürümün aynısı." |

## Bir şey ters giderse

| Durum | Ne yapılır |
|---|---|
| Uygulama açılmıyor / "Backend paketi bulunamadı" | Önce `baslat.bat` (sanal ortamı kurar), sonra yeniden `demo.bat`. |
| Adımlardan biri yanlış yapıldı (ör. bağış iki kez girildi) | Uygulamayı kapatıp `demo.bat`'ı yeniden çalıştır; veri baştan kurulur. |
| İnternet yok | Uygulama internetsiz çalışır; yalnızca ilk kurulum (`pip`) internet ister. |
| Zaman daraldı | 1, 3, 9 atlanabilir; 4–7 entegrasyonun kendisi, atlanmamalı. |

## Gösterilen bağlantılar (hangi modül hangi veriyi nereden alıyor)

```
Kimlik (H5)  ──oturum/rol──▶  her servis (modul_erisimi)
Bağış (H7)   ──stok_hareketi_uygula──▶  Envanter (H6)  ──▶ stok + stok_hareketi
Eşleştirme (H7) ──uygun stok = stok − rezerve──▶ Envanter verisi + depo/nokta koordinatları (H4)
Dağıtım "Yolda" ──stok_hareketi_uygula (çıkış)──▶ Envanter (H6)
Envanter çıkışı ──rezerve──▶ planlanmış dağıtımlar (H7)   ◀── Hafta 8 düzeltmesi (K9)
Panel ──sayımlar──▶ talep durumları, kritik stok
```
