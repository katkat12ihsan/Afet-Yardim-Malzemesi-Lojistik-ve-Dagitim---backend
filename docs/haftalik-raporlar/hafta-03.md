# Hafta 3 İlerleme Raporu — Kurulum, Mimari ve Veri Modeli

**Proje:** P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım
**Geliştirilen modül:** Proje iskeleti ve depo yapısı

## Yapılan teknik çalışmalar

| Görev (yönergeden) | Durum | Kanıt |
|---|---|---|
| Teknoloji yığını ve geliştirme ortamının kurulumu | ✅ | Python 3.12 + Git; Tkinter, SQLite standart kütüphanede |
| Boş proje iskeleti ve katmanlı klasör yapısı | ✅ | `backend/{models,services,data}` ve `frontend/`, `python main.py` ile açılan pencere |
| GitHub deposu, .gitignore ve README taslağı | ✅ | `README.md`, `.gitignore`, `.env.example` |
| ER diyagramı: malzeme, bağış, ihtiyaç noktası, dağıtım kaydı | ✅ | `docs/ER-Diyagrami.md`, `docs/er-diyagrami.svg` |
| Mimari şema | ✅ | `docs/Mimari.md`, `docs/mimari-sema.svg` |

Ek olarak: ER'deki her tablo `models/entities.py` içinde dataclass olarak tanımlandı; iskelet için 3 birim testi yazıldı (`python -m unittest`).

## Haftalık kontrol kriterleri

- [x] Depo erişilebilir ve düzenli
- [x] ER diyagramı varlık/ilişkileri doğru (1-N ve N-N ilişkiler, ara tablolar, PK/FK)
- [x] Mimari katmanlar tanımlı (Sunum → İş → Veri + Varlık)

## Gösterilecek ilerleme (demo sırası)

1. GitHub deposu: klasör yapısı, README, .gitignore
2. `python main.py` → ana pencere; menüden bir modüle tıklayınca "X. haftada geliştirilecek" sayfası
3. `docs/er-diyagrami.svg` → varlıklar ve ilişkiler
4. `docs/mimari-sema.svg` → katmanlar ve bağımlılık yönü

## Karşılaşılan sorunlar ve çözümler

- `.gitignore` içindeki `data/` kuralı, `backend/data` paketini de dışarıda bırakıyordu → kural `/data/` yapılarak yalnızca kök klasördeki veritabanı dosyası hariç tutuldu.

## Gelecek hafta (Hafta 4)

SQLite şema scripti (tablolar, PK/FK, kısıtlar, indeksler), sentetik örnek veri ve CRUD repository sınıfları.

## Ekran görüntüleri

`docs/ekran-goruntuleri/hafta-03-ana-panel.png`
