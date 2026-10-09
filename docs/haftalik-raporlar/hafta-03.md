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

## Yapay zekâ kullanımı özeti

Claude; mimari/şema önerisi, kod iskeleti ve test senaryoları için kullanıldı. Ayrıntı: [AI kullanım günlüğü](../ai-kullanim-gunlugu.md) (Kayıt 1–3). Önerilerin doğrulaması testler ve demo komutlarıyla yapıldı.

## Ekler — commit bağlantıları

- [be91e82](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/be91e82) chore: proje kurulumu (.gitignore, README, requirements, .env.example)
- [673e281](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/673e281) backend: varlık katmanı - ER tablolarının dataclass karşılıkları
- [ed889dc](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/ed889dc) backend: ayarlar, veri erişim (SQLite bağlantısı) ve iş katmanı iskeleti
- [b4fbd76](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/b4fbd76) frontend: Tkinter ana pencere iskeleti ve başlangıç noktası
- [99c03f3](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/99c03f3) test: backend iskelet birim testleri
- [a2eb8ce](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/a2eb8ce) docs: ER diyagramı ve mimari şema (frontend/backend ayrımı)
- [4e1ee30](https://github.com/karkatihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim/commit/4e1ee30) docs: hafta 3 ilerleme raporu, AI kullanım günlüğü, sözlü hazırlık, ekran görüntüsü
