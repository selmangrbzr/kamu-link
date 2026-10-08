"""İlan modeli ve saf filtre kuralları.

Supabase `ilanlar` satırını doğrulanmış, değişmez bir Ilan'a çevirir. Kaynak
veri LLM ile zenginleştirildiği için her alan şüpheyle okunur: boş metinler
None olur, kadro sayısı aralık dışındaysa yok sayılır, linkler yalnızca https.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit

from .kurumlar import belediye_varyanti, kurum_anahtari

from .metin import (
    ascii_slug,
    iptal_veya_duzeltme_mi,
    kisalt_slug,
    pozisyon_temizle,
    tr_baslik,
    tr_kucuk,
)

TR_SAAT = timezone(timedelta(hours=3))
SURESI_GECMIS_GUN = 60
EN_BUYUK_KADRO = 100_000
ID_ON_EK = 8
UZUN_ID_ON_EK = 16
_ID_KALIBI = re.compile(r"[0-9a-f]{16,64}")
# Resmî kaynak linkleri yalnızca bu sunuculara gidebilir (LLM verisi güvenilmez).
DETAY_SUNUCULARI = frozenset({"kamuilan.sbb.gov.tr"})
# Bundan fazla ilde kadro açan ilan "ulusal" sayılır; şehir sayfalarını tek başına doğurmaz.
ULUSAL_IL_ESIGI = 10

TUR_ETIKETI = {
    "Memur": "Memur",
    "Sözleşmeli Personel": "Sözleşmeli",
    "Akademik Personel": "Akademik",
    "İşçi": "İşçi",
    "Askeri Personel": "Askeri",
}
TUR_KODU = {
    "Memur": "memur",
    "Sözleşmeli Personel": "sozlesmeli",
    "Akademik Personel": "akademik",
    "İşçi": "isci",
    "Askeri Personel": "askeri",
}

# Liste satırlarında uzun resmî adların yerine bilinen kısaltmalar
# (proje/instagram/kartlar.py _KISA_ADLAR ile aynı).
_KISA_ADLAR = (
    ("bankacılık düzenleme ve denetleme kurumu", "BDDK"),
    ("sermaye piyasası kurulu", "SPK"),
    ("sigortacılık ve özel emeklilik düzenleme ve denetleme kurumu", "SEDDK"),
    ("enerji piyasası düzenleme kurumu", "EPDK"),
    ("bilgi teknolojileri ve iletişim kurumu", "BTK"),
    ("tasarruf mevduatı sigorta fonu", "TMSF"),
    ("sosyal güvenlik kurumu", "SGK"),
    ("istanbul elektrik tramvay ve tünel işletmeleri", "İETT"),
)

ILLER = (
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya", "Ankara",
    "Antalya", "Ardahan", "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman",
    "Bayburt", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa",
    "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce", "Edirne",
    "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun",
    "Gümüşhane", "Hakkâri", "Hatay", "Iğdır", "Isparta", "İstanbul", "İzmir",
    "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri",
    "Kilis", "Kırıkkale", "Kırklareli", "Kırşehir", "Kocaeli", "Konya",
    "Kütahya", "Malatya", "Manisa", "Mardin", "Mersin", "Muğla", "Muş",
    "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize", "Sakarya", "Samsun",
    "Siirt", "Sinop", "Sivas", "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat",
    "Trabzon", "Tunceli", "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak",
)
_IL_SLUG = {ascii_slug(il): il for il in ILLER}

_EGITIM_GRUBU = {
    "lise": "lise",
    "ortaöğretim": "lise",
    "ortaöğretim (lise ve dengi)": "lise",
    "önlisans": "onlisans",
    "ön lisans": "onlisans",
    "lisans": "lisans",
}
# Google JobPosting educationRequirements.credentialCategory değerleri.
EGITIM_KATEGORISI = {
    "lise": "high school",
    "ortaöğretim": "high school",
    "ortaöğretim (lise ve dengi)": "high school",
    "önlisans": "associate degree",
    "ön lisans": "associate degree",
    "lisans": "bachelor degree",
    "yüksek lisans": "postgraduate degree",
    "doktora": "postgraduate degree",
}


def _metin(deger: Any) -> str | None:
    if not isinstance(deger, str):
        return None
    temiz = " ".join(deger.split())
    return temiz or None


def _kadro(deger: Any) -> int | None:
    if isinstance(deger, bool) or not isinstance(deger, int):
        return None
    return deger if 0 < deger <= EN_BUYUK_KADRO else None


def _https(deger: Any, izinli: Callable[[str], bool]) -> str | None:
    metin = _metin(deger)
    if not metin or not metin.startswith("https://"):
        return None
    sunucu = (urlsplit(metin).hostname or "").lower()
    return metin if izinli(sunucu) else None


def _detay_sunucusu_mu(sunucu: str) -> bool:
    return sunucu in DETAY_SUNUCULARI


def _pdf_sunucusu_mu(sunucu: str) -> bool:
    return sunucu == "kamuilan.sbb.gov.tr" or sunucu.endswith(".supabase.co")


def _sayi(deger: Any) -> float | None:
    if isinstance(deger, bool) or not isinstance(deger, (int, float)):
        return None
    return float(deger) if 0 < deger <= 100 else None


def _tarih(deger: Any) -> date | None:
    if not isinstance(deger, str) or not deger:
        return None
    try:
        return date.fromisoformat(deger[:10])
    except ValueError:
        return None


def _zaman(deger: str) -> datetime:
    zaman = datetime.fromisoformat(deger)
    return zaman if zaman.tzinfo else zaman.replace(tzinfo=timezone.utc)


def il_adi(slug: str) -> str | None:
    return _IL_SLUG.get(slug)


def kisa_kurum_adi(kurum: str) -> str:
    kucuk = tr_kucuk(" ".join(kurum.split()))
    for onek, kisa in _KISA_ADLAR:
        if kucuk.startswith(onek):
            return kisa
    tam = tr_baslik(kurum)
    return belediye_varyanti(tam) or tam


@dataclass(frozen=True)
class KontenjanSatiri:
    pozisyon: str | None
    adet: int | None
    nitelik: str | None
    sehir: str | None = None

    @classmethod
    def from_satir(cls, satir: Any) -> "KontenjanSatiri | None":
        if not isinstance(satir, dict):
            return None
        pozisyon = _metin(satir.get("pozisyon"))
        nitelik = _metin(satir.get("nitelik")) or _metin(satir.get("mezuniyet_sarti"))
        adet = _kadro(satir.get("toplam"))
        if not (pozisyon or nitelik):
            return None
        return cls(pozisyon=pozisyon, adet=adet, nitelik=nitelik, sehir=_metin(satir.get("sehir")))


@dataclass(frozen=True)
class Ilan:
    id: str
    kurum: str
    pozisyon: str
    ilan_turu: str
    kisi_sayisi: int | None
    basvuru_baslangic: date | None
    basvuru_bitis: date
    eklenme_tarihi: datetime
    egitim_seviyesi: str | None
    kpss_puan_turu: str | None
    ales_puan_turu: str | None
    ales_min_puan: float | None
    yas_siniri: str | None
    cinsiyet: str | None
    sehirler: tuple[str, ...]
    basvuru_yeri: str | None
    basvuru_belgeleri: str | None
    ozel_sartlar: str | None
    pdf_url: str | None
    detay_link: str | None
    kontenjan: tuple[KontenjanSatiri, ...]
    enrichment_durum: str | None
    # Slug'daki id ön eki; yalnızca 8 karakterlik ön ek çakışırsa uzatılır.
    id_on_ek: int = ID_ON_EK

    @classmethod
    def from_satir(cls, satir: dict[str, Any]) -> "Ilan":
        if not isinstance(satir, dict):
            raise TypeError("Satır bir sözlük değil.")
        kimlik = str(satir["id"]).lower()
        if not _ID_KALIBI.fullmatch(kimlik):
            raise ValueError(f"Geçersiz ilan id'si: {kimlik[:40]!r}")
        sehirler = [s for s in (satir.get("sehirler") or []) if _metin(s)]
        if not sehirler and _metin(satir.get("sehir")):
            sehirler = [satir["sehir"]]
        kontenjan = (KontenjanSatiri.from_satir(k) for k in (satir.get("kontenjan") or []))
        return cls(
            id=kimlik,
            kurum=_metin(satir.get("kurum")) or "",
            pozisyon=_metin(satir.get("pozisyon")) or "",
            ilan_turu=_metin(satir.get("ilan_turu")) or "",
            kisi_sayisi=_kadro(satir.get("kisi_sayisi")),
            basvuru_baslangic=_tarih(satir.get("basvuru_baslangic")),
            basvuru_bitis=date.fromisoformat(satir["basvuru_bitis"][:10]),
            eklenme_tarihi=_zaman(satir["eklenme_tarihi"]),
            egitim_seviyesi=_metin(satir.get("egitim_seviyesi")),
            kpss_puan_turu=_metin(satir.get("kpss_puan_turu")),
            ales_puan_turu=_metin(satir.get("ales_puan_turu")),
            ales_min_puan=_sayi(satir.get("ales_min_puan")),
            yas_siniri=_metin(satir.get("yas_siniri")),
            cinsiyet=_metin(satir.get("cinsiyet")),
            sehirler=tuple(dict.fromkeys(" ".join(s.split()) for s in sehirler)),
            basvuru_yeri=_metin(satir.get("basvuru_yeri")),
            basvuru_belgeleri=_metin(satir.get("basvuru_belgeleri")),
            ozel_sartlar=_metin(satir.get("ozel_sartlar")),
            pdf_url=_https(satir.get("pdf_url"), _pdf_sunucusu_mu),
            detay_link=_https(satir.get("detay_link"), _detay_sunucusu_mu),
            kontenjan=tuple(k for k in kontenjan if k is not None),
            enrichment_durum=_metin(satir.get("enrichment_durum")),
        )

    @property
    def pozisyon_adi(self) -> str | None:
        ad = pozisyon_temizle(self.pozisyon, self.kurum, self.kisi_sayisi)
        # "5 ADET ÖĞRETİM ELEMANI" kalıbı; slug'a dokunulmaz (adres kalıcılığı).
        if ad and ad.startswith("Adet "):
            ad = ad[len("Adet "):] or None
        return ad

    @property
    def kurum_adi(self) -> str:
        return tr_baslik(self.kurum)

    @property
    def kisa_kurum(self) -> str:
        return kisa_kurum_adi(self.kurum)

    @property
    def belediye_adi(self) -> str | None:
        """Belediye ilanlarında aramaya uygun ad: "Mucur Belediyesi"."""
        return belediye_varyanti(self.kurum_adi)

    @property
    def kurum_slug(self) -> str:
        return kurum_anahtari(self.kurum)[0]

    @property
    def tur_etiketi(self) -> str:
        return TUR_ETIKETI.get(self.ilan_turu, self.ilan_turu or "Kamu")

    @property
    def tur_kodu(self) -> str:
        return TUR_KODU.get(self.ilan_turu, "diger")

    @property
    def is_basligi(self) -> str:
        """İşin adı: temiz pozisyon, yoksa ilan türü ("Sözleşmeli Personel")."""
        return self.pozisyon_adi or self.ilan_turu or "Kamu Personeli"

    @property
    def slug(self) -> str:
        """Kalıcı adres: yalnızca id'nin hash girdisi olan kurum ve pozisyondan türer.

        Zenginleştirmeyle değişebilen alanlar (kisi_sayisi vb.) kullanılmaz;
        böylece aynı ilanın adresi sonraki derlemelerde değişmez.
        """
        pozisyon = pozisyon_temizle(self.pozisyon, self.kurum) or "ilan"
        govde = kisalt_slug(ascii_slug(f"{self.kurum} {pozisyon}")) or "ilan"
        return f"{govde}-{self.id[:self.id_on_ek]}"

    @property
    def yol(self) -> str:
        return f"/ilan/{self.slug}/"

    @property
    def kpss_turleri(self) -> tuple[str, ...]:
        """"P3, P93" ve "KPSSP93" gibi yazımları ("P3", "P93") demetine çevirir."""
        bulunan = re.findall(r"P\d+", (self.kpss_puan_turu or "").upper())
        return tuple(dict.fromkeys(bulunan))

    @property
    def egitim_grubu(self) -> str | None:
        return _EGITIM_GRUBU.get(tr_kucuk(self.egitim_seviyesi or ""))

    @property
    def iller(self) -> tuple[str, ...]:
        """Şehirlerden 81 ilden biriyle eşleşenler (merkez sayfaları için)."""
        return tuple(il for il in self.sehirler if ascii_slug(il) in _IL_SLUG)

    @property
    def eklenme_gunu(self) -> date:
        return self.eklenme_tarihi.astimezone(TR_SAAT).date()

    def basvuru_basladi_mi(self, bugun: date) -> bool:
        return self.basvuru_baslangic is None or self.basvuru_baslangic <= bugun

    @property
    def ulusal_mi(self) -> bool:
        return len(self.iller) > ULUSAL_IL_ESIGI

    @property
    def yayin_tarihi(self) -> date:
        """İlanın yayımlandığı gün: sisteme eklenme ile başvuru başlangıcının erkeni."""
        eklenme = self.eklenme_gunu
        if self.basvuru_baslangic and self.basvuru_baslangic < eklenme:
            return self.basvuru_baslangic
        return eklenme

    @property
    def kontenjan_adetleri_tutarli(self) -> bool:
        """Kontenjan satır toplamı başlıktaki kadroyla çelişmiyorsa True."""
        adetler = [k.adet for k in self.kontenjan]
        if not adetler or any(a is None for a in adetler):
            return False
        return self.kisi_sayisi is None or sum(adetler) == self.kisi_sayisi


def yayinlanabilir_mi(ilan: Ilan) -> bool:
    """Zenginleştirmesi bitmiş, iptal/düzeltme olmayan gerçek ilan mı?"""
    return (
        ilan.enrichment_durum == "islendi"
        and bool(ilan.kurum)
        and bool(ilan.pozisyon)
        and not iptal_veya_duzeltme_mi(ilan.pozisyon)
        and not iptal_veya_duzeltme_mi(ilan.kurum)
    )


def acik_mi(ilan: Ilan, bugun: date) -> bool:
    return ilan.basvuru_bitis >= bugun


def sayfasi_olacak_mi(ilan: Ilan, bugun: date) -> bool:
    """Açık ilanlar ve son başvurusu son SURESI_GECMIS_GUN gün içinde dolanlar."""
    return yayinlanabilir_mi(ilan) and ilan.basvuru_bitis >= bugun - timedelta(
        days=SURESI_GECMIS_GUN
    )


def bugun_tr(simdi: datetime | None = None) -> date:
    return (simdi or datetime.now(timezone.utc)).astimezone(TR_SAAT).date()
