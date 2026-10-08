"""İlan sayfası: başlık bloğu, özet (defter, resmî kaynak, çağrı), gövde ve benzerler.

Dar ekranda tek DOM, sıra CSS ile değişir (başlık, defter, resmî, gövde, çağrı);
geniş ekranda özet sağda yapışkan sütundur.
"""

from collections import defaultdict
from datetime import date

from .baglam import Baglam
from .jsonld import ekmek_kirintisi, is_ilani
from .metin import (
    bulunma_eki,
    katla,
    sayi_bulunma_eki,
    cumle_duzeni,
    kalan_gun_metni,
    sart_parcalari,
    sayi_tr,
    tarih_araligi_tr,
    tarih_i,
    tarih_tr,
    tr_kucuk,
)
from .model import Ilan
from .sablon import (
    KAMPANYA_SEO,
    UYARI,
    SayfaBasi,
    bolum_bas,
    e,
    ilan_listesi,
    kirinti,
    rozet,
    uygulama_cagrisi,
    zaman,
)

ACIKLAMA_EN_UZUN = 158
BASLIK_SINIRI = 60
POZISYON_BASLIK_SINIRI = 60
KADRO_IZGARA_ILK = 12
_AYLAR = ("Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
          "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık")
_CINSIYET = {"karma": "Kadın ve erkek", "erkek": "Yalnızca erkek", "kadın": "Yalnızca kadın"}
TUR_MERKEZI = {
    "Memur": ("Memur alımları", "/memur-alimlari/"),
    "Sözleşmeli Personel": ("Sözleşmeli personel alımları", "/sozlesmeli-personel-alimlari/"),
    "İşçi": ("İşçi alımları", "/isci-alimlari/"),
    "Akademik Personel": ("Akademik personel alımları", "/akademik-personel-alimlari/"),
    "Askeri Personel": ("Askeri personel alımları", "/askeri-personel-alimlari/"),
}


def kisalt(metin: str, en_uzun: int = ACIKLAMA_EN_UZUN) -> str:
    if len(metin) <= en_uzun:
        return metin
    return metin[: en_uzun - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def tur_merkezi(ilan: Ilan, b: Baglam) -> tuple[str, str] | None:
    hedef = TUR_MERKEZI.get(ilan.ilan_turu)
    return hedef if hedef and hedef[1] in b.mevcut_yollar else None


# --- Başlıklar ---------------------------------------------------------------

def tarih_araligi(ilan: Ilan) -> str:
    """Başlık eki: "7–21 Ekim", "28 Eylül–12 Ekim" ya da "son başvuru 21 Ekim"."""
    bitis = ilan.basvuru_bitis
    bas = ilan.basvuru_baslangic
    if not bas or bas > bitis:
        return f"son başvuru {tarih_tr(bitis)}"
    if bas.month == bitis.month:
        return f"{bas.day}–{bitis.day} {_AYLAR[bitis.month - 1]}"
    return f"{tarih_tr(bas)}–{tarih_tr(bitis)}"


def ilan_basligi(ilan: Ilan, acik: bool, ek: str | None = None) -> str:
    kadro = f"{sayi_tr(ilan.kisi_sayisi)} Kadro" if ilan.kisi_sayisi else None
    parantez = ", ".join(x for x in (kadro, ek) if x)
    son = ": Şartlar ve Başvuru" if acik else ": Başvuru Süresi Doldu"
    is_adi = ilan.is_basligi
    if len(is_adi) > POZISYON_BASLIK_SINIRI:
        is_adi = kisalt(is_adi, POZISYON_BASLIK_SINIRI)

    def kur(kurum: str) -> str:
        metin = f"{kurum} {is_adi} Alımı"
        if parantez:
            metin += f" ({parantez})"
        return f"{metin}{son} | Kamu"

    tam = kur(ilan.belediye_adi or ilan.kurum_adi)
    return tam if len(tam) <= BASLIK_SINIRI else kur(ilan.kisa_kurum)


def ilan_basliklari(ilanlar: list[Ilan], bugun: date) -> dict[str, str]:
    """Her ilana benzersiz <title>: çakışanlara tarih aralığı, o da yetmezse ilan no."""
    basliklar = {i.id: ilan_basligi(i, i.basvuru_bitis >= bugun) for i in ilanlar}
    ekler = (
        lambda i: tarih_araligi(i),
        # Slug eki benzersiz olduğu için bu adım her zaman çakışmayı çözer.
        lambda i: f"{tarih_araligi(i)}, ilan no {i.slug.rsplit('-', 1)[1]}",
    )
    for ek in ekler:
        gruplar: dict[str, list[Ilan]] = defaultdict(list)
        for ilan in ilanlar:
            gruplar[basliklar[ilan.id]].append(ilan)
        for grup in gruplar.values():
            if len(grup) > 1:
                for ilan in grup:
                    basliklar[ilan.id] = ilan_basligi(ilan, ilan.basvuru_bitis >= bugun, ek(ilan))
    return basliklar


def ilan_aciklamasi(ilan: Ilan, acik: bool) -> str:
    kadro = f"{sayi_tr(ilan.kisi_sayisi)} kadro " if ilan.kisi_sayisi else ""
    parcalar = [f"{ilan.belediye_adi or ilan.kurum_adi} {kadro}{ilan.is_basligi} alımı."]
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


# --- Başlık bloğu ve özet sütunu -------------------------------------------------

def _ilan_ozeti(ilan: Ilan, b: Baglam, acik: bool) -> str:
    """Alanlardan tek özet cümle; belediye ilanlarında "X Belediyesi" varyantı da geçer."""
    kurum = ilan.kurum_adi
    if ilan.belediye_adi:
        kurum = f"{ilan.belediye_adi} ({ilan.kurum_adi})"
    kadro = f"{sayi_tr(ilan.kisi_sayisi)} kadro " if ilan.kisi_sayisi else ""
    cumleler = [f"{kurum}, {kadro}{tr_kucuk(ilan.is_basligi)} alımı için ilan yayımladı."]
    bitis = tarih_tr(ilan.basvuru_bitis, yil=True)
    if not acik:
        cumleler.append(f"Başvurular {bitis} tarihinde sona erdi.")
    elif ilan.basvuru_baslangic and ilan.basvuru_baslangic > b.bugun:
        cumleler.append(
            f"Başvurular {tarih_tr(ilan.basvuru_baslangic, yil=True)} tarihinde açılıyor, "
            f"son gün {bitis}."
        )
    else:
        cumleler.append(f"Son başvuru tarihi {bitis}.")
    cumleler += [c for c in (sart_cumlesi(ilan), basvuru_yolu_cumlesi(ilan), il_dagilimi_cumlesi(ilan)) if c]
    return f'<p class="ilan-ozet">{e(" ".join(cumleler))}</p>'


def sart_cumlesi(ilan: Ilan) -> str | None:
    """"Eğitim şartı lisans; KPSS puan türü P3; yaş sınırı 35 altı." (hangisi varsa)."""
    parcalar = []
    if ilan.egitim_seviyesi:
        parcalar.append(f"eğitim şartı {tr_kucuk(ilan.egitim_seviyesi)}")
    if ilan.kpss_puan_turu:
        parcalar.append(f"KPSS puan türü {ilan.kpss_puan_turu}")
    if ilan.ales_puan_turu:
        ales = f"ALES puan türü {ilan.ales_puan_turu}"
        if ilan.ales_min_puan:
            ales += f", en az {ilan.ales_min_puan:g}"
        parcalar.append(ales)
    if ilan.yas_siniri:
        parcalar.append(f"yaş sınırı {ilan.yas_siniri}")
    if not parcalar:
        return None
    metin = "; ".join(parcalar)
    return metin[:1].upper() + metin[1:] + "."


def basvuru_yolu_cumlesi(ilan: Ilan) -> str | None:
    """Yalnızca tanınan başvuru kalıplarında cümle kurar; tanınmazsa None."""
    yer = katla(ilan.basvuru_yeri or "")
    if not yer:
        return None
    if "osym" in yer:
        return "Başvuru ÖSYM üzerinden yapılıyor."
    if "e-devlet" in yer or "edevlet" in yer or "kariyer kapisi" in yer:
        return "Başvuru e-Devlet'te Kariyer Kapısı üzerinden yapılıyor."
    if "sahsen" in yer or "posta" in yer:
        return "Başvuru şahsen ya da posta ile yapılıyor."
    return None


def il_dagilimi_cumlesi(ilan: Ilan) -> str | None:
    """Çok illi ilanda: "Kadrolar 80 ile dağılıyor; en çok kadro Ankara'da (132)."."""
    sehirli = [k for k in ilan.kontenjan if k.sehir]
    iller = {k.sehir for k in sehirli}
    if len(iller) < 2 or len(sehirli) != len(ilan.kontenjan) or not ilan.kontenjan_adetleri_tutarli:
        return None
    en_cok = max(sehirli, key=lambda k: (k.adet or 0, k.sehir or ""))
    return (
        f"Kadrolar {len(iller)} ile dağılıyor; en çok kadro "
        f"{bulunma_eki(en_cok.sehir or '')} ({sayi_tr(en_cok.adet or 0)})."
    )


def _baslik_blogu(ilan: Ilan, b: Baglam, acik: bool) -> str:
    kurum_yolu = b.kurum_yollari.get(ilan.kurum_slug)
    if kurum_yolu:
        kurum = f'<a class="ilan-kurum" href="{kurum_yolu}">{e(ilan.kurum_adi)}</a>'
    else:
        kurum = f'<span class="ilan-kurum">{e(ilan.kurum_adi)}</span>'
    durum = ""
    if not acik:
        durum = (
            '<div class="durum" role="status"><b>Başvuru süresi doldu.</b> Son başvuru '
            f"tarihi {tarih_tr(ilan.basvuru_bitis, yil=True)} idi. Benzer açık ilanlar aşağıda.</div>"
        )
    acil = f"<p>{rozet(ilan, b.bugun)}</p>" if acik and rozet(ilan, b.bugun) else ""
    return (
        f'<header class="ilan-bas">{kurum}<h1>{e(ilan.is_basligi)} alımı</h1>'
        '<p class="ilan-meta">'
        f'<span class="tur" data-tur="{ilan.tur_kodu}">{e(ilan.tur_etiketi)} ilanı</span>'
        f"<span>{zaman(ilan.eklenme_gunu)}'{sayi_bulunma_eki(ilan.eklenme_gunu.year)} eklendi</span>"
        "<span>Kaynak: kamuilan.sbb.gov.tr</span></p>"
        f"{acil}{durum}{_ilan_ozeti(ilan, b, acik)}</header>"
    )


def _defter(ilan: Ilan, b: Baglam, acik: bool) -> str:
    if ilan.kisi_sayisi:
        kadro = f'<div class="defter-kadro"><b>{sayi_tr(ilan.kisi_sayisi)}</b><span>kadro</span></div>'
    else:
        kadro = '<div class="defter-kadro yok"><b>Kadro</b><span>resmî ilanda</span></div>'
    kalan = kalan_gun_metni(ilan.basvuru_bitis, b.bugun) if acik else "Süresi doldu"
    satirlar = [
        f"<div><dt>Son başvuru</dt><dd>{tarih_tr(ilan.basvuru_bitis)}<small>{e(kalan)}</small></dd></div>"
    ]
    if acik and ilan.basvuru_baslangic and ilan.basvuru_baslangic > b.bugun:
        gun = (ilan.basvuru_baslangic - b.bugun).days
        sonra = "Yarın" if gun == 1 else f"{gun} gün sonra"
        satirlar.append(
            f"<div><dt>Başvuru açılışı</dt><dd>{tarih_tr(ilan.basvuru_baslangic)}"
            f"<small>{sonra}</small></dd></div>"
        )
    if ilan.egitim_seviyesi:
        satirlar.append(f"<div><dt>Eğitim</dt><dd>{e(ilan.egitim_seviyesi)}</dd></div>")
    return f'<div class="defter">{kadro}<dl>{"".join(satirlar)}</dl></div>'


def _resmi(ilan: Ilan) -> str:
    linkler = []
    if ilan.pdf_url:
        linkler.append(
            f'<a class="dugme dugme-cizgi" href="{e(ilan.pdf_url)}" rel="noopener nofollow">İlan metni (PDF)</a>'
        )
    if ilan.detay_link:
        linkler.append(
            f'<a class="dugme dugme-cizgi" href="{e(ilan.detay_link)}" rel="noopener">Resmî ilan sayfası</a>'
        )
    if not linkler:
        return ""
    return (
        f'<div class="resmi">{"".join(linkler)}</div>'
    )


def _cagri(ilan: Ilan, acik: bool) -> str:
    tur = tr_kucuk(ilan.ilan_turu) if ilan.ilan_turu else "kamu"
    baslik = f"{tarih_i(ilan.basvuru_bitis)} kaçırma" if acik else "Yeni ilan çıkınca haberin olsun"
    metin = (
        f"Yeni {tur} ilanı çıktığında ve son güne az kaldığında telefonuna bildirim gelir. Ücretsiz."
    )
    return uygulama_cagrisi(baslik, metin, KAMPANYA_SEO, "ilan-cagri", "cagri-ilan")


# --- Gövde -------------------------------------------------------------------

def _metin_bolumu(kimlik: str, baslik: str, metin: str | None) -> str:
    if not metin:
        return ""
    parcalar = sart_parcalari(metin)
    if len(parcalar) >= 2:
        icerik = '<ul class="maddeler">' + "".join(f"<li>{e(p)}</li>" for p in parcalar) + "</ul>"
    else:
        icerik = f'<p class="metin-p">{e(parcalar[0] if parcalar else metin)}</p>'
    return f'<section class="bolum" aria-labelledby="{kimlik}">{bolum_bas(kimlik, baslik)}{icerik}</section>'


def _il_izgarasi(ilan: Ilan, adetli: bool) -> str:
    satirlar = sorted(ilan.kontenjan, key=lambda k: (-(k.adet or 0), k.sehir or ""))
    if not adetli:
        satirlar = sorted(ilan.kontenjan, key=lambda k: k.sehir or "")

    def li(ogeler: list) -> str:
        return "".join(
            f'<li><span>{e(k.sehir)}</span>{f"<b>{sayi_tr(k.adet)}</b>" if adetli and k.adet else ""}</li>'
            for k in ogeler
        )

    pozisyon = ilan.kontenjan[0].pozisyon or ilan.is_basligi
    giris = "En çok kadro olan iller:" if adetli else "Kadro açılan iller:"
    html = (
        f'<p class="kadro-ozet">Tüm kadrolar <b>{e(pozisyon)}</b>. {giris}</p>'
        f'<ul class="kadro-izgara">{li(satirlar[:KADRO_IZGARA_ILK])}</ul>'
    )
    kalan = satirlar[KADRO_IZGARA_ILK:]
    if kalan:
        html += (
            f'<details class="tumu"><summary>Tüm iller ({len(satirlar)})</summary>'
            f'<ul class="kadro-izgara">{li(sorted(kalan, key=lambda k: k.sehir or ""))}</ul></details>'
        )
    return html


def _kontenjan(ilan: Ilan) -> str:
    if not ilan.kontenjan:
        return ""
    adetli = ilan.kontenjan_adetleri_tutarli
    pozisyonlar = {k.pozisyon for k in ilan.kontenjan}
    sehirli = all(k.sehir for k in ilan.kontenjan) and len(ilan.kontenjan) > 1
    if len(pozisyonlar) == 1 and sehirli:
        icerik = _il_izgarasi(ilan, adetli)
        sag = f'<span class="not">{len(ilan.kontenjan)} il</span>'
    else:
        satirlar = []
        for k in ilan.kontenjan:
            adet = f'<span class="kadro-adet">{sayi_tr(k.adet)}</span>' if adetli and k.adet else ""
            nitelik = f'<p class="kadro-nitelik">{e(cumle_duzeni(k.nitelik))}</p>' if k.nitelik else ""
            ad = e(k.pozisyon) if k.pozisyon else "Kadro"
            if k.sehir:
                ad += f' <span class="kadro-sehir">{e(k.sehir)}</span>'
            satirlar.append(f'<li><div class="kadro-ust"><b>{ad}</b>{adet}</div>{nitelik}</li>')
        icerik = f'<ul class="kadrolar">{"".join(satirlar)}</ul>'
        sag = ""
    not_ = "" if adetli else '<p class="soluk">Kadro adetleri için resmî ilan metnine bak.</p>'
    return (
        f'<section class="bolum" aria-labelledby="kadrolar">{bolum_bas("kadrolar", "Kadro dağılımı", sag)}'
        f"{icerik}{not_}</section>"
    )


def _sehir_html(ilan: Ilan, b: Baglam) -> str:
    return ", ".join(
        f'<a href="{b.il_yollari[s]}">{e(s)}</a>' if s in b.il_yollari else e(s)
        for s in ilan.sehirler
    )


def _bilgi_listesi(ilan: Ilan, b: Baglam) -> str:
    satirlar: list[tuple[str, str]] = [("İlan türü", e(ilan.ilan_turu))]
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
        satirlar.append(("Cinsiyet", e(_CINSIYET.get(ilan.cinsiyet.casefold(), ilan.cinsiyet))))
    kontenjanda_il = any(k.sehir for k in ilan.kontenjan)
    if ilan.sehirler and not kontenjanda_il:
        satirlar.append(("Görev yeri", _sehir_html(ilan, b)))
    if ilan.basvuru_baslangic and ilan.basvuru_baslangic <= ilan.basvuru_bitis:
        satirlar.append(("Başvuru tarihleri", tarih_araligi_tr(ilan.basvuru_baslangic, ilan.basvuru_bitis)))
    if ilan.basvuru_yeri_temiz:
        satirlar.append(("Başvuru yeri", e(ilan.basvuru_yeri_temiz)))
    icerik = "".join(f"<div><dt>{ad}</dt><dd>{deger}</dd></div>" for ad, deger in satirlar)
    return (
        f'<section class="bolum" aria-labelledby="bilgi">{bolum_bas("bilgi", "İlan bilgileri")}'
        f'<dl class="bilgi">{icerik}</dl></section>'
    )


def _benzerler(ilan: Ilan, b: Baglam, benzerler: list[Ilan], kurum_acik: int) -> str:
    kurum_yolu = b.kurum_yollari.get(ilan.kurum_slug)
    tur = tur_merkezi(ilan, b)
    sag = ""
    if kurum_yolu and kurum_acik > 1:
        sag = f'<a href="{kurum_yolu}">Bu kurumun diğer açık ilanları</a>'
    elif tur:
        sag = f'<a href="{tur[1]}">Tüm {e(tr_kucuk(tur[0]))}</a>'
    if not benzerler and not sag:
        return ""
    liste = ilan_listesi(benzerler, b.bugun, b.yeni_sinir) if benzerler else ""
    alt = ""
    if tur and kurum_yolu and kurum_acik > 1:
        alt = f'<a class="daha" href="{tur[1]}">Tüm {e(tr_kucuk(tur[0]))}</a>'
    return (
        f'<section class="bolum" aria-labelledby="benzer">{bolum_bas("benzer", "Benzer açık ilanlar", sag)}'
        f"{liste}{alt}</section>"
    )


def ilan_sayfasi(
    ilan: Ilan,
    b: Baglam,
    benzerler: list[Ilan],
    baslik: str | None = None,
    kurum_acik: int = 0,
) -> str:
    acik = ilan.basvuru_bitis >= b.bugun
    tur = tur_merkezi(ilan, b)
    kirinti_ogeleri = [("Ana sayfa", "/")]
    if tur:
        kirinti_ogeleri.append(tur)
    kirinti_ogeleri.append((f"{ilan.kisa_kurum} {ilan.is_basligi}", ilan.yol))
    govde = (
        f'{kirinti(kirinti_ogeleri)}<article class="ilan-izgara">'
        f"{_baslik_blogu(ilan, b, acik)}"
        '<aside class="ozet" aria-label="İlan özeti">'
        f"{_defter(ilan, b, acik)}{_resmi(ilan)}{_cagri(ilan, acik)}</aside>"
        '<div class="govde">'
        f"{_metin_bolumu('sartlar', 'Özel şartlar', ilan.ozel_sartlar)}"
        f"{_metin_bolumu('belgeler', 'Başvuru belgeleri', ilan.basvuru_belgeleri)}"
        f"{_kontenjan(ilan)}{_bilgi_listesi(ilan, b)}"
        "</div></article>"
        f"{_benzerler(ilan, b, benzerler, kurum_acik)}"
    )
    bas = SayfaBasi(
        baslik=baslik or ilan_basligi(ilan, acik),
        aciklama=ilan_aciklamasi(ilan, acik),
        yol=ilan.yol,
        indekslenebilir=acik,
        og_turu="article",
        uygulama_argumani=True,
        kunye_alt=f"Güncelleme {b.saat}",
    )
    jsonld: tuple[dict, ...] = (ekmek_kirintisi(kirinti_ogeleri),)
    # JobPosting yalnızca başvuru penceresi açıkken: süresi dolmamış ve başlamış.
    if acik and ilan.basvuru_basladi_mi(b.bugun):
        jsonld = (is_ilani(ilan),) + jsonld
    return b.sayfa(bas, govde, jsonld)
