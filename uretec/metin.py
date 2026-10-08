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


_UNLULER = "aeıioöuü"
_KALIN = "aıouâ"
_SERT = "fstkçşhp"
_BILINEN_KISALTMALAR = frozenset({
    "İETT", "TÜİK", "TÜBİTAK", "BOTAŞ", "ASELSAN", "MEB", "DSİ", "MİT", "TOKİ", "ÖSYM", "YÖK",
    "İŞKUR", "AFAD", "TİKA", "DHMİ", "EÜAŞ", "TEİAŞ", "TEDAŞ", "MKE", "MTA", "TMO", "ÇAYKUR",
    "TÜRKSAT", "ASFAT", "SEDDK", "EPDK", "BDDK", "SPK", "SGK", "TRT", "PTT", "TCDD",
})


def _kisaltma_mi(kelime: str) -> bool:
    """"SGK", "TCDD" gibi tamamen büyük harfli kısaltmalar (2-5 harf, az ünlü)."""
    harfler = kelime.strip(".,()")
    if harfler in _BILINEN_KISALTMALAR:
        return True
    # Listede olmayanlarda yalnızca ünlüsüz yazımlar ("TCDD", "SGK"); "TÜRK", "VAN" gibi
    # kelimeler başlık düzenine geçer.
    if not (2 <= len(harfler) <= 5) or not harfler.isalpha() or harfler != tr_buyuk(harfler):
        return False
    return not any(h in "aeıioöuü" for h in tr_kucuk(harfler))


def kurum_basligi(metin: str) -> str:
    """Kurum adı başlık düzeni; "SGK", "TCDD", "TÜBİTAK" gibi kısaltmalar büyük harf kalır."""
    kaynak = " ".join(metin.split()).split(" ")
    hedef = tr_baslik(metin).split(" ")
    if len(kaynak) != len(hedef):
        return " ".join(hedef)
    return " ".join(k if _kisaltma_mi(k) else h for k, h in zip(kaynak, hedef))


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


# --- Türkçe ekler ve metin düzeltmeleri (sitede görünen cümleler için) ---------

# "3 Ağustos'ta", "8 Ekim'de" (bulunma) ve "22 Ekim'i" (belirtme) ekleri.
_AY_BULUNMA = dict(zip(_AYLAR, ("ta", "ta", "ta", "da", "ta", "da", "da", "ta", "de", "de", "da", "ta")))
_AY_BELIRTME = dict(zip(_AYLAR, ("ı", "ı", "ı", "ı", "ı", "ı", "u", "u", "ü", "i", "ı", "ı")))


# Sayıların okunuşuna göre bulunma eki: 3 "üç'te", 6 "altı'da", 20 "yirmi'de", 2026 "altı'da".
_BIRLER_EK = ("", "de", "de", "te", "te", "te", "da", "de", "de", "da")
_ONLAR_EK = ("", "da", "de", "da", "ta", "de", "ta", "te", "de", "da")


def sayi_bulunma_eki(sayi: int) -> str:
    if sayi % 10:
        return _BIRLER_EK[sayi % 10]
    if sayi % 100:
        return _ONLAR_EK[(sayi // 10) % 10]
    return "de" if sayi % 1000 == 0 else "de"  # "bin'de", "yüz'de"


def bulunma_eki(kelime: str) -> str:
    """Özel ada bulunma eki: "Ankara'da", "İzmir'de", "Kars'ta", "Uşak'ta"."""
    kucuk = tr_kucuk(kelime.strip())
    son_unlu = next((h for h in reversed(kucuk) if h in _UNLULER), "e")
    unlu = "a" if son_unlu in _KALIN else "e"
    sessiz = "t" if kucuk[-1:] in tuple(_SERT) else "d"
    return f"{kelime}'{sessiz}{unlu}"


def tarih_de(gun: date, yil: bool = False) -> str:
    """"3 Ağustos'ta", "8 Ekim'de"; yil=True ise "9 Ekim 2026'da"."""
    ay = _AYLAR[gun.month - 1]
    if yil:
        return f"{gun.day} {ay} {gun.year}'{sayi_bulunma_eki(gun.year)}"
    return f"{gun.day} {ay}'{_AY_BULUNMA[ay]}"


def tarih_i(gun: date) -> str:
    """"22 Ekim'i" (… kaçırma)."""
    ay = _AYLAR[gun.month - 1]
    return f"{gun.day} {ay}'{_AY_BELIRTME[ay]}"


def ayrilma_eki(ad: str) -> str:
    """Kurum adına ayrılma eki: "Gelir İdaresi Başkanlığı'ndan", "Rize Belediyesi'nden"."""
    kucuk = tr_kucuk(ad.strip())
    if not kucuk:
        return ad
    son_unlu = next((h for h in reversed(kucuk) if h in _UNLULER), "e")
    unlu = "a" if son_unlu in _KALIN else "e"
    if kucuk[-1] in _UNLULER:  # tamlama eki (-ı/-i/-u/-ü) sonrası kaynaştırma n
        return f"{ad}'nd{unlu}n"
    sessiz = "t" if kucuk[-1] in _SERT else "d"
    return f"{ad}'{sessiz}{unlu}n"


def tarih_araligi_tr(bas: date, bitis: date) -> str:
    """"20-22 Ekim 2026", "28 Eylül-12 Ekim 2026", "30 Aralık 2026-5 Ocak 2027"."""
    if bas.year != bitis.year:
        return f"{tarih_tr(bas, yil=True)}-{tarih_tr(bitis, yil=True)}"
    if bas.month != bitis.month:
        return f"{tarih_tr(bas)}-{tarih_tr(bitis, yil=True)}"
    return f"{bas.day}-{tarih_tr(bitis, yil=True)}"


def cumle_duzeni(metin: str) -> str:
    """Kelimelerin %60'ı büyük harfle başlıyorsa (Title Case) cümle düzenine çevirir."""
    kelimeler = [k for k in metin.split() if k[:1].isalpha()]
    if len(kelimeler) < 3:
        return metin
    buyuk = sum(1 for k in kelimeler if k[0].isupper())
    if buyuk / len(kelimeler) < 0.6:
        return metin
    kucuk = tr_kucuk(metin)
    return tr_buyuk(kucuk[:1]) + kucuk[1:]


def sart_parcalari(metin: str) -> list[str]:
    """Şart/belge metnini ";" ile maddelere böler; "≥" -> "en az", "≤" -> "en çok"."""
    duz = (
        metin.replace("≥", " en az ").replace(">=", " en az ")
        .replace("≤", " en çok ").replace("<=", " en çok ")
    )
    duz = re.sub(r"\s*;\s*", "; ", duz)
    duz = re.sub(r"(?<=\w)/(?=\w{3,})", " / ", duz) if re.search(r"\w{4,}/\w{4,}", duz) else duz
    duz = " ".join(duz.split())
    parcalar = [p.strip(" .") for p in duz.split(";") if p.strip(" .")]
    return [tr_buyuk(p[:1]) + p[1:] for p in parcalar]
