"""Türkçe metin yardımcıları.

proje/instagram/metin.py'den kopyalandı; slug ve kalan gün yardımcıları eklendi.
Kaynak verideki kurum ve pozisyon alanları büyük harfli ilan başlıklarıdır
("860 GELİR UZMAN YARDIMCISI ALACAK"). Python'un str.lower/title işlemleri
Türkçe İ/ı çiftini bozduğu için dönüşümler burada elle yapılır.
"""

import re
import unicodedata
from datetime import date

_AYLAR = (
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
)
_BAGLACLAR = frozenset({"ve", "ile", "veya", "ya", "da", "de", "için"})

# Başlık sonundaki ilan kalıpları; uzun olan önce denenir.
_SON_EKLER = (
    "TEMİN EDECEKTİR",
    "SINAV ALIM İLANI",
    "ALIM İLANI",
    "ALINACAKTIR",
    "ALACAKTIR",
    "ALACAK",
    "ALIMI",
)
# Katlanmış (ASCII) biçimde aranır: "IPTAL", "DUZELTME" gibi yazımlar da yakalanır.
_IPTAL_KELIMELERI = ("iptal", "duzeltme")
_KATLAMA = str.maketrans("ıüşçğöâîû", "iuscgoaiu")
SLUG_EN_UZUN = 72


def tr_kucuk(metin: str) -> str:
    return metin.replace("I", "ı").replace("İ", "i").lower()


def katla(metin: str) -> str:
    """Karşılaştırma için Türkçe harfleri ASCII karşılıklarına indirger."""
    return tr_kucuk(metin).translate(_KATLAMA)


def tr_buyuk(metin: str) -> str:
    return metin.replace("i", "İ").replace("ı", "I").upper()


def tr_baslik(metin: str) -> str:
    """Her kelimenin ilk harfini büyütür; bağlaçlar (ilk kelime değilse) küçük kalır."""
    kucuk = tr_kucuk(" ".join(metin.split()))
    buyutulmus = re.sub(
        r"(^|[\s/(\-.])([^\W\d_])",
        lambda m: m.group(1) + tr_buyuk(m.group(2)),
        kucuk,
    )
    kelimeler = buyutulmus.split(" ")
    return " ".join(
        [kelimeler[0]]
        + [tr_kucuk(k) if tr_kucuk(k) in _BAGLACLAR else k for k in kelimeler[1:]]
    )


def iptal_veya_duzeltme_mi(metin: str | None) -> bool:
    katli = katla(metin or "")
    return any(kelime in katli for kelime in _IPTAL_KELIMELERI)


def pozisyon_temizle(
    pozisyon: str | None, kurum: str | None, kisi_sayisi: int | None = None
) -> str | None:
    """İlan başlığından gösterilecek pozisyon adını çıkarır.

    Baştaki kurum adı, kadro sayısı ve "2026 YILI" ile sondaki "ALACAK" gibi
    kalıplar atılır. Baştaki sayı kisi_sayisi biliniyorsa yalnızca onunla
    eşleşirse atılır ("112 ACİL ÇAĞRI..." korunur). Geriye bir şey kalmazsa None döner.
    """
    metin = " ".join((pozisyon or "").split()).rstrip(".").strip()
    kurum_temiz = " ".join((kurum or "").split())
    if kurum_temiz and metin.startswith(kurum_temiz + " "):
        metin = metin[len(kurum_temiz) + 1:]

    metin = re.sub(r"^\d{4}\s+YILI\s+", "", metin)
    bastaki = re.match(r"^(\d+)\s+", metin)
    if bastaki and (kisi_sayisi is None or int(bastaki.group(1)) == kisi_sayisi):
        metin = metin[bastaki.end():]
    for ek in _SON_EKLER:
        if metin == ek:
            metin = ""
            break
        if metin.endswith(" " + ek):
            metin = metin[: -len(ek) - 1]
            break

    metin = metin.strip()
    return tr_baslik(metin) if metin else None


def ascii_slug(metin: str) -> str:
    """Türkçe metni küçük harfli, tireli ASCII'ye çevirir ("Ağrı İli" -> "agri-ili")."""
    katli = katla(metin)
    ayrik = unicodedata.normalize("NFKD", katli)
    sade = "".join(h for h in ayrik if not unicodedata.combining(h))
    return re.sub(r"[^a-z0-9]+", "-", sade).strip("-")


def kisalt_slug(slug: str, en_uzun: int = SLUG_EN_UZUN) -> str:
    """Slug'ı kelime sınırında en_uzun karaktere indirir."""
    if len(slug) <= en_uzun:
        return slug
    kesik = slug[:en_uzun]
    if "-" in kesik and slug[en_uzun] != "-":
        kesik = kesik.rsplit("-", 1)[0]
    return kesik.strip("-")


def tarih_tr(gun: date, yil: bool = False) -> str:
    metin = f"{gun.day} {_AYLAR[gun.month - 1]}"
    return f"{metin} {gun.year}" if yil else metin


def sayi_tr(sayi: int) -> str:
    return f"{sayi:,}".replace(",", ".")


def kalan_gun_metni(bitis: date, bugun: date) -> str:
    kalan = (bitis - bugun).days
    if kalan < 0:
        return "Başvuru süresi doldu"
    if kalan == 0:
        return "Bugün son gün"
    if kalan == 1:
        return "Yarın son gün"
    return f"{kalan} gün kaldı"
