"""Site derlemesi: ilan satırlarından tüm sayfaları, sitemap'i ve robots.txt'yi üretir.

derle() saftır (dosya sistemine dokunmaz) ve testlerde doğrudan kullanılır;
yaz() sonucu _site/ klasörüne döker ve statik dosyaları kopyalar.
"""

import dataclasses
import json
from collections import Counter
import logging
import shutil
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from .bilgi import BILGI_GUNCELLEME, BILGI_SAYFALARI
from .jsonld import SITE_URL
from .kurumlar import kalici_kurumlar, kurum_anahtari
from .merkezler import (
    SABIT_MERKEZLER,
    Merkez,
    MerkezVerisi,
    kurum_merkezi,
    sehir_merkezleri,
)
from .model import TR_SAAT, UZUN_ID_ON_EK, Ilan, bugun_tr, sayfasi_olacak_mi
from .sayfalar import (
    Baglam,
    ana_sayfa,
    bilgi_sayfasi,
    ilan_basliklari,
    ilan_sayfasi,
    merkez_sayfasi,
    sayfa_404,
)

log = logging.getLogger(__name__)

BENZER_ADET = 4
DIGER_SEHIR_ADET = 10
KAPANAN_ADET = 10
# Bundan az açık ilan gelirse veri kaynağı bozuk sayılır ve site yayınlanmaz
# (eksik çekim yüzlerce sayfayı silmesin). URETEC_EN_AZ_ACIK_ILAN ile değiştirilebilir.
EN_AZ_ACIK_ILAN = 20
CIKTI_ADI = "_site"
MANIFEST_ADI = ".indexnow.json"
LF = chr(10)  # Windows yerel derlemede de satır sonları LF olsun
KOK = Path(__file__).resolve().parent.parent
STATIK = Path(__file__).resolve().parent / "statik"
# Repo kökünden olduğu gibi kopyalanan dosyalar (/ig yönlendirmesi dahil).
KOK_DOSYALARI = ("ig", "yonlendir.js", "stil.css", "kamu-icon-512.png", "CNAME")


class DerlemeHatasi(RuntimeError):
    """Yayınlanmaması gereken bir derleme (boş veri, çakışan adres)."""


@dataclass
class Derleme:
    sayfalar: dict[str, str] = field(default_factory=dict)
    sitemap: list[tuple[str, datetime]] = field(default_factory=list)
    acik: int = 0
    kapali: int = 0
    merkezler: list[str] = field(default_factory=list)
    noindex_merkezler: list[str] = field(default_factory=list)


def _ilanlar(satirlar: Iterable[dict[str, Any]]) -> list[Ilan]:
    ilanlar: dict[str, Ilan] = {}
    for satir in satirlar:
        if not isinstance(satir, dict):
            log.warning("Sözlük olmayan satır atlandı.")
            continue
        try:
            ilan = Ilan.from_satir(satir)
        except (KeyError, TypeError, ValueError) as hata:
            log.warning("Satır atlandı (%s): %s", satir.get("id"), hata)
            continue
        ilanlar[ilan.id] = ilan
    return list(ilanlar.values())


def _slug_coz(ilanlar: list[Ilan]) -> list[Ilan]:
    """Aynı slug'a düşen ilanlarda ilk eklenen kısa slug'ını korur, sonrakiler uzun id alır.

    Uzatmadan sonra da çakışma kalırsa (pratikte imkânsız) derleme durur.
    """
    sirali = sorted(ilanlar, key=lambda i: (i.eklenme_tarihi, i.id))
    gorulen: set[str] = set()
    sonuc = []
    for ilan in sirali:
        if ilan.slug in gorulen:
            log.warning("Slug çakışması, id ön eki uzatıldı: %s", ilan.id)
            ilan = dataclasses.replace(ilan, id_on_ek=UZUN_ID_ON_EK)
            if ilan.slug in gorulen:
                raise DerlemeHatasi(f"Slug çakışması çözülemedi: {ilan.slug}")
        gorulen.add(ilan.slug)
        sonuc.append(ilan)
    return sonuc


def benzer_ilanlar(ilan: Ilan, acik: list[Ilan], adet: int = BENZER_ADET) -> list[Ilan]:
    """Aynı türdeki açık ilanlar; aynı ili paylaşanlar önce, sonra en yeniler."""
    adaylar = [i for i in acik if i.id != ilan.id and i.ilan_turu == ilan.ilan_turu]
    iller = set(ilan.iller)
    adaylar.sort(key=lambda i: (bool(iller & set(i.iller)), i.eklenme_tarihi, i.id), reverse=True)
    return adaylar[:adet]


def _kurum_merkezleri(acik: list[Ilan]) -> list[Merkez]:
    """Kalıcı kurumlar her zaman; diğerleri yalnızca açık ilanı varsa."""
    adlar: dict[str, tuple[str, bool]] = {slug: (ad, True) for slug, ad in kalici_kurumlar()}
    for ilan in sorted(acik, key=lambda i: (i.eklenme_tarihi, i.id)):
        slug, ad, kalici = kurum_anahtari(ilan.kurum)
        if slug and not kalici:
            adlar[slug] = (ad, False)  # en yeni ilandaki yazım kullanılır
    return [kurum_merkezi(slug, ad, kalici) for slug, (ad, kalici) in sorted(adlar.items())]


def merkez_verileri(sayfali: list[Ilan], acik: list[Ilan], simdi: datetime) -> list[MerkezVerisi]:
    """Üretilecek merkezler: kalıcı olanlar boş da olsa, diğerleri açık ilanı varsa."""
    acik_kimlikler = {i.id for i in acik}
    kapanmis = [i for i in sayfali if i.id not in acik_kimlikler]
    kapanmis.sort(key=lambda i: (i.basvuru_bitis, i.id), reverse=True)
    sonuc = []
    adaylar = [*SABIT_MERKEZLER, *sehir_merkezleri(), *_kurum_merkezleri(acik)]
    for merkez in adaylar:
        uyanlar = tuple(i for i in acik if merkez.filtre(i, simdi))
        if not uyanlar and not merkez.kalici:
            continue
        kapanan = tuple(i for i in kapanmis if merkez.filtre(i, simdi))
        sonuc.append(
            MerkezVerisi(
                merkez=merkez,
                acik=uyanlar,
                kapanan=kapanan[:KAPANAN_ADET],
                kapanan_sayisi=len(kapanan),
            )
        )
    return sonuc


def _diger_merkezler(veriler: list[MerkezVerisi]) -> list[Merkez]:
    """"Diğer kategoriler" kutusu: indekslenen sabit merkezler ve en büyük şehirler."""
    sabit = [v.merkez for v in veriler if v.merkez.grup not in {"sehir", "kurum"} and v.indekslenebilir]
    sehirler = sorted(
        (v for v in veriler if v.merkez.grup == "sehir" and v.indekslenebilir),
        key=lambda v: -len(v.acik),
    )
    return sabit + [v.merkez for v in sehirler[:DIGER_SEHIR_ADET]]


def derle(
    satirlar: Iterable[dict[str, Any]], simdi: datetime, en_az_acik: int = EN_AZ_ACIK_ILAN
) -> Derleme:
    bugun = bugun_tr(simdi)
    sayfali = _slug_coz([i for i in _ilanlar(satirlar) if sayfasi_olacak_mi(i, bugun)])
    acik = [i for i in sayfali if i.basvuru_bitis >= bugun]
    if len(acik) < en_az_acik:
        raise DerlemeHatasi(
            f"Yalnızca {len(acik)} açık ilan var (en az {en_az_acik} bekleniyordu); "
            "veri kaynağında sorun olabilir, site yayınlanmadı."
        )

    veriler = merkez_verileri(sayfali, acik, simdi)
    baglam = Baglam(
        simdi=simdi,
        bugun=bugun,
        mevcut_yollar=frozenset(v.merkez.yol for v in veriler),
        il_yollari={v.merkez.il: v.merkez.yol for v in veriler if v.merkez.il},
        kurum_yollari={
            v.merkez.yol.split("/")[2]: v.merkez.yol for v in veriler if v.merkez.grup == "kurum"
        },
        acik_sayisi=len(acik),
    )
    kurum_acik = Counter(i.kurum_slug for i in acik)
    derleme = Derleme(acik=len(acik), kapali=len(sayfali) - len(acik))

    basliklar = ilan_basliklari(sayfali, bugun)
    for ilan in sayfali:
        derleme.sayfalar[ilan.yol] = ilan_sayfasi(
            ilan, baglam, benzer_ilanlar(ilan, acik), basliklar[ilan.id], kurum_acik[ilan.kurum_slug]
        )
        if ilan.basvuru_bitis >= bugun:
            derleme.sitemap.append((ilan.yol, ilan.eklenme_tarihi))

    digerleri = _diger_merkezler(veriler)
    for veri in veriler:
        merkez = veri.merkez
        ulusal = [i for i in acik if merkez.il and merkez.il in i.iller and i.ulusal_mi]
        derleme.sayfalar[merkez.yol] = merkez_sayfasi(veri, baglam, digerleri, ulusal)
        if veri.indekslenebilir:
            derleme.merkezler.append(merkez.yol)
            derleme.sitemap.append((merkez.yol, kume_zamani(veri.acik, veri.kapanan, simdi)))
        else:
            derleme.noindex_merkezler.append(merkez.yol)

    bilgi_zamani = datetime.combine(BILGI_GUNCELLEME, time(), tzinfo=TR_SAAT)
    for bilgi in BILGI_SAYFALARI:
        derleme.sayfalar[bilgi.yol] = bilgi_sayfasi(bilgi, baglam)
        derleme.sitemap.append((bilgi.yol, bilgi_zamani))

    derleme.sayfalar["/"] = ana_sayfa(acik, baglam, veriler)
    tum_kapanan = [i for i in sayfali if i.basvuru_bitis < bugun]
    derleme.sitemap.insert(0, ("/", kume_zamani(acik, tum_kapanan, simdi)))
    derleme.sayfalar["/404.html"] = sayfa_404(baglam)
    return derleme


def sitemap_manifesti(girdiler: list[tuple[str, datetime]]) -> str:
    """IndexNow karşılaştırması için {url: lastmod} JSON'u (yayına çıkmaz, nokta ile başlar)."""
    return json.dumps(
        {SITE_URL + yol: zaman.replace(microsecond=0).isoformat() for yol, zaman in girdiler},
        ensure_ascii=False, indent=0, sort_keys=True,
    )


def sitemap_xml(girdiler: list[tuple[str, datetime]]) -> str:
    satirlar = "".join(
        f"<url><loc>{xml_escape(SITE_URL + yol)}</loc>"
        f"<lastmod>{zaman.replace(microsecond=0).isoformat()}</lastmod></url>\n"
        for yol, zaman in girdiler
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{satirlar}</urlset>\n"
    )


ROBOTS_TXT = f"""# kamuuygulama.me
# Arama, cevap motoru ve eğitim tarayıcılarının hepsine açık.
# Kendi grubu olan bot "*" grubunu okumaz; bu yüzden her grupta Allow: / var.

User-agent: *
Allow: /

# Arama ve cevap motoru dizinleri
User-agent: Googlebot
User-agent: Bingbot
User-agent: Applebot
User-agent: OAI-SearchBot
User-agent: PerplexityBot
User-agent: Claude-SearchBot
Allow: /

# Kullanıcı isteğiyle sayfa açan ajanlar
User-agent: ChatGPT-User
User-agent: Claude-User
User-agent: Perplexity-User
Allow: /

# Model eğitimi: marka ve ilan verisi model belleğine girebilsin diye açık
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: Google-Extended
User-agent: Applebot-Extended
User-agent: CCBot
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""


def robots_txt() -> str:
    return ROBOTS_TXT


def kume_zamani(acik: Iterable[Ilan], kapanan: Iterable[Ilan], simdi: datetime) -> datetime:
    """Bir ilan kümesinin son değiştiği an (sitemap lastmod).

    Küme iki yolla değişir: yeni ilan eklenir (eklenme_tarihi) ya da bir ilanın
    son başvurusu geçer (bitişin ertesi günü 00:00, Türkiye saati). Her derlemede
    "şimdi" yazılmaz; böylece IndexNow yalnızca gerçekten değişen adresleri bildirir.
    """
    adaylar = [i.eklenme_tarihi for i in acik]
    adaylar += [
        datetime.combine(i.basvuru_bitis + timedelta(days=1), time(), tzinfo=TR_SAAT)
        for i in kapanan
    ]
    return min(max(adaylar), simdi) if adaylar else simdi


def _dosya_yolu(cikti: Path, yol: str) -> Path:
    dosya = cikti / yol.lstrip("/") if yol.endswith(".html") else cikti / yol.strip("/") / "index.html"
    if not dosya.resolve().is_relative_to(cikti.resolve()):
        raise DerlemeHatasi(f"Çıktı dışına yazma girişimi: {yol}")
    return dosya


def _guvenli_temizle(cikti: Path, kok: Path) -> None:
    """Yalnızca adı _site olan, kaynak dosya içermeyen bir klasörü boşaltır."""
    hedef = cikti.resolve()
    kok_r = kok.resolve()
    korunan = [STATIK.resolve(), *((kok / ad).resolve() for ad in KOK_DOSYALARI)]
    if hedef.name != CIKTI_ADI or (hedef / ".git").exists():
        raise DerlemeHatasi(f"Çıktı klasörünün adı {CIKTI_ADI} olmalı: {hedef}")
    if (
        hedef == kok_r
        or hedef in kok_r.parents
        or any(k.is_relative_to(hedef) or hedef.is_relative_to(k) for k in korunan)
    ):
        raise DerlemeHatasi(f"Çıktı klasörü kaynak dosyalarla çakışıyor: {hedef}")
    if hedef.exists() and not hedef.is_dir():
        raise DerlemeHatasi(f"Çıktı yolu bir klasör değil: {hedef}")
    # Klasörün kendisi değil içeriği silinir (Windows'ta açık klasör kilidine takılmaz).
    for oge in hedef.iterdir() if hedef.exists() else ():
        if oge.is_symlink() or not oge.is_dir():
            oge.unlink()
        else:
            shutil.rmtree(oge)


def yaz(derleme: Derleme, cikti: Path, kok: Path = KOK) -> None:
    eksik = [ad for ad in KOK_DOSYALARI if not (kok / ad).exists()]
    if eksik:
        raise DerlemeHatasi(f"Statik dosyalar eksik: {', '.join(eksik)}")
    _guvenli_temizle(cikti, kok)
    cikti.mkdir(parents=True, exist_ok=True)
    for yol, icerik in derleme.sayfalar.items():
        dosya = _dosya_yolu(cikti, yol)
        dosya.parent.mkdir(parents=True, exist_ok=True)
        dosya.write_text(icerik, encoding="utf-8", newline=LF)
    (cikti / "sitemap.xml").write_text(sitemap_xml(derleme.sitemap), encoding="utf-8", newline=LF)
    (cikti / "robots.txt").write_text(robots_txt(), encoding="utf-8", newline=LF)
    (cikti / MANIFEST_ADI).write_text(sitemap_manifesti(derleme.sitemap), encoding="utf-8", newline=LF)
    shutil.copytree(STATIK, cikti, dirs_exist_ok=True)
    for ad in KOK_DOSYALARI:
        kaynak = kok / ad
        if kaynak.is_dir():
            shutil.copytree(kaynak, cikti / ad, dirs_exist_ok=True)
        else:
            shutil.copy2(kaynak, cikti / ad)
