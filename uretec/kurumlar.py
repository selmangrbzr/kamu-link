"""Kurum adları: kalıcı kurum sayfaları, kurum anahtarı ve "X Belediyesi" varyantı.

Kaynak verideki kurum adı aynı kurum için farklı yazılabilir ("SAĞLIK BAKANLIĞI",
"T.C. SAĞLIK BAKANLIĞI PERSONEL GENEL MÜDÜRLÜĞÜ"). Kalıcı listedeki bir kurumun
slug'ıyla başlayan adlar o kurumun sayfasında toplanır.
"""

from .metin import ascii_slug, kisalt_slug, tr_baslik

# Açık ilanı olmasa da sayfası hep üretilen kurumlar (bakanlıklar ve büyük başkanlıklar).
KALICI_KURUMLAR: tuple[str, ...] = (
    "Adalet Bakanlığı",
    "Aile ve Sosyal Hizmetler Bakanlığı",
    "Çalışma ve Sosyal Güvenlik Bakanlığı",
    "Çevre, Şehircilik ve İklim Değişikliği Bakanlığı",
    "Dışişleri Bakanlığı",
    "Enerji ve Tabii Kaynaklar Bakanlığı",
    "Gençlik ve Spor Bakanlığı",
    "Hazine ve Maliye Bakanlığı",
    "İçişleri Bakanlığı",
    "Kültür ve Turizm Bakanlığı",
    "Milli Eğitim Bakanlığı",
    "Milli Savunma Bakanlığı",
    "Sağlık Bakanlığı",
    "Sanayi ve Teknoloji Bakanlığı",
    "Tarım ve Orman Bakanlığı",
    "Ticaret Bakanlığı",
    "Ulaştırma ve Altyapı Bakanlığı",
    "Gelir İdaresi Başkanlığı",
    "Sosyal Güvenlik Kurumu",
    "Diyanet İşleri Başkanlığı",
    "Emniyet Genel Müdürlüğü",
    "Jandarma Genel Komutanlığı",
    "Sahil Güvenlik Komutanlığı",
    "Göç İdaresi Başkanlığı",
    "Türkiye İstatistik Kurumu",
    "Tapu ve Kadastro Genel Müdürlüğü",
    "Devlet Su İşleri Genel Müdürlüğü",
    "Karayolları Genel Müdürlüğü",
    "Orman Genel Müdürlüğü",
    "Türkiye İş Kurumu",
    "Yargıtay Başkanlığı",
    "Danıştay Başkanlığı",
    "Sayıştay Başkanlığı",
    "Bankacılık Düzenleme ve Denetleme Kurumu",
    "Sermaye Piyasası Kurulu",
)
_BELEDIYE_EKI = "Belediye Başkanlığı"


def _sade_slug(kurum: str) -> str:
    slug = ascii_slug(kurum)
    return slug.removeprefix("t-c-")


_KALICI: tuple[tuple[str, str], ...] = tuple(
    sorted(((_sade_slug(ad), ad) for ad in KALICI_KURUMLAR), key=lambda x: -len(x[0]))
)


def kurum_anahtari(kurum: str) -> tuple[str, str, bool]:
    """(slug, gösterilecek ad, kalıcı mı) üçlüsü."""
    slug = _sade_slug(kurum)
    for kalici_slug, ad in _KALICI:
        if slug == kalici_slug or slug.startswith(kalici_slug + "-"):
            return kalici_slug, ad, True
    return kisalt_slug(slug), tr_baslik(kurum), False


def kalici_kurumlar() -> tuple[tuple[str, str], ...]:
    return tuple((slug, ad) for slug, ad in _KALICI)


def belediye_varyanti(kurum_adi: str) -> str | None:
    """"Mucur Belediye Başkanlığı" -> "Mucur Belediyesi"; belediye değilse None."""
    if not kurum_adi.endswith(_BELEDIYE_EKI):
        return None
    on = kurum_adi[: -len(_BELEDIYE_EKI)].rstrip()
    return f"{on} Belediyesi" if on else None
