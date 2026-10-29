# P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım — **Backend**

Bağış malzemelerinin envanterini yönetip ihtiyaç noktalarına dağıtımı planlayan **Python masaüstü uygulaması**nın backend'i: varlık, iş ve veri erişim katmanları, veritabanı şeması, kimlik doğrulama ve testler.

| Depo | İçerik |
|---|---|
| **Backend (bu depo)** | `backend/` paketi, `tests/`, proje dokümantasyonu (`docs/`) |
| [Frontend](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend) | Tkinter masaüstü arayüzü (`frontend/`, `main.py`) |

Proje dokümantasyonu (haftalık raporlar, formlar, AI günlüğü) bu depodadır.

> Bilgisayar Uygulamaları I — Proje Tabanlı Öğrenme dersi projesi
> Durum: **Hafta 7 — Bağış Girişi ve İhtiyaç Eşleştirme** (bağış → stok, en yakın depo önerisi, fazla/eksik, dağıtım durumu)

## Problem ve amaç

Bağış malzemeleri envanteri ve dağıtımı düzensiz olduğunda israf ve eksik dağıtım oluşuyor. Bu proje; malzeme envanterini yöneten, bağışları kaydeden, ihtiyaç noktalarının talepleriyle stoğu eşleştiren ve dağıtımı planlayan bir sistem kurmayı amaçlar. Hedef kullanıcılar yardım kuruluşları ve depolardır.

## Modüller ve takvim

| Modül | Hafta |
|---|---|
| Kurulum, mimari, ER diyagramı | 3 ✅ |
| Veritabanı ve veri erişim katmanı | 4 ✅ |
| Kullanıcı yönetimi ve kimlik doğrulama | 5 ✅ |
| Envanter yönetimi | 6 ✅ |
| Bağış girişi ve ihtiyaç eşleştirme | 7 ✅ |
| Harita / rota API entegrasyonu | 9 |
| Yapay zekâ: dağıtım önceliği ve rota önerisi | 10 |
| Takip ve şeffaflık modülü | 11 |
| Dağıtım raporu ve bildirimler | 12 |
| Test, dokümantasyon, dağıtım hazırlığı | 13–15 |

## Teknolojiler

- Python 3.12
- Tkinter / ttk — masaüstü arayüz ([frontend deposu](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend))
- SQLite (`sqlite3`) — ilişkisel veritabanı (Python ile birlikte gelir)
- unittest — birim testleri

## Kurulum

Backend kurulabilir bir Python paketidir (`pyproject.toml`); ek bağımlılığı yoktur.

```bash
git clone https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend.git
cd Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m backend.data.kurulum --ornek-veri
```

Uygulamanın arayüzü için [frontend deposunun](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend) kurulum adımlarını izleyin; frontend bu paketi `requirements.txt` üzerinden GitHub'dan kurar.

Veritabanı varsayılan olarak ev klasöründe, `C:\Users\<kullanıcı>\AfetLojistik\afet_lojistik.db` dosyasındadır (Linux/macOS: `~/AfetLojistik`). Böylece backend ve frontend, hangi klasörden çalıştırılırsa çalıştırılsın aynı veritabanını kullanır; yol `AFET_DB_YOLU` ortam değişkeniyle değiştirilebilir. (AppData bilerek kullanılmaz: Windows, paket olarak kurulmuş uygulamaların içinden çalışan programların AppData'ya yazdıklarını başka bir klasöre yönlendirir ve aynı bilgisayarda iki ayrı veritabanı oluşur.)

Uygulama açılışında giriş ekranı gelir. `--ornek-veri` her rolden bir test kullanıcısı ekler: `yonetici`, `kurum1`, `depo1` (parolalar `backend/data/ornek_veri.py` → `KULLANICILAR`; yalnızca yerel demo içindir). Hiç kullanıcı yoksa kayıt ekranından ilk Yönetici hesabı açılabilir.

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
- [Güvenlik notu: parola, oturum, rol tabanlı erişim, rol düzenleme](docs/Guvenlik-Notu.md)
- [Envanter Yönetimi: veri modeli, iş kuralları K1–K8, akış](docs/Envanter.md)
- [Bağış Girişi ve İhtiyaç Eşleştirme: B1–B8, E1–E9, fazla/eksik, dağıtım durumu](docs/Bagis-ve-Eslestirme.md)
- [Haftalık ilerleme raporları](docs/haftalik-raporlar/) — Word sürümleri: [docs/haftalik-raporlar/word/](docs/haftalik-raporlar/word/)
- [Yapay zekâ kullanım günlüğü](docs/ai-kullanim-gunlugu.md)
- Formlar: [risk analizi](docs/formlar/risk-analizi.md) · [proje takvimi](docs/formlar/proje-takvimi.md) · [proje izleme](docs/formlar/proje-izleme-formu.md) · [haftalık kontrol listesi](docs/formlar/haftalik-kontrol-listesi.md) · [GitHub kontrol listesi](docs/formlar/github-kontrol-listesi.md)

## Klasör yapısı

```
pyproject.toml           paket tanımı (pip install)
backend/                 arayüzden bağımsız çekirdek
  config.py              ayarlar
  guvenlik.py            parola hash (PBKDF2), token
  models/                varlık katmanı (ER -> dataclass)
  services/              iş katmanı (kimlik, yetki, envanter, bağış, eşleştirme, özet, modül planı)
  data/                  veri erişim katmanı (SQLite)
    migrations/          numaralı şema dosyaları (001 ilk şema, 002 kullanıcı, 003 stok hareketi, 004 rol değişikliği, 005 eşleştirme)
    repositories/        CRUD sınıfları
tests/                   birim testleri (94 test)
docs/                    ER, mimari, raporlar, formlar, AI günlüğü, ekran görüntüleri
```

**Kural:** Frontend yalnızca `backend.services` ve `backend.models` kullanır; backend frontend'i hiç tanımaz. Bu yüzden backend ayrı bir depoda durabilir ve testleri pencere açmadan çalışır.

## Veri gizliliği

Projede yalnızca **sentetik/anonim** veri kullanılır; gerçek kişisel veri (KVKK) girilmez.
