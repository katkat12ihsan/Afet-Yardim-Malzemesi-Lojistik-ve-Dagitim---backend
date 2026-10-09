# P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım

Bağış malzemelerinin envanterini yönetip ihtiyaç noktalarına dağıtımı planlayan **Python masaüstü uygulaması**.

> Bilgisayar Uygulamaları I — Proje Tabanlı Öğrenme dersi projesi
> Durum: **Hafta 5 — Kullanıcı yönetimi ve kimlik doğrulama** (giriş/kayıt, PBKDF2 parola, oturum, rol tabanlı erişim)

## Problem ve amaç

Bağış malzemeleri envanteri ve dağıtımı düzensiz olduğunda israf ve eksik dağıtım oluşuyor. Bu proje; malzeme envanterini yöneten, bağışları kaydeden, ihtiyaç noktalarının talepleriyle stoğu eşleştiren ve dağıtımı planlayan bir sistem kurmayı amaçlar. Hedef kullanıcılar yardım kuruluşları ve depolardır.

## Modüller ve takvim

| Modül | Hafta |
|---|---|
| Kurulum, mimari, ER diyagramı | 3 ✅ |
| Veritabanı ve veri erişim katmanı | 4 ✅ |
| Kullanıcı yönetimi ve kimlik doğrulama | 5 ✅ |
| Envanter yönetimi | 6 |
| Bağış girişi ve ihtiyaç eşleştirme | 7 |
| Harita / rota API entegrasyonu | 9 |
| Yapay zekâ: dağıtım önceliği ve rota önerisi | 10 |
| Takip ve şeffaflık modülü | 11 |
| Dağıtım raporu ve bildirimler | 12 |
| Test, dokümantasyon, dağıtım hazırlığı | 13–15 |

## Teknolojiler

- Python 3.12
- Tkinter / ttk — masaüstü arayüz (Python ile birlikte gelir)
- SQLite (`sqlite3`) — ilişkisel veritabanı (Python ile birlikte gelir)
- unittest — birim testleri

## Kurulum ve çalıştırma

```bash
git clone https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim.git
cd Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m backend.data.kurulum --ornek-veri
python main.py
```

Açılışta giriş ekranı gelir. `--ornek-veri` her rolden bir test kullanıcısı ekler: `yonetici`, `kurum1`, `depo1` (parolalar `backend/data/ornek_veri.py` → `KULLANICILAR`; yalnızca yerel demo içindir). Hiç kullanıcı yoksa kayıt ekranından ilk Yönetici hesabı açılabilir.

| Rol | Erişebildiği modüller |
|---|---|
| Yönetici | Tümü + Kullanıcılar |
| Kurum | Panel, İhtiyaç, Dağıtım, YZ Önerisi, Takip, Rapor |
| Depo | Panel, Envanter, Bağış, Takip |

Veritabanı demosu (sorgular + kısıt denemeleri, kalıcı değişiklik yapmaz):

```bash
python -m backend.data.sorgu_ornekleri
```

Testler:

```bash
python -m unittest
```

Gizli bilgiler (API anahtarları) koda yazılmaz; `.env.example` dosyasındaki değişkenler ortam değişkeni olarak verilir. `.env` dosyası depoya yüklenmez.

## Dokümantasyon

- [ER diyagramı](docs/ER-Diyagrami.md) ([görsel](docs/er-diyagrami.svg))
- [Mimari şema](docs/Mimari.md) ([görsel](docs/mimari-sema.svg))
- [Veritabanı tasarımı: migration, kısıtlar, indeksler](docs/Veritabani.md)
- [Güvenlik notu: parola, oturum, rol tabanlı erişim](docs/Guvenlik-Notu.md)
- [Haftalık ilerleme raporları](docs/haftalik-raporlar/)
- [Yapay zekâ kullanım günlüğü](docs/ai-kullanim-gunlugu.md)
- Formlar: [risk analizi](docs/formlar/risk-analizi.md) · [proje takvimi](docs/formlar/proje-takvimi.md) · [proje izleme](docs/formlar/proje-izleme-formu.md) · [haftalık kontrol listesi](docs/formlar/haftalik-kontrol-listesi.md) · [GitHub kontrol listesi](docs/formlar/github-kontrol-listesi.md)

## Klasör yapısı

Proje iki ana bölüme ayrılmıştır:

```
main.py                  başlangıç noktası (frontend'i açar)
backend/                 arayüzden bağımsız çekirdek
  config.py              ayarlar
  guvenlik.py            parola hash (PBKDF2), token
  models/                varlık katmanı (ER -> dataclass)
  services/              iş katmanı (iş kuralları, eşleştirme, öneri)
  data/                  veri erişim katmanı (SQLite)
    migrations/          numaralı şema dosyaları (001_ilk_sema.sql)
    repositories/        CRUD sınıfları
frontend/                masaüstü arayüz (Tkinter)
  giris_penceresi.py     giriş / kayıt
  main_window.py         ana pencere, menü, sayfalar
tests/                   birim testleri
docs/                    ER, mimari, raporlar, AI günlüğü, ekran görüntüleri
```

**Kural:** `frontend` yalnızca `backend.services` ve `backend.models` kullanır; `backend` hiçbir zaman `frontend`'i import etmez. Bu yüzden backend testleri pencere açmadan çalışır.

## Veri gizliliği

Projede yalnızca **sentetik/anonim** veri kullanılır; gerçek kişisel veri (KVKK) girilmez.
