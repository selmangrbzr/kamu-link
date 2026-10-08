"""Merkez, ana sayfa, bilgi ve 404 sayfaları. İlan sayfası ilan_sayfasi.py'de."""

from datetime import timedelta

from .baglam import Baglam
from .bilgi import BilgiSayfasi, bilgi_sayfasi_parcalari
from .ilan_sayfasi import ilan_basliklari, ilan_sayfasi, kisalt
from .jsonld import ekmek_kirintisi, organizasyon, web_sitesi
from .merkezler import Merkez, MerkezVerisi
from .metin import sayi_tr
from .model import Ilan, kisa_kurum_adi
from .ozet import merkez_aciklamasi, ozet_parcalari
from .sablon import (
    KAMPANYA_SEO,
    SayfaBasi,
    bolum_bas,
    e,
    ilan_listesi,
    kirinti,
    siki_liste,
    uygulama_cagrisi,
)

__all__ = [
    "Baglam", "ana_sayfa", "bilgi_sayfasi", "ilan_basliklari", "ilan_sayfasi",
    "merkez_sayfasi", "sayfa_404",
]

KAMPANYA_ANA = "site"
ANA_SAYFA_KURUM_ADET = 12
DIZIN_SEHIR_ILK = 12
YAKLASAN_ADET = 6
YAKLASAN_GUN = 7
_KPSS_TURLERI = frozenset({"Memur", "Sözleşmeli Personel", "İşçi"})


def _sayilar_cumlesi(ilanlar: tuple[Ilan, ...] | list[Ilan], b: Baglam, bugun_on_ek: bool) -> str:
    """"Bugün 104 açık ilan ve toplam 2.950 kadro var. Son 7 günde 33 yeni ilan eklendi."."""
    if not ilanlar:
        return "Şu an açık ilan yok."
    kadro = sum(i.kisi_sayisi or 0 for i in ilanlar)
    yeni = sum(1 for i in ilanlar if i.eklenme_tarihi >= b.simdi - timedelta(days=7))
    bas = "Bugün " if bugun_on_ek else ""
    cumle = f"{bas}<b>{sayi_tr(len(ilanlar))}</b> açık ilan"
    cumle += f" ve toplam <b>{sayi_tr(kadro)}</b> kadro var." if kadro else " var."
    if yeni:
        cumle += f" Son 7 günde <b>{sayi_tr(yeni)}</b> yeni ilan eklendi."
    return cumle


# --- Merkez sayfası ----------------------------------------------------------

def _ozet_html(veri: MerkezVerisi, b: Baglam) -> str:
    parcalar = ozet_parcalari(veri, b.simdi, b.mevcut_yollar)
    if not parcalar:
        return ""
    metin = " ".join(f'<a href="{link}">{e(c)}</a>' if link else e(c) for c, link in parcalar)
    return f'<p class="ozet-cumleler">{metin}</p>'


def _diger_kategoriler(merkez: Merkez, digerleri: list[Merkez]) -> str:
    linkler = "".join(
        f'<li><a href="{m.yol}">{e(m.ad)}</a></li>' for m in digerleri if m.yol != merkez.yol
    )
    linkler += '<li><a href="/#kategori">Tüm kategoriler</a></li>'
    return (
        '<nav class="dizin-grup diger" aria-labelledby="diger">'
        f'{bolum_bas("diger", "Diğer kategoriler")}'
        f'<div class="dizin dizin-tek"><ul>{linkler}</ul></div></nav>'
    )


def _liste_bolumu(veri: MerkezVerisi, b: Baglam, ulusal: list[Ilan] | None) -> str:
    merkez = veri.merkez
    if not veri.acik:
        html = (
            '<section class="bolum" aria-labelledby="liste">'
            f'{bolum_bas("liste", "Açık ilanlar")}'
            '<div class="durum" role="status"><b>Şu an açık ilan yok.</b> Diğer '
            "kategorilerdeki açık ilanlara aşağıdan ulaşabilirsin.</div></section>"
        )
        if veri.kapanan:
            html += (
                '<section class="bolum" aria-labelledby="kapanan">'
                f'{bolum_bas("kapanan", "Son kapanan ilanlar")}'
                f"{ilan_listesi(list(veri.kapanan), b.bugun)}</section>"
            )
        return html
    not_ = "Son günü yakın olan üstte" if merkez.siralama == "bitis" else "En yeni üstte"
    liste = ilan_listesi(
        veri.sirali_acik, b.bugun, b.yeni_sinir,
        tur=merkez.grup != "tur", kurum=merkez.grup != "kurum",
    )
    html = (
        '<section class="bolum" aria-labelledby="liste">'
        f'{bolum_bas("liste", "Açık ilanlar", f"<span class=not>{not_}</span>")}{liste}</section>'
    )
    if merkez.il and ulusal:
        html += (
            '<section class="bolum" aria-labelledby="ulusal">'
            f'{bolum_bas("ulusal", "Türkiye genelinde kadro açan ilanlar")}'
            f'<p class="soluk">Bu ilanlar {e(merkez.il)} dahil çok sayıda ilde kadro içeriyor.</p>'
            f"{ilan_listesi(ulusal, b.bugun, b.yeni_sinir)}</section>"
        )
    return html


def merkez_sayfasi(
    veri: MerkezVerisi,
    b: Baglam,
    digerleri: list[Merkez],
    ulusal: list[Ilan] | None = None,
) -> str:
    merkez = veri.merkez
    uyari = f'<p class="uyari-not" role="note">{e(merkez.uyari)}</p>' if merkez.uyari else ""
    cagri = uygulama_cagrisi(
        "Yeni ilan çıkınca haberin olsun",
        "İlan türü, eğitim ve şehir seç; yalnızca sana uyan ilanlar için bildirim al. Ücretsiz.",
        KAMPANYA_SEO,
        "yalniz-genis",
        "cagri-merkez",
    )
    govde = (
        f"{kirinti([('Ana sayfa', '/'), (merkez.h1, merkez.yol)])}"
        '<section class="manset merkez-manset"><div>'
        f'<h1>{e(merkez.h1)}</h1><p class="manset-satir">{_sayilar_cumlesi(veri.acik, b, False)}</p>'
        "</div></section>"
        f'<p class="giris">{e(merkez.giris)}</p>{uyari}{_ozet_html(veri, b)}'
        '<div class="merkez-izgara">'
        f"<div>{_liste_bolumu(veri, b, ulusal)}</div>"
        f'<aside class="bolum">{cagri}{_diger_kategoriler(merkez, digerleri)}</aside>'
        "</div>"
    )
    bas = SayfaBasi(
        baslik=f"{merkez.baslik_metni(b.yil)} | Kamu",
        aciklama=kisalt(merkez_aciklamasi(veri)),
        yol=merkez.yol,
        indekslenebilir=veri.indekslenebilir,
    )
    jsonld = (ekmek_kirintisi([("Ana sayfa", "/"), (merkez.h1, merkez.yol)]),)
    return b.sayfa(bas, govde, jsonld)


# --- Ana sayfa ----------------------------------------------------------------

_DIZIN_GRUPLARI = (
    ("İlan türü", "tur"),
    ("Eğitim", "egitim"),
    ("KPSS puan türü", "puan"),
    ("Öne çıkanlar", "ozel"),
    ("Kurum", "kurum"),
)


def _cip_adi(merkez: Merkez) -> str:
    if merkez.il:
        return merkez.il
    return kisa_kurum_adi(merkez.ad) if merkez.grup == "kurum" else merkez.ad


def _dizin_li(veriler: list[MerkezVerisi]) -> str:
    return "".join(
        f'<li><a href="{v.merkez.yol}">{e(_cip_adi(v.merkez))}<span>{len(v.acik)}</span></a></li>'
        for v in veriler
    )


def kategori_dizini(veriler: list[MerkezVerisi]) -> str:
    """Kategoriler gazete dizini gibi; yalnızca indekslenebilir merkezler."""
    bloklar = []
    for baslik, grup in _DIZIN_GRUPLARI:
        uygun = [v for v in veriler if v.merkez.grup == grup and v.indekslenebilir]
        if grup == "kurum":
            uygun = sorted(uygun, key=lambda v: -len(v.acik))[:ANA_SAYFA_KURUM_ADET]
        if uygun:
            bloklar.append(f'<div class="dizin-grup"><h3>{baslik}</h3><ul>{_dizin_li(uygun)}</ul></div>')
    sehirler = sorted(
        (v for v in veriler if v.merkez.grup == "sehir" and v.indekslenebilir),
        key=lambda v: (-len(v.acik), v.merkez.il or ""),
    )
    if sehirler:
        ilk, kalan = sehirler[:DIZIN_SEHIR_ILK], sehirler[DIZIN_SEHIR_ILK:]
        tumu = ""
        if kalan:
            tumu = (
                f'<details class="tumu"><summary>Tüm şehirler ({len(sehirler)})</summary>'
                f'<ul>{_dizin_li(sorted(kalan, key=lambda v: v.merkez.il or ""))}</ul></details>'
            )
        bloklar.append(
            f'<div class="dizin-grup dizin-sehir"><h3>Şehir</h3><ul>{_dizin_li(ilk)}</ul>{tumu}</div>'
        )
    return f'<div class="dizin">{"".join(bloklar)}</div>'


def _yaklasanlar(acik: list[Ilan], b: Baglam) -> list[Ilan]:
    """Önümüzdeki 7 günde bitenler; KPSS ile alım yapan türler (memur, sözleşmeli, işçi) önce."""
    yakin = sorted(
        (i for i in acik if (i.basvuru_bitis - b.bugun).days <= YAKLASAN_GUN),
        key=lambda i: (i.basvuru_bitis, i.id),
    )
    kpss = [i for i in yakin if i.ilan_turu in _KPSS_TURLERI]
    return (kpss + [i for i in yakin if i.ilan_turu not in _KPSS_TURLERI])[:YAKLASAN_ADET]


def _ana_bolumler(acik: list[Ilan], b: Baglam) -> str:
    son = sorted(acik, key=lambda i: (i.eklenme_tarihi, i.id), reverse=True)[:12]
    buyuk = sorted(
        (i for i in acik if i.kisi_sayisi), key=lambda i: (i.kisi_sayisi or 0, i.id), reverse=True
    )[:6]
    yaklasan = _yaklasanlar(acik, b)
    bolumler = []
    if yaklasan:
        tumu = '<a href="/son-basvurusu-yaklasan-ilanlar/">Tümü</a>'
        bolumler.append(
            '<section class="bolum yaklasan" aria-labelledby="yak">'
            f'{bolum_bas("yak", "Son başvurusu yaklaşanlar", tumu)}{siki_liste(yaklasan, b.bugun)}</section>'
        )
    hafta = '<a href="/bu-hafta-eklenen-kamu-ilanlari/">Bu hafta eklenenler</a>'
    bolumler.append(
        '<section class="bolum son" aria-labelledby="son">'
        f'{bolum_bas("son", "Son eklenen ilanlar", hafta)}{ilan_listesi(son, b.bugun)}</section>'
    )
    if buyuk:
        bolumler.append(
            '<section class="bolum buyuk" aria-labelledby="buyuk">'
            f'{bolum_bas("buyuk", "En büyük alımlar")}{ilan_listesi(buyuk, b.bugun, b.yeni_sinir)}</section>'
        )
    return f'<div class="ana-izgara">{"".join(bolumler)}</div>'


def ana_sayfa(acik: list[Ilan], b: Baglam, veriler: list[MerkezVerisi]) -> str:
    cagri = uygulama_cagrisi(
        "Yeni ilan çıkınca haberin olsun",
        "Yeni ilan çıktığında ve son gün yaklaştığında telefonuna bildirim gelir. Ücretsiz.",
        KAMPANYA_ANA,
        "manset-cagri yalniz-genis",
        "cagri-ana",
    )
    govde = (
        '<section class="manset"><div><h1>Kamu ilanları, son başvuru kaçmadan</h1>'
        f'<p class="manset-satir">{_sayilar_cumlesi(acik, b, True)}</p>'
        '<p class="giris">Her ilanın kadrosunu, şartlarını ve son gününü tek sayfada gör; '
        "yeni ilan çıkınca uygulama haber versin.</p>"
        f"</div>{cagri}</section>"
        f"{_ana_bolumler(acik, b)}"
        '<section class="bolum" aria-labelledby="kategori">'
        f'{bolum_bas("kategori", "Kategoriler")}{kategori_dizini(veriler)}</section>'
    )
    bas = SayfaBasi(
        baslik=f"Kamu İlanları {b.yil}: Güncel Memur ve Kamu Personel Alımları | Kamu",
        aciklama=kisalt(
            f"{sayi_tr(len(acik))} açık kamu ilanı: memur, sözleşmeli, işçi ve akademik "
            "personel alımları. Kadro, şartlar ve son başvuru tarihleri tek sayfada."
        ),
        yol="/",
        kampanya=KAMPANYA_ANA,
    )
    return b.sayfa(bas, govde, (web_sitesi(), organizasyon()))


# --- Bilgi sayfaları ve 404 ---------------------------------------------------

def bilgi_sayfasi(bilgi: BilgiSayfasi, b: Baglam) -> str:
    bas, govde, kirinti_ogeleri = bilgi_sayfasi_parcalari(bilgi)
    return b.sayfa(bas, govde, (ekmek_kirintisi(kirinti_ogeleri),))


def sayfa_404(b: Baglam) -> str:
    govde = (
        '<article class="okuma"><h1>Aradığın sayfa burada değil</h1>'
        '<p class="giris">İlan kaldırılmış ya da başvuru süresi uzun zaman önce dolmuş '
        "olabilir. Güncel ilanlara ana sayfadan ulaşabilirsin.</p>"
        '<p><a class="dugme dugme-dolu" href="/">Güncel ilanlara git</a></p></article>'
    )
    bas = SayfaBasi(
        baslik="Sayfa bulunamadı | Kamu",
        aciklama="Aradığın sayfa bulunamadı. Güncel kamu ilanları için ana sayfaya dön.",
        yol="/404.html",
        indekslenebilir=False,
    )
    return b.sayfa(bas, govde)
