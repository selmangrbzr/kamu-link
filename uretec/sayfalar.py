"""İlan, merkez, ana sayfa ve 404 sayfalarının HTML üretimi."""

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .jsonld import ekmek_kirintisi, is_ilani, web_sitesi
from .merkezler import Merkez
from .metin import kalan_gun_metni, sayi_tr, tarih_tr, tr_baslik, tr_buyuk, tr_kucuk
from .model import Ilan
from .sablon import (
    UYARI,
    SayfaBasi,
    e,
    ilan_listesi,
    kirinti,
    magaza_butonlari,
    rozet,
    sayfa,
    ust_etiket,
    uygulama_cagrisi,
)

KAMPANYA_SEO = "seo"
KAMPANYA_ANA = "site"
ACIKLAMA_EN_UZUN = 158
_CINSIYET = {"karma": "Kadın ve erkek", "erkek": "Yalnızca erkek", "kadın": "Yalnızca kadın"}
_TUR_MERKEZI = {
    "Memur": ("Memur alımları", "/memur-alimlari/"),
    "Sözleşmeli Personel": ("Sözleşmeli personel alımları", "/sozlesmeli-personel-alimlari/"),
    "İşçi": ("İşçi alımları", "/isci-alimlari/"),
    "Akademik Personel": ("Akademik personel alımları", "/akademik-personel-alimlari/"),
    "Askeri Personel": ("Askeri personel alımları", "/askeri-personel-alimlari/"),
}


@dataclass(frozen=True)
class Baglam:
    simdi: datetime
    bugun: date
    mevcut_yollar: frozenset[str]
    il_yollari: dict[str, str]

    def sayfa(self, bas: SayfaBasi, govde: str, jsonld: tuple[dict, ...] = ()) -> str:
        return sayfa(bas, govde, self.simdi, self.mevcut_yollar, jsonld)


def kisalt(metin: str, en_uzun: int = ACIKLAMA_EN_UZUN) -> str:
    if len(metin) <= en_uzun:
        return metin
    return metin[: en_uzun - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def _tur_merkezi(ilan: Ilan, b: Baglam) -> tuple[str, str] | None:
    hedef = _TUR_MERKEZI.get(ilan.ilan_turu)
    return hedef if hedef and hedef[1] in b.mevcut_yollar else None


# --- İlan sayfası -----------------------------------------------------------

def ilan_basligi(ilan: Ilan, acik: bool) -> str:
    metin = f"{ilan.kisa_kurum} {ilan.is_basligi} Alımı"
    if ilan.kisi_sayisi:
        metin += f" ({sayi_tr(ilan.kisi_sayisi)} Kadro)"
    if not acik:
        metin += ", Süresi Doldu"
    return f"{metin} | Kamu"


def ilan_aciklamasi(ilan: Ilan, acik: bool) -> str:
    kadro = f"{sayi_tr(ilan.kisi_sayisi)} kadro " if ilan.kisi_sayisi else ""
    parcalar = [f"{ilan.kurum_adi} {kadro}{ilan.is_basligi} alımı."]
    if not acik:
        parcalar.append(f"Başvuru süresi {tarih_tr(ilan.basvuru_bitis, yil=True)} tarihinde doldu.")
    else:
        parcalar.append(f"Son başvuru {tarih_tr(ilan.basvuru_bitis, yil=True)}.")
    if ilan.egitim_seviyesi:
        parcalar.append(f"Eğitim: {ilan.egitim_seviyesi}.")
    if ilan.kpss_puan_turu:
        parcalar.append(f"KPSS {ilan.kpss_puan_turu}.")
    parcalar.append("Şartlar, belgeler ve resmî ilan linki.")
    return kisalt(" ".join(parcalar))


def _veri_satiri(ilan: Ilan, b: Baglam, acik: bool) -> str:
    kadro = sayi_tr(ilan.kisi_sayisi) if ilan.kisi_sayisi else "Resmî ilanda"
    kadro_sinif = "veri-deger buyuk" if ilan.kisi_sayisi else "veri-deger"
    kalan = kalan_gun_metni(ilan.basvuru_bitis, b.bugun) if acik else "Süresi doldu"
    # Tür üst etikette zaten yazar; eğitim biliniyorsa üçüncü sütun eğitimdir.
    if ilan.egitim_seviyesi:
        ucuncu = (
            '<div><span class="veri-etiket">Eğitim</span>'
            f'<span class="veri-deger">{e(ilan.egitim_seviyesi)}</span></div>'
        )
    else:
        ucuncu = (
            '<div><span class="veri-etiket">Tür</span>'
            f'<span class="veri-deger tur-renk" data-tur="{ilan.tur_kodu}">{e(ilan.tur_etiketi)}</span></div>'
        )
    return (
        '<div class="veri">'
        f'<div><span class="veri-etiket">Kadro</span><span class="{kadro_sinif}">{kadro}</span></div>'
        f'<div><span class="veri-etiket">Son başvuru</span>'
        f'<span class="veri-deger">{tarih_tr(ilan.basvuru_bitis)}</span>'
        f'<span class="veri-alt{"" if acik else " kapali"}">{e(kalan)}</span></div>'
        f"{ucuncu}</div>"
    )


def _sehir_html(ilan: Ilan, b: Baglam) -> str:
    return ", ".join(
        f'<a href="{b.il_yollari[s]}">{e(s)}</a>' if s in b.il_yollari else e(s)
        for s in ilan.sehirler
    )


def _bilgi_listesi(ilan: Ilan, b: Baglam, acik: bool) -> str:
    satirlar: list[tuple[str, str]] = [
        ("Kurum", e(ilan.kurum_adi)),
        ("İlan başlığı", e(tr_baslik(ilan.pozisyon))),
    ]
    if ilan.kisi_sayisi:
        satirlar.append(("Kadro sayısı", sayi_tr(ilan.kisi_sayisi)))
    satirlar.append(("İlan türü", e(ilan.ilan_turu)))
    if ilan.egitim_seviyesi:
        satirlar.append(("Eğitim seviyesi", e(ilan.egitim_seviyesi)))
    if ilan.kpss_puan_turu:
        satirlar.append(("KPSS puan türü", e(ilan.kpss_puan_turu)))
    if ilan.ales_puan_turu:
        ales = ilan.ales_puan_turu
        if ilan.ales_min_puan:
            ales += f" (en az {ilan.ales_min_puan:g})"
        satirlar.append(("ALES puan türü", e(ales)))
    if ilan.yas_siniri:
        satirlar.append(("Yaş sınırı", e(ilan.yas_siniri)))
    if ilan.cinsiyet:
        cinsiyet = _CINSIYET.get(ilan.cinsiyet.casefold(), ilan.cinsiyet)
        satirlar.append(("Cinsiyet", e(cinsiyet)))
    if ilan.sehirler:
        satirlar.append(("Görev yeri", _sehir_html(ilan, b)))
    if ilan.basvuru_baslangic:
        satirlar.append(("Başvuru başlangıcı", tarih_tr(ilan.basvuru_baslangic, yil=True)))
    satirlar.append(("Son başvuru", tarih_tr(ilan.basvuru_bitis, yil=True)))
    if acik:
        satirlar.append(("Kalan süre", e(kalan_gun_metni(ilan.basvuru_bitis, b.bugun))))
    if ilan.basvuru_yeri:
        satirlar.append(("Başvuru yeri", e(ilan.basvuru_yeri)))
    icerik = "".join(f"<div><dt>{ad}</dt><dd>{deger}</dd></div>" for ad, deger in satirlar)
    return f'<section aria-labelledby="bilgi"><h2 id="bilgi">İlan bilgileri</h2><dl class="bilgi">{icerik}</dl></section>'


def _kontenjan(ilan: Ilan) -> str:
    if not ilan.kontenjan:
        return ""
    adetli = ilan.kontenjan_adetleri_tutarli
    satirlar = []
    for k in ilan.kontenjan:
        adet = f'<span class="kadro-adet">{sayi_tr(k.adet)}</span>' if adetli and k.adet else ""
        nitelik = f'<p class="kadro-nitelik">{e(k.nitelik)}</p>' if k.nitelik else ""
        ad = e(k.pozisyon) if k.pozisyon else "Kadro"
        if k.sehir:
            ad += f' <span class="kadro-sehir">{e(k.sehir)}</span>'
        satirlar.append(f'<li><div class="kadro-ust"><b>{ad}</b>{adet}</div>{nitelik}</li>')
    not_ = "" if adetli else '<p class="soluk">Kadro adetleri için resmî ilan metnine bakın.</p>'
    return (
        '<section aria-labelledby="kadrolar"><h2 id="kadrolar">Kadro dağılımı</h2>'
        f'<ul class="kadrolar">{"".join(satirlar)}</ul>{not_}</section>'
    )


def _metin_bolumu(kimlik: str, baslik: str, metin: str | None) -> str:
    if not metin:
        return ""
    return f'<section aria-labelledby="{kimlik}"><h2 id="{kimlik}">{baslik}</h2><p>{e(metin)}</p></section>'


def _kaynaklar(ilan: Ilan) -> str:
    linkler = []
    if ilan.pdf_url:
        linkler.append(
            f'<a class="dugme dugme-cizgi" href="{e(ilan.pdf_url)}" rel="noopener nofollow">İlan metni (PDF)</a>'
        )
    if ilan.detay_link:
        linkler.append(
            f'<a class="dugme dugme-cizgi" href="{e(ilan.detay_link)}" rel="noopener">'
            "kamuilan.sbb.gov.tr'de resmî ilan</a>"
        )
    if not linkler:
        return ""
    return (
        '<section aria-labelledby="kaynak"><h2 id="kaynak">Resmî kaynak</h2>'
        f'<div class="kaynaklar">{"".join(linkler)}</div></section>'
    )


def ilan_sayfasi(ilan: Ilan, b: Baglam, benzerler: list[Ilan]) -> str:
    acik = ilan.basvuru_bitis >= b.bugun
    tur_merkezi = _tur_merkezi(ilan, b)
    kirinti_ogeleri = [("Ana sayfa", "/")]
    if tur_merkezi:
        kirinti_ogeleri.append(tur_merkezi)
    kirinti_ogeleri.append((ilan.is_basligi, ilan.yol))

    durum = (
        ""
        if acik
        else '<div class="durum" role="status"><b>Başvuru süresi doldu.</b> '
        f"Son başvuru tarihi {tarih_tr(ilan.basvuru_bitis, yil=True)} idi. "
        "Benzer açık ilanlar aşağıda.</div>"
    )
    eklendi = tarih_tr(ilan.eklenme_gunu)
    etiket = tr_buyuk(f"{ilan.tur_etiketi} ilanı · {eklendi} eklendi")
    benzer_html = ""
    if benzerler:
        benzer_html = (
            '<section aria-labelledby="benzer"><h2 id="benzer">Benzer açık ilanlar</h2>'
            f"{ilan_listesi(benzerler, b.bugun)}"
            + (f'<p><a class="ok-link" href="{tur_merkezi[1]}">Tüm {e(tr_kucuk(tur_merkezi[0]))}</a></p>' if tur_merkezi else "")
            + "</section>"
        )
    govde = (
        f'{kirinti(kirinti_ogeleri)}<article class="ilan">'
        f"{ust_etiket(etiket)}"
        f'<h1><span class="h1-kurum">{e(ilan.kurum_adi)}</span>'
        f"{e(ilan.is_basligi)} alımı</h1>"
        f"{rozet(ilan, b.bugun) if acik else ''}{durum}"
        f"{_veri_satiri(ilan, b, acik)}"
        f"{_bilgi_listesi(ilan, b, acik)}"
        f"{_kontenjan(ilan)}"
        f"{_metin_bolumu('sartlar', 'Özel şartlar', ilan.ozel_sartlar)}"
        f"{_metin_bolumu('belgeler', 'Başvuru belgeleri', ilan.basvuru_belgeleri)}"
        f"{_kaynaklar(ilan)}"
        f'<aside class="uyari" role="note">{e(UYARI)}</aside>'
        "</article>"
        + uygulama_cagrisi(
            "Bu tür ilanlar çıktığında bildirim al",
            f"Kamu, {tr_kucuk(ilan.tur_etiketi)} ilanlarını ve son başvuru tarihlerini takip eder. "
            "Yeni ilan çıktığında ve son gün yaklaştığında telefonuna bildirim gelir. Ücretsiz.",
            KAMPANYA_SEO,
        )
        + benzer_html
    )
    bas = SayfaBasi(
        baslik=ilan_basligi(ilan, acik),
        aciklama=ilan_aciklamasi(ilan, acik),
        yol=ilan.yol,
        indekslenebilir=acik,
        og_turu="article",
        bolum="İLAN",
    )
    jsonld: tuple[dict, ...] = (ekmek_kirintisi(kirinti_ogeleri),)
    # JobPosting yalnızca başvuru penceresi açıkken: süresi dolmamış ve başlamış.
    if acik and ilan.basvuru_basladi_mi(b.bugun):
        jsonld = (is_ilani(ilan),) + jsonld
    return b.sayfa(bas, govde, jsonld)


# --- Merkez sayfası ----------------------------------------------------------

def _istatistik(ilanlar: list[Ilan], b: Baglam) -> str:
    kadro = sum(i.kisi_sayisi or 0 for i in ilanlar)
    hafta = b.simdi - timedelta(days=7)
    yeni = sum(1 for i in ilanlar if i.eklenme_tarihi >= hafta)
    kutular = [("açık ilan", sayi_tr(len(ilanlar)))]
    if kadro:
        kutular.append(("kadro", sayi_tr(kadro)))
    kutular.append(("son 7 günde", sayi_tr(yeni)))
    return '<div class="sayilar">' + "".join(
        f'<div><span class="sayi">{deger}</span><span class="sayi-etiket">{ad}</span></div>'
        for ad, deger in kutular
    ) + "</div>"


def merkez_ozeti(ilanlar: list[Ilan]) -> str:
    """Veriden üretilen, merkeze özgü özet cümleleri."""
    kurumlar = [k for k, _ in Counter(i.kisa_kurum for i in ilanlar).most_common(3)]
    en_yakin = min(ilanlar, key=lambda i: i.basvuru_bitis)
    en_buyuk = max(ilanlar, key=lambda i: i.kisi_sayisi or 0)
    cumleler = [f"En çok ilan veren kurumlar: {', '.join(kurumlar)}."]
    if en_buyuk.kisi_sayisi and len(ilanlar) > 1:
        cumleler.append(
            f"En büyük alım {en_buyuk.kisa_kurum} için {sayi_tr(en_buyuk.kisi_sayisi)} kadro."
        )
    cumleler.append(
        f"Son başvurusu en yakın ilan {en_yakin.kisa_kurum} {en_yakin.is_basligi}, "
        f"{tarih_tr(en_yakin.basvuru_bitis)}."
    )
    return " ".join(cumleler)


def merkez_sayfasi(
    merkez: Merkez,
    ilanlar: list[Ilan],
    b: Baglam,
    digerleri: list[Merkez],
    ulusal: list[Ilan] | None = None,
) -> str:
    sirali = sorted(ilanlar, key=lambda i: (i.eklenme_tarihi, i.id), reverse=True)
    indeks = len(ilanlar) >= merkez.en_az_indeks
    diger = "".join(
        f'<li><a href="{m.yol}">{e(m.ad)}</a></li>' for m in digerleri if m.yol != merkez.yol
    ) + '<li><a href="/#kategori">Tüm şehirler</a></li>'
    ulusal_html = ""
    if merkez.il and ulusal:
        ulusal_html = (
            '<section aria-labelledby="ulusal"><h2 id="ulusal">Türkiye genelinde kadro açan ilanlar</h2>'
            f'<p class="soluk">Bu ilanlar {e(merkez.il)} dahil çok sayıda ilde kadro içerir.</p>'
            f"{ilan_listesi(ulusal, b.bugun)}</section>"
        )
    govde = (
        f"{kirinti([('Ana sayfa', '/'), (merkez.h1, merkez.yol)])}"
        f"{ust_etiket(merkez.etiket)}<h1>{e(merkez.h1)}</h1>"
        f'<p class="giris">{e(merkez.giris)}</p>'
        f"{_istatistik(ilanlar, b)}"
        f'<p class="ozet">{e(merkez_ozeti(ilanlar))}</p>'
        f'<section aria-labelledby="liste"><h2 id="liste">Açık ilanlar</h2>'
        f"{ilan_listesi(sirali, b.bugun)}</section>"
        + ulusal_html
        + uygulama_cagrisi(
            "Yeni ilan çıktığında ilk sen gör",
            "Kamu uygulamasında ilan türü, eğitim ve şehir seçerek yalnızca sana uyan "
            "ilanlar için bildirim alabilirsin. Ücretsiz.",
            KAMPANYA_SEO,
        )
        + f'<nav aria-labelledby="diger"><h2 id="diger">Diğer kategoriler</h2><ul class="cipler">{diger}</ul></nav>'
    )
    bas = SayfaBasi(
        baslik=f"{merkez.baslik} | Kamu",
        aciklama=kisalt(
            f"{merkez.h1}: {sayi_tr(len(ilanlar))} açık ilan. Kadro, eğitim şartı, KPSS puan "
            "türü ve son başvuru tarihleriyle her gün güncellenen liste."
        ),
        yol=merkez.yol,
        indekslenebilir=indeks,
        bolum=merkez.etiket,
    )
    return b.sayfa(bas, govde, (ekmek_kirintisi([("Ana sayfa", "/"), (merkez.h1, merkez.yol)]),))


# --- Ana sayfa ve 404 -------------------------------------------------------

def ana_sayfa(acik: list[Ilan], b: Baglam, merkezler: list[tuple[Merkez, int]]) -> str:
    son = sorted(acik, key=lambda i: (i.eklenme_tarihi, i.id), reverse=True)[:12]
    buyuk = sorted(
        (i for i in acik if i.kisi_sayisi),
        key=lambda i: (i.kisi_sayisi or 0, i.id),
        reverse=True,
    )[:6]

    def cipler(grup: str) -> str:
        return "".join(
            f'<li><a href="{m.yol}">{e(m.il or m.ad)} <span class="adet">{n}</span></a></li>'
            for m, n in merkezler
            if m.grup == grup
        )

    kategoriler = "".join(
        f'<div class="kategori"><h3>{baslik}</h3><ul class="cipler">{cipler(grup)}</ul></div>'
        for baslik, grup in (
            ("İlan türü", "tur"),
            ("Eğitim", "egitim"),
            ("KPSS puan türü", "puan"),
            ("Şehir", "sehir"),
        )
        if cipler(grup)
    )
    buyuk_html = (
        f'<section aria-labelledby="buyuk"><h2 id="buyuk">En büyük alımlar</h2>'
        f"{ilan_listesi(buyuk, b.bugun)}</section>"
        if buyuk
        else ""
    )
    govde = (
        '<section class="kahraman">'
        f"{ust_etiket('KAMU PERSONEL ALIMLARI')}"
        "<h1>Kamu ilanları, son başvuru kaçmadan</h1>"
        '<p class="giris">Memur, sözleşmeli, işçi ve akademik personel alımları tek '
        "yerde. İlanın şartlarını, kadro sayısını ve son başvuru tarihini sade bir "
        "sayfada gör; uygulamayla yeni ilan çıktığında bildirim al.</p>"
        f"{magaza_butonlari(KAMPANYA_ANA)}"
        f"{_istatistik(acik, b)}"
        "</section>"
        f'<section aria-labelledby="son"><h2 id="son">Son eklenen ilanlar</h2>'
        f"{ilan_listesi(son, b.bugun)}</section>"
        f"{buyuk_html}"
        f'<section aria-labelledby="kategori"><h2 id="kategori">Kategoriler</h2>{kategoriler}</section>'
        '<section aria-labelledby="nasil"><h2 id="nasil">Bu sayfalar nasıl hazırlanıyor?</h2>'
        "<p>İlanlar kamuilan.sbb.gov.tr'de yayımlanan kamu personel alım ilanlarından "
        "günde birkaç kez otomatik olarak alınır. İlan metnindeki kadro, eğitim, puan "
        "türü ve tarih bilgileri otomatik çıkarılır; bu yüzden hata içerebilir. Her "
        "ilan sayfasında resmî ilan metnine giden link vardır, başvurmadan önce "
        "mutlaka resmî ilanı oku.</p></section>"
    )
    bas = SayfaBasi(
        baslik="Kamu İlanları: Güncel Memur ve Kamu Personel Alımları | Kamu",
        aciklama=kisalt(
            f"{sayi_tr(len(acik))} açık kamu ilanı: memur, sözleşmeli, işçi ve akademik "
            "personel alımları. Kadro, şartlar ve son başvuru tarihleri her gün güncel."
        ),
        yol="/",
    )
    return b.sayfa(bas, govde, (web_sitesi(),))


def sayfa_404(b: Baglam) -> str:
    govde = (
        f"{ust_etiket('SAYFA BULUNAMADI')}<h1>Aradığın sayfa burada değil</h1>"
        '<p class="giris">İlan kaldırılmış ya da başvuru süresi uzun zaman önce dolmuş '
        "olabilir. Güncel ilanlara aşağıdan ulaşabilirsin.</p>"
        '<p><a class="dugme dugme-dolu" href="/">Güncel ilanlara git</a></p>'
    )
    bas = SayfaBasi(
        baslik="Sayfa bulunamadı | Kamu",
        aciklama="Aradığın sayfa bulunamadı. Güncel kamu ilanları için ana sayfaya dön.",
        yol="/404.html",
        indekslenebilir=False,
    )
    return b.sayfa(bas, govde)
