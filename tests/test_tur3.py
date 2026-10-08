"""Üçüncü tur: editoryal tasarım ve yapay zekâ ayak izi metin düzeltmeleri."""

import html as html_lib
import re
from pathlib import Path

from test_tur2 import baslik, kimlik
from test_uretec import SIMDI, satir

from uretec.derle import derle
from uretec.model import Ilan

STATIK = Path(__file__).resolve().parent.parent / "uretec" / "statik"
_RESMI_HITAP = re.compile(r"\b(edin|bakın|ediniz|bakınız|ulaşabilirsiniz)\b|\w+(ınız|iniz|unuz|ünüz)\b", re.I)
_DIR_EKI = re.compile(r"\b\w{3,}(dır|dir|dur|dür|tır|tir|tur|tür)\b")


def gorunen_metin(sayfa: str) -> str:
    govde = re.sub(r"<script.*?</script>|<style.*?</style>|<head>.*?</head>", " ", sayfa, flags=re.S)
    return html_lib.unescape(re.sub(r"<[^>]+>", " ", govde))


def karisik_veri() -> list[dict]:
    """Farklı şehir, kurum, tür ve eğitimde açık ve kapanmış ilanlar."""
    return [
        satir(),
        satir(id=kimlik(101), kurum="ANKARA ÜNİVERSİTESİ", pozisyon="12 ÖĞRETİM ÜYESİ ALACAK",
              kisi_sayisi=12, ilan_turu="Akademik Personel", sehirler=["Ankara"], kpss_puan_turu=None,
              egitim_seviyesi="Doktora", basvuru_yeri="Rektörlük; şahsen veya posta ile"),
        satir(id=kimlik(102), kurum="ANKARA ÜNİVERSİTESİ", pozisyon="3 ÖĞRETİM ELEMANI ALACAK",
              kisi_sayisi=3, ilan_turu="Akademik Personel", sehirler=["Ankara"], kpss_puan_turu=None,
              egitim_seviyesi="Yüksek Lisans", basvuru_yeri="Şahsen başvuru"),
        satir(id=kimlik(103), kurum="SAĞLIK BAKANLIĞI", pozisyon="40 SÖZLEŞMELİ PERSONEL ALACAK",
              kisi_sayisi=40, ilan_turu="Sözleşmeli Personel", sehirler=["Ankara"],
              egitim_seviyesi="Lise", kpss_puan_turu="P94"),
        satir(id=kimlik(104), kurum="ÇANKAYA BELEDİYE BAŞKANLIĞI", pozisyon="2 MEMUR ALACAK",
              kisi_sayisi=2, ilan_turu="Memur", sehirler=["Ankara"], egitim_seviyesi="Lisans"),
        satir(id=kimlik(105), kurum="İZMİR BÜYÜKŞEHİR BELEDİYE BAŞKANLIĞI", pozisyon="25 İTFAİYE ERİ ALACAK",
              kisi_sayisi=25, ilan_turu="Memur", sehirler=["İzmir"], egitim_seviyesi="Lise",
              eklenme_tarihi="2026-09-20T10:00:00+00:00"),
        satir(id=kimlik(106), kurum="EGE ÜNİVERSİTESİ", pozisyon="4 ÖĞRETİM ÜYESİ ALACAK",
              kisi_sayisi=4, ilan_turu="Akademik Personel", sehirler=["İzmir"], kpss_puan_turu=None,
              egitim_seviyesi="Doktora", eklenme_tarihi="2026-09-25T10:00:00+00:00"),
        satir(id=kimlik(107), kurum="EGE ÜNİVERSİTESİ", pozisyon="7 SÖZLEŞMELİ PERSONEL ALACAK",
              kisi_sayisi=7, ilan_turu="Sözleşmeli Personel", sehirler=["İzmir"],
              egitim_seviyesi="Ön Lisans", kpss_puan_turu="P93", eklenme_tarihi="2026-09-26T10:00:00+00:00"),
        satir(id=kimlik(108), kurum="EGE ÜNİVERSİTESİ", pozisyon="2 ÖĞRETİM ÜYESİ ALACAK",
              kisi_sayisi=2, ilan_turu="Akademik Personel", sehirler=["İzmir"], basvuru_bitis="2026-09-20"),
    ]


def ozet_metni(sayfa: str) -> str:
    bulunan = re.search(r'<p class="ozet-cumleler">(.*?)</p>', sayfa, re.S)
    return gorunen_metin(bulunan.group(1)) if bulunan else ""


# --- Tasarım -------------------------------------------------------------------

def test_buyuk_harfli_etiket_kalmadi():
    css = (STATIK / "kamu.css").read_text(encoding="utf-8")
    assert "uppercase" not in css
    derleme = derle(karisik_veri(), SIMDI, en_az_acik=1)
    for yol, sayfa in derleme.sayfalar.items():
        assert 'class="ust-etiket"' not in sayfa, yol
        assert not re.search(r"\b(İLANI|EKLENDİ|İLAN TÜRÜ|EĞİTİM|ŞEHİR|KURUM)\b", gorunen_metin(sayfa)), yol
    assert '<span class="kunye-sag"><b>8 Ekim 2026</b>' in derleme.sayfalar["/"]


def test_uygulamada_ac_ifadesi_kalkti_magaza_etiketleri_tek():
    for sayfa in derle(karisik_veri(), SIMDI, en_az_acik=1).sayfalar.values():
        assert "Uygulamada aç" not in sayfa
        assert "Google Play'den indir" not in sayfa and "App Store'dan indir" not in sayfa


def test_kolofon_cift_cizgi_ve_tek_dipnot():
    sayfa = derle([satir()], SIMDI, en_az_acik=1).sayfalar["/"]
    kolofon = sayfa[sayfa.index('<footer class="kolofon">'):]
    assert '<div class="cift-cizgi">' in kolofon
    assert kolofon.count('class="dipnot"') == 1
    assert "Kamu hakkında" in kolofon and ">Uygulama<" in kolofon


# --- Metin: hitap ve ekler -------------------------------------------------------

def test_siz_hitabi_ve_inizli_ekler_yok():
    for yol, sayfa in derle(karisik_veri(), SIMDI, en_az_acik=1).sayfalar.items():
        bulunan = _RESMI_HITAP.search(gorunen_metin(sayfa))
        assert bulunan is None, (yol, bulunan and bulunan.group(0))
        assert "kontrol edin" not in sayfa  # JSON-LD dahil


def test_bilgi_sayfalarinda_dir_eki_yok():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    for yol in ("/hakkinda/", "/nasil-calisir/", "/iletisim/", "/gizlilik/", "/"):
        bulunan = _DIR_EKI.findall(gorunen_metin(derleme.sayfalar[yol]))
        assert bulunan == [], (yol, bulunan)


# --- İlan sayfası metinleri ---------------------------------------------------------

def test_ozel_sartlar_madde_listesi_ve_buyuk_esit_isareti_yok():
    sartli = satir(ozel_sartlar="DMK 48 şartları;1.1.1991 sonrası doğumlu; KPSS P48 ≥70; mezuniyet/denklik belgesi")
    sayfa = derle([sartli], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(sartli).yol]
    bolum = sayfa[sayfa.index('id="sartlar"'):]
    assert '<ul class="maddeler">' in bolum[:400]
    assert "<li>KPSS P48 en az 70</li>" in sayfa
    assert "<li>1.1.1991 sonrası doğumlu</li>" in sayfa
    assert "≥" not in sayfa


def test_baslikta_adet_ve_alacak_gecmez():
    kaliplar = [
        "5 ADET ÖĞRETİM ELEMANI ALACAK",
        "SÖZLEŞMELİ PERSONEL (MÜHENDİS) ALACAK",
        "3 ADET SÜREKLİ İŞÇİ ALINACAKTIR",
        "SÖZLEŞMELİ PERSONEL ALACAK (TEKNİKER)",
    ]
    satirlar = [satir(id=kimlik(200 + n), pozisyon=p, kisi_sayisi=None) for n, p in enumerate(kaliplar)]
    derleme = derle(satirlar, SIMDI, en_az_acik=1)
    for s in satirlar:
        ilan = Ilan.from_satir(s)
        sayfa = derleme.sayfalar[ilan.yol]
        for metin in (baslik(sayfa), re.search(r"<h1>(.*?)</h1>", sayfa).group(1)):
            assert not re.search(r"\b(Adet|ADET|Alacak|ALACAK|Alınacaktır)\b", metin), metin
    assert Ilan.from_satir(satirlar[1]).is_basligi == "Sözleşmeli Personel (Mühendis)"


def test_ilan_bilgilerinden_tekrarlar_cikti_ve_tarih_araligi_tek_satir():
    sayfa = derle([satir()], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(satir()).yol]
    bilgi = sayfa[sayfa.index('id="bilgi"'):sayfa.index('class="dipnot-kutu"')]
    for cikan in ("<dt>Kurum</dt>", "<dt>İlan başlığı</dt>", "<dt>Kadro sayısı</dt>",
                  "<dt>Son başvuru</dt>", "<dt>Kalan süre</dt>"):
        assert cikan not in bilgi
    assert "<dt>Başvuru tarihleri</dt><dd>1 Ekim-2 Kasım 2026</dd>" in bilgi


def test_basvuru_yerinde_uzun_tire_virgul_olur_nitelik_cumle_duzeni():
    ilan_satiri = satir(
        basvuru_yeri="https://www.siirt.edu.tr — ilgili birimlere şahsen",
        kontenjan=[{"pozisyon": "Profesör", "toplam": 15,
                    "nitelik": "Doçentliğini Felsefe Bilim Alanında Almış Olmak"}],
    )
    sayfa = derle([ilan_satiri], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(ilan_satiri).yol]
    assert "https://www.siirt.edu.tr, ilgili birimlere şahsen" in sayfa
    assert "—" not in gorunen_metin(sayfa)
    assert "Doçentliğini felsefe bilim alanında almış olmak" in sayfa


def test_ilan_cagri_kutusu_tam_tur_adi_ve_tarih_eki():
    akademik = satir(id=kimlik(301), ilan_turu="Akademik Personel", basvuru_bitis="2026-10-22")
    sayfa = derle([akademik], SIMDI, en_az_acik=1).sayfalar[Ilan.from_satir(akademik).yol]
    assert "22 Ekim&#x27;i kaçırma" in sayfa or "22 Ekim'i kaçırma" in sayfa
    assert "Yeni akademik personel ilanı çıktığında ve son güne az kaldığında" in sayfa


# --- Merkezler ------------------------------------------------------------------------

def test_yeni_merkez_basliklari():
    derleme = derle([satir()], SIMDI, en_az_acik=1)
    assert baslik(derleme.sayfalar["/kpss-siz-kamu-ilanlari/"]) == "KPSS Şartı Belirtilmeyen Kamu İlanları 2026 | Kamu"
    assert "Ortaöğretim Puanıyla" in baslik(derleme.sayfalar["/kpss-p94-ilanlari/"])
    assert "Ön Lisans Puanıyla" in baslik(derleme.sayfalar["/kpss-p93-ilanlari/"])
    assert "Önümüzdeki 7 Günde Bitenler" in baslik(derleme.sayfalar["/son-basvurusu-yaklasan-ilanlar/"])
    yaklasan = gorunen_metin(derleme.sayfalar["/son-basvurusu-yaklasan-ilanlar/"])
    assert "çoğu ilanda" not in yaklasan and "son güne bırakma" in yaklasan


def test_merkez_meta_aciklamasi_ozet_verisinden():
    sayfa = derle(karisik_veri(), SIMDI, en_az_acik=1).sayfalar["/memur-alimlari/"]
    aciklama = re.search(r'<meta name="description" content="([^"]+)"', sayfa).group(1)
    assert aciklama.startswith("Memur alımları: 2 açık ilan, toplam 27 kadro. En yakın son başvuru")


def test_tek_kurumlu_merkezde_hepsi_cumlesi_ve_kucuk_alimda_buyuk_cumlesi_yok():
    sayfa = derle([satir()], SIMDI, en_az_acik=1).sayfalar["/sozlesmeli-personel-alimlari/"]
    ozet = ozet_metni(sayfa)
    assert "Buradaki ilanların hepsi Bankacılık Düzenleme ve Denetleme Kurumu Başkanlığı'ndan." in ozet
    assert "En çok kadro" not in ozet
    assert "En yakın son başvuru 2 Kasım'da" in ozet


def test_sehir_ve_kurum_ozetleri_sayfalar_arasinda_birebir_ayni_degil():
    derleme = derle(karisik_veri(), SIMDI, en_az_acik=1)
    yollar = ["/sehir/ankara/", "/sehir/izmir/", "/sehir/istanbul/",
              "/kurum/ankara-universitesi/", "/kurum/ege-universitesi/", "/kurum/saglik-bakanligi/",
              "/kurum/bankacilik-duzenleme-ve-denetleme-kurumu/"]
    ozetler = {yol: ozet_metni(derleme.sayfalar[yol]) for yol in yollar}
    assert all(ozetler.values()), ozetler
    assert len(set(ozetler.values())) == len(yollar)
    # Cümleler veriye bağlı: şehirde tür dağılımı ve lise sayısı, kurumda geçmiş ilan sayısı.
    assert "Açık ilanlar: 2 akademik, 1 sözleşmeli, 1 memur." in ozetler["/sehir/ankara/"]
    assert "Lise mezunlarına açık 1 ilan var." in ozetler["/sehir/ankara/"]
    assert "Son 60 günde 1 ilanın başvurusu kapandı." in ozetler["/sehir/izmir/"]
    assert "Son 60 günde 3 ilan verdi" in ozetler["/kurum/ege-universitesi/"]
    assert "şahsen ya da posta" in ozetler["/kurum/ankara-universitesi/"]


def test_ilan_sayfasinda_kurumun_diger_ilanlari_linki():
    derleme = derle(karisik_veri(), SIMDI, en_az_acik=1)
    sayfa = derleme.sayfalar[Ilan.from_satir(karisik_veri()[1]).yol]
    assert '<a href="/kurum/ankara-universitesi/">Bu kurumun diğer açık ilanları</a>' in sayfa
    assert '<a class="ilan-kurum" href="/kurum/ankara-universitesi/">' in sayfa


def test_ucuncu_turda_seo_kazanimlari_korunur():
    derleme = derle(karisik_veri(), SIMDI, en_az_acik=1)
    basliklar = [baslik(s) for y, s in derleme.sayfalar.items() if y != "/404.html"]
    assert len(basliklar) == len(set(basliklar))
    for yol, _ in derleme.sitemap:
        assert 'content="index,follow' in derleme.sayfalar[yol]
    assert "JobPosting" in derleme.sayfalar[Ilan.from_satir(satir()).yol]


def test_kurum_kisaltmalari_korunur_kelimeler_baslik_duzenine_gecer():
    from uretec.metin import kurum_basligi

    assert kurum_basligi("TÜRK PATENT VE MARKA KURUMU") == "Türk Patent ve Marka Kurumu"
    assert kurum_basligi("VAN BÜYÜKŞEHİR BELEDİYE BAŞKANLIĞI") == "Van Büyükşehir Belediye Başkanlığı"
    assert kurum_basligi("TCDD TAŞIMACILIK A.Ş.") .startswith("TCDD ")
    assert kurum_basligi("MEB") == "MEB" and kurum_basligi("SGK") == "SGK"
