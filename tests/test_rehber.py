"""Rehber sayfaları: üretim, resmî kaynak, Article JSON-LD, metin kuralları ve veri bölümü."""

import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from test_tur2 import baslik, kimlik, robots
from test_tur3 import _DIR_EKI, _RESMI_HITAP, gorunen_metin, karisik_veri
from test_uretec import SIMDI, jsonld_listesi, satir

from uretec.derle import derle
from uretec.rehber import basvuru_yollari, kaynak_listesi, uzman_yardimcisi_mi
from uretec.rehber_icerik import MERKEZ_REHBERI, REHBER_KOK, REHBERLER, REHBER_SLUGLARI
from uretec.rehber_kaynak import Olgu, resmi_mi
from uretec.model import Ilan

YOLLAR = [r.yol for r in REHBERLER]
SUREC_IFADELERI = (
    "günde dört kez", "yapay zek", "hata olabilir", "otomatik", "çekiyoruz", "çıkarıyoruz",
)
_KAYNAK_ATIF = re.compile(r'<span class="atif">\(<a href="([^"]+)">')


def uzman_ilani(**alanlar) -> dict:
    temel = dict(
        id=kimlik(901), kurum="SERMAYE PİYASASI KURULU BAŞKANLIĞI",
        pozisyon="40 UZMAN YARDIMCISI ALACAK", kisi_sayisi=40, ilan_turu="Memur",
        kpss_puan_turu="P1, P2, P3, P25", egitim_seviyesi="Lisans", sehirler=["Ankara"],
        basvuru_bitis="2026-10-26", basvuru_yeri="https://kariyerkapisi.gov.tr/isealim",
    )
    temel.update(alanlar)
    return satir(**temel)


def rehber_derlemesi():
    return derle([*karisik_veri(), uzman_ilani()], SIMDI, en_az_acik=1)


def graf(sayfa: str) -> dict:
    return next(v for v in jsonld_listesi(sayfa) if "@graph" in v)


# --- Üretim ve indeks -----------------------------------------------------------------

def test_yedi_rehber_ve_dizin_uretilir_indekslenir_sitemapte():
    derleme = rehber_derlemesi()
    harita = dict(derleme.sitemap)
    assert len(REHBERLER) == 7 and len(set(YOLLAR)) == 7
    for yol in [*YOLLAR, REHBER_KOK]:
        assert yol in derleme.sayfalar, yol
        assert robots(derleme.sayfalar[yol]).startswith("index"), yol
        assert yol in harita, yol
    dizin = derleme.sayfalar[REHBER_KOK]
    for yol in YOLLAR:
        assert f'href="{yol}"' in dizin


def test_rehber_lastmod_kontrol_gunu_ile_veri_degisiminin_yenisi():
    rehber = REHBER_SLUGLARI["uzman-yardimciligi-alimlari"]
    kontrol = datetime.combine(rehber.kontrol_tarihi, datetime.min.time(),
                               tzinfo=timezone(timedelta(hours=3)))
    bos = dict(derle([satir()], SIMDI, en_az_acik=1).sitemap)
    assert bos[rehber.yol] == kontrol  # uzman ilanı yok: elle kontrol günü
    yeni = uzman_ilani(eklenme_tarihi="2026-10-08T08:00:00+00:00")
    dolu = dict(derle([satir(), yeni], SIMDI, en_az_acik=1).sitemap)
    assert dolu[rehber.yol] == datetime(2026, 10, 8, 8, 0, tzinfo=timezone.utc)
    assert dolu[REHBER_KOK] >= dolu[rehber.yol]


# --- Kaynaklar ----------------------------------------------------------------------

def test_her_olgunun_kaynagi_resmi_alan_adinda_ve_kontrol_tarihli():
    for rehber in REHBERLER:
        olgular = list(rehber.olgular())
        assert olgular, rehber.slug
        assert any(isinstance(p, Olgu) for p in rehber.cevap), rehber.slug
        for olgu in olgular:
            sunucu = urlsplit(olgu.kaynak_url).hostname or ""
            assert resmi_mi(olgu.kaynak_url), (rehber.slug, olgu.kaynak_url)
            assert sunucu.endswith(".gov.tr"), sunucu
            assert olgu.kontrol_tarihi <= SIMDI.date(), olgu
            assert olgu.metin.strip() and olgu.kaynak_adi and olgu.kaynak_kisa_adi


def test_resmi_alan_adi_denetimi_sahte_adresleri_reddeder():
    assert resmi_mi("https://www.mevzuat.gov.tr/MevzuatMetin/1.5.657.pdf")
    for kotu in ("http://www.mevzuat.gov.tr/x", "https://memurlar.net/haber/1",
                 "https://gov.tr.ornek.com/", "https://ornekgov.tr/"):
        assert not resmi_mi(kotu), kotu


def test_sayfadaki_atiflar_ve_kaynaklar_listesi_resmi():
    derleme = rehber_derlemesi()
    for rehber in REHBERLER:
        sayfa = derleme.sayfalar[rehber.yol]
        atiflar = _KAYNAK_ATIF.findall(sayfa)
        assert len(atiflar) >= 3, rehber.slug
        assert all(resmi_mi(u) for u in atiflar), rehber.slug
        kaynaklar = sayfa[sayfa.index('<ol class="kaynaklar">'):]
        for olgu in kaynak_listesi(rehber):
            assert f'href="{olgu.kaynak_url}"' in kaynaklar, (rehber.slug, olgu.kaynak_url)
        assert "Son kontrol:" in gorunen_metin(sayfa)


# --- JSON-LD --------------------------------------------------------------------

def test_article_jsonld_alanlari_tam():
    derleme = rehber_derlemesi()
    for rehber in REHBERLER:
        sayfa = derleme.sayfalar[rehber.yol]
        dugumler = {d["@type"]: d for d in graf(sayfa)["@graph"]}
        makale = dugumler["Article"]
        assert dugumler["Organization"]["@id"] == "https://kamuuygulama.me/#kurulus"
        assert makale["headline"] == rehber.h1
        assert makale["datePublished"] == rehber.yayin_tarihi.isoformat()
        assert makale["dateModified"] == rehber.kontrol_tarihi.isoformat()
        assert makale["author"] == {"@id": "https://kamuuygulama.me/#kurulus"}
        assert makale["publisher"] == {"@id": "https://kamuuygulama.me/#kurulus"}
        assert makale["inLanguage"] == "tr-TR"
        assert makale["mainEntityOfPage"] == "https://kamuuygulama.me" + rehber.yol
        assert all(resmi_mi(u) for u in makale["citation"])
        kirinti = next(v for v in jsonld_listesi(sayfa) if v.get("@type") == "BreadcrumbList")
        assert [o["name"] for o in kirinti["itemListElement"]] == ["Ana sayfa", "Rehberler", rehber.ad]


# --- Metin kuralları ---------------------------------------------------------------

def test_rehberlerde_surec_metni_siz_hitabi_ve_dir_eki_yok():
    derleme = rehber_derlemesi()
    for yol in [*YOLLAR, REHBER_KOK]:
        metin = gorunen_metin(derleme.sayfalar[yol])
        govde = metin[: metin.index("Kategoriler")] if "Kategoriler" in metin else metin
        for ifade in SUREC_IFADELERI:
            assert ifade not in govde.lower(), (yol, ifade)
        assert _RESMI_HITAP.search(govde) is None, (yol, _RESMI_HITAP.search(govde))
        # "Genel Kültür" bir test adı; -dır/-dir eki değil.
        kalan = [m.group(0) for m in _DIR_EKI.finditer(govde) if m.group(0).lower() != "kültür"]
        assert kalan == [], (yol, kalan)


def test_kopya_baslik_ve_aciklama_yok():
    derleme = rehber_derlemesi()
    basliklar = [baslik(h) for y, h in derleme.sayfalar.items() if y != "/404.html"]
    assert [b for b, n in Counter(basliklar).items() if n > 1] == []
    aciklamalar = [r.aciklama for r in REHBERLER]
    assert len(set(aciklamalar)) == len(aciklamalar)
    for rehber in REHBERLER:
        assert len(rehber.aciklama) <= 158 and len(rehber.baslik) <= 75, rehber.slug


def test_dogrudan_cevap_ustte_ve_tarihli():
    derleme = rehber_derlemesi()
    for rehber in REHBERLER:
        sayfa = derleme.sayfalar[rehber.yol]
        h1 = sayfa.index("<h1>")
        cevap = sayfa.index('class="kisa-cevap"')
        assert h1 < cevap < sayfa.index('class="bolum-bas"'), rehber.slug
        assert sayfa.count("<h1>") == 1


# --- Bağlantılar ----------------------------------------------------------------------

def test_kolofonda_rehberler_grubu_ve_merkezden_tek_rehber_linki():
    derleme = rehber_derlemesi()
    ana = derleme.sayfalar["/"]
    kolofon = ana[ana.index('<footer class="kolofon">'):]
    assert ">Rehberler<" in kolofon
    for yol in [*YOLLAR, REHBER_KOK]:
        assert f'href="{yol}"' in kolofon
    for merkez_yolu, slug in MERKEZ_REHBERI.items():
        sayfa = derleme.sayfalar.get(merkez_yolu)
        if sayfa is None:
            continue
        govde = sayfa[: sayfa.index('<footer class="kolofon">')]
        assert govde.count('class="rehber-bag"') == 1, merkez_yolu
        assert f'href="{REHBER_SLUGLARI[slug].yol}"' in govde


# --- Veri bölümü ------------------------------------------------------------------------

def test_veri_bolumu_guncel_sayilari_yazar():
    derleme = rehber_derlemesi()
    gecerlilik = " ".join(gorunen_metin(derleme.sayfalar["/rehber/kpss-puani-gecerlilik-suresi/"]).split())
    # P3: satir(), iki memur ilanı (varsayılan P3) ve uzman ilanı; P93 ve P94 birer ilan.
    assert ("8 Ekim 2026 itibarıyla Kamu'da listelenen açık ilanlardan 4 ilan KPSS P3, 1 ilan P93, "
            "1 ilan P94 puanı istiyor.") in gecerlilik
    uzman = derleme.sayfalar["/rehber/uzman-yardimciligi-alimlari/"]
    assert f'href="{Ilan.from_satir(uzman_ilani()).yol}"' in uzman
    assert "KPSS P1, P2, P3, P25" in gorunen_metin(uzman)


def test_uzman_yardimcisi_eslesmesi_kontenjandan_da_yapilir():
    assert uzman_yardimcisi_mi(Ilan.from_satir(uzman_ilani()))
    bddk = Ilan.from_satir(satir(pozisyon="135 MESLEK PERSONELİ ALACAK",
                                 kontenjan=[{"pozisyon": "Bankacılık Uzman Yardımcısı", "toplam": 50}]))
    assert uzman_yardimcisi_mi(bddk)
    assert not uzman_yardimcisi_mi(Ilan.from_satir(satir()))


def test_basvuru_yolu_olumsuz_ifadeleri_saymaz():
    assert basvuru_yollari(
        "Kariyer Kapısı (https://kariyerkapisi.gov.tr) üzerinden; şahsen, kargo veya posta "
        "yoluyla başvuru kabul edilmez."
    ) == ["Kariyer Kapısı (e-Devlet)"]
    assert basvuru_yollari("Rektörlüğe adresine (şahsen başvuru, posta kabul edilmez)") == ["Şahsen"]
    assert basvuru_yollari("İlgili birime şahsen veya posta ile (e-posta ile başvuru kabul edilmez).") == [
        "Şahsen", "Posta ya da kargo",
    ]
    assert basvuru_yollari("https://basvuru.ornek.edu.tr adresinden çevrimiçi") == [
        "Kurumun internet başvuru sistemi",
    ]
    assert basvuru_yollari("ornek@belediye.bel.tr e-posta adresine elektronik ortamda") == ["E-posta"]
