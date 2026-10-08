"""1200x630 genel paylaşım (Open Graph) görselini üretir: uretec/statik/og-kamu.png.

Derlemenin parçası değildir; tasarım değişince elle çalıştırılır:
    python -m uretec.og_gorseli
Playwright (Chromium) gerektirir.
"""

from pathlib import Path

STATIK = Path(__file__).resolve().parent / "statik"
KOK = Path(__file__).resolve().parent.parent
CIKTI = STATIK / "og-kamu.png"

_HTML = """<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8"><style>
@font-face {{ font-family: P; src: url("{font4}"); font-weight: 400; }}
@font-face {{ font-family: P; src: url("{font7}"); font-weight: 700; }}
@font-face {{ font-family: P; src: url("{font8}"); font-weight: 800; }}
* {{ margin: 0; box-sizing: border-box; }}
body {{ width: 1200px; height: 630px; background: #16265C; color: #fff; font-family: P;
  padding: 72px 88px; position: relative; overflow: hidden; }}
.kunye {{ display: flex; align-items: center; gap: 20px; }}
.kunye img {{ width: 72px; height: 72px; border-radius: 18px; }}
.kunye span {{ font-size: 44px; font-weight: 800; letter-spacing: -0.03em; }}
.cizgi {{ height: 3px; background: #fff; margin-top: 28px; }}
.cizgi2 {{ height: 1px; background: rgba(255,255,255,.35); margin-top: 9px; }}
.etiket {{ display: flex; align-items: center; gap: 16px; margin-top: 56px; font-size: 22px;
  font-weight: 700; letter-spacing: .16em; color: #CBD5E1; }}
.cubuk {{ width: 40px; height: 10px; border-radius: 5px; background: #2DD4BF; }}
h1 {{ font-size: 104px; font-weight: 800; letter-spacing: -0.05em; line-height: .95; margin-top: 18px; }}
p {{ font-size: 30px; color: #CBD5E1; margin-top: 26px; max-width: 900px; line-height: 1.35; }}
.adres {{ position: absolute; right: 88px; bottom: 64px; font-size: 26px; font-weight: 700; color: #fff; }}
.motif {{ position: absolute; right: -40px; top: 120px; display: flex; gap: 18px; align-items: flex-end; opacity: .08; }}
.motif div {{ width: 46px; background: #fff; border-radius: 10px; }}
</style></head><body>
<div class="motif"><div style="height:120px"></div><div style="height:190px"></div><div style="height:260px"></div><div style="height:330px"></div></div>
<div class="kunye"><img src="{ikon}" alt=""><span>Kamu</span></div>
<div class="cizgi"></div><div class="cizgi2"></div>
<div class="etiket"><span class="cubuk"></span>KAMU PERSONEL ALIMLARI</div>
<h1>Kamu ilanları</h1>
<p>Memur, sözleşmeli, işçi ve akademik alımlar. Son başvuru kaçmadan, yeni ilanda bildirim.</p>
<div class="adres">kamuuygulama.me</div>
</body></html>"""


def uret(cikti: Path = CIKTI) -> Path:
    from playwright.sync_api import sync_playwright

    html = _HTML.format(
        font4=(STATIK / "fontlar/pjs-400.woff2").as_uri(),
        font7=(STATIK / "fontlar/pjs-700.woff2").as_uri(),
        font8=(STATIK / "fontlar/pjs-800.woff2").as_uri(),
        ikon=(KOK / "kamu-icon-512.png").as_uri(),
    )
    gecici = STATIK.parent / "_og_gecici.html"
    gecici.write_text(html, encoding="utf-8")
    try:
        with sync_playwright() as p:
            tarayici = p.chromium.launch()
            sayfa = tarayici.new_page(viewport={"width": 1200, "height": 630})
            sayfa.goto(gecici.as_uri(), wait_until="networkidle")
            sayfa.screenshot(path=str(cikti))
            tarayici.close()
    finally:
        gecici.unlink(missing_ok=True)
    return cikti


if __name__ == "__main__":
    print(uret())
