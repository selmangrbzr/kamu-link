"""Rehberlerin elle yazılmış, kaynaklı kalıcı metni.

Her mevzuat, sınav ve kurum bilgisi bir Olgu olarak yazılır ve resmî kaynağına
bağlanır (rehber_kaynak.py). Düz metin (str) parçaları yalnızca bağlayıcı ya da
yönlendirici cümlelerdir; bilgi taşımaz. Hitap "sen", "-dır/-dir" eki yok.
Merkezi yerleştirme (tercih kılavuzu) kontenjanları bilerek yazılmaz.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date

from .rehber_kaynak import (
    DMK_657,
    GENEL_YONETMELIK,
    IS_KANUNU_4857,
    ISCI_YONETMELIGI,
    KAMUILAN,
    KARIYER_KAPISI_SSS,
    KONTROL_2026_10_08,
    KPSS_LISANS_2026,
    KPSS_ONLISANS_2026,
    KPSS_ORTAOGRETIM_2026,
    OGRETIM_ELEMANI_YONETMELIGI,
    OSYM_MEB_AGS,
    RESMI_GAZETE_CBK,
    SOZLESMELI_ESASLAR,
    Olgu,
    olgu,
)

YAYIN = date(2026, 10, 8)
REHBER_KOK = "/rehber/"

Parca = Olgu | str


@dataclass(frozen=True)
class Bolum:
    kimlik: str
    soru: str
    paragraflar: tuple[tuple[Parca, ...], ...]
    liste: bool = False  # True ise her paragraf bir madde olarak yazılır


@dataclass(frozen=True)
class Rehber:
    slug: str
    ad: str
    baslik: str
    aciklama: str
    h1: str
    soru: str
    cevap: tuple[Parca, ...]
    bolumler: tuple[Bolum, ...]
    veri_basligi: str
    merkezler: tuple[str, ...]
    ilgili: tuple[str, ...]  # diğer rehberlerin slug'ları
    yayin_tarihi: date = YAYIN
    kontrol_tarihi: date = KONTROL_2026_10_08

    @property
    def yol(self) -> str:
        return f"{REHBER_KOK}{self.slug}/"

    def olgular(self) -> Iterator[Olgu]:
        parcalar = list(self.cevap)
        for bolum in self.bolumler:
            for paragraf in bolum.paragraflar:
                parcalar.extend(paragraf)
        yield from (p for p in parcalar if isinstance(p, Olgu))


# --- 1. KPSS puanı geçerlilik süresi ------------------------------------------------

KPSS_GECERLILIK = Rehber(
    slug="kpss-puani-gecerlilik-suresi",
    ad="KPSS puanı kaç yıl geçerli?",
    baslik="KPSS Puanı Kaç Yıl Geçerli? Geçerlilik Süresi ve 2026 Sınavları | Kamu",
    aciklama=(
        "KPSS sonuçları açıklandığı tarihten itibaren iki yıl geçerli. Genel Yönetmelik ve "
        "2026 ÖSYM kılavuzlarına göre süre, düzey değişikliği ve açık ilanlar."
    ),
    h1="KPSS puanı kaç yıl geçerli?",
    soru="KPSS kaç yıl geçerli?",
    cevap=(
        olgu(GENEL_YONETMELIK, "md. 11",
             "KPSS sonuçları, açıklandığı tarihten itibaren iki yıl geçerli; bu sürede yeni bir "
             "sınav yapılamazsa sonuçlar, bir sonraki sınavın sonuçları açıklanana kadar "
             "geçerliliğini koruyor."),
    ),
    bolumler=(
        Bolum("baslangic", "İki yıllık süre ne zaman başlıyor?", (
            (
                olgu(GENEL_YONETMELIK, "md. 11",
                     "Süre sınav gününden değil, sonuçların açıklandığı tarihten başlıyor."),
                olgu(KPSS_LISANS_2026, "madde 1.11",
                     "2026 KPSS Lisans Kılavuzu da 2026-KPSS sonuçlarının açıklanmasından itibaren "
                     "iki yıl geçerli olacağını yazıyor."),
                olgu(KPSS_LISANS_2026, "bölüm 1",
                     "Aynı kılavuza göre 2025-KPSS sonuçları da açıklandığı tarihten itibaren iki "
                     "yıl geçerliliğini koruyor."),
            ),
        )),
        Bolum("eski-puan", "2024 KPSS puanım hâlâ geçerli mi?", (
            (
                olgu(KPSS_ORTAOGRETIM_2026, "madde 1.5",
                     "2024'te yapılan KPSS'nin ortaöğretim düzeyindeki geçerliliği, 2026'da "
                     "yapılacak sınavların sonuçları açıklandığında sona eriyor."),
                olgu(KPSS_ONLISANS_2026, "madde 1.5",
                     "Ön lisans düzeyinde de 2024 puanlarının geçerliliği 2026 sınavlarının "
                     "sonuçları açıklandığında bitiyor."),
                olgu(KPSS_ORTAOGRETIM_2026, "madde 1.5",
                     "Bu yüzden ortaöğretim ve ön lisans düzeyinde B grubu kadrolara tercih yapmak "
                     "isteyen adayların 2026 sınavına girmesi gerekiyor."),
            ),
            (
                olgu(KPSS_LISANS_2026, "madde 1.10",
                     "2026 KPSS Lisans'ın Genel Yetenek-Genel Kültür oturumu için 6 Eylül 2026, "
                     "alan bilgisi oturumları için 12-13 Eylül 2026 tarihleri belirlendi."),
                olgu(KPSS_ONLISANS_2026, "sınav tarihi",
                     "KPSS Ön Lisans'ın sınav tarihi 4 Ekim 2026."),
                olgu(KPSS_ORTAOGRETIM_2026, "madde 1.7",
                     "KPSS Ortaöğretim'in sınav tarihi 25 Ekim 2026."),
            ),
        )),
        Bolum("duzey", "Başka düzeyde sınava girersen eski puanın ne oluyor?", (
            (
                olgu(KPSS_ORTAOGRETIM_2026, "madde 1.11",
                     "Ortaöğretim düzeyinden giren biri sonraki KPSS Ön Lisans ya da B grubu "
                     "Lisans sınavına girerse, o sınavın sonucu açıklandığı tarihte ortaöğretim "
                     "puanının geçerliliği bitiyor."),
                olgu(KPSS_ORTAOGRETIM_2026, "madde 1.11",
                     "Sonraki A grubu sınavına girmek ise ortaöğretim puanını etkilemiyor."),
                olgu(KPSS_LISANS_2026, "madde 1.12",
                     "2024'te ortaöğretim ya da ön lisans düzeyinden girenler 2026 KPSS Lisans'a "
                     "girerse, bu sınavın sonucu açıklandığında eski puanlarının geçerliliği "
                     "sona eriyor."),
            ),
            (
                olgu(KPSS_LISANS_2026, "madde 2.1",
                     "Bir aday 2026'da hem KPSS Lisans'a hem de KPSS Ortaöğretim ya da Ön Lisans "
                     "sınavına katılamıyor."),
            ),
        )),
        Bolum("hak", "Geçerli bir KPSS puanı atanma hakkı veriyor mu?", (
            (
                olgu(GENEL_YONETMELIK, "md. 26",
                     "Hayır. KPSS'de yüksek puan almak, kamu kurumlarında görev almak için tek "
                     "başına bir hak doğurmuyor."),
                olgu(KPSS_LISANS_2026, "madde 1.5",
                     "Kamu kurumlarının A ve B grubu kadrolarına ilk defa atanacakların geçerli "
                     "bir KPSS puanına sahip olması ise zorunlu."),
            ),
        )),
        Bolum("ogretmen", "Öğretmenler için ayrı bir kural var mı?", (
            (
                olgu(GENEL_YONETMELIK, "md. 3",
                     "11 Ocak 2025'te yapılan değişiklikle Millî Eğitim Bakanlığında istihdam "
                     "edilen öğretmenler Genel Yönetmeliğin kapsamı dışına çıkarıldı."),
                olgu(OSYM_MEB_AGS, "sınav grubu sayfası",
                     "ÖSYM, Millî Eğitim Bakanlığı Akademi Giriş Sınavı'nı (MEB-AGS) ayrı bir "
                     "sınav grubu olarak yürütüyor; 2026 sınavının sonuçları 26 Ağustos "
                     "2026'da açıklandı."),
            ),
        )),
        Bolum("ales", "ALES puanı da iki yıl mı geçerli?", (
            (
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 5",
                     "Hayır. Öğretim görevlisi ve araştırma görevlisi alımlarında kullanılan ALES "
                     "sonuçları, açıklandığı tarihten itibaren beş yıl geçerli."),
            ),
        )),
    ),
    veri_basligi="Şu an hangi ilanlar KPSS puanı istiyor?",
    merkezler=("/kpss-p3-ilanlari/", "/kpss-p93-ilanlari/", "/kpss-p94-ilanlari/"),
    ilgili=("kpss-puan-turleri", "memur-sozlesmeli-isci-farki"),
)


# --- 2. Memur, sözleşmeli ve işçi farkı ----------------------------------------------

MEMUR_SOZLESMELI_ISCI = Rehber(
    slug="memur-sozlesmeli-isci-farki",
    ad="Memur, sözleşmeli ve işçi farkı",
    baslik="Memur, Sözleşmeli Personel ve İşçi Farkı: 657 4/A, 4/B ve İş Kanunu | Kamu",
    aciklama=(
        "Memur, sözleşmeli personel (4/B) ve kamu işçisi arasındaki fark: 657 sayılı Kanun "
        "md. 4, İş Kanunu, alım yolları ve türlere göre güncel açık ilan sayıları."
    ),
    h1="Memur, sözleşmeli personel ve işçi arasındaki fark ne?",
    soru="Memur, sözleşmeli personel ve işçi arasındaki fark ne?",
    cevap=(
        olgu(DMK_657, "md. 4/A",
             "Memur, Devlet ve diğer kamu tüzel kişiliklerinin genel idare esaslarına göre "
             "yürüttüğü asli ve sürekli kamu hizmetlerinde görevlendirilen kişi."),
        olgu(DMK_657, "md. 4/B",
             "Sözleşmeli personel, mali yılla sınırlı olarak sözleşmeyle çalıştırılan ve işçi "
             "sayılmayan kamu hizmeti görevlisi."),
        olgu(DMK_657, "md. 4/D",
             "Kamu işçisi iş sözleşmesiyle çalışıyor ve 657 sayılı Kanun hükümleri ona "
             "uygulanmıyor."),
    ),
    bolumler=(
        Bolum("istihdam", "657 sayılı Kanun kaç istihdam şekli sayıyor?", (
            (
                olgu(DMK_657, "md. 4",
                     "Kanuna göre kamu hizmetleri memurlar, sözleşmeli personel, geçici personel "
                     "ve işçiler eliyle görülüyor."),
                olgu(DMK_657, "md. 4/C",
                     "Geçici personeli düzenleyen (C) bendi 20 Kasım 2017'de yürürlükten kaldırıldı."),
                olgu(DMK_657, "md. 5",
                     "Kanuna tabi kurumlar bu istihdam şekilleri dışında personel çalıştıramıyor."),
            ),
        )),
        Bolum("memur", "Memur olmak için hangi şartlar aranıyor?", (
            (
                olgu(DMK_657, "md. 48",
                     "Genel şartlar arasında Türk vatandaşı olmak, Kanundaki yaş ve öğrenim "
                     "şartlarını taşımak, kamu haklarından mahrum bulunmamak, sayılan suçlardan "
                     "mahkûm olmamak ve askerlik durumu bakımından uygun olmak var."),
                olgu(DMK_657, "md. 50",
                     "Devlet memuru olarak atanacakların açılan sınavlara girmesi ve sınavı "
                     "kazanması şart."),
            ),
            (
                olgu(GENEL_YONETMELIK, "md. 12 ve 22",
                     "Genel Yönetmelik, B grubu kadrolar için ÖSYM'nin KPSS puanıyla yaptığı "
                     "yerleştirmeyi, A grubu kadrolar için ise esas olarak kurumun kendi giriş "
                     "sınavıyla seçimi düzenliyor."),
            ),
        )),
        Bolum("sozlesmeli", "Sözleşmeli personel (4/B) nasıl alınıyor?", (
            (
                olgu(SOZLESMELI_ESASLAR, "ek md. 2",
                     "Kurumlar sözleşmeli personeli KPSS (B) grubu puan sıralamasına göre ÖSYM'nin "
                     "merkezi yerleştirmesiyle, kendi yaptıkları yerleştirmeyle ya da belirli "
                     "unvanlarda boş pozisyonun on katına kadar aday arasından yapacakları yazılı "
                     "ve/veya sözlü sınavla alıyor."),
                olgu(SOZLESMELI_ESASLAR, "ek md. 2",
                     "Merkezi yerleştirme dışındaki alımlarda kurum, ilanı yerleştirme ya da sınav "
                     "tarihinden en az on beş gün önce yayımlamak zorunda."),
            ),
            (
                olgu(DMK_657, "md. 4/B",
                     "Cumhurbaşkanınca belirlenen pozisyon unvanlarında aynı kurumda üç yılını "
                     "dolduran sözleşmeli personel, sürenin bitiminden itibaren otuz gün içinde "
                     "talep ederse bulunduğu yerde aynı unvanlı memur kadrosuna atanıyor."),
            ),
        )),
        Bolum("isci", "Kamu işçisi nasıl alınıyor?", (
            (
                olgu(IS_KANUNU_4857, "md. 2",
                     "İş Kanunu, bir iş sözleşmesine dayanarak çalışan gerçek kişiyi işçi olarak "
                     "tanımlıyor."),
                olgu(DMK_657, "md. 4/D",
                     "Kamuda sürekli işçiler belirsiz süreli, geçici işçiler ise altı aydan az "
                     "süreli iş sözleşmesiyle çalışıyor."),
            ),
            (
                olgu(ISCI_YONETMELIGI, "md. 6",
                     "Kamu kurumları işçi ihtiyacını kural olarak Türkiye İş Kurumundan (İŞKUR) "
                     "talep etmek ve "
                     "İŞKUR'un gönderdiği adaylar arasından karşılamak zorunda."),
                olgu(ISCI_YONETMELIGI, "md. 10",
                     "Ön lisans ve lisans düzeyindeki işçi alımlarında KPSS puanı, ortaöğretim ve "
                     "daha alt düzeyde ise noter huzurunda çekilen kura kullanılıyor."),
                olgu(ISCI_YONETMELIGI, "md. 10",
                     "Ön lisans ve lisans düzeyindeki işçi ilanlarına ilgili KPSS puan türünden 60 "
                     "ve üzeri alanlar başvurabiliyor."),
            ),
        )),
    ),
    veri_basligi="Açık ilanlar türlere göre nasıl dağılıyor?",
    merkezler=("/memur-alimlari/", "/sozlesmeli-personel-alimlari/", "/isci-alimlari/"),
    ilgili=("kpss-puan-turleri", "lise-mezunu-kamu-is"),
)


# --- 3. KPSS puan türleri ------------------------------------------------------------

KPSS_PUAN_TURLERI = Rehber(
    slug="kpss-puan-turleri",
    ad="KPSS puan türleri",
    baslik="KPSS Puan Türleri: P3, P93, P94 ve A Grubu (P1-P48) Ne Demek? | Kamu",
    aciklama=(
        "KPSS P3 lisans, P93 ön lisans, P94 ortaöğretim puan türü; A grubu P1-P48 alan "
        "bilgisi testlerini de içeriyor. 2026 ÖSYM kılavuzları ve açık ilanlar."
    ),
    h1="KPSS puan türleri ne anlama geliyor?",
    soru="KPSS P3, P93 ve P94 ne demek?",
    cevap=(
        olgu(KPSS_LISANS_2026, "madde 1.14",
             "ÖSYM'nin 2026 KPSS kılavuzlarında lisans düzeyi için KPSSP3, ön lisans düzeyi için "
             "KPSSP93, ortaöğretim düzeyi için KPSSP94 puan türü kullanılıyor."),
        olgu(KPSS_ORTAOGRETIM_2026, "madde 3.10",
             "Bu puanlar Genel Yetenek ve Genel Kültür testlerinin her birine 0,50 ağırlık "
             "verilerek hesaplanıyor."),
    ),
    bolumler=(
        Bolum("hesap", "P3, P93 ve P94 nasıl hesaplanıyor?", (
            (
                olgu(KPSS_LISANS_2026, "madde 3.1",
                     "Genel Yetenek ve Genel Kültür oturumunda 60'ar soru olmak üzere 120 soru "
                     "130 dakikada cevaplanıyor."),
                olgu(KPSS_LISANS_2026, "Tablo-2",
                     "KPSSP3, Genel Yetenek ve Genel Kültür'ün 0,50'şer ağırlığıyla hesaplanıyor."),
                olgu(KPSS_ONLISANS_2026, "Tablo-2",
                     "KPSSP93 de aynı 0,50 ve 0,50 ağırlıklarını kullanıyor."),
                olgu(KPSS_ORTAOGRETIM_2026, "madde 1.9",
                     "Genel Yönetmelik kapsamı dışında olup KPSS sonucunu kullanan kurumlar da B "
                     "grubu niteliğindeki kadrolu ve sözleşmeli alımlarda bu üç puan türünü "
                     "kullanıyor."),
            ),
            (
                olgu(KPSS_ORTAOGRETIM_2026, "madde 3.10",
                     "Her testte doğru sayısından yanlış sayısının dörtte biri çıkarılarak ham "
                     "puan bulunuyor."),
                olgu(KPSS_ORTAOGRETIM_2026, "madde 3.10",
                     "KPSS puanı hesaplanabilmesi için Genel Yetenek ve Genel Kültür testlerinin "
                     "ikisinden de en az 1 net gerekiyor."),
                olgu(KPSS_ORTAOGRETIM_2026, "madde 3.10",
                     "Sonuçta her puan türü için 100 üzerinden bir puan elde ediliyor."),
            ),
            (
                olgu(KPSS_ORTAOGRETIM_2026, "Tablo-1",
                     "Genel Yetenek testi yarı yarıya sözel ve sayısal bölümden oluşuyor; Genel "
                     "Kültür'de tarih yüzde 45, Türkiye coğrafyası yüzde 30, temel yurttaşlık "
                     "bilgisi yüzde 15, Türkiye ve dünyayla ilgili genel, kültürel ve sosyoekonomik "
                     "konular yüzde 10 ağırlık taşıyor."),
            ),
        )),
        Bolum("a-grubu", "A grubu puan türleri (P1-P48) neyi ölçüyor?", (
            (
                olgu(KPSS_LISANS_2026, "madde 1.6",
                     "A grubu kadrolar müfettiş yardımcılığı, uzman yardımcılığı ve denetmen "
                     "yardımcılığı gibi kadrolar."),
                olgu(KPSS_LISANS_2026, "Tablo-2",
                     "KPSSP1, Genel Yetenek 0,70 ve Genel Kültür 0,30; KPSSP2 ise 0,60 ve 0,40 "
                     "ağırlıkla hesaplanıyor."),
                olgu(KPSS_LISANS_2026, "madde 3.1 ve Tablo-2",
                     "KPSSP4'ten KPSSP48'e kadar olan puan türlerine hukuk, iktisat, işletme, maliye, "
                     "muhasebe, çalışma ekonomisi ve endüstri ilişkileri, istatistik, kamu yönetimi "
                     "ve uluslararası ilişkiler alan bilgisi testleri farklı ağırlıklarla giriyor."),
            ),
            (
                olgu(KPSS_LISANS_2026, "madde 1.10",
                     "2026 kılavuzunda alan bilgisi oturumlarının tarihi 12-13 Eylül 2026; tüm "
                     "adayların 6 Eylül 2026'daki Genel Yetenek-Genel Kültür oturumuna girmesi "
                     "zorunlu, diğer oturumları adaylar kendisi seçiyor."),
                olgu(KPSS_LISANS_2026, "Tablo-2 dipnotu",
                     "KPSS puanıyla alım yapan kurumlar A grubu kadroları için bu tablodaki puan "
                     "türlerini kullanıyor; ÖSYM, hangi puan türünün kullanılacağını sınava "
                     "girmeden önce kurumdan öğrenmeni öneriyor."),
            ),
        )),
        Bolum("ilan", "Hangi puan türünün istendiğini nereden anlarım?", (
            (
                olgu(GENEL_YONETMELIK, "md. 13",
                     "A grubu kadrolara alım yapacak kurumlar KPSS puan türünü ya da türlerini ve "
                     "asgari puanı ilanlarında duyuruyor."),
                "Başvurmadan önce resmî ilanda hangi puan türünün ve hangi asgari puanın "
                "istendiğine bak; bazı ilanlar birden fazla puan türü kabul ediyor.",
            ),
        )),
    ),
    veri_basligi="Hangi puan türü kaç açık ilanda isteniyor?",
    merkezler=("/kpss-p3-ilanlari/", "/kpss-p93-ilanlari/", "/kpss-p94-ilanlari/"),
    ilgili=("kpss-puani-gecerlilik-suresi", "uzman-yardimciligi-alimlari"),
)


# --- 4. Lise mezunu kamu işi -----------------------------------------------------------

LISE_MEZUNU = Rehber(
    slug="lise-mezunu-kamu-is",
    ad="Lise mezunu kamuya nasıl girer?",
    baslik="Lise Mezunu Kamuda Nasıl İşe Girer? KPSS P94, İŞKUR ve Kura | Kamu",
    aciklama=(
        "Lise mezunu kamuya KPSS P94 ile memur ve sözleşmeli kadrolara, İŞKUR ve noter "
        "kurasıyla işçi alımlarına giriyor. Kurallar ve açık ilan dağılımı."
    ),
    h1="Lise mezunu kamuda nasıl işe girer?",
    soru="Lise mezunu kamuda nasıl işe girer?",
    cevap=(
        olgu(KPSS_ORTAOGRETIM_2026, "madde 3.10",
             "Lise mezunlarının B grubu kadrolara yerleştirmesinde KPSS Ortaöğretim sınavından "
             "hesaplanan KPSSP94 puanı esas alınıyor."),
        olgu(SOZLESMELI_ESASLAR, "ek md. 2",
             "Sözleşmeli personel alımlarında da KPSS (B) grubu puan sıralaması kullanılıyor."),
        olgu(ISCI_YONETMELIGI, "md. 10 ve 12",
             "Kamu kurumlarının ortaöğretim düzeyindeki işçi alımlarında ise adaylar, İŞKUR'a "
             "başvuranlar arasından noter huzurunda çekilen kurayla belirleniyor."),
    ),
    bolumler=(
        Bolum("kpss", "KPSS Ortaöğretim'e kimler, ne zaman giriyor?", (
            (
                olgu(KPSS_ORTAOGRETIM_2026, "madde 1.4",
                     "Sınav lise ve meslek lisesi mezunları ile iki yıllık geçerlilik süresi içinde "
                     "mezun olabilecek durumda olanlar için."),
                olgu(KPSS_ORTAOGRETIM_2026, "madde 1.7",
                     "2026 KPSS Ortaöğretim 25 Ekim 2026'da, saat 10.15'te başlayıp 130 dakika "
                     "sürecek."),
                olgu(KPSS_ORTAOGRETIM_2026, "madde 1.5",
                     "2024 sınavının ortaöğretim puanları 2026 sonuçları açıklandığında geçersiz "
                     "olacağı için B grubu kadrolara tercih yapmak isteyenlerin bu sınava girmesi "
                     "gerekiyor."),
            ),
        )),
        Bolum("iskur", "İŞKUR üzerinden işçi alımı nasıl işliyor?", (
            (
                olgu(ISCI_YONETMELIGI, "md. 9",
                     "Kamu kurumlarının işçi talepleri İŞKUR'un internet sayfasında ilan ediliyor ve "
                     "ilandan itibaren beş günlük başvuru süresi tanınıyor."),
                olgu(ISCI_YONETMELIGI, "md. 9",
                     "Başvuruda Adrese Dayalı Nüfus Kayıt Sistemi'ndeki adresin dikkate alınıyor; "
                     "ilçe, il ya da bölge düzeyindeki ilanlarda başvuru süresi içinde ikametini o "
                     "yere taşıyanların başvurusu kabul edilmiyor."),
            ),
            (
                olgu(ISCI_YONETMELIGI, "md. 12",
                     "Kura, ilanda belirtilen gün, saat ve adreste noter huzurunda çekiliyor ve "
                     "adaylar isterse kurayı izleyebiliyor."),
                olgu(ISCI_YONETMELIGI, "md. 10",
                     "Temizlik, güvenlik ve koruma, bakım ve onarım hizmetlerindeki işçi alımlarında "
                     "da kura kullanılıyor."),
                olgu(ISCI_YONETMELIGI, "md. 4",
                     "İşçi olarak alınmak için Türk vatandaşı olmak ve 18 yaşını tamamlamış olmak "
                     "gibi şartlar aranıyor."),
            ),
        )),
        Bolum("belediye", "Belediyeler nasıl alım yapıyor?", (
            (
                olgu(GENEL_YONETMELIK, "md. 27/A",
                     "Belediyeler ve il özel idareleri B grubu kadrolarına ÖSYM yerleştirmesiyle ya "
                     "da KPSS (B) grubu puan sırasına göre kadro sayısının beş katına kadar aday "
                     "arasından yapacakları yazılı ve/veya sözlü sınavla atama yapabiliyor."),
            ),
        )),
    ),
    veri_basligi="Lise mezunlarına açık ilanlar hangi türde?",
    merkezler=("/lise-mezunu-kamu-ilanlari/", "/kpss-p94-ilanlari/", "/isci-alimlari/"),
    ilgili=("memur-sozlesmeli-isci-farki", "kpss-puani-gecerlilik-suresi"),
)


# --- 5. Kamu ilanına başvuru yolları ------------------------------------------------------

BASVURU_YOLLARI = Rehber(
    slug="kamu-ilanina-basvuru-yollari",
    ad="Kamu ilanına başvuru yolları",
    baslik="Kamu İlanına Başvuru Yolları: Kariyer Kapısı, ÖSYM, İŞKUR, Şahsen | Kamu",
    aciklama=(
        "Kamu ilanına başvuru, kurumun ilanda belirttiği yoldan yapılıyor: Kariyer Kapısı, "
        "ÖSYM, İŞKUR, kurum sistemi ya da şahsen. Kurallar ve dağılım."
    ),
    h1="Kamu ilanına nereden ve nasıl başvurulur?",
    soru="Kamu ilanına nereden başvurulur?",
    cevap=(
        olgu(RESMI_GAZETE_CBK, "md. 5",
             "Kamu kurumları personel alım ilanlarının tamamını Resmî Gazete'de, Cumhurbaşkanınca "
             "belirlenen kurumun internet sitesinde ve kendi internet sitelerinde duyuruyor."),
        olgu(KARIYER_KAPISI_SSS, "soru 7",
             "Kariyer Kapısı'nda yayımlanan ilanlara e-Devlet üzerinden başvuru yapılabiliyor."),
        "Başvurunun nereden yapılacağını her zaman resmî ilan metninden kontrol et.",
    ),
    bolumler=(
        Bolum("ilanlar", "İlanlar nerede yayımlanıyor?", (
            (
                olgu(RESMI_GAZETE_CBK, "md. 5",
                     "Bu kural, ihtiyacını okullara öğrenci alarak karşılayan kurumlar dahil tüm "
                     "personel alım ilanları için geçerli."),
                olgu(KAMUILAN, "ana sayfa",
                     "kamuilan.sbb.gov.tr sitesi kendini \"Tüm kamu personeli alım ilanları tek "
                     "adreste\" diye tanıtıyor."),
            ),
        )),
        Bolum("kariyer-kapisi", "Kariyer Kapısı nedir?", (
            (
                olgu(KARIYER_KAPISI_SSS, "soru 1",
                     "Kariyer Kapısı İşe Alım Platformu, Cumhurbaşkanlığı koordinasyonunda yürütülen "
                     "ve e-Devlet entegrasyonuyla çalışan bir çevrim içi platform."),
                olgu(KARIYER_KAPISI_SSS, "soru 2",
                     "Platform e-Devlet erişimi olan herkese ücretsiz; girişte e-Devlet şifresi "
                     "kullanılıyor."),
                olgu(KARIYER_KAPISI_SSS, "soru 7",
                     "Başvuru sonuçlarını ve değerlendirme aşamalarını da platformdan takip "
                     "edebiliyorsun."),
            ),
            (
                olgu(KARIYER_KAPISI_SSS, "soru 5 ve 6",
                     "Kariyer Kapısı istenen KPSS, YDS gibi şartları değiştirmiyor; seçme ve "
                     "yerleştirmeyi ilanı açan kurum kendi mevzuatına göre yürütüyor."),
            ),
        )),
        Bolum("osym", "ÖSYM'nin sistemi ne zaman gerekiyor?", (
            (
                olgu(KPSS_LISANS_2026, "madde 2.2",
                     "KPSS'ye başvuru ÖSYM Aday İşlemleri Sistemi (ais.osym.gov.tr) ya da ÖSYM Aday "
                     "İşlemleri Mobil Uygulaması üzerinden yapılıyor."),
                olgu(GENEL_YONETMELIK, "md. 22",
                     "B grubu kadrolar için ÖSYM bir tercih kılavuzu hazırlıyor; adaylar "
                     "tercihlerini kılavuzda belirlenen yolla veriyor."),
                olgu(KPSS_LISANS_2026, "madde 1.6",
                     "A grubu kadrolarda ise adaylar sınavdan sonra ilan veren kuruma doğrudan "
                     "başvuruyor."),
            ),
        )),
        Bolum("iskur", "İşçi ilanlarına nereden başvurulur?", (
            (
                olgu(ISCI_YONETMELIGI, "md. 9",
                     "Kamu kurumlarının işçi talepleri İŞKUR'un internet sayfasında ilan ediliyor; "
                     "başvuru süresi ilandan itibaren beş gün."),
                olgu(KPSS_LISANS_2026, "İŞKUR duyurusu",
                     "Adaylar İŞKUR il ve şube müdürlüklerine şahsen ya da iskur.gov.tr'ye üye olarak "
                     "başvuruyor; başvuru yapmadan doğrudan işe yerleştirme yapılmıyor."),
            ),
        )),
        Bolum("sahsen", "Şahsen ya da posta ile başvuru hangi ilanlarda var?", (
            (
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 8",
                     "Öğretim görevlisi ve araştırma görevlisi ilanlarında başvuru, ilanda belirtilen "
                     "adrese şahsen ya da posta yoluyla, ilanda belirtilmişse internet üzerinden "
                     "yapılıyor."),
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 8",
                     "Bu ilanlarda son başvuru tarihi ilandan itibaren on beş günden kısa olamıyor ve "
                     "postadaki gecikme yüzünden süresinde ulaşmayan başvurular dikkate alınmıyor."),
            ),
        )),
    ),
    veri_basligi="Açık ilanlarda başvuru en çok nereden yapılıyor?",
    merkezler=("/son-basvurusu-yaklasan-ilanlar/", "/bu-hafta-eklenen-kamu-ilanlari/"),
    ilgili=("akademik-ilan-ales-sarti", "lise-mezunu-kamu-is"),
)


# --- 6. Akademik ilanlarda ALES şartı ------------------------------------------------------

AKADEMIK_ALES = Rehber(
    slug="akademik-ilan-ales-sarti",
    ad="Akademik ilan şartları",
    baslik="Akademik İlanlarda ALES ve Yabancı Dil Şartı: Kaç Puan Gerekiyor? | Kamu",
    aciklama=(
        "Öğretim görevlisi ve araştırma görevlisi alımlarında ALES'ten en az 70, yabancı "
        "dilden en az 50 puan gerekiyor. İstisnalar ve açık akademik ilanlar."
    ),
    h1="Akademik ilanlarda ALES ve yabancı dil şartı ne?",
    soru="Akademik ilanlarda ALES şartı kaç puan?",
    cevap=(
        olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 6",
             "Öğretim görevlisi ve araştırma görevlisi kadrolarına atanmak için ALES'ten en az 70, "
             "YÖK'ün kabul ettiği merkezi yabancı dil sınavından en az 50 puan ya da eşdeğeri "
             "gerekiyor."),
        olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 5",
             "ALES sonuçları açıklandığı tarihten itibaren beş yıl geçerli."),
    ),
    bolumler=(
        Bolum("kapsam", "Bu kurallar hangi kadroları kapsıyor?", (
            (
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 1 ve 2",
                     "Yönetmelik devlet ve vakıf yükseköğretim kurumlarının öğretim görevlisi ve "
                     "araştırma görevlisi kadrolarını kapsıyor; öğretim üyesi kadroları bu "
                     "Yönetmeliğin konusu değil."),
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 2",
                     "Görev süresi uzatımı niteliğindeki atamalarda ve yabancı uyruklu öğretim "
                     "elemanlarının sözleşmeli çalıştırılmasında uygulanmıyor."),
            ),
        )),
        Bolum("istisna", "ALES ve yabancı dil şartının istisnaları var mı?", (
            (
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 14",
                     "Doktora, tıpta, diş hekimliğinde, eczacılıkta ya da veteriner hekimlikte "
                     "uzmanlık veya sanatta yeterlik eğitimini tamamlayanlar ile yükseköğretim "
                     "kurumlarında öğretim elemanı olarak çalışmış ya da çalışanlar ALES şartından "
                     "muaf."),
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 6",
                     "Muafiyetten yararlananların ALES puanı değerlendirmede 70 kabul ediliyor."),
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 14",
                     "Meslek yüksekokullarının kadrolarına başvurularda, 85 yabancı dil puanı "
                     "istenen kadrolar dışında yabancı dil şartı aranmıyor."),
            ),
            (
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 6",
                     "Yabancı dille öğretim yapılan programlar ve zorunlu yabancı dil derslerini "
                     "verecek öğretim görevlileri gibi kadrolarda en az 85 yabancı dil puanı "
                     "isteniyor."),
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 6",
                     "Üniversiteler, meslek yüksekokullarının belirli kadroları dışında, senato "
                     "kararıyla ALES ve yabancı dil için daha yüksek bir asgari puan "
                     "belirleyebiliyor."),
            ),
        )),
        Bolum("diger", "Araştırma görevlisi ve öğretim görevlisi için başka şart var mı?", (
            (
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 7",
                     "Araştırma görevlisi kadrosuna başvurmak için giriş sınavının yapıldığı yılın 1 "
                     "Ocak'ı itibarıyla 35 yaşını doldurmamış olmak gerekiyor."),
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 7",
                     "Devlet üniversitelerinin araştırma görevlisi kadrolarında tezli yüksek lisans, "
                     "doktora ya da sanatta yeterlik öğrencisi olma şartı aranıyor."),
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 7",
                     "Öğretim görevlisi kadrosuna başvurmak için en az tezli yüksek lisans derecesi "
                     "ya da lisans ve yüksek lisansı birlikte veren bir programdan mezuniyet "
                     "gerekiyor; meslek yüksekokullarının bazı kadrolarında bunun yerine lisans "
                     "mezuniyeti ve mesleki tecrübe aranıyor."),
            ),
        )),
        Bolum("degerlendirme", "Adaylar nasıl değerlendiriliyor?", (
            (
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 10",
                     "Ön değerlendirmede kadro sayısının on katına kadar aday giriş sınavına "
                     "çağrılıyor; genel kadrolarda ALES'in yüzde 60'ı ve yabancı dil puanının yüzde "
                     "40'ı, meslek yüksekokullarında ALES'in yüzde 70'i ve lisans mezuniyet notunun "
                     "yüzde 30'u esas alınıyor."),
                olgu(OGRETIM_ELEMANI_YONETMELIGI, "md. 12",
                     "Nihai değerlendirmede genel kadrolarda ALES yüzde 30, lisans notu yüzde 30, "
                     "yabancı dil yüzde 10 ve giriş sınavı yüzde 30 ağırlık taşıyor; 65'in altında "
                     "kalan aday başarısız sayılıyor."),
            ),
        )),
    ),
    veri_basligi="Şu an kaç akademik ilan açık?",
    merkezler=("/akademik-personel-alimlari/",),
    ilgili=("kamu-ilanina-basvuru-yollari", "kpss-puani-gecerlilik-suresi"),
)


# --- 7. Uzman yardımcılığı alımları -----------------------------------------------------------

UZMAN_YARDIMCILIGI = Rehber(
    slug="uzman-yardimciligi-alimlari",
    ad="Uzman yardımcılığı alımları",
    baslik="Uzman Yardımcılığı Nedir? Hangi KPSS Puanı İsteniyor, Açık İlanlar | Kamu",
    aciklama=(
        "Uzman yardımcılığı KPSS'nin A grubu kadrolarından biri; kurumlar kendi giriş "
        "sınavıyla alıyor. İstenen puanlar ve açık uzman yardımcısı ilanları."
    ),
    h1="Uzman yardımcılığı nedir, hangi puanlar isteniyor?",
    soru="Uzman yardımcılığı nedir?",
    cevap=(
        olgu(KPSS_LISANS_2026, "madde 1.6",
             "Uzman yardımcılığı, müfettiş ve denetmen yardımcılığı gibi KPSS'nin A grubu "
             "kadrolarından biri."),
        olgu(GENEL_YONETMELIK, "md. 12 ve 14",
             "Kurumlar bu kadrolara, KPSS puanı belirledikleri tabanın üzerinde olan adayları kendi "
             "mevzuatlarına göre yaptıkları giriş sınavıyla seçiyor."),
    ),
    bolumler=(
        Bolum("a-grubu", "A grubu kadro ne demek?", (
            (
                olgu(GENEL_YONETMELIK, "md. 2",
                     "A grubu, özel yarışma sınavıyla girilen ve belirli bir yetişme programından "
                     "sonra yeterlik sınavına tabi tutulan mesleklerin kadrolarını kapsıyor."),
                olgu(GENEL_YONETMELIK, "md. 12",
                     "Kurumun kendi mevzuatında hüküm varsa giriş sınavı yapılmadan doğrudan KPSS "
                     "puanıyla da atama yapılabiliyor."),
            ),
        )),
        Bolum("secim", "Seçim nasıl yapılıyor?", (
            (
                olgu(GENEL_YONETMELIK, "md. 13",
                     "Kurum ilanında kadro sayısını, KPSS puan türünü ya da türlerini, asgari puanı, "
                     "sınavın yerini, zamanını, içeriğini ve değerlendirme yöntemini duyuruyor."),
                olgu(GENEL_YONETMELIK, "md. 14",
                     "Adayların kurumun belirlediği taban puanın üzerinde olması ve 657 sayılı "
                     "Kanun'un 48. maddesindeki şartları taşıması gerekiyor."),
                olgu(GENEL_YONETMELIK, "md. 17",
                     "Giriş sınavına kadro sayısının en fazla 20 katı aday çağrılıyor."),
            ),
        )),
        Bolum("puan", "Hangi KPSS puanları isteniyor?", (
            (
                olgu(KPSS_LISANS_2026, "Tablo-2",
                     "A grubu kadrolarda KPSSP1-P48 gibi puan türleri kullanılıyor; P1 ve P2 "
                     "dışındakiler alan bilgisi testlerini de içeriyor."),
                olgu(KPSS_LISANS_2026, "madde 1.10",
                     "2026 kılavuzunda bu puanlar için alan bilgisi oturumlarının tarihi 12-13 "
                     "Eylül 2026."),
                "Hangi puan türünün istendiği kurumdan kuruma değişiyor; aşağıdaki listede açık "
                "ilanların puan şartlarını görebilirsin.",
            ),
        )),
        Bolum("kapsam", "Her uzman yardımcılığı Genel Yönetmeliğe tabi mi?", (
            (
                olgu(GENEL_YONETMELIK, "md. 3",
                     "Hayır. Yurtdışı Türkler ve Akraba Topluluklar uzman yardımcıları ile İletişim "
                     "uzman yardımcıları Genel Yönetmeliğin kapsamı dışında."),
            ),
        )),
    ),
    veri_basligi="Şu an açık uzman yardımcısı ilanları",
    merkezler=("/memur-alimlari/", "/lisans-mezunu-kamu-ilanlari/"),
    ilgili=("kpss-puan-turleri", "kpss-puani-gecerlilik-suresi"),
)


REHBERLER: tuple[Rehber, ...] = (
    KPSS_GECERLILIK,
    MEMUR_SOZLESMELI_ISCI,
    KPSS_PUAN_TURLERI,
    LISE_MEZUNU,
    BASVURU_YOLLARI,
    AKADEMIK_ALES,
    UZMAN_YARDIMCILIGI,
)
REHBER_SLUGLARI = {r.slug: r for r in REHBERLER}

# Merkez sayfasından ilgili rehbere tek link.
MERKEZ_REHBERI: dict[str, str] = {
    "/memur-alimlari/": MEMUR_SOZLESMELI_ISCI.slug,
    "/sozlesmeli-personel-alimlari/": MEMUR_SOZLESMELI_ISCI.slug,
    "/isci-alimlari/": MEMUR_SOZLESMELI_ISCI.slug,
    "/akademik-personel-alimlari/": AKADEMIK_ALES.slug,
    "/lise-mezunu-kamu-ilanlari/": LISE_MEZUNU.slug,
    "/onlisans-mezunu-kamu-ilanlari/": KPSS_GECERLILIK.slug,
    "/lisans-mezunu-kamu-ilanlari/": UZMAN_YARDIMCILIGI.slug,
    "/kpss-p3-ilanlari/": KPSS_PUAN_TURLERI.slug,
    "/kpss-p93-ilanlari/": KPSS_PUAN_TURLERI.slug,
    "/kpss-p94-ilanlari/": KPSS_PUAN_TURLERI.slug,
    "/son-basvurusu-yaklasan-ilanlar/": BASVURU_YOLLARI.slug,
    "/kpss-siz-kamu-ilanlari/": BASVURU_YOLLARI.slug,
}
