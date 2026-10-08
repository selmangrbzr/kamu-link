"""Rehber sayfalarının resmî kaynakları ve elle doğrulanmış olgu yapısı.

Rehberlerdeki her mevzuat, sınav ve kurum bilgisi bir Olgu'dur: metni, kaynağın
adı, ilgili madde ya da bölüm, kaynak adresi ve elle kontrol edildiği gün birlikte
tutulur. Kaynak adresleri yalnızca resmî alan adlarına (.gov.tr) gidebilir; testler
bunu denetler. Bir bilgi değişirse metni ve kontrol tarihini aynı yerde güncelle.
"""

from dataclasses import dataclass
from datetime import date
from urllib.parse import urlsplit

KONTROL_2026_10_08 = date(2026, 10, 8)
RESMI_SONEK = ".gov.tr"


@dataclass(frozen=True)
class Kaynak:
    ad: str  # Kaynaklar listesindeki tam ad
    kisa_ad: str  # Metin içi atıftaki ad: "657 sayılı Kanun"
    url: str
    kontrol_tarihi: date = KONTROL_2026_10_08


@dataclass(frozen=True)
class Olgu:
    """Resmî kaynaktan elle doğrulanmış tek cümlelik bilgi."""

    metin: str
    kaynak_adi: str
    kaynak_kisa_adi: str
    yer: str  # "md. 11", "madde 1.11" gibi; boş olabilir
    kaynak_url: str
    kontrol_tarihi: date

    @property
    def atif(self) -> str:
        return f"{self.kaynak_kisa_adi}, {self.yer}" if self.yer else self.kaynak_kisa_adi


def olgu(kaynak: Kaynak, yer: str, metin: str) -> Olgu:
    return Olgu(
        metin=metin,
        kaynak_adi=kaynak.ad,
        kaynak_kisa_adi=kaynak.kisa_ad,
        yer=yer,
        kaynak_url=kaynak.url,
        kontrol_tarihi=kaynak.kontrol_tarihi,
    )


def resmi_mi(url: str) -> bool:
    parca = urlsplit(url)
    sunucu = (parca.hostname or "").lower()
    return parca.scheme == "https" and (sunucu.endswith(RESMI_SONEK))


# --- Kaynaklar (hepsi 8 Ekim 2026'da okundu) -----------------------------------

DMK_657 = Kaynak(
    ad="657 sayılı Devlet Memurları Kanunu (güncel metin)",
    kisa_ad="657 sayılı Kanun",
    url="https://www.mevzuat.gov.tr/MevzuatMetin/1.5.657.pdf",
)
IS_KANUNU_4857 = Kaynak(
    ad="4857 sayılı İş Kanunu (güncel metin)",
    kisa_ad="4857 sayılı İş Kanunu",
    url="https://www.mevzuat.gov.tr/MevzuatMetin/1.5.4857.pdf",
)
GENEL_YONETMELIK = Kaynak(
    ad="Kamu Görevlerine İlk Defa Atanacaklar İçin Yapılacak Sınavlar Hakkında Genel Yönetmelik",
    kisa_ad="Genel Yönetmelik",
    url="https://www.mevzuat.gov.tr/MevzuatMetin/21.5.20023975.pdf",
)
ISCI_YONETMELIGI = Kaynak(
    ad="Kamu Kurum ve Kuruluşlarına İşçi Alınmasında Uygulanacak Usul ve Esaslar Hakkında Yönetmelik",
    kisa_ad="İşçi Alımı Yönetmeliği",
    url="https://www.mevzuat.gov.tr/MevzuatMetin/21.5.200915188.pdf",
)
SOZLESMELI_ESASLAR = Kaynak(
    ad="Sözleşmeli Personel Çalıştırılmasına İlişkin Esaslar",
    kisa_ad="Sözleşmeli Personel Esasları",
    url="https://www.mevzuat.gov.tr/MevzuatMetin/21.5.715754.pdf",
)
RESMI_GAZETE_CBK = Kaynak(
    ad="10 sayılı Resmî Gazete Hakkında Cumhurbaşkanlığı Kararnamesi",
    kisa_ad="10 sayılı CBK",
    url="https://www.mevzuat.gov.tr/MevzuatMetin/19.5.10.pdf",
)
OGRETIM_ELEMANI_YONETMELIGI = Kaynak(
    ad=(
        "Öğretim Üyesi Dışındaki Öğretim Elemanı Kadrolarına Yapılacak Atamalarda Uygulanacak "
        "Merkezi Sınav ile Giriş Sınavlarına İlişkin Usul ve Esaslar Hakkında Yönetmelik"
    ),
    kisa_ad="Öğretim Elemanı Yönetmeliği",
    url="https://www.mevzuat.gov.tr/MevzuatMetin/yonetmelik/7.5.28947.pdf",
)
KPSS_LISANS_2026 = Kaynak(
    ad="ÖSYM, 2026 KPSS Lisans Kılavuzu",
    kisa_ad="2026 KPSS Lisans Kılavuzu",
    url="https://dokuman.osym.gov.tr/pdfdokuman/2026/KPSS/LISANS/kilavuz_Ld01072026.pdf",
)
KPSS_ONLISANS_2026 = Kaynak(
    ad="ÖSYM, 2026 KPSS Ön Lisans Başvuru Kılavuzu",
    kisa_ad="2026 KPSS Ön Lisans Kılavuzu",
    url="https://dokuman.osym.gov.tr/web/2026/8/basvuru-kilavuzu-fqs59p-13083438.pdf",
)
KPSS_ORTAOGRETIM_2026 = Kaynak(
    ad="ÖSYM, 2026 KPSS Ortaöğretim Başvuru Kılavuzu",
    kisa_ad="2026 KPSS Ortaöğretim Kılavuzu",
    url="https://dokuman.osym.gov.tr/web/2026/8/basvuru-kilavuzu-ci4pae-27090228.pdf",
)
OSYM_MEB_AGS = Kaynak(
    ad="ÖSYM, MEB-AGS sınav grubu sayfası",
    kisa_ad="ÖSYM, MEB-AGS",
    url="https://www.osym.gov.tr/SinavGrubu/Index/15",
)
KARIYER_KAPISI_SSS = Kaynak(
    ad="Kariyer Kapısı, Sıkça Sorulan Sorular",
    kisa_ad="Kariyer Kapısı SSS",
    url="https://kariyerkapisi.gov.tr/sss",
)
KAMUILAN = Kaynak(
    ad="Kamu Personeli Alım İlanları (kamuilan.sbb.gov.tr)",
    kisa_ad="kamuilan.sbb.gov.tr",
    url="https://kamuilan.sbb.gov.tr/",
)
