"""Rehber sayfaları: kalıcı, kaynaklı metin ile her derlemede güncellenen veri bölümü.

Yapı (cevap motorlarının alıntılayabileceği biçim): en üstte hedef soruya tarihli,
kaynaklı 1-2 cümlelik doğrudan cevap; ardından soru biçimli H2'ler, sitenin güncel
verisiyle bir bölüm, iç linkler, kaynaklar listesi ve tek uygulama çağrısı.
Kalıcı metin rehber_icerik.py'de; burada yalnızca biçim ve veri cümleleri var.
"""

import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, time

from .baglam import Baglam
from .jsonld import ekmek_kirintisi, makale_grafigi
from .merkezler import SABIT_MERKEZLER
from .metin import katla, sayi_tr, tarih_tr
from .model import TR_SAAT, Ilan
from .rehber_icerik import REHBER_KOK, REHBER_SLUGLARI, REHBERLER, Parca, Rehber
from .rehber_kaynak import Olgu
from .sablon import SayfaBasi, bolum_bas, e, kirinti, uygulama_cagrisi, zaman

KAMPANYA = "rehber"
DIZIN_ADI = "Rehberler"
_MERKEZ_ADLARI = {m.yol: m.ad for m in SABIT_MERKEZLER}
_TEMEL_PUANLAR = ("P3", "P93", "P94")
_ALES_TURLERI = ("SAY", "SÖZ", "EA")
EN_SIK_A_GRUBU = 6
_RED_KALIBI = re.compile(r"kabul edilme|kabul olunma|yapilamaz|gecersiz")


# --- Metin parçaları ------------------------------------------------------------

def _atif(olgu: Olgu) -> str:
    return (
        f' <span class="atif">(<a href="{e(olgu.kaynak_url)}">{e(olgu.atif)}</a>)</span>'
    )


def paragraf_html(parcalar: tuple[Parca, ...]) -> str:
    """Cümleler; art arda aynı kaynağa ve maddeye dayanan olgular tek atıfla kapanır."""
    cikti: list[str] = []
    for sira, parca in enumerate(parcalar):
        if isinstance(parca, str):
            cikti.append(e(parca))
            continue
        sonraki = parcalar[sira + 1] if sira + 1 < len(parcalar) else None
        ayni = (
            isinstance(sonraki, Olgu)
            and sonraki.kaynak_url == parca.kaynak_url
            and sonraki.yer == parca.yer
        )
        if ayni:
            cikti.append(e(parca.metin))
        elif parca.metin.endswith("."):
            # Atıf cümle sonundaki noktadan önce: "... geçerli (Genel Yönetmelik, md. 11)."
            cikti.append(e(parca.metin[:-1]) + _atif(parca) + ".")
        else:
            cikti.append(e(parca.metin) + _atif(parca))
    return " ".join(cikti)


def _bolum_html(rehber: Rehber) -> str:
    parcalar = []
    for bolum in rehber.bolumler:
        if bolum.liste:
            govde = "<ul>" + "".join(f"<li>{paragraf_html(p)}</li>" for p in bolum.paragraflar) + "</ul>"
        else:
            govde = "".join(f"<p>{paragraf_html(p)}</p>" for p in bolum.paragraflar)
        parcalar.append(f"{bolum_bas(bolum.kimlik, bolum.soru)}{govde}")
    return "".join(parcalar)


def kaynak_listesi(rehber: Rehber) -> list[Olgu]:
    """Rehberde geçen kaynaklar, ilk geçiş sırasıyla, tekil."""
    gorulen: dict[str, Olgu] = {}
    for olgu in rehber.olgular():
        gorulen.setdefault(olgu.kaynak_url, olgu)
    return list(gorulen.values())


def _kaynaklar_html(rehber: Rehber) -> str:
    maddeler = "".join(
        f'<li><a href="{e(o.kaynak_url)}">{e(o.kaynak_adi)}</a>'
        f'<span class="soluk"> Son kontrol: {zaman(o.kontrol_tarihi)}</span></li>'
        for o in kaynak_listesi(rehber)
    )
    return f'{bolum_bas("kaynaklar", "Kaynaklar")}<ol class="kaynaklar">{maddeler}</ol>'


# --- Veri bölümleri ---------------------------------------------------------------

@dataclass(frozen=True)
class RehberVerisi:
    acik: tuple[Ilan, ...]
    b: Baglam
    indeksli: frozenset[str]

    @property
    def tarih(self) -> str:
        return zaman(self.b.bugun)

    def link(self, yol: str, ad: str) -> str:
        return f'<a href="{e(yol)}">{e(ad)}</a>' if yol in self.indeksli else e(ad)


def _tablo(
    basliklar: tuple[str, ...],
    satirlar: list[tuple[str, ...]],
    sayisal: tuple[int, ...] | None = None,
) -> str:
    """Sade veri tablosu; sayisal sütunlar (varsayılan: ilki hariç hepsi) sağa yaslanır."""
    sutunlar = set(range(1, len(basliklar)) if sayisal is None else sayisal)
    bas = "".join(
        f'<th scope="col"{" class=sayi" if i in sutunlar else ""}>{e(b)}</th>'
        for i, b in enumerate(basliklar)
    )
    govde = "".join(
        "<tr>" + "".join(
            f'<td{" class=sayi" if i in sutunlar else ""}>{h}</td>' for i, h in enumerate(satir)
        ) + "</tr>"
        for satir in satirlar
    )
    return f'<div class="tablo-kap"><table class="veri-tablo"><thead><tr>{bas}</tr></thead><tbody>{govde}</tbody></table></div>'


def _p(metin: str) -> str:
    return f'<p class="veri-cumle">{metin}</p>'


def _puan_sayilari(acik: tuple[Ilan, ...]) -> Counter[str]:
    return Counter(p for i in acik for p in i.kpss_turleri)


def _veri_gecerlilik(v: RehberVerisi) -> str:
    sayim = _puan_sayilari(v.acik)
    yollar = {"P3": "/kpss-p3-ilanlari/", "P93": "/kpss-p93-ilanlari/", "P94": "/kpss-p94-ilanlari/"}
    cumle = (
        f"{v.tarih} itibarıyla Kamu'da listelenen açık ilanlardan "
        f"<b>{sayim['P3']}</b> ilan KPSS P3, <b>{sayim['P93']}</b> ilan P93, "
        f"<b>{sayim['P94']}</b> ilan P94 puanı istiyor."
    )
    satirlar = [(v.link(yollar[p], f"KPSS {p}"), sayi_tr(sayim[p])) for p in _TEMEL_PUANLAR]
    return _p(cumle) + _tablo(("Puan türü", "Açık ilan"), satirlar)


_TUR_SIRASI = ("Memur", "Sözleşmeli Personel", "İşçi", "Akademik Personel", "Askeri Personel")
_TUR_YOLLARI = {
    "Memur": "/memur-alimlari/",
    "Sözleşmeli Personel": "/sozlesmeli-personel-alimlari/",
    "İşçi": "/isci-alimlari/",
    "Akademik Personel": "/akademik-personel-alimlari/",
    "Askeri Personel": "/askeri-personel-alimlari/",
}


def _veri_fark(v: RehberVerisi) -> str:
    satirlar = []
    for tur in _TUR_SIRASI:
        ilanlar = [i for i in v.acik if i.ilan_turu == tur]
        kpssli = sum(1 for i in ilanlar if i.kpss_turleri)
        oran = f"yüzde {round(100 * kpssli / len(ilanlar))}" if ilanlar else "-"
        satirlar.append((v.link(_TUR_YOLLARI[tur], tur), sayi_tr(len(ilanlar)), sayi_tr(kpssli), oran))
    memur = [i for i in v.acik if i.ilan_turu == "Memur"]
    cumle = f"{v.tarih} itibarıyla Kamu'da <b>{sayi_tr(len(v.acik))}</b> açık ilan listeleniyor."
    if memur:
        oran = round(100 * sum(1 for i in memur if i.kpss_turleri) / len(memur))
        cumle += f" Memur ilanlarında KPSS puan türü yazan ilanların oranı yüzde {oran}."
    return _p(cumle) + _tablo(("İlan türü", "Açık ilan", "KPSS puan türü yazan", "Oran"), satirlar)


def _veri_puan_turleri(v: RehberVerisi) -> str:
    sayim = _puan_sayilari(v.acik)
    yollar = {"P3": "/kpss-p3-ilanlari/", "P93": "/kpss-p93-ilanlari/", "P94": "/kpss-p94-ilanlari/"}
    a_grubu = [i for i in v.acik if set(i.kpss_turleri) - set(_TEMEL_PUANLAR)]
    satirlar = [(v.link(yollar[p], f"KPSS {p}"), sayi_tr(sayim[p])) for p in _TEMEL_PUANLAR]
    satirlar.append(("Diğer puan türleri (A grubu)", sayi_tr(len(a_grubu))))
    cumle = (
        f"{v.tarih} itibarıyla Kamu'da listelenen açık ilanlardan <b>{sayi_tr(len(a_grubu))}</b> "
        "ilan P3, P93 ve P94 dışında en az bir puan türü istiyor."
    )
    diger = Counter(p for i in a_grubu for p in i.kpss_turleri if p not in _TEMEL_PUANLAR)
    if diger:
        sik = ", ".join(
            f"{p} ({n})" for p, n in sorted(diger.items(), key=lambda x: (-x[1], int(x[0][1:])))[:EN_SIK_A_GRUBU]
        )
        cumle += f" Bu ilanlarda en sık geçenler: {e(sik)}."
    return _p(cumle) + _tablo(("Puan türü", "Açık ilan"), satirlar)


def _veri_lise(v: RehberVerisi) -> str:
    lise = [i for i in v.acik if i.egitim_grubu == "lise"]
    p94 = sum(1 for i in lise if "P94" in i.kpss_turleri)
    cumle = (
        f"{v.tarih} itibarıyla Kamu'da lise mezunlarına açık <b>{sayi_tr(len(lise))}</b> ilan "
        f"listeleniyor; bunlardan <b>{sayi_tr(p94)}</b> ilan KPSS P94 puanı istiyor."
    )
    sayim = Counter(i.ilan_turu for i in lise)
    satirlar = [
        (v.link(_TUR_YOLLARI[t], t), sayi_tr(sayim[t])) for t in _TUR_SIRASI if sayim[t]
    ]
    tablo = _tablo(("İlan türü", "Açık ilan"), satirlar) if satirlar else ""
    tumu = v.link("/lise-mezunu-kamu-ilanlari/", "Lise mezunlarına açık tüm ilanlar")
    return _p(cumle) + tablo + f'<p class="veri-cumle">{tumu}</p>'


_KARIYER = "Kariyer Kapısı (e-Devlet)"
_OSYM = "ÖSYM"
_ISKUR = "İŞKUR"
_INTERNET = "Kurumun internet başvuru sistemi"
_SAHSEN = "Şahsen"
_POSTA = "Posta ya da kargo"
_EPOSTA = "E-posta"
YOL_ADLARI = (_KARIYER, _OSYM, _ISKUR, _INTERNET, _SAHSEN, _POSTA, _EPOSTA)
_URL = re.compile(r"https?://|www\.")
_CEVRIMICI = re.compile(r"online|on-line|cevrimici|cevrim ici|elektronik ortam")


def _olumlu_parcalar(metin: str) -> list[str]:
    """Başvuru yeri metninin "kabul edilmez" türü olumsuz ifade içermeyen parçaları.

    Olumsuz parçada virgülle ayrılan ve en az iki kelimelik olumlu kısımlar korunur:
    "(şahsen başvuru, posta kabul edilmez)" -> "şahsen başvuru"; "şahsen, kargo veya
    posta yoluyla başvuru kabul edilmez" -> hiçbiri.
    """
    sonuc = []
    for parca in re.split(r"[;()]|\.\s", katla(metin)):
        if not _RED_KALIBI.search(parca):
            sonuc.append(parca)
            continue
        sonuc += [a for a in parca.split(",") if not _RED_KALIBI.search(a) and len(a.split()) >= 2]
    return sonuc


def basvuru_yollari(metin: str) -> list[str]:
    """Başvuru yeri metninde geçen başvuru yolları (bir ilanda birden fazla olabilir)."""
    parcalar = _olumlu_parcalar(metin)
    tumu = " ".join(parcalar)
    bulunan: list[str] = []
    if "kariyer kapisi" in tumu or "kariyerkapisi" in tumu:
        bulunan.append(_KARIYER)
    if "osym" in tumu:
        bulunan.append(_OSYM)
    if "iskur" in tumu or "is kurumu" in tumu:
        bulunan.append(_ISKUR)
    sahsen = "sahsen" in tumu
    posta = bool(re.search(r"(?<!e-)posta|kargo", tumu))
    eposta = "e-posta" in tumu or "@" in tumu
    if not bulunan:
        # E-posta parçasındaki "elektronik ortam" ve yalnızca form/bilgi için verilen
        # adresler internet başvurusu sayılmaz; tek başına adres, başka yol yoksa sayılır.
        acik_ifade = any(
            _CEVRIMICI.search(p) and "e-posta" not in p and "@" not in p for p in parcalar
        )
        adres = any(_URL.search(p) and not re.search(r"form|bilgi", p) for p in parcalar)
        if acik_ifade or (adres and not (sahsen or posta or eposta)):
            bulunan.append(_INTERNET)
    if sahsen:
        bulunan.append(_SAHSEN)
    if posta:
        bulunan.append(_POSTA)
    if eposta:
        bulunan.append(_EPOSTA)
    return bulunan


def _veri_basvuru(v: RehberVerisi) -> str:
    bilgili = [i for i in v.acik if i.basvuru_yeri]
    sayim = Counter(y for i in bilgili for y in basvuru_yollari(i.basvuru_yeri or ""))
    satirlar = [(e(ad), sayi_tr(sayim[ad])) for ad in YOL_ADLARI if sayim[ad]]
    cumle = (
        f"{v.tarih} itibarıyla Kamu'da başvuru yeri bilgisi olan <b>{sayi_tr(len(bilgili))}</b> açık "
        "ilan, ilan metninde geçen başvuru yollarına göre aşağıdaki gibi dağılıyor. Bir ilanda "
        "birden fazla yol geçebildiği için toplam, ilan sayısından büyük olabilir."
    )
    if satirlar:
        en_cok, n = sayim.most_common(1)[0]
        cumle += f" En sık geçen yol: {e(en_cok)} ({sayi_tr(n)} ilan)."
    return _p(cumle) + (_tablo(("Başvuru yolu", "Açık ilan"), satirlar) if satirlar else "")


def ales_turleri(metin: str | None) -> set[str]:
    return set(re.findall(r"SAY|SÖZ|EA", (metin or "").upper().replace("SOZ", "SÖZ")))


def _veri_akademik(v: RehberVerisi) -> str:
    akademik = [i for i in v.acik if i.ilan_turu == "Akademik Personel"]
    alesli = [i for i in akademik if i.ales_puan_turu]
    cumle = (
        f"{v.tarih} itibarıyla Kamu'da <b>{sayi_tr(len(akademik))}</b> açık akademik ilan "
        f"listeleniyor; bunlardan <b>{sayi_tr(len(alesli))}</b> ilanın bilgilerinde ALES puan "
        "türü yazıyor."
    )
    sayim = Counter(t for i in alesli for t in ales_turleri(i.ales_puan_turu))
    adlar = {"SAY": "ALES sayısal (SAY)", "SÖZ": "ALES sözel (SÖZ)", "EA": "ALES eşit ağırlık (EA)"}
    satirlar = [(adlar[t], sayi_tr(sayim[t])) for t in _ALES_TURLERI if sayim[t]]
    tumu = v.link("/akademik-personel-alimlari/", "Açık akademik ilanların tamamı")
    tablo = _tablo(("ALES puan türü", "Açık ilan"), satirlar) if satirlar else ""
    return _p(cumle) + tablo + f'<p class="veri-cumle">{tumu}</p>'


def uzman_yardimcisi_mi(ilan: Ilan) -> bool:
    metinler = [ilan.pozisyon, *(k.pozisyon or "" for k in ilan.kontenjan)]
    return any("uzman yardimci" in katla(m) for m in metinler)


def _puan_sarti(ilan: Ilan) -> str:
    if ilan.kpss_turleri:
        return "KPSS " + ", ".join(ilan.kpss_turleri)
    return "Resmî ilana bak"


def _veri_uzman(v: RehberVerisi) -> str:
    ilanlar = sorted((i for i in v.acik if uzman_yardimcisi_mi(i)), key=lambda i: (i.basvuru_bitis, i.id))
    if not ilanlar:
        return _p(f"{v.tarih} itibarıyla açık uzman yardımcısı ilanı yok.")
    cumle = (
        f"{v.tarih} itibarıyla Kamu'da uzman yardımcısı kadrosu içeren <b>{sayi_tr(len(ilanlar))}</b> "
        "açık ilan var. Son başvurusu en yakın olan üstte."
    )
    satirlar = [
        (
            f'<a href="{e(i.yol)}"><b>{e(i.kisa_kurum)}</b></a><br><span class="soluk">{e(i.is_basligi)}</span>',
            sayi_tr(i.kisi_sayisi) if i.kisi_sayisi else "-",
            e(tarih_tr(i.basvuru_bitis, yil=True)),
            e(_puan_sarti(i)),
        )
        for i in ilanlar
    ]
    return _p(cumle) + _tablo(("Kurum ve kadro", "Kadro", "Son başvuru", "Puan şartı"), satirlar, (1, 2))


VERI_BOLUMLERI: dict[str, Callable[[RehberVerisi], str]] = {
    "kpss-puani-gecerlilik-suresi": _veri_gecerlilik,
    "memur-sozlesmeli-isci-farki": _veri_fark,
    "kpss-puan-turleri": _veri_puan_turleri,
    "lise-mezunu-kamu-is": _veri_lise,
    "kamu-ilanina-basvuru-yollari": _veri_basvuru,
    "akademik-ilan-ales-sarti": _veri_akademik,
    "uzman-yardimciligi-alimlari": _veri_uzman,
}

# Veri bölümünün dayandığı ilan kümesi (sitemap lastmod için).
VERI_FILTRELERI: dict[str, Callable[[Ilan], bool]] = {
    "kpss-puani-gecerlilik-suresi": lambda i: bool(set(i.kpss_turleri) & set(_TEMEL_PUANLAR)),
    "memur-sozlesmeli-isci-farki": lambda i: i.ilan_turu in _TUR_SIRASI,
    "kpss-puan-turleri": lambda i: bool(i.kpss_turleri),
    "lise-mezunu-kamu-is": lambda i: i.egitim_grubu == "lise",
    "kamu-ilanina-basvuru-yollari": lambda i: bool(i.basvuru_yeri),
    "akademik-ilan-ales-sarti": lambda i: i.ilan_turu == "Akademik Personel",
    "uzman-yardimciligi-alimlari": uzman_yardimcisi_mi,
}


def kontrol_zamani(rehber: Rehber) -> datetime:
    return datetime.combine(rehber.kontrol_tarihi, time(), tzinfo=TR_SAAT)


# --- Sayfalar -------------------------------------------------------------------

def _ilgili_html(rehber: Rehber, v: RehberVerisi) -> str:
    linkler = [
        f'<li><a href="{e(yol)}">{e(_MERKEZ_ADLARI.get(yol, yol))}</a></li>'
        for yol in rehber.merkezler
        if yol in v.indeksli
    ]
    linkler += [
        f'<li><a href="{e(REHBER_SLUGLARI[s].yol)}">{e(REHBER_SLUGLARI[s].h1)}</a></li>'
        for s in rehber.ilgili
    ]
    linkler.append(f'<li><a href="{REHBER_KOK}">Tüm rehberler</a></li>')
    return f'{bolum_bas("ilgili", "İlgili sayfalar")}<ul class="ilgili">{"".join(linkler)}</ul>'


def rehber_sayfasi(rehber: Rehber, b: Baglam, acik: list[Ilan], indeksli: frozenset[str]) -> str:
    v = RehberVerisi(acik=tuple(acik), b=b, indeksli=indeksli)
    kirinti_ogeleri = [("Ana sayfa", "/"), (DIZIN_ADI, REHBER_KOK), (rehber.ad, rehber.yol)]
    cagri = uygulama_cagrisi(
        "Yeni ilan çıkınca haberin olsun",
        "Puan türünü, eğitimini ve şehrini seç; sana uyan yeni ilanlar ve son günler için "
        "bildirim al. Ücretsiz.",
        KAMPANYA,
    )
    govde = (
        f"{kirinti(kirinti_ogeleri)}<article class=\"okuma rehber\">"
        f"<h1>{e(rehber.h1)}</h1>"
        f'<p class="rehber-meta">Son kontrol: {zaman(rehber.kontrol_tarihi)}. '
        "Kaynaklar sayfanın sonunda.</p>"
        f'<section class="kisa-cevap" aria-label="Kısa cevap"><p>{paragraf_html(rehber.cevap)}</p></section>'
        f"{_bolum_html(rehber)}"
        f'<section class="veri" aria-labelledby="veri">{bolum_bas("veri", rehber.veri_basligi)}'
        f"{VERI_BOLUMLERI[rehber.slug](v)}</section>"
        f"{_ilgili_html(rehber, v)}{_kaynaklar_html(rehber)}{cagri}</article>"
    )
    bas = SayfaBasi(
        baslik=rehber.baslik, aciklama=rehber.aciklama, yol=rehber.yol,
        og_turu="article", kampanya=KAMPANYA,
    )
    jsonld = (
        makale_grafigi(
            rehber.yol, rehber.h1, rehber.aciklama,
            rehber.yayin_tarihi.isoformat(), rehber.kontrol_tarihi.isoformat(),
            [o.kaynak_url for o in kaynak_listesi(rehber)],
        ),
        ekmek_kirintisi(kirinti_ogeleri),
    )
    return b.sayfa(bas, govde, jsonld)


def rehber_dizini(b: Baglam) -> str:
    kirinti_ogeleri = [("Ana sayfa", "/"), (DIZIN_ADI, REHBER_KOK)]
    maddeler = "".join(
        f'<li><a href="{e(r.yol)}">{e(r.h1)}</a><p>{e(r.aciklama)}</p></li>' for r in REHBERLER
    )
    son = max(r.kontrol_tarihi for r in REHBERLER)
    govde = (
        f"{kirinti(kirinti_ogeleri)}<article class=\"okuma\">"
        "<h1>Kamu ilanı rehberleri</h1>"
        '<p class="giris">KPSS, başvuru yolları ve kamu personel alımı hakkında sık sorulan '
        "soruların kısa cevapları. Her rehberde resmî kaynaklar ve son kontrol tarihi yazıyor; "
        f"en son kontrol {zaman(son)}.</p>"
        f'<ul class="rehber-dizin">{maddeler}</ul></article>'
    )
    bas = SayfaBasi(
        baslik="Rehberler: KPSS, Başvuru Yolları ve Kamu Personel Alımı Soruları | Kamu",
        aciklama=(
            "KPSS geçerlilik süresi, puan türleri, memur-sözleşmeli-işçi farkı, ALES şartı ve "
            "başvuru yolları hakkında resmî kaynaklı kısa rehberler."
        ),
        yol=REHBER_KOK,
        kampanya=KAMPANYA,
    )
    return b.sayfa(bas, govde, (ekmek_kirintisi(kirinti_ogeleri),))
