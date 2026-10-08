"""Merkez (hub) sayfalarının tanımları.

Her merkezin elle yazılmış, özgün bir giriş metni vardır; sayfa ayrıca o anki
veriden özet cümleler üretir. Açık ilanı olmayan merkez hiç üretilmez.
"""

from collections.abc import Callable
from dataclasses import dataclass

from .metin import ascii_slug
from .model import ILLER, Ilan

# Bu sayının altında açık ilanı olan şehir sayfası üretilir ama noindex olur
# (ince içerik koruması); sitemap'e de girmez.
SEHIR_INDEKS_ESIGI = 3


@dataclass(frozen=True)
class Merkez:
    yol: str
    ad: str
    baslik: str
    h1: str
    etiket: str
    giris: str
    filtre: Callable[[Ilan], bool]
    grup: str
    en_az_indeks: int = 1
    il: str | None = None


def _tur(tur: str) -> Callable[[Ilan], bool]:
    return lambda ilan: ilan.ilan_turu == tur


def _egitim(grup: str) -> Callable[[Ilan], bool]:
    return lambda ilan: ilan.egitim_grubu == grup


def _puan(puan: str) -> Callable[[Ilan], bool]:
    return lambda ilan: puan in ilan.kpss_turleri


def _il(il: str) -> Callable[[Ilan], bool]:
    return lambda ilan: il in ilan.iller and not ilan.ulusal_mi


SABIT_MERKEZLER: tuple[Merkez, ...] = (
    Merkez(
        yol="/memur-alimlari/",
        ad="Memur alımları",
        baslik="Memur Alımları: Güncel Kamu Memur İlanları",
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
        baslik="Sözleşmeli Personel Alımları: Güncel Kamu İlanları",
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
        baslik="Kamu İşçi Alımları: Güncel İlanlar",
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
        baslik="Akademik Personel Alımları: Üniversite İlanları",
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
        baslik="Askeri Personel Alımları: Subay, Astsubay ve Uzman İlanları",
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
        baslik="Lise Mezunu Kamu İlanları: Güncel Alımlar",
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
        baslik="Ön Lisans Mezunu Kamu İlanları: Güncel Alımlar",
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
        baslik="Lisans Mezunu Kamu İlanları: Güncel Alımlar",
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
        baslik="KPSS P3 ile Başvurulabilen Kamu İlanları",
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
        baslik="KPSS P93 ile Başvurulabilen Kamu İlanları",
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
        baslik="KPSS P94 ile Başvurulabilen Kamu İlanları",
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
)


def sehir_merkezi(il: str) -> Merkez:
    return Merkez(
        yol=f"/sehir/{ascii_slug(il)}/",
        ad=f"{il} ilanları",
        baslik=f"{il} Kamu İlanları: Güncel Memur ve Personel Alımları",
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
    )


def tum_merkezler() -> tuple[Merkez, ...]:
    return SABIT_MERKEZLER + tuple(sehir_merkezi(il) for il in ILLER)
