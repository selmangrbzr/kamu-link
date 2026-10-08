"""Yapılandırılmış veri (JSON-LD).

JobPosting yalnızca açık ilanlarda ve yalnızca veride gerçekten olan alanlarla
üretilir; bilinmeyen alan (maaş, deneyim, sokak adresi) eklenmez.
Kaynak: https://developers.google.com/search/docs/appearance/structured-data/job-posting
"""

import html
import json
from typing import Any

from .metin import katla, sart_parcalari, tarih_tr, tr_kucuk
from .model import EGITIM_KATEGORISI, Ilan

SITE_URL = "https://kamuuygulama.me"
SITE_ADI = "Kamu"
_TAM_ZAMANLI_TURLER = frozenset(
    {"Memur", "Sözleşmeli Personel", "Akademik Personel", "Askeri Personel"}
)


def istihdam_turu(ilan: Ilan) -> str | None:
    """Google employmentType; metinden emin olunamıyorsa None (alan hiç yazılmaz)."""
    metin = katla(" ".join(filter(None, (ilan.pozisyon, ilan.ozel_sartlar))))
    if "kismi zamanli" in metin or "ders ucretli" in metin:
        return "PART_TIME"
    if "gecici" in metin or "mevsimlik" in metin:
        return "TEMPORARY"
    if ilan.ilan_turu in _TAM_ZAMANLI_TURLER:
        return "FULL_TIME"
    if ilan.ilan_turu == "İşçi" and "surekli" in metin:
        return "FULL_TIME"
    return None


def gecerlilik_sonu(ilan: Ilan) -> str:
    """Son başvuru gününün sonu, Türkiye saatiyle (ISO 8601)."""
    return f"{ilan.basvuru_bitis.isoformat()}T23:59:59+03:00"


def _e(metin: str) -> str:
    return html.escape(metin, quote=False)


def aciklama_html(ilan: Ilan) -> str:
    """JobPosting.description: sayfada görünen bilgilerin HTML özeti."""
    parcalar = [f"<p>{_e(ilan.kurum_adi)}, {_e(ilan.is_basligi)} alımı yapıyor.</p>"]
    satirlar: list[str] = []
    if ilan.kisi_sayisi:
        satirlar.append(f"Kadro: {ilan.kisi_sayisi}")
    satirlar.append(f"İlan türü: {ilan.ilan_turu}")
    if ilan.egitim_seviyesi:
        satirlar.append(f"Eğitim: {ilan.egitim_seviyesi}")
    if ilan.kpss_puan_turu:
        satirlar.append(f"KPSS puan türü: {ilan.kpss_puan_turu}")
    if ilan.ales_puan_turu:
        satirlar.append(f"ALES puan türü: {ilan.ales_puan_turu}")
    if ilan.yas_siniri:
        satirlar.append(f"Yaş sınırı: {ilan.yas_siniri}")
    if ilan.sehirler:
        satirlar.append(f"Görev yeri: {', '.join(ilan.sehirler)}")
    satirlar.append(f"Son başvuru: {tarih_tr(ilan.basvuru_bitis, yil=True)}")
    if ilan.basvuru_yeri:
        satirlar.append(f"Başvuru yeri: {ilan.basvuru_yeri_temiz}")
    parcalar.append("<ul>" + "".join(f"<li>{_e(s)}</li>" for s in satirlar) + "</ul>")

    pozisyonlar = list(dict.fromkeys(k.pozisyon for k in ilan.kontenjan if k.pozisyon))
    if pozisyonlar:
        maddeler = "".join(f"<li>{_e(p)}</li>" for p in pozisyonlar)
        parcalar.append(f"<p>Pozisyonlar:</p><ul>{maddeler}</ul>")
    for baslik, metin in (("Özel şartlar", ilan.ozel_sartlar), ("Başvuru belgeleri", ilan.basvuru_belgeleri)):
        if metin:
            maddeler = "".join(f"<li>{_e(m)}</li>" for m in sart_parcalari(metin))
            parcalar.append(f"<p>{baslik}:</p><ul>{maddeler}</ul>")
    return "".join(parcalar)


def _konumlar(ilan: Ilan) -> list[dict[str, Any]]:
    iller = ilan.iller or (None,)
    return [
        {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                **({"addressRegion": il} if il else {}),
                "addressCountry": "TR",
            },
        }
        for il in iller
    ]


def is_ilani(ilan: Ilan) -> dict[str, Any]:
    veri: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": ilan.is_basligi,
        "description": aciklama_html(ilan),
        "datePosted": ilan.yayin_tarihi.isoformat(),
        "validThrough": gecerlilik_sonu(ilan),
        "hiringOrganization": {"@type": "Organization", "name": ilan.kurum_adi},
        "jobLocation": _konumlar(ilan),
        "directApply": False,
    }
    tur = istihdam_turu(ilan)
    if tur:
        veri["employmentType"] = tur
    if ilan.kisi_sayisi:
        veri["totalJobOpenings"] = ilan.kisi_sayisi
    kategori = EGITIM_KATEGORISI.get(tr_kucuk(ilan.egitim_seviyesi or ""))
    if kategori:
        veri["educationRequirements"] = {
            "@type": "EducationalOccupationalCredential",
            "credentialCategory": kategori,
        }
    return veri


def ekmek_kirintisi(ogeler: list[tuple[str, str]]) -> dict[str, Any]:
    """BreadcrumbList; ogeler (ad, mutlak olmayan yol) çiftleridir."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": sira, "name": ad, "item": SITE_URL + yol}
            for sira, (ad, yol) in enumerate(ogeler, start=1)
        ],
    }


SITE_TAM_ADI = "Kamu: Memur Alım İlanları"
ALTERNATIF_ADLAR = ["Kamu", "Kamu uygulaması", "kamuuygulama.me"]
KURULUS_ACIKLAMASI = (
    "Türkiye'deki kamu personel alım ilanlarını takip eden bağımsız mobil uygulama. "
    "Resmî kurum değil."
)
PLAY_URL = "https://play.google.com/store/apps/details?id=com.selman.memur_ilanlari"
APP_STORE_URL = "https://apps.apple.com/tr/app/id6792290422"
INSTAGRAM_URL = "https://www.instagram.com/kamu.uygulama/"
FACEBOOK_URL = "https://www.facebook.com/profile.php?id=61595200171443"
KURULUS_ID = f"{SITE_URL}/#kurulus"
SITE_ID = f"{SITE_URL}/#site"
UYGULAMA_ID = f"{SITE_URL}/#uygulama"


def _kurulus() -> dict[str, Any]:
    return {
        "@type": "Organization",
        "@id": KURULUS_ID,
        "name": SITE_TAM_ADI,
        "alternateName": ALTERNATIF_ADLAR,
        "url": SITE_URL + "/",
        "logo": {"@type": "ImageObject", "url": SITE_URL + "/kamu-icon-512.png", "width": 512, "height": 512},
        "description": KURULUS_ACIKLAMASI,
        "sameAs": [PLAY_URL, APP_STORE_URL, INSTAGRAM_URL, FACEBOOK_URL],
    }


def _site() -> dict[str, Any]:
    return {
        "@type": "WebSite",
        "@id": SITE_ID,
        "name": SITE_TAM_ADI,
        "alternateName": ALTERNATIF_ADLAR,
        "url": SITE_URL + "/",
        "inLanguage": "tr-TR",
        "publisher": {"@id": KURULUS_ID},
    }


def _uygulama() -> dict[str, Any]:
    # Puan/yorum verisi yok; AggregateRating bilerek eklenmez.
    return {
        "@type": "MobileApplication",
        "@id": UYGULAMA_ID,
        "name": SITE_TAM_ADI,
        "operatingSystem": "Android, iOS",
        "applicationCategory": "BusinessApplication",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "TRY"},
        "installUrl": [PLAY_URL, APP_STORE_URL],
        "publisher": {"@id": KURULUS_ID},
    }


def varlik_grafigi(hakkinda_yolu: str | None = None) -> dict[str, Any]:
    """Kuruluş, site ve uygulamayı tek @graph'ta bağlar; hakkında sayfasında AboutPage de eklenir."""
    dugumler = [_kurulus(), _site(), _uygulama()]
    if hakkinda_yolu:
        dugumler.append({
            "@type": "AboutPage",
            "@id": f"{SITE_URL}{hakkinda_yolu}#sayfa",
            "url": SITE_URL + hakkinda_yolu,
            "name": "Kamu hakkında",
            "inLanguage": "tr-TR",
            "isPartOf": {"@id": SITE_ID},
            "mainEntity": {"@id": KURULUS_ID},
        })
    return {"@context": "https://schema.org", "@graph": dugumler}


def script_etiketi(veri: dict[str, Any]) -> str:
    """JSON-LD'yi <script> içine güvenle gömer ("</script>" kaçışı dahil)."""
    metin = json.dumps(veri, ensure_ascii=False, separators=(",", ":"))
    metin = metin.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f'<script type="application/ld+json">{metin}</script>'
