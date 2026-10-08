"""Güven sayfaları: hakkında, nasıl çalışır, iletişim, gizlilik.

İçerik elle yazıldı; yalnızca gerçek ve doğrulanabilir bilgi içerir. Hitap "sen",
"-dır/-dir" ekleri yok. Okuma şablonu: 68ch sütun, bölüm çizgili başlıklar, sonda tek çağrı.
"""

from dataclasses import dataclass
from datetime import date

from .sablon import SayfaBasi, e, kirinti, uygulama_cagrisi

ILETISIM_EPOSTA = "selmangurbuzer@gmail.com"
UYGULAMA_GIZLILIK = "https://selmangrbzr.github.io/memur-ilanlari/privacy-policy.html"
INSTAGRAM = "https://www.instagram.com/kamu.uygulama/"
# İçerik elle değiştirildiğinde güncellenir (sitemap lastmod).
BILGI_GUNCELLEME = date(2026, 10, 8)
KAMPANYA = "site"
_EPOSTA_LINK = f'<a href="mailto:{ILETISIM_EPOSTA}">{ILETISIM_EPOSTA}</a>'


@dataclass(frozen=True)
class BilgiSayfasi:
    yol: str
    ad: str
    baslik: str
    aciklama: str
    h1: str
    govde: str


def _bolum(kimlik: str, baslik: str, *paragraflar: str) -> str:
    icerik = "".join(f"<p>{p}</p>" for p in paragraflar)
    return f'<div class="bolum-bas"><h2 id="{kimlik}">{e(baslik)}</h2></div>{icerik}'


BILGI_SAYFALARI: tuple[BilgiSayfasi, ...] = (
    BilgiSayfasi(
        yol="/hakkinda/",
        ad="Hakkında",
        baslik="Kamu Hakkında: Bağımsız Kamu İlanları Uygulaması | Kamu",
        aciklama=(
            "Kamu, kamu personel alım ilanlarını tek yerde toplayan ve yeni ilanda "
            "bildirim gönderen bağımsız bir mobil uygulama. Resmî kurum değil."
        ),
        h1="Kamu hakkında",
        govde=(
            '<p class="giris">Kamu, Türkiye\'deki kamu personel alım ilanlarını tek yerde '
            "toplayan ve yeni ilan çıktığında telefona bildirim gönderen bağımsız bir "
            "mobil uygulama. Bu site, uygulamadaki ilanların herkese açık sayfaları.</p>"
            + _bolum(
                "resmi", "Resmî kurum değiliz",
                "Kamu herhangi bir bakanlık, kurum ya da Cumhurbaşkanlığı birimiyle "
                "bağlantılı değil ve onlar adına konuşmuyor. Başvuruları biz almıyoruz; "
                "her ilanın başvurusu, ilanı veren kurumun belirttiği yerden yapılıyor.",
                "İlanların kaynağı, kamu kurumlarının personel alım ilanlarını yayımladığı "
                "kamuilan.sbb.gov.tr. Her ilan sayfasında resmî ilan metnine giden link var.",
            )
            + '<div class="bolum-bas"><h2 id="ne">Ne yapıyoruz?</h2></div><ul>'
            "<li>İlanları günde dört kez kontrol ediyor, yenilerini ekliyoruz.</li>"
            "<li>Kadro sayısı, eğitim şartı, KPSS puan türü ve tarihleri sade bir sayfada gösteriyoruz.</li>"
            "<li>Uygulamada, seçtiğin ilan türü, eğitim ve şehir için bildirim gönderiyoruz.</li>"
            "<li>İptal ve düzeltme duyuruları ayrı ilan olarak gösterilmez.</li>"
            "</ul>"
            + _bolum(
                "yapmayiz", "Ne yapmıyoruz?",
                "Taban puan tahmini yapmıyoruz, \"bu puanla girersin\" demiyoruz. İlan "
                "bilgilerini otomatik çıkardığımız için hata olabilir; başvurmadan önce "
                'resmî ilanı mutlaka oku. Ayrıntılar <a href="/nasil-calisir/">nasıl '
                "çalışır</a> sayfasında.",
            )
        ),
    ),
    BilgiSayfasi(
        yol="/nasil-calisir/",
        ad="Nasıl çalışır?",
        baslik="Kamu Nasıl Çalışır? İlanların Kaynağı ve Güncelleme | Kamu",
        aciklama=(
            "Kamu'daki ilanlar kamuilan.sbb.gov.tr'den günde dört kez alınıyor, "
            "bilgiler yapay zekâyla çıkarılıyor. Hata payı ve hata bildirimi."
        ),
        h1="İlanlar nasıl hazırlanıyor?",
        govde=(
            '<p class="giris">Bu sitedeki ve uygulamadaki her ilanı resmî bir kaynaktan '
            "otomatik olarak alıp sadeleştiriyoruz. Süreç dört adımda ilerliyor.</p>"
            + _bolum(
                "kaynak", "1. Kaynak",
                "İlanlar, kamu kurumlarının personel alım ilanlarını yayımladığı "
                "kamuilan.sbb.gov.tr adresinden geliyor. Kurumun kendi sitesinde olup bu "
                "adreste yayımlanmayan ilanlar listede olmayabilir.",
            )
            + _bolum(
                "guncelleme", "2. Güncelleme",
                "Kaynağı günde dört kez kontrol ediyor, yeni ilanları ekleyip siteyi "
                "yeniden oluşturuyoruz. Yeni bir ilanın burada görünmesi bu yüzden birkaç "
                "saat sürebilir. Her sayfanın altında son güncelleme zamanı yazıyor.",
            )
            + _bolum(
                "cikarim", "3. Bilgilerin çıkarılması",
                "Kadro sayısı, eğitim seviyesi, KPSS ve ALES puan türü, yaş sınırı, görev "
                "yeri, başvuru tarihleri, başvuru yeri ve belgeleri ilan metninden bir yapay "
                "zekâ modeliyle otomatik çıkarıyoruz. İlan başlığı ve kurum adı kaynaktan "
                "olduğu gibi geliyor.",
                "Otomatik çıkarım hata yapabilir: bir tarih, puan türü ya da kadro sayısı "
                "yanlış okunmuş olabilir. Başlıktaki kadro sayısı ile kadro dağılımı "
                "uyuşmadığında adetleri göstermiyor, seni resmî ilana yönlendiriyoruz.",
            )
            + _bolum(
                "eleme", "4. Eleme",
                "İptal ve düzeltme duyuruları ayrı ilan olarak gösterilmez. Son başvuru "
                "tarihi geçen ilanın sayfası 60 gün daha \"başvuru süresi doldu\" notuyla "
                "kalıyor, sonra kaldırılıyor.",
            )
            + _bolum(
                "hata", "Hata gördüysen",
                f"Yanlış bir bilgi gördüysen ilan sayfasının adresiyle birlikte {_EPOSTA_LINK} "
                "adresine yaz. Başvurmadan önce her zaman resmî ilan metnini oku; bağlayıcı "
                "olan resmî ilan.",
            )
        ),
    ),
    BilgiSayfasi(
        yol="/iletisim/",
        ad="İletişim",
        baslik="İletişim: Kamu Uygulaması | Kamu",
        aciklama="Kamu uygulaması ve kamuuygulama.me ile ilgili soru, öneri ve hata bildirimleri için iletişim.",
        h1="İletişim",
        govde=(
            '<p class="giris">Soru, öneri ve hata bildirimleri için e-posta gönderebilirsin.</p>'
            '<dl class="bilgi">'
            f"<div><dt>E-posta</dt><dd>{_EPOSTA_LINK}</dd></div>"
            f'<div><dt>Instagram</dt><dd><a href="{INSTAGRAM}" rel="noopener">@kamu.uygulama</a></dd></div>'
            "</dl>"
            + _bolum(
                "bildirim", "Hata bildirirken",
                "İlan sayfasının adresini ve hangi bilginin yanlış olduğunu yaz. Mümkünse "
                "resmî ilandaki doğru bilgiyi de ekle.",
                "İlanlara başvuru, sınav sonucu ya da atama konularında bilgi veremiyoruz; "
                "bunlar için ilanı veren kurumla iletişime geç.",
            )
        ),
    ),
    BilgiSayfasi(
        yol="/gizlilik/",
        ad="Gizlilik",
        baslik="Gizlilik: Çerez ve Veri Kullanımı | Kamu",
        aciklama="kamuuygulama.me çerez ya da analiz aracı kullanmıyor. Uygulamanın gizlilik politikası ve barındırma bilgisi.",
        h1="Gizlilik",
        govde=(
            '<p class="giris">Bu site çerez, reklam ya da analiz aracı kullanmıyor ve '
            "senden hiçbir bilgi istemiyor.</p>"
            + _bolum(
                "site", "Site",
                "Sayfalar statik dosyalar; giriş, form ya da takip kodu yok. Yazı tipleri "
                "de bu sitenin kendi sunucusundan yükleniyor, üçüncü taraf bir hizmete "
                "istek gitmiyor.",
                "Site GitHub Pages üzerinde barındırılıyor. GitHub, hizmetin güvenliği ve "
                "işletimi için ziyaretçilerin IP adresi gibi teknik kayıtları tutabilir; bu "
                "kayıtlar GitHub'ın kendi gizlilik bildirimine tabi.",
                "Mağaza butonları Apple App Store ve Google Play'e gidiyor. Bu bağlantılar, "
                "hangi kanaldan gelindiğini mağazaya bildiren bir kampanya etiketi içeriyor; "
                "kişisel bilgi içermiyor.",
            )
            + _bolum(
                "uygulama", "Uygulama",
                "Kamu mobil uygulamasının topladığı veriler ve kullanım amaçları "
                f'<a href="{UYGULAMA_GIZLILIK}" rel="noopener">uygulama gizlilik politikasında</a> '
                "anlatılıyor.",
                f"Sorular için: {_EPOSTA_LINK}",
            )
        ),
    ),
)


def bilgi_sayfasi_parcalari(sayfa: BilgiSayfasi) -> tuple[SayfaBasi, str, list[tuple[str, str]]]:
    kirinti_ogeleri = [("Ana sayfa", "/"), (sayfa.ad, sayfa.yol)]
    cagri = uygulama_cagrisi(
        "Yeni ilan çıkınca haberin olsun",
        "Kamu, ilanları günde dört kez tarar; seçtiğin türde yeni ilan çıktığında ve son "
        "güne az kaldığında bildirim gönderir. Ücretsiz.",
        KAMPANYA,
    )
    govde = (
        f'{kirinti(kirinti_ogeleri)}<article class="okuma">'
        f"<h1>{e(sayfa.h1)}</h1>{sayfa.govde}{cagri}</article>"
    )
    bas = SayfaBasi(baslik=sayfa.baslik, aciklama=sayfa.aciklama, yol=sayfa.yol, kampanya=KAMPANYA)
    return bas, govde, kirinti_ogeleri

