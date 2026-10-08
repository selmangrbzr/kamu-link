"""Merkez (hub) sayfalarının tanımları.

Her merkezin elle yazılmış, özgün bir giriş metni vardır; sayfa ayrıca o anki
veriden özet cümleler üretir.

- Sabit merkezler ve kalıcı kurumlar adreslerini korur: açık ilan sayısı
  eşiğin altına düşerse "şu an açık ilan yok" der ve noindex olur.
- Şehir ve diğer kurum sayfaları yalnızca açık ilan varken üretilir.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .metin import ascii_slug, katla
from .model import ILLER, Ilan, bugun_tr

# Merkezin indekslenmesi için gereken en az açık ilan sayısı (ince içerik koruması).
MERKEZ_INDEKS_ESIGI = 2
SEHIR_INDEKS_ESIGI = 3
KURUM_INDEKS_ESIGI = 2
YAKLASAN_GUN = 7
HAFTA_GUN = 7

Filtre = Callable[[Ilan, datetime], bool]


@dataclass(frozen=True)
class Merkez:
    yol: str
    ad: str
    baslik: str  # "{yil}" yer tutucusu derleme yılıyla doldurulur
    h1: str
    etiket: str
    giris: str
    filtre: Filtre
    grup: str
    en_az_indeks: int = MERKEZ_INDEKS_ESIGI
    il: str | None = None
    kalici: bool = True
    siralama: str = "yeni"  # "yeni": eklenme tarihine göre, "bitis": son başvuruya göre
    uyari: str | None = None

    def baslik_metni(self, yil: int) -> str:
        return self.baslik.replace("{yil}", str(yil))


def _tur(tur: str) -> Filtre:
    return lambda ilan, _simdi: ilan.ilan_turu == tur


def _egitim(grup: str) -> Filtre:
    return lambda ilan, _simdi: ilan.egitim_grubu == grup


def _puan(puan: str) -> Filtre:
    return lambda ilan, _simdi: puan in ilan.kpss_turleri


def _il(il: str) -> Filtre:
    return lambda ilan, _simdi: il in ilan.iller and not ilan.ulusal_mi


def _kurum(slug: str) -> Filtre:
    return lambda ilan, _simdi: ilan.kurum_slug == slug


def _belediye(ilan: Ilan, _simdi: datetime) -> bool:
    return "belediye" in katla(ilan.kurum)


def _kpss_siz(ilan: Ilan, _simdi: datetime) -> bool:
    return not ilan.kpss_puan_turu and ilan.ilan_turu != "Akademik Personel"


def _yaklasan(ilan: Ilan, simdi: datetime) -> bool:
    return 0 <= (ilan.basvuru_bitis - bugun_tr(simdi)).days <= YAKLASAN_GUN


def _bu_hafta(ilan: Ilan, simdi: datetime) -> bool:
    return ilan.eklenme_tarihi >= simdi - timedelta(days=HAFTA_GUN)


SABIT_MERKEZLER: tuple[Merkez, ...] = (
    Merkez(
        yol="/memur-alimlari/",
        ad="Memur alımları",
        baslik="Memur Alımları {yil}: Güncel Kamu Memur İlanları",
        h1="Memur alımları",
        etiket="İLAN TÜRÜ",
        giris=(
            "Memur alımları, 657 sayılı Devlet Memurları Kanunu'na tabi kadrolu "
            "pozisyonlardır. İlanların çoğunda KPSS puanı istenir: lisans mezunları "
            "genellikle P3, ön lisans mezunları P93, ortaöğretim mezunları P94 puan "
            "türüyle başvurur. Bazı kurumlar KPSS yerine kendi yazılı ve sözlü "
            "sınavını yapar; hangi yolun geçerli olduğu her ilanın kendi metninde yazar."
        ),
        filtre=_tur("Memur"),
        grup="tur",
    ),
    Merkez(
        yol="/sozlesmeli-personel-alimlari/",
        ad="Sözleşmeli personel alımları",
        baslik="Sözleşmeli Personel Alımları {yil}: Güncel Kamu İlanları",
        h1="Sözleşmeli personel alımları",
        etiket="İLAN TÜRÜ",
        giris=(
            "Sözleşmeli personel ilanları çoğunlukla 657 sayılı Kanun'un 4/B maddesine "
            "göre yapılır ve yerleştirme genellikle KPSS puan sırasına göre olur. "
            "Bakanlık ve kurumların bilişim personeli alımları ise ayrı bir düzenlemeyle "
            "yapılır; bu ilanlarda mesleki deneyim, programlama bilgisi ve sözlü sınav "
            "öne çıkar."
        ),
        filtre=_tur("Sözleşmeli Personel"),
        grup="tur",
    ),
    Merkez(
        yol="/isci-alimlari/",
        ad="İşçi alımları",
        baslik="Kamu İşçi Alımları {yil}: Güncel İlanlar",
        h1="Kamu işçi alımları",
        etiket="İLAN TÜRÜ",
        giris=(
            "Kamu kurumlarının işçi alımları 4857 sayılı İş Kanunu'na tabidir. Sürekli "
            "ve geçici işçi kadroları bu başlıkta toplanır. Birçok işçi alımında KPSS "
            "şartı aranmaz; başvurular çoğu zaman kurumun kendi kanalından ya da İŞKUR "
            "üzerinden alınır ve bazı alımlarda noter kurası yapılır."
        ),
        filtre=_tur("İşçi"),
        grup="tur",
    ),
    Merkez(
        yol="/akademik-personel-alimlari/",
        ad="Akademik personel alımları",
        baslik="Akademik Personel Alımları {yil}: Üniversite İlanları",
        h1="Akademik personel alımları",
        etiket="İLAN TÜRÜ",
        giris=(
            "Üniversitelerin profesör, doçent ve doktor öğretim üyesi kadroları ile "
            "öğretim görevlisi ve araştırma görevlisi alımları. Öğretim elemanı "
            "ilanlarında genellikle ALES ve yabancı dil puanı istenir; öğretim üyesi "
            "ilanlarında ise alan şartı ve yayın koşulları belirleyicidir."
        ),
        filtre=_tur("Akademik Personel"),
        grup="tur",
    ),
    Merkez(
        yol="/askeri-personel-alimlari/",
        ad="Askeri personel alımları",
        baslik="Askeri Personel Alımları {yil}: Subay, Astsubay ve Uzman İlanları",
        h1="Askeri personel alımları",
        etiket="İLAN TÜRÜ",
        giris=(
            "Milli Savunma Bakanlığı, Jandarma Genel Komutanlığı ve Sahil Güvenlik "
            "Komutanlığı gibi kurumların subay, astsubay, uzman erbaş ve sözleşmeli "
            "er alımları. Bu ilanlarda yaş sınırı, sağlık şartları ve fiziki yeterlilik "
            "sınavı gibi ek koşullar sık görülür."
        ),
        filtre=_tur("Askeri Personel"),
        grup="tur",
    ),
    Merkez(
        yol="/lise-mezunu-kamu-ilanlari/",
        ad="Lise mezunu ilanları",
        baslik="Lise Mezunu Kamu İlanları {yil}: Güncel Alımlar",
        h1="Lise mezunu kamu ilanları",
        etiket="EĞİTİM",
        giris=(
            "En az lise ya da dengi okul mezuniyeti isteyen kamu ilanları. KPSS "
            "isteyen ilanlarda ortaöğretim mezunları için puan türü P94'tür. Lise "
            "mezunlarına açık kadroların önemli bir kısmı işçi ve sözleşmeli "
            "personel alımlarıdır."
        ),
        filtre=_egitim("lise"),
        grup="egitim",
    ),
    Merkez(
        yol="/onlisans-mezunu-kamu-ilanlari/",
        ad="Ön lisans mezunu ilanları",
        baslik="Ön Lisans Mezunu Kamu İlanları {yil}: Güncel Alımlar",
        h1="Ön lisans mezunu kamu ilanları",
        etiket="EĞİTİM",
        giris=(
            "İki yıllık ön lisans mezuniyeti isteyen kamu ilanları. KPSS isteyen "
            "ilanlarda ön lisans mezunları için puan türü P93'tür. Tekniker, sağlık "
            "teknikeri ve büro personeli gibi kadrolar bu grupta sık görülür."
        ),
        filtre=_egitim("onlisans"),
        grup="egitim",
    ),
    Merkez(
        yol="/lisans-mezunu-kamu-ilanlari/",
        ad="Lisans mezunu ilanları",
        baslik="Lisans Mezunu Kamu İlanları {yil}: Güncel Alımlar",
        h1="Lisans mezunu kamu ilanları",
        etiket="EĞİTİM",
        giris=(
            "Dört yıllık lisans mezuniyeti isteyen kamu ilanları. Genel kadrolarda "
            "çoğunlukla KPSS P3 puanı istenir; mühendis, uzman yardımcısı ve "
            "denetçi gibi kadrolarda ise bölüm şartı ve kuruma özel sınav öne çıkar."
        ),
        filtre=_egitim("lisans"),
        grup="egitim",
    ),
    Merkez(
        yol="/kpss-p3-ilanlari/",
        ad="KPSS P3 ilanları",
        baslik="KPSS P3 İlanları {yil}: P3 Puanıyla Başvurulan Kamu Alımları",
        h1="KPSS P3 puanıyla başvurulan ilanlar",
        etiket="PUAN TÜRÜ",
        giris=(
            "KPSS P3, lisans mezunlarının Genel Yetenek ve Genel Kültür testlerinden "
            "hesaplanan puan türüdür. Aşağıdaki ilanlar, ilan metninde P3 puanını "
            "şart olarak belirtir. Taban puanlar ilandan ilana ve yıldan yıla "
            "değiştiği için burada puan tahmini yapılmaz."
        ),
        filtre=_puan("P3"),
        grup="puan",
    ),
    Merkez(
        yol="/kpss-p93-ilanlari/",
        ad="KPSS P93 ilanları",
        baslik="KPSS P93 İlanları {yil}: Ön Lisans Mezunu Kamu Alımları",
        h1="KPSS P93 puanıyla başvurulan ilanlar",
        etiket="PUAN TÜRÜ",
        giris=(
            "KPSS P93, ön lisans mezunlarının puan türüdür. Aşağıdaki ilanlar, ilan "
            "metninde P93 puanını şart olarak belirtir. Bazı ilanlar birden fazla "
            "puan türü kabul eder; her kadro için hangi puanın geçerli olduğunu "
            "ilan sayfasında görebilirsin."
        ),
        filtre=_puan("P93"),
        grup="puan",
    ),
    Merkez(
        yol="/kpss-p94-ilanlari/",
        ad="KPSS P94 ilanları",
        baslik="KPSS P94 İlanları {yil}: Lise Mezunu Kamu Alımları",
        h1="KPSS P94 puanıyla başvurulan ilanlar",
        etiket="PUAN TÜRÜ",
        giris=(
            "KPSS P94, ortaöğretim (lise ve dengi) mezunlarının puan türüdür. "
            "Aşağıdaki ilanlar, ilan metninde P94 puanını şart olarak belirtir. "
            "Lise mezunlarına açık ilanların tamamı için lise mezunu ilanları "
            "sayfasına bakabilirsin."
        ),
        filtre=_puan("P94"),
        grup="puan",
    ),
    Merkez(
        yol="/son-basvurusu-yaklasan-ilanlar/",
        ad="Son başvurusu yaklaşanlar",
        baslik="Son Başvurusu Yaklaşan Kamu İlanları {yil}: Bu Hafta Bitenler",
        h1="Son başvurusu yaklaşan ilanlar",
        etiket="SON GÜNLER",
        giris=(
            f"Son başvuru tarihi önümüzdeki {YAKLASAN_GUN} gün içinde dolan açık kamu "
            "ilanları, en yakın tarihten başlayarak. Başvuru çoğu ilanda son gün mesai "
            "bitiminde ya da e-Devlet'te gece yarısı kapanır; saat bilgisi her ilanın "
            "resmî metninde yazar, son güne bırakmamak en güvenlisidir."
        ),
        filtre=_yaklasan,
        grup="ozel",
        en_az_indeks=1,
        siralama="bitis",
    ),
    Merkez(
        yol="/bu-hafta-eklenen-kamu-ilanlari/",
        ad="Bu hafta eklenenler",
        baslik="Bu Hafta Eklenen Kamu İlanları {yil}: Yeni Alımlar",
        h1="Bu hafta eklenen kamu ilanları",
        etiket="YENİ İLANLAR",
        giris=(
            f"Son {HAFTA_GUN} günde kamuilan.sbb.gov.tr'de yayımlanan ve Kamu'ya eklenen "
            "personel alım ilanları, en yeniden eskiye. Liste günde dört kez "
            "güncellenir; iptal ve düzeltme duyuruları listeye alınmaz."
        ),
        filtre=_bu_hafta,
        grup="ozel",
        en_az_indeks=1,
    ),
    Merkez(
        yol="/belediye-personel-alimlari/",
        ad="Belediye personel alımları",
        baslik="Belediye Personel Alımları {yil}: Güncel Belediye İlanları",
        h1="Belediye personel alımları",
        etiket="KURUM TÜRÜ",
        giris=(
            "İl, ilçe ve büyükşehir belediyelerinin memur, sözleşmeli personel ve işçi "
            "alımları. Belediye ilanlarında görev yeri o belediyenin sınırlarıdır; "
            "bazı ilanlarda o ilçede ikamet şartı ya da belediyenin kendi yaptığı "
            "sınav bulunur."
        ),
        filtre=_belediye,
        grup="ozel",
    ),
    Merkez(
        yol="/kpss-siz-kamu-ilanlari/",
        ad="KPSS puan türü belirtilmemiş ilanlar",
        baslik="KPSS'siz Kamu İlanları {yil}: Puan Türü İstenmeyen Alımlar",
        h1="KPSS puan türü belirtilmemiş kamu ilanları",
        etiket="PUAN TÜRÜ",
        giris=(
            "İlan metninden KPSS puan türü çıkarılamayan, akademik olmayan kamu "
            "ilanları. Bu ilanların bir kısmı kurumun kendi sınavıyla, mülakatla ya da "
            "kurayla personel alır. Akademik ilanlar ALES ile yapıldığı için bu "
            "listeye alınmaz."
        ),
        filtre=_kpss_siz,
        grup="ozel",
        uyari=(
            "KPSS şartı ilan metninde belirtilmemiş olabilir; bu liste KPSS'siz "
            "başvuru garantisi vermez. Başvurmadan önce resmî ilanı kontrol edin."
        ),
    ),
)


def sehir_merkezi(il: str) -> Merkez:
    return Merkez(
        yol=f"/sehir/{ascii_slug(il)}/",
        ad=f"{il} ilanları",
        baslik=f"{il} Kamu Personel Alımı " + "{yil}: Güncel İlanlar",
        h1=f"{il} kamu ilanları",
        etiket="ŞEHİR",
        giris=(
            f"Görev yeri {il} olan kamu personel alımları. Birkaç ilde birden kadro "
            f"açan ilanlar da bu listede yer alır; kadronun {il} için olup olmadığını "
            "ilanın kadro dağılımından ve resmî ilan metninden kontrol et. Türkiye "
            "genelinde çok sayıda ilde kadro açan ilanlar ayrıca listelenir."
        ),
        filtre=_il(il),
        grup="sehir",
        en_az_indeks=SEHIR_INDEKS_ESIGI,
        il=il,
        kalici=False,
    )


def kurum_merkezi(slug: str, ad: str, kalici: bool) -> Merkez:
    return Merkez(
        yol=f"/kurum/{slug}/",
        ad=ad,
        baslik=f"{ad} Personel Alımı " + "{yil}: Güncel İlanlar",
        h1=f"{ad} personel alımları",
        etiket="KURUM",
        giris=(
            f"{ad} tarafından kamuilan.sbb.gov.tr'de yayımlanan personel alım "
            "ilanları. Liste günde dört kez güncellenir; iptal ve düzeltme "
            "duyuruları ayrı ilan olarak gösterilmez."
        ),
        filtre=_kurum(slug),
        grup="kurum",
        en_az_indeks=KURUM_INDEKS_ESIGI,
        kalici=kalici,
    )


def sehir_merkezleri() -> tuple[Merkez, ...]:
    return tuple(sehir_merkezi(il) for il in ILLER)


@dataclass(frozen=True)
class MerkezVerisi:
    merkez: Merkez
    acik: tuple[Ilan, ...]
    kapanan: tuple[Ilan, ...] = ()

    @property
    def indekslenebilir(self) -> bool:
        return len(self.acik) >= self.merkez.en_az_indeks

    @property
    def sirali_acik(self) -> list[Ilan]:
        if self.merkez.siralama == "bitis":
            return sorted(self.acik, key=lambda i: (i.basvuru_bitis, i.id))
        return sorted(self.acik, key=lambda i: (i.eklenme_tarihi, i.id), reverse=True)
