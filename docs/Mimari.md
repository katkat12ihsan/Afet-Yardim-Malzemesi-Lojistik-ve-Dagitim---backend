# Mimari Şema — P16 Afet Yardım Malzemesi Lojistik ve Dağıtım

**Uygulama türü:** Python masaüstü uygulaması
**Teknoloji yığını:** Python 3.12 · Tkinter/ttk (arayüz) · SQLite (`sqlite3`, veritabanı) · unittest (test)

## Katmanlı mimari (3 katman + ortak varlık katmanı)

```mermaid
flowchart TB
    K([Kullanıcı: depo / yardım kuruluşu görevlisi])
    subgraph UI["Sunum Katmanı — frontend"]
        AP[AnaPencere: menü + sayfalar<br/>Tkinter / ttk]
    end
    subgraph BL["İş Katmanı — backend/services"]
        S1[Envanter / Bağış / İhtiyaç eşleştirme<br/>Dağıtım planı / Rapor servisleri]
    end
    subgraph DAL["Veri Erişim Katmanı — backend/data"]
        D1[database.py: bağlantı<br/>repository sınıfları: CRUD]
    end
    DB[(SQLite<br/>afet_lojistik.db)]
    M[[Varlık Katmanı — backend/models<br/>Malzeme, Bağış, Depo, İhtiyaçNoktası, Dağıtım ...]]
    EXT[/Harici servisler: Harita-Rota API · LLM API/]

    K --> AP --> S1 --> D1 --> DB
    S1 -. Hafta 9-10 .-> EXT
    AP -.- M
    S1 -.- M
    D1 -.- M
```

Görsel sürüm: [mimari-sema.svg](mimari-sema.svg)

## Katmanların görevleri

| Katman | Klasör | Görev | Yapmaması gereken |
|---|---|---|---|
| Sunum | `frontend` | Pencereler, formlar, tablolar; kullanıcı girdisini alıp iş katmanına iletmek | SQL yazmak, iş kuralı uygulamak |
| İş | `backend/services` | Doğrulama, stok yeterli mi?, ihtiyaç–stok eşleştirme, öncelik/rota önerisi | Tkinter'a bağımlı olmak |
| Veri erişim | `backend/data` | Veritabanı bağlantısı, CRUD sorguları | İş kararı vermek |
| Varlık | `backend/models` | ER diyagramındaki tabloların Python karşılığı (dataclass) | Başka katmana bağımlı olmak |

**Frontend / backend ayrımı:** Sunum katmanı `frontend/` klasöründe; iş, veri erişim ve varlık katmanları `backend/` klasöründe. Frontend yalnızca backend'in servislerini çağırır, backend frontend'i hiç tanımaz.

**Bağımlılık yönü tek yönlüdür:** Sunum → İş → Veri. Alt katman üst katmanı tanımaz. Bu sayede ör. arayüz Tkinter'dan başka bir kütüphaneye geçse iş ve veri katmanı değişmez; iş kuralları arayüz açılmadan `unittest` ile test edilebilir.

## Depo ve klasör yapısı

Proje iki ayrı GitHub deposundan oluşur. Ayrım, katmanların bağımlılık yönüyle aynıdır: frontend backend'e bağımlıdır, backend frontend'i tanımaz.

| Depo | İçerik | Bağımlılık |
|---|---|---|
| [Backend](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend) | Varlık, iş ve veri erişim katmanları; şema; testler; dokümantasyon | Yalnızca Python standart kütüphanesi |
| [Frontend](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---fronted) | Tkinter arayüzü ve başlangıç noktası | Backend paketi (`requirements.txt` → GitHub) |

```
Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/
├── pyproject.toml           # Paket tanımı: frontend bunu pip ile kurar
├── backend/                 # BACKEND: arayüzden bağımsız çekirdek
│   ├── config.py            # Ayarlar; gizli anahtarlar ortam değişkeninden
│   ├── guvenlik.py          # Parola hash, token
│   ├── models/entities.py   # Varlık katmanı (ER → dataclass)
│   ├── services/            # İş katmanı
│   └── data/                # Veri erişim katmanı (SQLite, migration'lar, repository'ler)
├── tests/                   # Birim testleri (unittest)
└── docs/                    # ER, mimari, haftalık raporlar, formlar, AI günlüğü

Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---fronted/
├── main.py                  # Başlangıç noktası (python main.py)
├── frontend/                # FRONTEND: masaüstü arayüz
│   ├── giris_penceresi.py   # Giriş / kayıt
│   └── main_window.py       # Ana pencere (Tkinter)
└── requirements.txt         # afet-lojistik-backend @ git+...backend.git
```

> Hafta 3–5 boyunca proje tek depoda geliştirildi ([eski tek depo](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim)); Hafta 6 öncesinde commit geçmişi korunarak iki depoya ayrıldı.

## Neden bu teknolojiler?

- **Python + Tkinter:** Python ile birlikte gelir, ek kurulum gerektirmez; kurumların depo bilgisayarlarında internet olmadan da çalışan bir masaüstü uygulaması hedefleniyor (afet bölgesinde bağlantı kesintisi gerçek bir risk).
- **SQLite:** Sunucu kurulumu gerektirmeyen, tek dosyalık, ilişkisel (yabancı anahtar ve transaction destekli) veritabanı. Tek depo/kurum ölçeği için yeterli; ileride PostgreSQL'e geçilirse yalnızca veri erişim katmanı değişir.
- **Katmanlı mimari:** Modüller (envanter, bağış, eşleştirme, dağıtım, takip, rapor) haftalık olarak eklenecek; her modül aynı üç katmanı izlediği için kod düzenli ve açıklanabilir kalır.
