"""Ortak HTML iskeleti ve bileşenler.

Tüm veri html.escape'ten geçer (e()). Sayfalar JS kullanmaz; mağaza linkleri
kampanya parametreleriyle derleme anında yazılır.
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
UYARI = (
    "Bilgiler ilan metninden otomatik çıkarılmıştır, hata içerebilir; başvurmadan "
    "önce resmî ilanı kontrol edin. Kamu bağımsız bir uygulamadır, resmî kurum değildir."
)


def e(metin: object) -> str:
    return html.escape(str(metin), quote=True)


def magaza_linkleri(kampanya: str) -> tuple[str, str]:
    """(App Store, Google Play) linkleri; yonlendir.js ile aynı biçim."""
    ios = (
        "https://apps.apple.com/tr/app/apple-store/id6792290422"
        f"?pt=129188874&ct={kampanya}&mt=8"
    )
    referrer = f"utm_source={kampanya}&utm_medium=social&utm_campaign={kampanya}"
    android = (
        "https://play.google.com/store/apps/details?id=com.selman.memur_ilanlari"
        f"&referrer={quote(referrer, safe='')}"
    )
    return ios, android


def magaza_butonlari(kampanya: str) -> str:
    ios, android = magaza_linkleri(kampanya)
    return (
        '<div class="magazalar">'
        f'<a class="dugme dugme-dolu" href="{e(android)}">Google Play\'den indir</a>'
        f'<a class="dugme dugme-cizgi" href="{e(ios)}">App Store\'dan indir</a>'
        "</div>"
    )


@dataclass(frozen=True)
class SayfaBasi:
    baslik: str
    aciklama: str
    yol: str
    indekslenebilir: bool = True
    og_turu: str = "website"
    bolum: str = ""


def _kunye(bolum: str, simdi: datetime) -> str:
    gun = tarih_tr(simdi.astimezone(TR_SAAT).date())
    sag = f"{e(bolum)} · {gun}" if bolum else gun
    return (
        '<header class="kunye"><div class="kap kunye-ic">'
        f'<a class="marka" href="/"><img src="{IKON_KUCUK}" width="32" height="32" alt="">'
        f"<span>{SITE_ADI}</span></a>"
        f'<span class="kunye-sag">{sag}</span>'
        "</div></header>"
    )


ALT_LINKLER = (
    ("Memur alımları", "/memur-alimlari/"),
    ("Sözleşmeli personel", "/sozlesmeli-personel-alimlari/"),
    ("İşçi alımları", "/isci-alimlari/"),
    ("Akademik personel", "/akademik-personel-alimlari/"),
    ("Lise mezunu", "/lise-mezunu-kamu-ilanlari/"),
    ("Ön lisans mezunu", "/onlisans-mezunu-kamu-ilanlari/"),
    ("Lisans mezunu", "/lisans-mezunu-kamu-ilanlari/"),
    ("KPSS P3", "/kpss-p3-ilanlari/"),
    ("KPSS P93", "/kpss-p93-ilanlari/"),
    ("KPSS P94", "/kpss-p94-ilanlari/"),
)


def _alt_bilgi(simdi: datetime, mevcut_yollar: frozenset[str]) -> str:
    linkler = "".join(
        f'<li><a href="{yol}">{e(ad)}</a></li>'
        for ad, yol in ALT_LINKLER
        if yol in mevcut_yollar
    )
    zaman = simdi.astimezone(TR_SAAT)
    return (
        '<footer class="alt"><div class="kap">'
        f'<nav aria-label="Kategoriler"><ul class="alt-linkler">{linkler}</ul></nav>'
        f'<p class="dipnot">{e(UYARI)}</p>'
        f'<p class="dipnot">Son güncelleme: {tarih_tr(zaman.date(), yil=True)} '
        f"{zaman:%H:%M}. Kaynak: kamuilan.sbb.gov.tr ilanları.</p>"
        "</div></footer>"
    )


def sayfa(
    bas: SayfaBasi,
    govde: str,
    simdi: datetime,
    mevcut_yollar: frozenset[str],
    jsonld: tuple[dict, ...] = (),
) -> str:
    kanonik = SITE_URL + bas.yol
    robots = "index,follow,max-image-preview:large" if bas.indekslenebilir else "noindex,follow"
    yapisal = "".join(script_etiketi(v) for v in jsonld)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="tr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{e(bas.baslik)}</title>"
        f'<meta name="description" content="{e(bas.aciklama)}">'
        f'<meta name="robots" content="{robots}">'
        f'<link rel="canonical" href="{e(kanonik)}">'
        '<meta name="theme-color" content="#16265C">'
        f'<link rel="preload" href="/fontlar/pjs-400.woff2" as="font" type="font/woff2" crossorigin>'
        f'<link rel="preload" href="/fontlar/pjs-800.woff2" as="font" type="font/woff2" crossorigin>'
        f'<link rel="stylesheet" href="{CSS_YOLU}">'
        '<link rel="icon" type="image/png" href="/kamu-ikon-96.png">'
        f'<link rel="apple-touch-icon" href="{IKON}">'
        f'<meta property="og:title" content="{e(bas.baslik)}">'
        f'<meta property="og:description" content="{e(bas.aciklama)}">'
        f'<meta property="og:url" content="{e(kanonik)}">'
        f'<meta property="og:type" content="{bas.og_turu}">'
        f'<meta property="og:site_name" content="{SITE_ADI}">'
        '<meta property="og:locale" content="tr_TR">'
        f'<meta property="og:image" content="{SITE_URL}{IKON}">'
        '<meta name="twitter:card" content="summary">'
        f"{yapisal}</head><body>"
        f"{_kunye(bas.bolum, simdi)}"
        f'<main class="kap">{govde}</main>'
        f"{_alt_bilgi(simdi, mevcut_yollar)}"
        "</body></html>\n"
    )


def kirinti(ogeler: list[tuple[str, str]]) -> str:
    """Görünür ekmek kırıntısı; son öğe link değildir."""
    parcalar = [f'<a href="{e(yol)}">{e(ad)}</a>' for ad, yol in ogeler[:-1]]
    parcalar.append(f'<span aria-current="page">{e(ogeler[-1][0])}</span>')
    return f'<nav class="kirinti" aria-label="Konum">{" / ".join(parcalar)}</nav>'


def ust_etiket(metin: str) -> str:
    return f'<p class="ust-etiket"><span class="cubuk" aria-hidden="true"></span>{e(metin)}</p>'


def acil_mi(ilan: Ilan, bugun: date) -> bool:
    return 0 <= (ilan.basvuru_bitis - bugun).days <= ACIL_GUN_SINIRI


def rozet(ilan: Ilan, bugun: date) -> str:
    if not acil_mi(ilan, bugun):
        return ""
    return f'<span class="rozet">{e(kalan_gun_metni(ilan.basvuru_bitis, bugun))}</span>'


def ilan_karti(ilan: Ilan, bugun: date) -> str:
    kadro = f"<b>{sayi_tr(ilan.kisi_sayisi)}</b> kadro · " if ilan.kisi_sayisi else ""
    kalan = (ilan.basvuru_bitis - bugun).days
    sure = f"{kalan} gün" if kalan > ACIL_GUN_SINIRI else ""
    sure_html = f' · <span class="kalan">{sure}</span>' if sure else ""
    return (
        f'<li class="kart" data-tur="{ilan.tur_kodu}"><a href="{ilan.yol}">'
        f'<span class="kart-ust"><span class="tur">{e(ilan.tur_etiketi)}</span>'
        f'<span class="kart-kurum">{e(ilan.kisa_kurum)}</span></span>'
        f'<span class="kart-baslik">{e(ilan.is_basligi)}</span>'
        f'<span class="kart-alt">{kadro}Son başvuru {tarih_tr(ilan.basvuru_bitis)}'
        f"{sure_html}{rozet(ilan, bugun)}</span>"
        "</a></li>"
    )


def ilan_listesi(ilanlar: list[Ilan], bugun: date) -> str:
    return '<ul class="liste">' + "".join(ilan_karti(i, bugun) for i in ilanlar) + "</ul>"


def uygulama_cagrisi(baslik: str, metin: str, kampanya: str) -> str:
    return (
        '<section class="cagri" aria-labelledby="cagri-baslik">'
        f'<h2 id="cagri-baslik">{e(baslik)}</h2>'
        f"<p>{e(metin)}</p>"
        f"{magaza_butonlari(kampanya)}"
        "</section>"
    )
