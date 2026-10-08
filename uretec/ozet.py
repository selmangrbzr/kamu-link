"""Merkez sayfalarının veriye bağlı özet cümleleri ve meta açıklamaları.

Cümleler koşulludur: yalnızca verinin desteklediği bilgi yazılır (eşanlamlı
rotasyonu yok). Böylece şehir ve kurum sayfaları birbirinin kopyası olmaz.
"""

from collections import Counter
from datetime import datetime, timedelta

from .merkezler import MerkezVerisi
from .metin import ayrilma_eki, katla, sayi_tr, tarih_de, tarih_tr, tr_kucuk
from .model import Ilan

BUYUK_ALIM_ESIGI = 10
BASKIN_ORAN = 0.6
META_SINIRI = 158
LISE_YOLU = "/lise-mezunu-kamu-ilanlari/"


def _ve_ile(ogeler: list[str]) -> str:
    if len(ogeler) <= 1:
        return "".join(ogeler)
    return f"{', '.join(ogeler[:-1])} ve {ogeler[-1]}"


def _tur_adi(ilan: Ilan) -> str:
    return tr_kucuk(ilan.tur_etiketi)


def _en_yakin(ilanlar: tuple[Ilan, ...]) -> str:
    ilan = min(ilanlar, key=lambda i: (i.basvuru_bitis, i.id))
    return (
        f"En yakın son başvuru {tarih_de(ilan.basvuru_bitis, yil=True)}: "
        f"{ilan.kisa_kurum} {tr_kucuk(ilan.is_basligi)} alımı."
    )


def _en_buyuk(ilanlar: tuple[Ilan, ...]) -> str | None:
    ilan = max(ilanlar, key=lambda i: (i.kisi_sayisi or 0, i.id))
    if len(ilanlar) < 2 or (ilan.kisi_sayisi or 0) < BUYUK_ALIM_ESIGI:
        return None
    return (
        f"En çok kadro {ilan.kisa_kurum} {tr_kucuk(ilan.is_basligi)} ilanında: "
        f"{sayi_tr(ilan.kisi_sayisi or 0)}."
    )


def _tur_dagilimi(ilanlar: tuple[Ilan, ...]) -> str:
    sayim = sorted(Counter(_tur_adi(i) for i in ilanlar).items(), key=lambda x: (-x[1], x[0]))
    return "Açık ilanlar: " + ", ".join(f"{n} {tur}" for tur, n in sayim) + "."


def _yenilik(ilanlar: tuple[Ilan, ...], simdi: datetime) -> str:
    yeni = sum(1 for i in ilanlar if i.eklenme_tarihi >= simdi - timedelta(days=7))
    if yeni:
        return f"Son 7 günde {yeni} yeni ilan eklendi."
    en_son = max(i.eklenme_gunu for i in ilanlar)
    return f"En son ilan {tarih_de(en_son, yil=True)} eklendi."


def _kurumlar(ilanlar: tuple[Ilan, ...]) -> str:
    adlar = Counter(i.kurum_adi for i in ilanlar)
    if len(adlar) == 1:
        return f"Buradaki ilanların hepsi {ayrilma_eki(next(iter(adlar)))}."
    kisalar = [k for k, _ in Counter(i.kisa_kurum for i in ilanlar).most_common(3)]
    return f"En çok ilan veren kurumlar: {_ve_ile(kisalar)}."


def _basvuru_yolu(ilanlar: tuple[Ilan, ...]) -> str | None:
    yerler = [katla(i.basvuru_yeri) for i in ilanlar if i.basvuru_yeri]
    if not yerler:
        return None
    edevlet = sum(1 for y in yerler if "e-devlet" in y or "kariyer kapisi" in y)
    sahsen = sum(1 for y in yerler if "sahsen" in y or "posta" in y)
    if edevlet / len(yerler) >= BASKIN_ORAN:
        return "Başvurular çoğunlukla e-Devlet (Kariyer Kapısı) üzerinden alınıyor."
    if sahsen / len(yerler) >= BASKIN_ORAN:
        return "Başvurular çoğunlukla şahsen ya da posta ile yapılıyor."
    return None


def _baskin(ilanlar: tuple[Ilan, ...]) -> list[str]:
    cumleler = []
    tur, n = Counter(tr_kucuk(i.ilan_turu) for i in ilanlar).most_common(1)[0]
    if n / len(ilanlar) >= BASKIN_ORAN and len(ilanlar) > 1:
        cumleler.append(f"İlanların çoğu {tur} ilanı.")
    else:
        cumleler.append(_tur_dagilimi(ilanlar))
    egitimler = [i.egitim_seviyesi for i in ilanlar if i.egitim_seviyesi]
    if egitimler:
        egitim, m = Counter(egitimler).most_common(1)[0]
        if m / len(egitimler) >= BASKIN_ORAN:
            cumleler.append(f"Eğitim şartı çoğunlukla {tr_kucuk(egitim)}.")
    return cumleler


def _memur_yok(veri: MerkezVerisi) -> str | None:
    """Eğitim merkezinde açık memur ilanı yoksa bunu açıkça söyler (koşullu)."""
    if veri.merkez.grup != "egitim" or any(i.ilan_turu == "Memur" for i in veri.acik):
        return None
    turler = [t for t, _ in Counter(tr_kucuk(i.ilan_turu) for i in veri.acik).most_common()]
    return (
        f"Şu an {veri.merkez.ozne} memur ilanı yok; açık ilanların hepsi "
        f"{_ve_ile(turler)} alımı."
    )


def ozet_parcalari(veri: MerkezVerisi, simdi: datetime, mevcut_yollar: frozenset[str]) -> list[tuple[str, str | None]]:
    """(cümle, link) parçaları; link verilirse cümle o adrese bağlanır."""
    ilanlar = veri.acik
    if not ilanlar:
        return []
    grup = veri.merkez.grup
    parcalar: list[tuple[str, str | None]] = []
    if grup == "kurum":
        toplam = len(ilanlar) + veri.kapanan_sayisi
        en_son = max(i.eklenme_gunu for i in ilanlar)
        parcalar.append((f"Son 60 günde {toplam} ilan verdi, sonuncusu {tarih_de(en_son, yil=True)} eklendi.", None))
        parcalar += [(c, None) for c in _baskin(ilanlar)]
        yol = _basvuru_yolu(ilanlar)
        if yol:
            parcalar.append((yol, None))
    elif grup == "sehir":
        parcalar.append((_tur_dagilimi(ilanlar), None))
        parcalar.append((_kurumlar(ilanlar), None))
        buyuk = _en_buyuk(ilanlar)
        if buyuk:
            parcalar.append((buyuk, None))
        parcalar.append((_yenilik(ilanlar, simdi), None))
        lise = sum(1 for i in ilanlar if i.egitim_grubu == "lise")
        if lise:
            link = LISE_YOLU if LISE_YOLU in mevcut_yollar else None
            parcalar.append((f"Lise mezunlarına açık {lise} ilan var.", link))
        if veri.kapanan_sayisi:
            parcalar.append((f"Son 60 günde {veri.kapanan_sayisi} ilanın başvurusu kapandı.", None))
    else:
        if grup in ("egitim", "puan"):
            parcalar.append((_tur_dagilimi(ilanlar), None))
            memursuz = _memur_yok(veri)
            if memursuz:
                parcalar.append((memursuz, None))
        parcalar.append((_kurumlar(ilanlar), None))
        buyuk = _en_buyuk(ilanlar)
        if buyuk:
            parcalar.append((buyuk, None))
    if grup != "kurum":  # kurumda en yakın son başvuru manşette zaten yazıyor
        parcalar.append((_en_yakin(ilanlar), None))
    return parcalar


def merkez_aciklamasi(veri: MerkezVerisi) -> str:
    """Meta açıklama: "Memur alımları: 22 açık ilan, toplam 1.204 kadro. En yakın son başvuru 9 Ekim 2026 (SEDDK). En büyük alım: …"."""
    h1 = veri.merkez.h1
    if not veri.acik:
        return f"{h1}: şu an açık ilan yok. Yeni ilanlar yayımlandığında burada listelenir."
    kadro = sum(i.kisi_sayisi or 0 for i in veri.acik)
    kadro_metni = f", toplam {sayi_tr(kadro)} kadro" if kadro else ""
    yakin = min(veri.acik, key=lambda i: (i.basvuru_bitis, i.id))
    metin = (
        f"{h1}: {sayi_tr(len(veri.acik))} açık ilan{kadro_metni}. En yakın son başvuru "
        f"{tarih_tr(yakin.basvuru_bitis, yil=True)} ({yakin.kisa_kurum})."
    )
    buyuk = max(veri.acik, key=lambda i: (i.kisi_sayisi or 0, i.id))
    if buyuk.kisi_sayisi:
        ek = f" En büyük alım: {buyuk.kisa_kurum}, {sayi_tr(buyuk.kisi_sayisi)} kadro."
        # Meta açıklama sınırını aşarsa cümle yarıda kesilmez, hiç eklenmez.
        if len(metin + ek) <= META_SINIRI:
            metin += ek
    return metin
