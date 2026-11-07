"""Ziyaret ölçümü (PostHog, çerezsiz): betik her sayfada, ölçülen linkler işaretli."""

import re
from pathlib import Path

from test_uretec import SIMDI, satir

from uretec.derle import STATIK, derle, yaz
from uretec.model import Ilan

BETIK = '<script src="/olcum.js" defer></script>'


def test_her_sayfada_olcum_betigi_head_icinde_bir_kez():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    for yol, html in derleme.sayfalar.items():
        bas = html.split("</head>", 1)[0]
        assert bas.count(BETIK) == 1, yol
        assert html.count("olcum.js") == 1, yol


def test_ilan_sayfasinda_pdf_ve_resmi_link_isaretli():
    ilan = Ilan.from_satir(satir())
    html = derle([satir()], SIMDI, en_az_acik=1).sayfalar[ilan.yol]
    assert re.search(r'<a [^>]*rel="noopener nofollow" data-olay="pdf">İlan metni \(PDF\)</a>', html)
    assert re.search(r'<a [^>]*data-olay="resmi">Resmî ilan sayfası</a>', html)


def test_tum_magaza_linkleri_isaretli():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    for yol, html in derleme.sayfalar.items():
        for etiket in re.findall(r'<a [^>]*href="https://(?:apps\.apple\.com|play\.google\.com)[^>]*>', html):
            assert 'data-olay="magaza"' in etiket, (yol, etiket)


def test_betik_yalnizca_canli_alan_adinda_ve_cerezsiz_calisir():
    js = (STATIK / "olcum.js").read_text(encoding="utf-8")
    assert "location.hostname !== 'kamuuygulama.me'" in js
    assert "cookieless_mode: 'always'" in js
    assert "api_host: SUNUCU" in js and "https://eu.i.posthog.com" in js
    assert "autocapture: false" in js
    assert "disable_session_recording: true" in js
    assert "phc_" in js and "phx_" not in js  # yalnızca herkese açık proje jetonu


def test_yaz_olcum_betigini_kopyalar_ig_yonlendirmesine_eklemez(tmp_path: Path):
    cikti = tmp_path / "_site"
    yaz(derle([satir()], SIMDI, en_az_acik=1), cikti)
    assert (cikti / "olcum.js").exists()
    assert "olcum.js" not in (cikti / "ig/index.html").read_text(encoding="utf-8")


def test_gizlilik_sayfasi_olcumu_anlatir():
    gizlilik = derle([satir()], SIMDI, en_az_acik=1).sayfalar["/gizlilik/"]
    for ifade in ("PostHog", "çerezsiz", "Avrupa Birliği", "IP adresi saklanmıyor"):
        assert ifade in gizlilik
    assert "analiz aracı kullanmıyor" not in gizlilik
