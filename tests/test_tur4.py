"""Dördüncü tur: AEO (yapay zekâ cevap motorları) önerileri."""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from test_tur2 import kimlik
from test_tur3 import gorunen_metin, karisik_veri, ozet_metni
from test_uretec import SIMDI, jsonld_listesi, satir

from uretec.derle import derle, kume_zamani, robots_txt, sitemap_manifesti, yaz
from uretec.indexnow import (
    INDEXNOW_ANAHTARI,
    degisen_adresler,
    istek_govdesi,
    sitemap_oku,
)
from uretec.model import Ilan

STATIK = Path(__file__).resolve().parent.parent / "uretec" / "statik"


def manset(sayfa: str) -> str:
    return re.search(r'<p class="manset-satir">(.*?)</p>', sayfa, re.S).group(1)


def duz(parca: str) -> str:
    """Etiketleri boşluksuz siler: "<time>1</time>-<time>8 Ekim</time>" -> "1-8 Ekim"."""
    return re.sub(r"<[^>]+>", "", parca)


def graf(sayfa: str) -> dict:
    return next(v for v in jsonld_listesi(sayfa) if "@graph" in v)


# --- 1. KPSS'siz merkez veri hatası -----------------------------------------------

def test_kpss_siz_merkez_sartlarda_kpss_gecen_ilani_almaz():
    gib = satir(id=kimlik(401), kurum="GELİR İDARESİ BAŞKANLIĞI", ilan_turu="Memur",
                kpss_puan_turu=None, ozel_sartlar="DMK 48 şartları; KPSSP17/18/22/23/47/48 en az 65")
    kpsssiz = satir(id=kimlik(402), kpss_puan_turu=None, ilan_turu="İşçi", ozel_sartlar="Sürücü belgesi")
    sayfa = derle([satir(), gib, kpsssiz], SIMDI, en_az_acik=1).sayfalar["/kpss-siz-kamu-ilanlari/"]
    assert Ilan.from_satir(gib).yol not in sayfa
    assert Ilan.from_satir(kpsssiz).yol in sayfa


# --- 2. Tarihli ve özneli manşet --------------------------------------------------

def test_merkez_mansetinde_tarih_ozne_ve_aralik():
    p3 = [satir(id=kimlik(410 + n), kpss_puan_turu="P3", kisi_sayisi=10 + n) for n in range(3)]
    sayfa = derle(p3, SIMDI, en_az_acik=1).sayfalar["/kpss-p3-ilanlari/"]
    assert duz(manset(sayfa)) == (
        "8 Ekim 2026 itibarıyla KPSS P3 puanı isteyen 3 açık kamu ilanı ve toplam 33 kadro var. "
        "1-8 Ekim 2026 arasında 3 yeni ilan eklendi."
    )
    assert '<time datetime="2026-10-08">8 Ekim 2026</time> itibarıyla' in sayfa
    assert '<time datetime="2026-10-01">1</time>-<time datetime="2026-10-08">8 Ekim 2026</time>' in sayfa


def test_ana_sayfa_bugun_yerine_tarihli():
    ana = derle([satir()], SIMDI, en_az_acik=1).sayfalar["/"]
    assert "Bugün <b>" not in ana
    assert manset(ana).startswith('<time datetime="2026-10-08">8 Ekim 2026</time> itibarıyla <b>1</b> açık kamu ilanı')


def test_sehir_ve_bos_merkez_mansetleri():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    assert "itibarıyla görev yeri İstanbul olan <b>1</b> açık kamu ilanı" in derleme.sayfalar["/sehir/istanbul/"]
    assert "itibarıyla memur alımı için açık kamu ilanı yok." in derleme.sayfalar["/memur-alimlari/"]


# --- 3. Özet tarihlerinde yıl, ilan tarihinde <time> --------------------------------

def test_ozet_tarihlerinde_yil_var():
    ozet = ozet_metni(derle([satir()], SIMDI, en_az_acik=1).sayfalar["/sozlesmeli-personel-alimlari/"])
    assert "En yakın son başvuru 2 Kasım 2026'da" in ozet
    assert not re.search(r"\d+ (Ekim|Kasım)'(da|de|ta|te)", ozet)


def test_ilan_eklenme_tarihi_time_etiketi():
    sayfa = derle([satir()], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(satir()).yol]
    assert "<time datetime=\"2026-10-03\">3 Ekim 2026</time>'da eklendi" in sayfa


# --- 4. İlan özetinde koşullu cümleler ----------------------------------------------

def ilan_ozeti(s: dict) -> str:
    sayfa = derle([s], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(s).yol]
    return gorunen_metin(re.search(r'<p class="ilan-ozet">(.*?)</p>', sayfa, re.S).group(1))


def test_ilan_ozeti_sart_cumlesi():
    ozet = ilan_ozeti(satir(yas_siniri="35 altı"))
    assert "Eğitim şartı lisans; KPSS puan türü P3; yaş sınırı 35 altı." in ozet
    yok = ilan_ozeti(satir(egitim_seviyesi=None, kpss_puan_turu=None))
    assert "şartı" not in yok and "puan türü" not in yok


def test_ilan_ozeti_basvuru_yolu_yalnizca_taninan_kaliplarda():
    assert "Başvuru ÖSYM üzerinden yapılıyor." in ilan_ozeti(satir(basvuru_yeri="https://ais.osym.gov.tr"))
    assert "Başvuru e-Devlet'te Kariyer Kapısı üzerinden yapılıyor." in ilan_ozeti(satir())
    assert "Başvuru şahsen ya da posta ile yapılıyor." in ilan_ozeti(satir(basvuru_yeri="Şahsen veya posta ile"))
    assert "Başvurular" not in ilan_ozeti(satir(basvuru_yeri="Kurum binası 3. kat")).replace("Başvurular 1", "")


def test_ilan_ozeti_cok_illi_dagilim():
    kontenjan = [{"pozisyon": "Gelir Uzman Yardımcısı", "sehir": il, "toplam": n}
                 for il, n in (("Ankara", 10), ("İzmir", 3), ("Kars", 2))]
    ozet = ilan_ozeti(satir(kisi_sayisi=15, kontenjan=kontenjan))
    assert "Kadrolar 3 ile dağılıyor; en çok kadro Ankara'da (10)." in ozet


# --- 5. Kurum cevabı ve merkez tür dağılımı ------------------------------------------

def test_kurum_sayfasinda_dogrudan_cevap():
    msb = [satir(id=kimlik(420 + n), kurum="MİLLİ SAVUNMA BAKANLIĞI", basvuru_bitis=f"2026-10-2{n}")
           for n in range(2)]
    sayfa = derle(msb, SIMDI, en_az_acik=1).sayfalar["/kurum/milli-savunma-bakanligi/"]
    assert duz(manset(sayfa)) == (
        "Milli Savunma Bakanlığı: 8 Ekim 2026 itibarıyla 2 açık personel alım ilanı var; "
        "en yakın son başvuru 20 Ekim 2026."
    )
    bos = derle([satir()], SIMDI, en_az_acik=1).sayfalar["/kurum/saglik-bakanligi/"]
    assert "Sağlık Bakanlığı: " in bos and "itibarıyla açık personel alım ilanı yok." in bos


def test_egitim_ve_puan_merkezlerinde_tur_dagilimi_ve_lisede_memur_yok_cumlesi():
    derleme = derle(karisik_veri(), SIMDI, en_az_acik=1)
    lise = ozet_metni(derleme.sayfalar["/lise-mezunu-kamu-ilanlari/"])
    assert "Açık ilanlar: 1 memur, 1 sözleşmeli." in lise
    assert "memur ilanı yok" not in lise  # lisede memur var: cümle yazılmaz
    assert "Açık ilanlar:" in ozet_metni(derleme.sayfalar["/kpss-p3-ilanlari/"])
    memursuz = derle([satir(id=kimlik(430), egitim_seviyesi="Lise", ilan_turu="İşçi"),
                      satir(id=kimlik(431), egitim_seviyesi="Lise")], SIMDI, en_az_acik=1)
    assert ("Şu an lise mezunlarına açık memur ilanı yok; açık ilanların hepsi işçi ve "
            "sözleşmeli personel alımı.") in ozet_metni(memursuz.sayfalar["/lise-mezunu-kamu-ilanlari/"])


# --- 6. Varlık grafiği ---------------------------------------------------------------

def test_ana_sayfada_tek_graph_kurulus_site_uygulama():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    ana = derleme.sayfalar["/"]
    dugumler = {d["@type"]: d for d in graf(ana)["@graph"]}
    org = dugumler["Organization"]
    assert org["@id"] == "https://kamuuygulama.me/#kurulus"
    assert org["name"] == "Kamu: Memur Alım İlanları"
    assert org["alternateName"] == ["Kamu", "Kamu uygulaması", "kamuuygulama.me"]
    assert org["description"].endswith("Resmî kurum değil.")
    assert "https://www.facebook.com/profile.php?id=61595200171443" in org["sameAs"]
    assert len(org["sameAs"]) == 4
    site = dugumler["WebSite"]
    assert site["publisher"] == {"@id": org["@id"]} and site["inLanguage"] == "tr-TR"
    app = dugumler["MobileApplication"]
    assert app["offers"] == {"@type": "Offer", "price": "0", "priceCurrency": "TRY"}
    assert app["operatingSystem"] == "Android, iOS" and len(app["installUrl"]) == 2
    assert '<meta property="og:site_name" content="Kamu: Memur Alım İlanları">' in ana
    for sayfa in derleme.sayfalar.values():
        assert "AggregateRating" not in sayfa


def test_hakkinda_aboutpage_mainentity_kurulus():
    sayfa = derle([satir()], SIMDI, en_az_acik=1).sayfalar["/hakkinda/"]
    dugumler = {d["@type"]: d for d in graf(sayfa)["@graph"]}
    assert dugumler["AboutPage"]["mainEntity"] == {"@id": "https://kamuuygulama.me/#kurulus"}


# --- 7. Meta açıklama ------------------------------------------------------------------

def test_merkez_meta_aciklamasinda_surec_cumlesi_yok_veri_cumlesi_var():
    derleme = derle(karisik_veri(), SIMDI, en_az_acik=1)
    for yol, sayfa in derleme.sayfalar.items():
        if yol not in ("/hakkinda/", "/nasil-calisir/"):  # süreç anlatımı yalnızca bilgi sayfalarında
            assert "günde dört kez" not in sayfa, yol
    meta = re.search(r'<meta name="description" content="([^"]+)"', derleme.sayfalar["/memur-alimlari/"]).group(1)
    assert meta.endswith("En büyük alım: İzmir Büyükşehir Belediyesi, 25 kadro.")
    assert "…" not in meta


# --- 8. robots.txt ---------------------------------------------------------------------

def test_robots_txt_birebir():
    beklenen = (
        "# kamuuygulama.me\n"
        "# Arama, cevap motoru ve eğitim tarayıcılarının hepsine açık.\n"
        "# Kendi grubu olan bot \"*\" grubunu okumaz; bu yüzden her grupta Allow: / var.\n\n"
        "User-agent: *\nAllow: /\n\n"
        "# Arama ve cevap motoru dizinleri\n"
        "User-agent: Googlebot\nUser-agent: Bingbot\nUser-agent: Applebot\n"
        "User-agent: OAI-SearchBot\nUser-agent: PerplexityBot\nUser-agent: Claude-SearchBot\nAllow: /\n\n"
        "# Kullanıcı isteğiyle sayfa açan ajanlar\n"
        "User-agent: ChatGPT-User\nUser-agent: Claude-User\nUser-agent: Perplexity-User\nAllow: /\n\n"
        "# Model eğitimi: marka ve ilan verisi model belleğine girebilsin diye açık\n"
        "User-agent: GPTBot\nUser-agent: ClaudeBot\nUser-agent: Google-Extended\n"
        "User-agent: Applebot-Extended\nUser-agent: CCBot\nAllow: /\n\n"
        "Sitemap: https://kamuuygulama.me/sitemap.xml\n"
    )
    assert robots_txt() == beklenen


# --- 9. IndexNow ve sitemap lastmod ------------------------------------------------------

def test_indexnow_fark_saf_fonksiyon():
    eski = {"https://kamuuygulama.me/a/": "2026-10-01", "https://kamuuygulama.me/b/": "2026-10-01",
            "https://kamuuygulama.me/silinen/": "2026-09-01"}
    yeni = {"https://kamuuygulama.me/a/": "2026-10-01", "https://kamuuygulama.me/b/": "2026-10-08",
            "https://kamuuygulama.me/c/": "2026-10-08"}
    assert degisen_adresler(eski, yeni) == ["https://kamuuygulama.me/b/", "https://kamuuygulama.me/c/"]
    assert degisen_adresler({}, yeni) == sorted(yeni)
    assert degisen_adresler(yeni, yeni) == []


def test_indexnow_govdesi_ve_anahtar_dosyasi():
    assert re.fullmatch(r"[0-9a-f]{32}", INDEXNOW_ANAHTARI)
    dosya = STATIK / f"{INDEXNOW_ANAHTARI}.txt"
    assert dosya.read_text(encoding="utf-8").strip() == INDEXNOW_ANAHTARI
    govde = istek_govdesi(["https://kamuuygulama.me/x/"])
    assert govde == {
        "host": "kamuuygulama.me",
        "key": INDEXNOW_ANAHTARI,
        "keyLocation": f"https://kamuuygulama.me/{INDEXNOW_ANAHTARI}.txt",
        "urlList": ["https://kamuuygulama.me/x/"],
    }


def test_sitemap_okuma_ve_manifest(tmp_path):
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    cikti = tmp_path / "_site"
    yaz(derleme, cikti)
    harita = sitemap_oku((cikti / "sitemap.xml").read_text(encoding="utf-8"))
    assert harita == json.loads((cikti / ".indexnow.json").read_text(encoding="utf-8"))
    assert (cikti / f"{INDEXNOW_ANAHTARI}.txt").exists()
    assert (cikti / "robots.txt").read_bytes() == robots_txt().encode("utf-8")  # LF, birebir
    assert json.loads(sitemap_manifesti(derleme.sitemap)) == harita


def test_merkez_lastmod_kume_degismedikce_sabit_degisince_ilerler():
    sabah = SIMDI
    aksam = SIMDI + timedelta(hours=8)  # aynı gün, aynı ilan kümesi
    iki = [satir(), satir(id=kimlik(442))]
    a = dict(derle(iki, sabah, en_az_acik=1).sitemap)
    b = dict(derle(iki, aksam, en_az_acik=1).sitemap)
    assert a["/"] == b["/"] and a["/sozlesmeli-personel-alimlari/"] == b["/sozlesmeli-personel-alimlari/"]
    # Bir ilanın süresi dolunca küme değişir: lastmod bitişin ertesi günü olur.
    biten = satir(id=kimlik(440), basvuru_bitis="2026-10-07")
    c = dict(derle([satir(), satir(id=kimlik(441)), biten], SIMDI, en_az_acik=1).sitemap)
    assert c["/"].isoformat().startswith("2026-10-08T00:00:00+03:00")


def test_kume_zamani_gelecegi_gecmez():
    gelecek = Ilan.from_satir(satir(eklenme_tarihi="2026-12-01T00:00:00+00:00"))
    assert kume_zamani([gelecek], [], SIMDI) == SIMDI
    assert kume_zamani([], [], SIMDI) == SIMDI
    assert isinstance(kume_zamani([Ilan.from_satir(satir())], [], SIMDI), datetime)
    assert SIMDI.tzinfo == timezone.utc
