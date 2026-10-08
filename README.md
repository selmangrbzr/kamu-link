# kamu-link

kamuuygulama.me: Kamu uygulamasının web sitesi. Açık kamu ilanları için statik,
indekslenebilir sayfalar ve mağaza yönlendirmesi.

## Sayfalar

- `/`: Giriş sayfası (yönlendirmesiz). Son ilanlar, en büyük alımlar, kategoriler. Mağaza kampanyası `site`.
- `/ilan/<slug>/`: İlan sayfası. Açık ilanda JobPosting JSON-LD; son başvurusu son 60 günde dolan ilan `noindex`.
- `/memur-alimlari/`, `/lise-mezunu-kamu-ilanlari/`, `/kpss-p3-ilanlari/`, `/sehir/<il>/` vb.: Merkez sayfaları (yalnızca açık ilanı olanlar).
- `/kurum/<slug>/`: Kurum sayfaları (bakanlıklar ve büyük başkanlıklar kalıcı; diğerleri açık ilan varken). 2+ açık ilanda indekslenir.
- `/son-basvurusu-yaklasan-ilanlar/`, `/bu-hafta-eklenen-kamu-ilanlari/`, `/belediye-personel-alimlari/`, `/kpss-siz-kamu-ilanlari/`: Ek merkezler.
- Sabit merkezler ilan kalmasa da üretilir ("şu an açık ilan yok", `noindex`, sitemap dışı).
- `/hakkinda/`, `/nasil-calisir/`, `/iletisim/`, `/gizlilik/`: Güven sayfaları (`uretec/bilgi.py`).
- `/ig`: Instagram bio linki. Cihaza göre mağazaya yönlendirir (`yonlendir.js`, kampanya `ig`), `noindex`.
- Yönlendirmeli sayfalara `?k=story` gibi ekleyerek kampanya adı değiştirilebilir.

## Üreteç

```bash
python -m uretec --env-dosyasi ../proje/.env   # SUPABASE_URL ve SUPABASE_ANON_KEY
python -m uretec --json ilanlar.json           # çevrimdışı, yerel satırlarla
python -m pytest -q
```

Çıktı `_site/` klasörüne yazılır (git dışı). `.github/workflows/site.yml` günde dört kez
(01:30, 07:30, 13:30, 19:30 UTC) üretip GitHub Pages'e yayınlar; Pages kaynağı
"GitHub Actions" olmalıdır.

- `uretec/model.py`: İlan modeli, eleme kuralları (iptal/düzeltme, zenginleştirme, 60 gün).
- `uretec/jsonld.py`: JobPosting ve BreadcrumbList.
- `uretec/merkezler.py`: Merkez tanımları ve giriş metinleri.
- `uretec/sayfalar.py`, `uretec/sablon.py`: HTML.
- `uretec/derle.py`: Derleme, sitemap, robots.txt, dosya yazımı.
- `uretec/kurumlar.py`: Kalıcı kurum listesi, kurum anahtarı, "X Belediyesi" varyantı.
- `uretec/og_gorseli.py`: 1200x630 paylaşım görselini üretir (`python -m uretec.og_gorseli`, Playwright gerekir).
- `uretec/statik/`: `kamu.css`, Plus Jakarta Sans WOFF2 alt kümeleri (OFL), küçük simge.
