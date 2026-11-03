"""Mobil uygulamanın Supabase yerine sitemizden okuyacağı JSON dosyaları.

Neden: ilan listesi her açılışta Supabase'ten `select=*` ile (satır başına
~4 KB, çoğu `kontenjan`) çekiliyordu ve egress kotasının büyük kısmı buydu.
Liste site yayınıyla 6 saatte bir zaten değişiyor; statik dosya olarak GitHub
Pages'ten sunulması yeterli. Detay ekranı Supabase'ten okumaya devam eder.

Üç dosya:
- `veri/ilanlar-v1.json`: açık ilanların hafif listesi (her açılışta iner).
- `veri/gecmis-v1.json`: süresi geçen son 200 ilan; yalnızca o sıralama
  seçilince istenir, ana dosyayı şişirmesin diye ayrı.
  İkisinde de şemayı kıran değişiklikte yeni ad (`-v2`) kullanılır; eski
  sürümler eski dosyayı okumayı sürdürür.
- `uygulama/surum.json`: zorunlu güncelleme eşiği ve API adresi. Değerler
  ortamdan değil buradaki sabitlerden gelir — değiştirmek bilinçli bir commit
  olsun diye.
"""

import json
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .veri import sayfali_cek

LISTE_YOLU = "veri/ilanlar-v1.json"
GECMIS_YOLU = "veri/gecmis-v1.json"
SURUM_YOLU = "uygulama/surum.json"
LISTE_SEMA = 1
SURUM_SEMA = 1
# Uygulamadaki "süresi geçen ilanlar" sıralaması da 200'lük pencere kullanıyor.
GECMIS_SINIRI = 200

# Ilan.fromMap'in `as String` ile okuduğu alanlar (lib/features/ilanlar/data/ilan_model.dart).
ZORUNLU_ALANLAR = ("id", "kurum", "pozisyon", "ilan_turu", "detay_link", "eklenme_tarihi")
# Kart, süzgeç ve uygunluk hesabının kullandığı alanlar. kontenjan, ozel_sartlar,
# basvuru_belgeleri ve basvuru_yeri yalnızca detayda gerekiyor: bilerek yok.
LISTE_SUTUNLARI = ZORUNLU_ALANLAR + (
    "kisi_sayisi",
    "sehir",
    "sehirler",
    "cinsiyet",
    "basvuru_baslangic",
    "basvuru_bitis",
    "pdf_url",
    "kpss_puan_turu",
    "ales_min_puan",
    "ales_puan_turu",
    "yabanci_dil_min_puan",
    "egitim_seviyesi",
    "yas_siniri",
    "enrichment_durum",
)
# Sıra Dart'taki `altPozisyonlar` ile aynı olmalı.
ALT_POZISYON_ANAHTARLARI = ("pozisyon", "unvan", "kadro", "gorev", "görev")

# Uygulamanın bağlanacağı Supabase. Başka bir sunucuya (ör. kendi barındırdığımız
# Supabase) geçerken yalnızca bu değişir; uygulama izinli sunucu listesini kendisi denetler.
API_URL = "https://ohgyrhlngsxaenxsyyml.supabase.co"
# Bu build numarasının altındaki sürümler güncelleme ekranına yönlendirilir. 0 = kapalı.
MIN_BUILD = {"android": 0, "ios": 0}
MAGAZA = {
    "android": "https://play.google.com/store/apps/details?id=com.selman.memur_ilanlari",
    "ios": "https://apps.apple.com/tr/app/id6792290422",
}


def _metin(deger: Any) -> str | None:
    if deger is None:
        return None
    if isinstance(deger, bool):
        # Dart'ın toString()'i ile aynı yazım.
        metin = "true" if deger else "false"
    else:
        metin = str(deger).strip()
    return metin or None


def alt_pozisyonlar(kontenjan: Any) -> list[str]:
    """Dart'taki `Ilan.altPozisyonlar`'ın birebir karşılığı.

    Tekilleştirmede Dart'ın `toLowerCase()`'i 'İ'yi tek 'i'ye indiriyor;
    Python'un `lower()`'ı 'i̇' (iki karakter) üretir. Aynı sonuç için önce çevrilir.
    """
    gorulen: set[str] = set()
    sonuc: list[str] = []
    for satir in kontenjan if isinstance(kontenjan, list) else []:
        if not isinstance(satir, dict):
            continue
        metin = next(
            (m for m in (_metin(satir.get(a)) for a in ALT_POZISYON_ANAHTARLARI) if m), None
        )
        if metin is None:
            continue
        anahtar = metin.replace("İ", "i").lower()
        if anahtar not in gorulen:
            gorulen.add(anahtar)
            sonuc.append(metin)
    return sonuc


def liste_satiri(satir: dict[str, Any]) -> dict[str, Any] | None:
    """Uygulamaya gidecek hafif satır; zorunlu alanı eksikse None."""
    if any(not isinstance(satir.get(a), str) or not satir[a] for a in ZORUNLU_ALANLAR):
        return None
    hafif = {a: satir[a] for a in LISTE_SUTUNLARI if satir.get(a) is not None}
    hafif["alt_pozisyonlar"] = alt_pozisyonlar(satir.get("kontenjan"))
    return hafif


def _hafifler(satirlar: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [h for h in map(liste_satiri, satirlar) if h is not None]


def liste_json(satirlar: Iterable[dict], simdi: datetime) -> str:
    return json.dumps(
        {"sema": LISTE_SEMA, "uretildi": simdi.isoformat(), "ilanlar": _hafifler(satirlar)},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def surum_json() -> str:
    return json.dumps(
        {
            "sema": SURUM_SEMA,
            "api": {"url": API_URL},
            **{p: {"min_build": MIN_BUILD[p], "magaza": MAGAZA[p]} for p in ("android", "ios")},
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def liste_cek(supabase_url: str, anahtar: str, bugun: date) -> tuple[list[dict], list[dict]]:
    """(aktif, geçmiş). Aktif: süresi geçmemiş ya da tarihsiz, hepsi. Geçmiş: son 200."""
    secim = ",".join(LISTE_SUTUNLARI + ("kontenjan",))
    gun = bugun.isoformat()
    aktif = sayfali_cek(
        supabase_url,
        anahtar,
        {
            "select": secim,
            "or": f"(basvuru_bitis.gte.{gun},basvuru_bitis.is.null)",
            "order": "eklenme_tarihi.desc,id.asc",
        },
    )
    gecmis = sayfali_cek(
        supabase_url,
        anahtar,
        {"select": secim, "basvuru_bitis": f"lt.{gun}", "order": "basvuru_bitis.desc,id.asc"},
        en_fazla=GECMIS_SINIRI,
    )
    return aktif, gecmis


def yaz(cikti: Path, aktif: Iterable[dict], gecmis: Iterable[dict], simdi: datetime) -> None:
    dosyalar = (
        (LISTE_YOLU, liste_json(aktif, simdi)),
        (GECMIS_YOLU, liste_json(gecmis, simdi)),
        (SURUM_YOLU, surum_json()),
    )
    for yol, icerik in dosyalar:
        dosya = cikti / yol
        dosya.parent.mkdir(parents=True, exist_ok=True)
        dosya.write_text(icerik, encoding="utf-8")
