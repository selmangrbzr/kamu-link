"""uretec için birim ve derleme testleri (ağ gerektirmez)."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from uretec.derle import DerlemeHatasi, derle, robots_txt, sitemap_xml, yaz
from uretec.jsonld import is_ilani, script_etiketi
from uretec.metin import ascii_slug, iptal_veya_duzeltme_mi
from uretec.model import Ilan, yayinlanabilir_mi

SIMDI = datetime(2026, 10, 8, 9, 0, tzinfo=timezone.utc)  # TR: 8 Ekim 12:00


def satir(**alanlar):
    temel = {
        "id": "0b4b97d5b926ef4505879502779dafb8",
        "kurum": "BANKACILIK DÜZENLEME VE DENETLEME KURUMU BAŞKANLIĞI",
        "pozisyon": "15 SÖZLEŞMELİ BİLİŞİM PERSONELİ ALACAK",
        "ilan_turu": "Sözleşmeli Personel",
        "kisi_sayisi": 15,
        "kontenjan": [{"pozisyon": "Sistem Uzmanı", "toplam": 15}],
        "basvuru_baslangic": "2026-10-01",
        "basvuru_bitis": "2026-11-02",
        "eklenme_tarihi": "2026-10-03T12:26:41.344173+00:00",
        "egitim_seviyesi": "Lisans",
        "kpss_puan_turu": "P3",
        "ales_puan_turu": None,
        "ales_min_puan": None,
        "yas_siniri": None,
        "cinsiyet": None,
        "sehir": "İstanbul",
        "sehirler": ["İstanbul"],
        "basvuru_yeri": "e-Devlet üzerinden Kariyer Kapısı",
        "basvuru_belgeleri": None,
        "ozel_sartlar": "En az iki programlama dilini bilmek.",
        "pdf_url": "https://ornek.supabase.co/storage/v1/object/public/ilanlar-pdf/x.pdf",
        "detay_link": "https://kamuilan.sbb.gov.tr/ilanDetay.aspx?kod=abc",
        "enrichment_durum": "islendi",
    }
    temel.update(alanlar)
    return temel


def jsonld_listesi(html: str) -> list[dict]:
    return [
        json.loads(m)
        for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html)
    ]


# --- Slug -------------------------------------------------------------------

def test_ascii_slug_turkce_harfleri_cevirir():
    assert ascii_slug("Ağrı İbrahim Çeçen Üniversitesi Şube") == "agri-ibrahim-cecen-universitesi-sube"
    assert ascii_slug("Hakkâri / IĞDIR") == "hakkari-igdir"


def test_slug_kurum_pozisyon_ve_id_on_ekinden_olusur():
    ilan = Ilan.from_satir(satir())
    assert ilan.slug == (
        "bankacilik-duzenleme-ve-denetleme-kurumu-baskanligi-sozlesmeli-bilisim-0b4b97d5"
    )
    assert re.fullmatch(r"[a-z0-9-]+", ilan.slug)


def test_slug_zenginlestirmeyle_degismez():
    once = Ilan.from_satir(satir(kisi_sayisi=None, egitim_seviyesi=None))
    sonra = Ilan.from_satir(satir(kisi_sayisi=15, egitim_seviyesi="Lisans"))
    assert once.slug == sonra.slug


def test_slug_uzun_basliklarda_sinirli_kalir():
    ilan = Ilan.from_satir(satir(kurum="ÇOK " * 60, pozisyon="UZUN " * 60))
    assert len(ilan.slug) <= 72 + 9
    assert ilan.slug.endswith("-0b4b97d5")


def test_slug_cakismasinda_sonraki_ilan_uzun_id_alir():
    a = satir()
    b = satir(id="0b4b97d5ffffffffffffffffffffffff", eklenme_tarihi="2026-10-05T10:00:00+00:00")
    yollar = set(derle([b, a], SIMDI, en_az_acik=1).sayfalar)
    assert Ilan.from_satir(a).yol in yollar  # ilk eklenen kısa slug'ını korur
    assert "/ilan/bankacilik-duzenleme-ve-denetleme-kurumu-baskanligi-sozlesmeli-bilisim-0b4b97d5ffffffff/" in yollar


@pytest.mark.parametrize("kotu_id", ["../../../etc", "0b4b97d5/../../x", "abc", "ZZZZZZZZZZZZZZZZZZ"])
def test_gecersiz_id_satiri_atlanir(kotu_id):
    derleme = derle([satir(), satir(id=kotu_id)], SIMDI, en_az_acik=1)
    assert all(".." not in yol for yol in derleme.sayfalar)
    assert derleme.acik == 1


# --- İptal / düzeltme -------------------------------------------------------

@pytest.mark.parametrize(
    "pozisyon",
    ["DÜZELTME İLANI", "SÖZLEŞMELİ MÜHENDİS ALIMI İPTALİ", "IPTAL ILANI", "1 ÖĞRETİM ÜYESİ DUZELTME"],
)
def test_iptal_ve_duzeltme_ilanlari_elenir(pozisyon):
    assert iptal_veya_duzeltme_mi(pozisyon)
    assert not yayinlanabilir_mi(Ilan.from_satir(satir(pozisyon=pozisyon)))


def test_zenginlestirmesi_bitmemis_ilan_elenir():
    assert not yayinlanabilir_mi(Ilan.from_satir(satir(enrichment_durum="bekliyor")))


def test_iptal_ilaninin_sayfasi_uretilmez():
    derleme = derle([satir(), satir(id="ffff0000aaaaffff0000aaaaffff0000", pozisyon="İPTAL İLANI")], SIMDI, en_az_acik=1)
    assert not any("ffff0000" in yol for yol in derleme.sayfalar)


# --- JobPosting -------------------------------------------------------------

def test_jobposting_zorunlu_alanlar_ve_tarih_bicimleri():
    veri = is_ilani(Ilan.from_satir(satir()))
    for alan in ("title", "description", "datePosted", "validThrough", "hiringOrganization", "jobLocation"):
        assert veri[alan]
    assert veri["@type"] == "JobPosting"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", veri["datePosted"])
    assert veri["datePosted"] == "2026-10-01"  # başvuru başlangıcı eklenmeden önce
    assert veri["validThrough"] == "2026-11-02T23:59:59+03:00"
    datetime.fromisoformat(veri["validThrough"])
    assert veri["hiringOrganization"]["name"] == "Bankacılık Düzenleme ve Denetleme Kurumu Başkanlığı"
    assert veri["jobLocation"][0]["address"] == {
        "@type": "PostalAddress", "addressRegion": "İstanbul", "addressCountry": "TR",
    }
    assert veri["directApply"] is False
    assert veri["totalJobOpenings"] == 15
    assert veri["employmentType"] == "FULL_TIME"
    assert veri["title"] == "Sözleşmeli Bilişim Personeli"


def test_jobposting_bilinmeyen_alanlari_eklemez():
    veri = is_ilani(Ilan.from_satir(satir(
        kisi_sayisi=None, sehirler=[], sehir=None, egitim_seviyesi=None,
        ilan_turu="İşçi", pozisyon="TEMİZLİK PERSONELİ ALACAK",
    )))
    assert "totalJobOpenings" not in veri
    assert "educationRequirements" not in veri
    assert "employmentType" not in veri
    assert "baseSalary" not in veri
    assert veri["jobLocation"] == [
        {"@type": "Place", "address": {"@type": "PostalAddress", "addressCountry": "TR"}}
    ]


def test_jsonld_script_kapanis_etiketini_kacirir():
    etiket = script_etiketi({"x": "</script><b>"})
    assert "</script><b>" not in etiket.removesuffix("</script>")
    assert json.loads(re.search(r">(.*)</script>$", etiket).group(1)) == {"x": "</script><b>"}


def test_acik_ilan_sayfasi_indekslenir_ve_jobposting_icerir():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    html = derleme.sayfalar[Ilan.from_satir(satir()).yol]
    assert 'content="index,follow' in html
    assert any(v["@type"] == "JobPosting" for v in jsonld_listesi(html))
    assert '<link rel="canonical" href="https://kamuuygulama.me/ilan/' in html
    assert "otomatik çıkarıyoruz" in html
    assert "ct=seo" in html and "utm_campaign%3Dseo" in html
    assert 'href="https://kamuilan.sbb.gov.tr/ilanDetay.aspx?kod=abc"' in html


def test_bos_alanlar_sayfada_gorunmez():
    html = derle([satir(yas_siniri=None, ales_puan_turu=None)], SIMDI, en_az_acik=1).sayfalar[
        Ilan.from_satir(satir()).yol
    ]
    assert "Yaş sınırı" not in html
    assert "ALES" not in html
    assert "None" not in html


def test_javascript_ve_yabanci_sunucu_linki_yazilmaz():
    ilan = Ilan.from_satir(satir(pdf_url="javascript:alert(1)", detay_link="http://x"))
    assert ilan.pdf_url is None and ilan.detay_link is None
    yabanci = Ilan.from_satir(satir(
        pdf_url="https://kotu.example.com/a.pdf",
        detay_link="https://kamuilan.sbb.gov.tr.kotu.example/ilan",
    ))
    assert yabanci.pdf_url is None and yabanci.detay_link is None


def test_basvurusu_baslamamis_ilanda_jobposting_yok_ama_indekslenir():
    ileride = satir(basvuru_baslangic="2026-10-19")
    html = derle([ileride], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(ileride).yol]
    assert 'content="index,follow' in html
    assert not any(v["@type"] == "JobPosting" for v in jsonld_listesi(html))


def test_eklenme_gunu_turkiye_saatine_gore():
    gece = Ilan.from_satir(satir(eklenme_tarihi="2026-10-07T22:30:00+00:00"))  # TR 8 Ekim 01:30
    assert gece.eklenme_gunu.isoformat() == "2026-10-08"
    html = derle([satir(eklenme_tarihi="2026-10-07T22:30:00+00:00")], SIMDI, en_az_acik=1).sayfalar[gece.yol]
    assert "8 Ekim'de eklendi" in html


def test_kontenjan_sehri_gosterilir_ve_aciklamada_tekrar_yok():
    kontenjan = [{"pozisyon": "Gelir Uzman Yardımcısı", "sehir": il, "toplam": 5} for il in ("Adana", "Van", "Muş")]
    ilan_satiri = satir(kisi_sayisi=15, kontenjan=kontenjan)
    html = derle([ilan_satiri], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(ilan_satiri).yol]
    assert '<li><span>Van</span><b>5</b></li>' in html
    aciklama = is_ilani(Ilan.from_satir(ilan_satiri))["description"]
    assert aciklama.count("Gelir Uzman Yardımcısı") == 1


# --- Süresi geçmiş ilanlar ---------------------------------------------------

def test_suresi_gecmis_ilan_noindex_ve_jobposting_yok():
    gecmis = satir(id="aaaa1111bbbbaaaa1111bbbbaaaa1111", basvuru_bitis="2026-09-20")
    derleme = derle([satir(), gecmis], SIMDI, en_az_acik=1)
    yol = Ilan.from_satir(gecmis).yol
    html = derleme.sayfalar[yol]
    assert 'content="noindex,follow"' in html
    assert "Başvuru süresi doldu" in html
    assert not any(v["@type"] == "JobPosting" for v in jsonld_listesi(html))
    assert yol not in {y for y, _ in derleme.sitemap}


def test_60_gunden_eski_ilan_icin_sayfa_uretilmez():
    eski = satir(id="cccc2222ddddcccc2222ddddcccc2222", basvuru_bitis="2026-08-01")
    derleme = derle([satir(), eski], SIMDI, en_az_acik=1)
    assert Ilan.from_satir(eski).yol not in derleme.sayfalar


def test_son_gun_bugunse_ilan_hala_acik():
    bugun = satir(basvuru_bitis="2026-10-08")
    html = derle([bugun], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(bugun).yol]
    assert "Bugün son gün" in html and "JobPosting" in html


# --- Merkez sayfaları --------------------------------------------------------

def iki_ilan(**alanlar):
    """Aynı özellikte iki açık ilan (merkez indeks eşiği 2)."""
    return [satir(**alanlar), satir(id="1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f", **alanlar)]


def test_sabit_merkez_bosken_de_uretilir_ama_noindex_ve_sitemap_disi():
    derleme = derle([satir()], SIMDI, en_az_acik=1)  # yalnızca sözleşmeli, lisans, P3, İstanbul
    site_haritasi = {y for y, _ in derleme.sitemap}
    for bos in ("/memur-alimlari/", "/isci-alimlari/", "/lise-mezunu-kamu-ilanlari/",
                "/kpss-p94-ilanlari/", "/belediye-personel-alimlari/"):
        html = derleme.sayfalar[bos]
        assert "Şu an açık ilan yok" in html
        assert 'content="noindex,follow"' in html
        assert 'aria-labelledby="diger"' in html  # diğer kategorilere linkler
        assert bos not in site_haritasi
    assert "/sehir/ankara/" not in derleme.sayfalar  # şehirlerde eski davranış


def test_esik_alti_merkez_noindex_esik_ustu_indekslenir():
    tek = derle([satir()], SIMDI, en_az_acik=1)
    assert 'content="noindex,follow"' in tek.sayfalar["/sozlesmeli-personel-alimlari/"]
    iki = derle(iki_ilan(), SIMDI, en_az_acik=1)
    assert 'content="index,follow' in iki.sayfalar["/sozlesmeli-personel-alimlari/"]
    assert "/sozlesmeli-personel-alimlari/" in {y for y, _ in iki.sitemap}


def test_yalnizca_suresi_gecmis_ilani_olan_merkez_kapananlari_gosterir():
    gecmis_memur = satir(id="eeee3333ffffeeee3333ffffeeee3333", ilan_turu="Memur", basvuru_bitis="2026-09-30")
    html = derle([satir(), gecmis_memur], SIMDI, en_az_acik=1).sayfalar["/memur-alimlari/"]
    assert "Şu an açık ilan yok" in html and "Son kapanan ilanlar" in html
    assert 'content="noindex,follow"' in html


def test_az_ilanli_sehir_sayfasi_noindex_ve_sitemap_disi():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    assert 'content="noindex,follow"' in derleme.sayfalar["/sehir/istanbul/"]
    assert "/sehir/istanbul/" not in {y for y, _ in derleme.sitemap}


def test_ulusal_ilan_tek_basina_sehir_sayfasi_dogurmaz():
    iller = ["Ankara", "İzmir", "Bursa", "Konya", "Adana", "Sivas", "Van", "Muş", "Rize", "Kars", "Uşak"]
    derleme = derle([satir(sehirler=iller)], SIMDI, en_az_acik=1)
    assert not any(y.startswith("/sehir/") for y in derleme.sayfalar)


def test_kpss_puan_turu_ayristirma():
    ilan = Ilan.from_satir(satir(kpss_puan_turu="P3, P39, KPSSP93"))
    assert ilan.kpss_turleri == ("P3", "P39", "P93")


# --- Ana sayfa, sitemap, robots, dosyalar -----------------------------------

def test_ana_sayfada_yonlendirme_yok():
    html = derle([satir()], SIMDI, en_az_acik=1).sayfalar["/"]
    assert "<script src" not in html
    assert "location" not in html
    assert 'http-equiv="refresh"' not in html
    assert 'content="index,follow' in html
    assert "Son eklenen ilanlar" in html


def test_sitemap_lastmod_ve_kapsam():
    derleme = derle(iki_ilan(), SIMDI, en_az_acik=1)
    xml = sitemap_xml(derleme.sitemap)
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<loc>https://kamuuygulama.me/</loc>" in xml
    assert "<loc>https://kamuuygulama.me/sozlesmeli-personel-alimlari/</loc>" in xml
    assert xml.count("<url>") == xml.count("<lastmod>")
    assert re.search(r"<lastmod>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00</lastmod>", xml)
    # Merkezlerin lastmod'u derleme zamanıdır.
    zamanlar = dict(derleme.sitemap)
    assert zamanlar["/sozlesmeli-personel-alimlari/"] == SIMDI
    assert zamanlar["/"] == SIMDI
    for yol, _ in derleme.sitemap:
        assert 'content="index,follow' in derleme.sayfalar[yol]


def test_robots_sitemap_satiri():
    assert "Sitemap: https://kamuuygulama.me/sitemap.xml" in robots_txt()


def test_acik_ilan_yoksa_derleme_durur():
    with pytest.raises(DerlemeHatasi):
        derle([satir(basvuru_bitis="2026-09-01")], SIMDI, en_az_acik=1)


def test_yaz_statik_dosyalari_ve_ig_yonlendirmesini_kopyalar(tmp_path: Path):
    cikti = tmp_path / "_site"
    yaz(derle([satir()], SIMDI, en_az_acik=1), cikti)
    for dosya in ("index.html", "404.html", "sitemap.xml", "robots.txt", "kamu.css",
                  "fontlar/pjs-400.woff2", "CNAME", "yonlendir.js", "stil.css",
                  "kamu-icon-512.png", "ig/index.html"):
        assert (cikti / dosya).exists(), dosya
    ig = (cikti / "ig/index.html").read_text(encoding="utf-8")
    assert 'data-k="ig"' in ig and "noindex" in ig
    assert "noindex" in (cikti / "404.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("hedef", [".", "uretec", "uretec/statik", "tests", "ig", "_onizleme", "uretec/statik/_site"])
def test_yaz_kaynak_klasorleri_silmeyi_reddeder(hedef):
    from uretec.derle import KOK
    with pytest.raises(DerlemeHatasi):
        yaz(derle([satir()], SIMDI, en_az_acik=1), KOK / hedef)


def test_varsayilan_en_az_acik_ilan_esigi_eksik_veriyi_durdurur():
    with pytest.raises(DerlemeHatasi, match="en az"):
        derle([satir()], SIMDI)


def test_turuncu_ve_amber_kullanilmaz():
    css = (Path(__file__).resolve().parent.parent / "uretec/statik/kamu.css").read_text(encoding="utf-8").lower()
    for renk in ("#f59e0b", "#ea580c", "orange", "amber", "#f97316", "#fb923c"):
        assert renk not in css


# --- Veri çekme --------------------------------------------------------------

def test_supabase_url_https_olmali():
    from datetime import date

    from uretec.veri import VeriHatasi, ilanlari_cek

    with pytest.raises(VeriHatasi):
        ilanlari_cek("http://ornek.supabase.co", "anahtar", date(2026, 10, 8))


def test_content_range_toplami():
    from uretec.veri import _toplam

    assert _toplam("0-999/1234") == 1234
    assert _toplam("*/0") == 0
    assert _toplam(None) is None
    assert _toplam("0-9/*") is None
