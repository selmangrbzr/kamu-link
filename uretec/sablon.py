"""Ortak HTML iskeleti ve bileşenler ("editoryal bülten" tasarımı).

Tüm veri html.escape'ten geçer (e()). Sayfalar JS kullanmaz; mağaza linkleri
kampanya parametreleriyle derleme anında yazılır. Büyük harfli etiket yoktur.
"""

import html
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import quote

from .jsonld import SITE_ADI, SITE_URL, script_etiketi
from .metin import kalan_gun_metni, sayi_tr, tarih_tr
from .model import TR_SAAT, Ilan

ACIL_GUN_SINIRI = 3
CSS_YOLU = "/kamu.css"
IKON = "/kamu-icon-512.png"
IKON_KUCUK = "/kamu-ikon-96.png"
OG_GORSEL = "/og-kamu.png"
APP_STORE_ID = "6792290422"
APP_STORE_PT = "129188874"
PLAY_PAKET = "com.selman.memur_ilanlari"
KAMPANYA_SEO = "seo"
FONT_AGIRLIKLARI = (400, 700, 800)
UYARI = (
    "Bu bilgileri ilan metninden otomatik çıkarıyoruz, hata olabilir. Başvurmadan önce "
    "resmî ilanı oku. Kamu bağımsız bir uygulama, resmî kurum değil."
)
OK_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'


def e(metin: object) -> str:
    return html.escape(str(metin), quote=True)


def magaza_linkleri(kampanya: str) -> tuple[str, str]:
    """(App Store, Google Play) linkleri; yonlendir.js ile aynı biçim."""
    ios = (
        f"https://apps.apple.com/tr/app/apple-store/id{APP_STORE_ID}"
        f"?pt={APP_STORE_PT}&ct={kampanya}&mt=8"
    )
    referrer = f"utm_source={kampanya}&utm_medium=social&utm_campaign={kampanya}"
    android = (
        f"https://play.google.com/store/apps/details?id={PLAY_PAKET}"
        f"&referrer={quote(referrer, safe='')}"
    )
    return ios, android


def magaza_butonlari(kampanya: str) -> str:
    ios, android = magaza_linkleri(kampanya)
    return (
        '<div class="magazalar">'
        f'<a class="dugme dugme-dolu" href="{e(android)}">Google Play</a>'
        f'<a class="dugme dugme-cizgi" href="{e(ios)}">App Store</a>'
        "</div>"
    )


def apple_uygulama_meta(uygulama_argumani: str | None = None) -> str:
    """Safari Smart App Banner; ilan sayfalarında açılacak adres de verilir."""
    icerik = f"app-id={APP_STORE_ID}, affiliate-data=pt={APP_STORE_PT}&ct={KAMPANYA_SEO}"
    if uygulama_argumani:
        icerik += f", app-argument={uygulama_argumani}"
    return f'<meta name="apple-itunes-app" content="{e(icerik)}">'


@dataclass(frozen=True)
class SayfaBasi:
    baslik: str
    aciklama: str
    yol: str
    indekslenebilir: bool = True
    og_turu: str = "website"
    kampanya: str = KAMPANYA_SEO
    uygulama_argumani: bool = False
    kunye_alt: str | None = None  # künyenin ikinci satırı; None ise "N açık ilan"


def _kunye(simdi: datetime, alt_satir: str) -> str:
    gun = tarih_tr(simdi.astimezone(TR_SAAT).date(), yil=True)
    return (
        '<header class="kunye"><div class="kap kunye-ic">'
        f'<a class="marka" href="/"><img src="{IKON_KUCUK}" width="32" height="32" alt="">'
        f"<span>{SITE_ADI}</span></a>"
        f'<span class="kunye-sag"><b>{gun}</b><br>{e(alt_satir)}</span>'
        '</div><div class="cift-cizgi"></div></header>'
    )


ALT_LINKLER = (
    ("Memur alımları", "/memur-alimlari/"),
    ("Sözleşmeli personel", "/sozlesmeli-personel-alimlari/"),
    ("İşçi alımları", "/isci-alimlari/"),
    ("Akademik personel", "/akademik-personel-alimlari/"),
    ("Askeri personel", "/askeri-personel-alimlari/"),
    ("Belediye alımları", "/belediye-personel-alimlari/"),
    ("Lise mezunu", "/lise-mezunu-kamu-ilanlari/"),
    ("Ön lisans mezunu", "/onlisans-mezunu-kamu-ilanlari/"),
    ("Lisans mezunu", "/lisans-mezunu-kamu-ilanlari/"),
    ("KPSS P3", "/kpss-p3-ilanlari/"),
    ("KPSS P93", "/kpss-p93-ilanlari/"),
    ("KPSS P94", "/kpss-p94-ilanlari/"),
    ("Son başvurusu yaklaşanlar", "/son-basvurusu-yaklasan-ilanlar/"),
    ("Bu hafta eklenenler", "/bu-hafta-eklenen-kamu-ilanlari/"),
)
HAKKINDA_LINKLERI = (
    ("Hakkında", "/hakkinda/"),
    ("Nasıl çalışır?", "/nasil-calisir/"),
    ("İletişim", "/iletisim/"),
    ("Gizlilik", "/gizlilik/"),
)


def _link_listesi(linkler: tuple[tuple[str, str], ...]) -> str:
    return "<ul>" + "".join(f'<li><a href="{e(yol)}">{e(ad)}</a></li>' for ad, yol in linkler) + "</ul>"


def _kolofon(simdi: datetime, mevcut_yollar: frozenset[str], kampanya: str) -> str:
    """Alt bilgi: künyenin aynası (çift çizgi), kategoriler, hakkında, uygulama, tek dipnot."""
    kategoriler = tuple((ad, yol) for ad, yol in ALT_LINKLER if yol in mevcut_yollar)
    yarim = (len(kategoriler) + 1) // 2
    ios, android = magaza_linkleri(kampanya)
    zaman = simdi.astimezone(TR_SAAT)
    return (
        '<footer class="kolofon"><div class="kap"><div class="cift-cizgi"></div>'
        '<div class="kolofon-izgara">'
        '<nav aria-labelledby="k-kategori"><h2 id="k-kategori">Kategoriler</h2>'
        '<div class="kolofon-sutun">'
        f"{_link_listesi(kategoriler[:yarim])}{_link_listesi(kategoriler[yarim:])}</div></nav>"
        '<nav aria-labelledby="k-hakkinda"><h2 id="k-hakkinda">Kamu hakkında</h2>'
        f"{_link_listesi(HAKKINDA_LINKLERI)}</nav>"
        '<div><h2>Uygulama</h2>'
        f'<ul><li><a href="{e(android)}">Google Play</a></li><li><a href="{e(ios)}">App Store</a></li></ul></div>'
        "</div>"
        f'<p class="dipnot">{e(UYARI)} Kaynak: kamuilan.sbb.gov.tr. Son güncelleme '
        f"{tarih_tr(zaman.date(), yil=True)}, {zaman:%H:%M}.</p>"
        "</div></footer>"
    )


def alt_cubuk(kampanya: str) -> str:
    """Mobilde altta sabit uygulama çubuğu (JS'siz; geniş ekranda CSS ile gizlenir)."""
    ios, android = magaza_linkleri(kampanya)
    return (
        '<div class="alt-cubuk" role="complementary" aria-label="Kamu uygulaması">'
        '<span class="alt-cubuk-metin"><b>Son günü kaçırma</b>Ücretsiz bildirim al</span>'
        f'<a class="mini-dolu" href="{e(android)}">Google Play</a>'
        f'<a class="mini-cizgi" href="{e(ios)}">App Store</a>'
        "</div>"
    )


def _font_onyukleme() -> str:
    return "".join(
        f'<link rel="preload" href="/fontlar/pjs-{agirlik}.woff2" as="font" type="font/woff2" crossorigin>'
        for agirlik in FONT_AGIRLIKLARI
    )


def sayfa(
    bas: SayfaBasi,
    govde: str,
    simdi: datetime,
    mevcut_yollar: frozenset[str],
    jsonld: tuple[dict, ...] = (),
    kunye_alt: str = "",
) -> str:
    kanonik = SITE_URL + bas.yol
    robots = "index,follow,max-image-preview:large" if bas.indekslenebilir else "noindex,follow"
    yapisal = "".join(script_etiketi(v) for v in jsonld)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="tr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
        f"<title>{e(bas.baslik)}</title>"
        f'<meta name="description" content="{e(bas.aciklama)}">'
        f'<meta name="robots" content="{robots}">'
        f'<link rel="canonical" href="{e(kanonik)}">'
        '<meta name="theme-color" content="#16265C">'
        f"{apple_uygulama_meta(kanonik if bas.uygulama_argumani else None)}"
        f"{_font_onyukleme()}"
        f'<link rel="stylesheet" href="{CSS_YOLU}">'
        f'<link rel="icon" type="image/png" href="{IKON_KUCUK}">'
        f'<link rel="apple-touch-icon" href="{IKON}">'
        f'<meta property="og:title" content="{e(bas.baslik)}">'
        f'<meta property="og:description" content="{e(bas.aciklama)}">'
        f'<meta property="og:url" content="{e(kanonik)}">'
        f'<meta property="og:type" content="{bas.og_turu}">'
        f'<meta property="og:site_name" content="{SITE_ADI}">'
        '<meta property="og:locale" content="tr_TR">'
        f'<meta property="og:image" content="{SITE_URL}{OG_GORSEL}">'
        '<meta property="og:image:width" content="1200">'
        '<meta property="og:image:height" content="630">'
        '<meta property="og:image:alt" content="Kamu: kamu personel alım ilanları">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'{yapisal}</head><body class="cubuklu">'
        f"{_kunye(simdi, bas.kunye_alt or kunye_alt)}"
        f'<main class="kap">{govde}</main>'
        f"{_kolofon(simdi, mevcut_yollar, bas.kampanya)}"
        f"{alt_cubuk(bas.kampanya)}"
        "</body></html>\n"
    )


def kirinti(ogeler: list[tuple[str, str]]) -> str:
    """Görünür ekmek kırıntısı; son öğe link değildir."""
    parcalar = [f'<a href="{e(yol)}">{e(ad)}</a>' for ad, yol in ogeler[:-1]]
    parcalar.append(f'<span aria-current="page">{e(ogeler[-1][0])}</span>')
    return f'<nav class="kirinti" aria-label="Konum">{" / ".join(parcalar)}</nav>'


def bolum_bas(kimlik: str, baslik: str, sag: str = "") -> str:
    """Gazete bölüm çizgisiyle başlık; sağda link ya da kısa not."""
    return f'<div class="bolum-bas"><h2 id="{kimlik}">{e(baslik)}</h2>{sag}</div>'


def acil_mi(ilan: Ilan, bugun: date) -> bool:
    return 0 <= (ilan.basvuru_bitis - bugun).days <= ACIL_GUN_SINIRI


def rozet(ilan: Ilan, bugun: date) -> str:
    if not acil_mi(ilan, bugun):
        return ""
    return f'<span class="rozet">{e(kalan_gun_metni(ilan.basvuru_bitis, bugun))}</span>'


def ilan_satiri(
    ilan: Ilan,
    bugun: date,
    yeni_sinir: datetime | None = None,
    tur: bool = True,
    kurum: bool = True,
) -> str:
    """Liste satırı: solda kadro sayısı, sonra kurum, pozisyon ve meta."""
    if ilan.kisi_sayisi:
        sayi = f'<span class="satir-sayi"><b>{sayi_tr(ilan.kisi_sayisi)}</b><small>kadro</small></span>'
    else:
        sayi = '<span class="satir-sayi yok"><small>Kadro<br>ilanda</small></span>'
    meta = []
    if yeni_sinir and ilan.eklenme_tarihi >= yeni_sinir:
        meta.append('<span class="yeni">Yeni</span>')
    if tur:
        meta.append(f'<span class="tur" data-tur="{ilan.tur_kodu}">{e(ilan.tur_etiketi)}</span>')
    kalan = (ilan.basvuru_bitis - bugun).days
    meta.append(f"<span>Son başvuru {tarih_tr(ilan.basvuru_bitis)}</span>")
    if kalan < 0:
        meta.append('<span class="kapali-etiket">Süresi doldu</span>')
    elif kalan <= ACIL_GUN_SINIRI:
        meta.append(rozet(ilan, bugun))
    else:
        meta.append(f'<span class="kalan">{kalan} gün</span>')
    if kurum:
        baslik = (
            f'<span class="satir-kurum">{e(ilan.kisa_kurum)}</span>'
            f'<span class="satir-poz">{e(ilan.is_basligi)}</span>'
        )
    else:
        baslik = f'<span class="satir-kurum">{e(ilan.is_basligi)}</span>'
    return (
        f'<li class="satir"><a href="{ilan.yol}">{sayi}{baslik}'
        f'<span class="satir-meta">{"".join(meta)}</span></a></li>'
    )


def ilan_listesi(
    ilanlar: list[Ilan],
    bugun: date,
    yeni_sinir: datetime | None = None,
    tur: bool = True,
    kurum: bool = True,
) -> str:
    satirlar = "".join(ilan_satiri(i, bugun, yeni_sinir, tur, kurum) for i in ilanlar)
    return f'<ul class="satirlar">{satirlar}</ul>'


def _gun(ilan: Ilan, bugun: date) -> str:
    kalan = (ilan.basvuru_bitis - bugun).days
    if kalan == 0:
        return '<span class="gun bugun"><b>Bugün</b><small>son gün</small></span>'
    alt = "Yarın" if kalan == 1 else f"{kalan} gün"
    return f'<span class="gun"><b>{tarih_tr(ilan.basvuru_bitis)}</b><small>{alt}</small></span>'


def siki_liste(ilanlar: list[Ilan], bugun: date) -> str:
    """Yan sütun listesi: kurum, pozisyon ve sağda son gün."""
    return '<ul class="sikilar">' + "".join(
        f'<li><a href="{i.yol}"><span class="k">{e(i.kisa_kurum)}</span>'
        f'<span class="p">{e(i.is_basligi)}</span>{_gun(i, bugun)}</a></li>'
        for i in ilanlar
    ) + "</ul>"


def uygulama_cagrisi(
    baslik: str, metin: str, kampanya: str, sinif: str = "", kimlik: str = "cagri"
) -> str:
    """Lacivert kapanış kutusu; turkuaz ok dairesi sayfadaki tek dolu turkuaz öğe."""
    siniflar = f"cagri {sinif}".strip()
    return (
        f'<section class="{siniflar}" aria-labelledby="{kimlik}">'
        f'<div class="cagri-bas"><span class="cagri-ok">{OK_SVG}</span><div>'
        f'<h2 id="{kimlik}">{e(baslik)}</h2><p>{e(metin)}</p></div></div>'
        f"{magaza_butonlari(kampanya)}</section>"
    )
