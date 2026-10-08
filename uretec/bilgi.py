"""Güven sayfaları: hakkında, nasıl çalışır, iletişim, gizlilik.

İçerik elle yazılmıştır; yalnızca gerçek ve doğrulanabilir bilgi içerir.
"""

from dataclasses import dataclass
from datetime import date

from .sablon import SayfaBasi, e, kirinti, magaza_butonlari, ust_etiket

ILETISIM_EPOSTA = "selmangurbuzer@gmail.com"
UYGULAMA_GIZLILIK = "https://selmangrbzr.github.io/memur-ilanlari/privacy-policy.html"
INSTAGRAM = "https://www.instagram.com/kamu.uygulama/"
# İçerik elle değiştirildiğinde güncellenir (sitemap lastmod).
BILGI_GUNCELLEME = date(2026, 10, 8)
_EPOSTA_LINK = f'<a href="mailto:{ILETISIM_EPOSTA}">{ILETISIM_EPOSTA}</a>'


@dataclass(frozen=True)
class BilgiSayfasi:
    yol: str
    ad: str
    baslik: str
    aciklama: str
    etiket: str
    h1: str
    govde: str


def _paragraflar(*metinler: str) -> str:
    return "".join(f"<p>{m}</p>" for m in metinler)


BILGI_SAYFALARI: tuple[BilgiSayfasi, ...] = (
    BilgiSayfasi(
        yol="/hakkinda/",
        ad="Hakkında",
        baslik="Kamu Hakkında: Bağımsız Kamu İlanları Uygulaması | Kamu",
        aciklama=(
            "Kamu, kamu personel alım ilanlarını tek yerde toplayan ve yeni ilanda "
            "bildirim gönderen bağımsız bir mobil uygulamadır. Resmî kurum değildir."
        ),
        etiket="HAKKINDA",
        h1="Kamu hakkında",
        govde=(
            '<p class="giris">Kamu, Türkiye\'deki kamu personel alım ilanlarını tek yerde '
            "toplayan ve yeni ilan çıktığında telefona bildirim gönderen bağımsız bir "
            "mobil uygulamadır. Bu site, uygulamadaki ilanların herkese açık "
            "sayfalarıdır.</p>"
            "<h2>Resmî kurum değiliz</h2>"
            + _paragraflar(
                "Kamu herhangi bir bakanlık, kurum ya da Cumhurbaşkanlığı birimiyle "
                "bağlantılı değildir ve onlar adına konuşmaz. Başvuruları biz almayız; "
                "her ilanın başvurusu ilanı veren kurumun belirttiği yerden yapılır.",
                "İlanların kaynağı, kamu kurumlarının personel alım ilanlarını yayımladığı "
                "kamuilan.sbb.gov.tr adresidir. Her ilan sayfasında resmî ilan metnine "
                "giden link bulunur.",
            )
            + "<h2>Ne yaparız?</h2>"
            + "<ul class=\"madde\">"
            "<li>İlanları günde dört kez kontrol eder, yenilerini ekleriz.</li>"
            "<li>Kadro sayısı, eğitim şartı, KPSS puan türü ve tarihleri sade bir sayfada gösteririz.</li>"
            "<li>Uygulamada, seçtiğin ilan türü, eğitim ve şehir için bildirim göndeririz.</li>"
            "<li>İptal ve düzeltme duyurularını ilan listesine almayız.</li>"
            "</ul>"
            + "<h2>Ne yapmayız?</h2>"
            + _paragraflar(
                "Taban puan tahmini yapmayız, \"bu puanla girersin\" demeyiz. İlan "
                "bilgileri otomatik çıkarıldığı için hata içerebilir; başvurmadan önce "
                "resmî ilanı mutlaka oku. Ayrıntılar için "
                '<a href="/nasil-calisir/">nasıl çalışır</a> sayfasına bak.'
            )
            + "<h2>Uygulama</h2>"
            + _paragraflar("Kamu ücretsizdir. Android ve iPhone için indirilebilir.")
            + magaza_butonlari("site")
        ),
    ),
    BilgiSayfasi(
        yol="/nasil-calisir/",
        ad="Nasıl çalışır?",
        baslik="Kamu Nasıl Çalışır? İlanların Kaynağı ve Güncelleme | Kamu",
        aciklama=(
            "Kamu'daki ilanlar kamuilan.sbb.gov.tr'den günde dört kez alınır, "
            "bilgiler yapay zekâyla çıkarılır. Hata payı ve hata bildirimi."
        ),
        etiket="NASIL ÇALIŞIR",
        h1="İlanlar nasıl hazırlanıyor?",
        govde=(
            '<p class="giris">Bu sitedeki ve uygulamadaki her ilan, resmî bir kaynaktan '
            "otomatik olarak alınır ve sadeleştirilir. Süreç dört adımdan oluşur.</p>"
            "<h2>1. Kaynak</h2>"
            + _paragraflar(
                "İlanlar, kamu kurumlarının personel alım ilanlarını yayımladığı "
                "kamuilan.sbb.gov.tr adresinden alınır. Kurumun kendi sitesinde olup "
                "bu adreste yayımlanmayan ilanlar listede yer almayabilir."
            )
            + "<h2>2. Güncelleme</h2>"
            + _paragraflar(
                "Kaynak günde dört kez kontrol edilir, yeni ilanlar eklenir ve site "
                "yeniden oluşturulur. Bu yüzden yeni bir ilanın burada görünmesi birkaç "
                "saat sürebilir. Her sayfanın altında son güncelleme zamanı yazar."
            )
            + "<h2>3. Bilgilerin çıkarılması</h2>"
            + _paragraflar(
                "İlan metninden kadro sayısı, eğitim seviyesi, KPSS ve ALES puan türü, "
                "yaş sınırı, görev yeri, başvuru tarihleri, başvuru yeri ve belgeler bir "
                "yapay zekâ modeliyle otomatik olarak çıkarılır. İlan başlığı ve kurum "
                "adı kaynaktan olduğu gibi alınır.",
                "Otomatik çıkarım hata yapabilir: bir tarih, puan türü ya da kadro "
                "sayısı yanlış okunmuş olabilir. Başlıktaki kadro sayısı ile kadro "
                "dağılımı uyuşmadığında adetleri göstermeyiz ve resmî ilana yönlendiririz.",
            )
            + "<h2>4. Eleme</h2>"
            + _paragraflar(
                "İptal ve düzeltme duyuruları ayrı ilan olarak gösterilmez. Son başvuru "
                "tarihi geçen ilanların sayfası 60 gün daha \"başvuru süresi doldu\" "
                "notuyla kalır, sonra kaldırılır."
            )
            + "<h2>Hata gördüysen</h2>"
            + _paragraflar(
                f"Yanlış bir bilgi gördüysen ilan sayfasının adresiyle birlikte {_EPOSTA_LINK} "
                "adresine yazabilirsin. Başvurmadan önce her zaman resmî ilan metnini oku; "
                "bağlayıcı olan resmî ilandır."
            )
        ),
    ),
    BilgiSayfasi(
        yol="/iletisim/",
        ad="İletişim",
        baslik="İletişim: Kamu Uygulaması | Kamu",
        aciklama="Kamu uygulaması ve kamuuygulama.me ile ilgili soru, öneri ve hata bildirimleri için iletişim.",
        etiket="İLETİŞİM",
        h1="İletişim",
        govde=(
            '<p class="giris">Soru, öneri ve hata bildirimleri için e-posta gönderebilirsin.</p>'
            '<dl class="bilgi">'
            f"<div><dt>E-posta</dt><dd>{_EPOSTA_LINK}</dd></div>"
            f'<div><dt>Instagram</dt><dd><a href="{INSTAGRAM}" rel="noopener">@kamu.uygulama</a></dd></div>'
            "</dl>"
            "<h2>Hata bildirirken</h2>"
            + _paragraflar(
                "İlan sayfasının adresini ve hangi bilginin yanlış olduğunu yaz. "
                "Mümkünse resmî ilandaki doğru bilgiyi de ekle.",
                "İlanlara başvuru, sınav sonucu ya da atama gibi konularda bilgi "
                "veremeyiz; bunlar için ilanı veren kurumla iletişime geç.",
            )
        ),
    ),
    BilgiSayfasi(
        yol="/gizlilik/",
        ad="Gizlilik",
        baslik="Gizlilik: Çerez ve Veri Kullanımı | Kamu",
        aciklama="kamuuygulama.me çerez ya da analiz aracı kullanmaz. Uygulamanın gizlilik politikası ve barındırma bilgisi.",
        etiket="GİZLİLİK",
        h1="Gizlilik",
        govde=(
            '<p class="giris">Bu site çerez, reklam ya da analiz aracı kullanmaz ve '
            "senden hiçbir bilgi istemez.</p>"
            "<h2>Site</h2>"
            + _paragraflar(
                "Sayfalar statik dosyalardır; giriş, form ya da takip kodu yoktur. "
                "Yazı tipleri de bu sitenin kendi sunucusundan yüklenir, üçüncü taraf "
                "bir hizmete istek gönderilmez.",
                "Site GitHub Pages üzerinde barındırılır. GitHub, hizmetin güvenliği ve "
                "işletimi için ziyaretçilerin IP adresi gibi teknik kayıtları tutabilir; "
                "bu kayıtlar GitHub'ın kendi gizlilik bildirimine tabidir.",
                "Mağaza butonları Apple App Store ve Google Play'e gider. Bu bağlantılar "
                "hangi kanaldan gelindiğini mağazaya bildiren bir kampanya etiketi içerir; "
                "kişisel bilgi içermez.",
            )
            + "<h2>Uygulama</h2>"
            + _paragraflar(
                "Kamu mobil uygulamasının topladığı veriler ve kullanım amaçları "
                f'<a href="{UYGULAMA_GIZLILIK}" rel="noopener">uygulama gizlilik politikasında</a> '
                "anlatılır.",
                f"Sorular için: {_EPOSTA_LINK}",
            )
        ),
    ),
)


def bilgi_sayfasi_parcalari(sayfa: BilgiSayfasi) -> tuple[SayfaBasi, str, list[tuple[str, str]]]:
    kirinti_ogeleri = [("Ana sayfa", "/"), (sayfa.ad, sayfa.yol)]
    govde = (
        f"{kirinti(kirinti_ogeleri)}{ust_etiket(sayfa.etiket)}"
        f'<h1>{e(sayfa.h1)}</h1><div class="metin">{sayfa.govde}</div>'
    )
    bas = SayfaBasi(
        baslik=sayfa.baslik,
        aciklama=sayfa.aciklama,
        yol=sayfa.yol,
        bolum=sayfa.etiket,
        kampanya="site",
    )
    return bas, govde, kirinti_ogeleri
