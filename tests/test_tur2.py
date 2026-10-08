"""İkinci tur: kalıcı merkezler, başlıklar, dönüşüm, güven sayfaları, yeni merkezler."""

import json
import re
import struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from test_uretec import SIMDI, iki_ilan, jsonld_listesi, satir

from uretec.derle import derle
from uretec.model import Ilan

STATIK = Path(__file__).resolve().parent.parent / "uretec" / "statik"


def kimlik(n: int) -> str:
    return f"{n:08x}" + "ab" * 12  # ilk 8 karakter (slug eki) benzersiz


def baslik(html: str) -> str:
    return re.search(r"<title>(.*?)</title>", html).group(1)


def robots(html: str) -> str:
    return re.search(r'<meta name="robots" content="([^"]+)"', html).group(1)


def site_haritasi(derleme) -> set[str]:
    return {y for y, _ in derleme.sitemap}


# --- 1. Kalıcı merkez adresleri ---------------------------------------------

def test_kalici_kurum_ve_yeni_merkezler_bosken_de_uretilir():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    for yol in ("/kurum/saglik-bakanligi/", "/kurum/adalet-bakanligi/",
                "/belediye-personel-alimlari/", "/kpss-siz-kamu-ilanlari/",
                "/askeri-personel-alimlari/"):
        html = derleme.sayfalar[yol]
        assert "Şu an açık ilan yok" in html
        assert robots(html) == "noindex,follow"
        assert yol not in site_haritasi(derleme)


def test_kalici_olmayan_kurum_acik_ilan_yoksa_uretilmez():
    gecmis = satir(id=kimlik(7), kurum="MUCUR BELEDİYE BAŞKANLIĞI", basvuru_bitis="2026-09-20")
    derleme = derle([satir(), gecmis], SIMDI, en_az_acik=1)
    assert "/kurum/mucur-belediye-baskanligi/" not in derleme.sayfalar


# --- 2. Başlık ve meta ------------------------------------------------------

def test_merkez_basligi_yili_derleme_zamanindan_alir():
    assert baslik(derle([satir()], SIMDI, en_az_acik=1).sayfalar["/memur-alimlari/"]) == (
        "Memur Alımları 2026: Güncel Kamu Memur İlanları | Kamu"
    )
    sonraki_yil = datetime(2027, 1, 5, 9, 0, tzinfo=timezone.utc)
    ileri = satir(basvuru_baslangic="2027-01-01", basvuru_bitis="2027-01-20",
                  eklenme_tarihi="2027-01-02T10:00:00+00:00")
    html = derle([ileri], sonraki_yil, en_az_acik=1).sayfalar["/memur-alimlari/"]
    assert "Memur Alımları 2027:" in baslik(html)


def test_sehir_basligi_kalibi():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    assert baslik(derleme.sayfalar["/sehir/istanbul/"]) == (
        "İstanbul Kamu Personel Alımı 2026: Güncel İlanlar | Kamu"
    )


def test_ilan_basligi_kalibi_ve_uzunsa_kisa_kurum():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    html = derleme.sayfalar[Ilan.from_satir(satir()).yol]
    # Tam kurum adıyla 60 karakteri aştığı için kısa ad (BDDK) kullanılır.
    assert baslik(html) == "BDDK Sözleşmeli Bilişim Personeli Alımı (15 Kadro): Şartlar ve Başvuru | Kamu"
    kisa = satir(id=kimlik(9), kurum="SGK", pozisyon="5 MEMUR ALACAK", kisi_sayisi=5, ilan_turu="Memur")
    html2 = derle([kisa], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(kisa).yol]
    assert baslik(html2) == "SGK Memur Alımı (5 Kadro): Şartlar ve Başvuru | Kamu"


def test_belediye_ilaninda_belediyesi_varyanti_gecer():
    bel = satir(id=kimlik(3), kurum="MUCUR BELEDİYE BAŞKANLIĞI", pozisyon="2 MEMUR ALACAK",
                kisi_sayisi=2, ilan_turu="Memur", sehirler=["Kırşehir"])
    html = derle([bel], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(bel).yol]
    assert "Mucur Belediyesi (Mucur Belediye Başkanlığı)" in html
    assert baslik(html).startswith("Mucur Belediyesi Memur Alımı (2 Kadro)")


def test_ayni_kurum_ve_pozisyonda_kopya_baslik_kalmaz():
    ortak = dict(kurum="ATATÜRK ÜNİVERSİTESİ", pozisyon="9 ÖĞRETİM ÜYESİ ALACAK",
                 kisi_sayisi=9, ilan_turu="Akademik Personel", sehirler=["Erzurum"])
    satirlar = [
        satir(id=kimlik(21), basvuru_baslangic="2026-10-01", basvuru_bitis="2026-10-15", **ortak),
        satir(id=kimlik(22), basvuru_baslangic="2026-10-05", basvuru_bitis="2026-10-20", **ortak),
        satir(id=kimlik(23), basvuru_baslangic="2026-10-05", basvuru_bitis="2026-10-20", **ortak),
        satir(),
    ]
    derleme = derle(satirlar, SIMDI, en_az_acik=1)
    basliklar = [baslik(h) for y, h in derleme.sayfalar.items() if y != "/404.html"]
    kopyalar = [b for b, n in Counter(basliklar).items() if n > 1]
    assert kopyalar == []
    birinci = baslik(derleme.sayfalar[Ilan.from_satir(satirlar[0]).yol])
    assert "1–15 Ekim" in birinci


def test_ekmek_kirintisi_son_ogesinde_kurum_var():
    html = derle([satir()], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(satir()).yol]
    kirinti = next(v for v in jsonld_listesi(html) if v["@type"] == "BreadcrumbList")
    assert kirinti["itemListElement"][-1]["name"] == "BDDK Sözleşmeli Bilişim Personeli"
    assert '<span aria-current="page">BDDK Sözleşmeli Bilişim Personeli</span>' in html


# --- 3. Dönüşüm ---------------------------------------------------------------

def test_apple_itunes_app_her_sayfada_ilanda_app_argument():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    temel = 'content="app-id=6792290422, affiliate-data=pt=129188874&amp;ct=seo'
    for yol, html in derleme.sayfalar.items():
        assert f'<meta name="apple-itunes-app" {temel}' in html, yol
    ilan = Ilan.from_satir(satir())
    assert f"app-argument=https://kamuuygulama.me{ilan.yol}" in derleme.sayfalar[ilan.yol]
    assert "app-argument" not in derleme.sayfalar["/memur-alimlari/"]


def test_mobil_alt_cubuk_ve_ilan_ozet_sirasi():
    html = derle([satir()], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(satir()).yol]
    assert 'class="alt-cubuk"' in html and "Son günü kaçırma" in html
    assert "Uygulamada aç" not in html
    # Tek DOM: başlık, özet (defter, resmî kaynak, çağrı), gövde.
    sira = [html.index(x) for x in ('class="ilan-bas"', 'class="defter"', 'class="resmi"',
                                     'class="cagri ilan-cagri"', 'class="govde"')]
    assert sira == sorted(sira)
    assert "viewport-fit=cover" in html
    css = (STATIK / "kamu.css").read_text(encoding="utf-8")
    assert "safe-area-inset-bottom" in css
    assert "body.cubuklu { padding-bottom: calc(76px + env(safe-area-inset-bottom)); }" in css
    assert ".ilan-izgara > .ozet { display: contents; }" in css


# --- 4. Güven sayfaları ---------------------------------------------------------

def test_guven_sayfalari_ve_icerikleri():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    for yol in ("/hakkinda/", "/iletisim/", "/gizlilik/", "/nasil-calisir/"):
        assert robots(derleme.sayfalar[yol]).startswith("index")
        assert yol in site_haritasi(derleme)
    assert "mailto:selmangurbuzer@gmail.com" in derleme.sayfalar["/iletisim/"]
    gizlilik = derleme.sayfalar["/gizlilik/"]
    assert "https://selmangrbzr.github.io/memur-ilanlari/privacy-policy.html" in gizlilik
    assert "çerez" in gizlilik
    nasil = derleme.sayfalar["/nasil-calisir/"]
    for ifade in ("kamuilan.sbb.gov.tr", "günde dört kez", "yapay zekâ", "hata", "mailto:"):
        assert ifade in nasil


def test_footer_hakkinda_grubu_ve_ana_sayfa_nasil_calisir_linki():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    assert "Kamu hakkında" in derleme.sayfalar["/memur-alimlari/"]
    ana = derleme.sayfalar["/"]
    assert 'href="/nasil-calisir/">Bu sayfalar nasıl hazırlanıyor?</a>' in ana


def test_ana_sayfa_organization_ve_website_jsonld():
    ana = derle([satir()], SIMDI, en_az_acik=1).sayfalar["/"]
    veriler = {v["@type"]: v for v in jsonld_listesi(ana)}
    org = veriler["Organization"]
    assert org["name"] == "Kamu" and org["url"] == "https://kamuuygulama.me/"
    assert org["logo"].startswith("https://kamuuygulama.me/")
    assert "https://www.instagram.com/kamu.uygulama/" in org["sameAs"]
    assert any("play.google.com" in s for s in org["sameAs"])
    assert any("apps.apple.com" in s for s in org["sameAs"])
    assert veriler["WebSite"]["alternateName"] == "Kamu: Memur Alım İlanları"


# --- 5. Yeni merkezler --------------------------------------------------------

def test_kurum_sayfasi_esik_ve_ilandan_link():
    tek = derle([satir()], SIMDI, en_az_acik=1)
    yol = "/kurum/bankacilik-duzenleme-ve-denetleme-kurumu/"
    assert robots(tek.sayfalar[yol]) == "noindex,follow"
    ilan_html = tek.sayfalar[Ilan.from_satir(satir()).yol]
    assert f'href="{yol}"' in ilan_html
    iki = derle(iki_ilan(), SIMDI, en_az_acik=1)
    assert robots(iki.sayfalar[yol]).startswith("index")
    assert yol in site_haritasi(iki)
    assert "Bankacılık Düzenleme ve Denetleme Kurumu Personel Alımı 2026" in baslik(iki.sayfalar[yol])


def test_kurum_slugi_alt_birimleri_kalici_kuruma_toplar():
    alt = satir(id=kimlik(5), kurum="T.C. SAĞLIK BAKANLIĞI PERSONEL GENEL MÜDÜRLÜĞÜ")
    assert Ilan.from_satir(alt).kurum_slug == "saglik-bakanligi"


def test_son_basvurusu_yaklasan_ve_bu_hafta_eklenen():
    yakin = satir(id=kimlik(11), basvuru_bitis="2026-10-12", eklenme_tarihi="2026-09-20T10:00:00+00:00")
    uzak = satir(id=kimlik(12), basvuru_bitis="2026-11-30", eklenme_tarihi="2026-10-06T10:00:00+00:00")
    derleme = derle([yakin, uzak], SIMDI, en_az_acik=1)
    yaklasan = derleme.sayfalar["/son-basvurusu-yaklasan-ilanlar/"]
    assert Ilan.from_satir(yakin).yol in yaklasan and Ilan.from_satir(uzak).yol not in yaklasan
    hafta = derleme.sayfalar["/bu-hafta-eklenen-kamu-ilanlari/"]
    assert Ilan.from_satir(uzak).yol in hafta and Ilan.from_satir(yakin).yol not in hafta


def test_belediye_merkezi():
    bel = satir(id=kimlik(3), kurum="ŞİLE BELEDİYE BAŞKANLIĞI")
    html = derle([satir(), bel], SIMDI, en_az_acik=1).sayfalar["/belediye-personel-alimlari/"]
    assert Ilan.from_satir(bel).yol in html
    assert Ilan.from_satir(satir()).yol not in html


def test_kpss_siz_merkez_akademigi_ve_kpssli_ilani_almaz_uyari_verir():
    kpss_siz = satir(id=kimlik(31), kpss_puan_turu=None, ilan_turu="İşçi")
    akademik = satir(id=kimlik(32), kpss_puan_turu=None, ilan_turu="Akademik Personel")
    derleme = derle([satir(), kpss_siz, akademik], SIMDI, en_az_acik=1)
    html = derleme.sayfalar["/kpss-siz-kamu-ilanlari/"]
    assert Ilan.from_satir(kpss_siz).yol in html
    assert Ilan.from_satir(akademik).yol not in html
    assert Ilan.from_satir(satir()).yol not in html
    assert "KPSS şartı ilan metninde belirtilmemiş olabilir" in html
    assert "resmî ilanı kontrol et" in html


# --- 6. Küçük düzeltmeler -----------------------------------------------------

def test_ana_sayfa_yalnizca_indekslenen_sehirlere_link_verir():
    istanbul = [satir(id=kimlik(40 + n)) for n in range(3)]  # İstanbul: 3 ilan, eşik 3
    ankara = satir(id=kimlik(50), sehirler=["Ankara"], sehir="Ankara")
    ana = derle([*istanbul, ankara], SIMDI, en_az_acik=1).sayfalar["/"]
    assert 'href="/sehir/istanbul/"' in ana
    assert 'href="/sehir/ankara/"' not in ana


def test_font_yedegi_ve_onyukleme():
    css = (STATIK / "kamu.css").read_text(encoding="utf-8")
    assert '"PJS Yedek"' in css and "size-adjust:" in css and "ascent-override:" in css
    html = derle([satir()], SIMDI, en_az_acik=1).sayfalar["/"]
    for agirlik in (400, 700, 800):
        assert f'href="/fontlar/pjs-{agirlik}.woff2" as="font"' in html
        assert (STATIK / f"fontlar/pjs-{agirlik}.woff2").exists()


def test_og_gorseli_1200x630_ve_buyuk_kart():
    png = (STATIK / "og-kamu.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", png[16:24]) == (1200, 630)
    html = derle([satir()], SIMDI, en_az_acik=1).sayfalar["/"]
    assert 'content="https://kamuuygulama.me/og-kamu.png"' in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html


def test_jsonld_gecerli_json_her_sayfada():
    derleme = derle(iki_ilan(), SIMDI, en_az_acik=1)
    for html in derleme.sayfalar.values():
        for blok in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html):
            json.loads(blok)


def test_uzun_pozisyon_basligi_kisaltilir_adet_atilir():
    uzun = satir(id=kimlik(61), kurum="MİLLİ SAVUNMA BAKANLIĞI", kisi_sayisi=None,
                 pozisyon="2026 YILI TABİP, DİŞ TABİBİ SINIFI SÖZLEŞMELİ/MUVAZZAF SUBAY VE ÖZEL "
                          "NİTELİKLİ BEDEN EĞİTİMİ ÖĞRETMENİ SINIFI MUVAZZAF SUBAY ADAYI TEMİNİ")
    html = derle([uzun], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(uzun).yol]
    assert len(baslik(html)) < 140 and "…" in baslik(html)
    adet = Ilan.from_satir(satir(pozisyon="5 ADET ÖĞRETİM ELEMANI ALACAK", kisi_sayisi=5))
    assert adet.is_basligi == "Öğretim Elemanı"
    assert adet.slug == Ilan.from_satir(satir(pozisyon="5 ADET ÖĞRETİM ELEMANI ALACAK", kisi_sayisi=None)).slug
