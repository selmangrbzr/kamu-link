"""Supabase REST'ten ilan satırlarını çeker (anon anahtar, herkese açık okuma).

Anahtar yalnızca istek başlığında kullanılır; hiçbir yere yazılmaz ya da loglanmaz.
"""

import http.client
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Any

from .model import SURESI_GECMIS_GUN

log = logging.getLogger(__name__)

SAYFA_BOYUTU = 1000
DENEME = 3
ZAMAN_ASIMI = 60
SUTUNLAR = (
    "id,kurum,pozisyon,ilan_turu,kisi_sayisi,kontenjan,basvuru_baslangic,basvuru_bitis,"
    "eklenme_tarihi,egitim_seviyesi,kpss_puan_turu,ales_puan_turu,ales_min_puan,"
    "yas_siniri,cinsiyet,sehir,sehirler,basvuru_yeri,basvuru_belgeleri,ozel_sartlar,"
    "pdf_url,detay_link,enrichment_durum"
)


class VeriHatasi(RuntimeError):
    pass


def _toplam(content_range: str | None) -> int | None:
    """PostgREST "0-999/1234" başlığından toplam satır sayısı."""
    if not content_range or "/" not in content_range:
        return None
    toplam = content_range.rsplit("/", 1)[1]
    return int(toplam) if toplam.isdigit() else None


def _istek(url: str, anahtar: str) -> tuple[list[dict[str, Any]], int | None]:
    istek = urllib.request.Request(
        url,
        headers={"apikey": anahtar, "Authorization": f"Bearer {anahtar}", "Prefer": "count=exact"},
    )
    for deneme in range(1, DENEME + 1):
        try:
            with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI) as yanit:
                veri = json.load(yanit)
                toplam = _toplam(yanit.headers.get("Content-Range"))
            if not isinstance(veri, list):
                raise VeriHatasi("Supabase beklenmeyen yanıt döndürdü (liste değil).")
            return veri, toplam
        except urllib.error.HTTPError as hata:
            # 4xx (429 hariç) tekrar denemekle düzelmez.
            if hata.code < 500 and hata.code != 429:
                raise VeriHatasi(f"Supabase isteği reddedildi: HTTP {hata.code}") from hata
            son_hata: Exception = hata
        except (urllib.error.URLError, OSError, http.client.HTTPException, json.JSONDecodeError) as hata:
            son_hata = hata
        if deneme == DENEME:
            raise VeriHatasi(f"Supabase isteği başarısız: {son_hata}") from son_hata
        log.warning("Supabase isteği başarısız (deneme %d): %s", deneme, son_hata)
        time.sleep(2**deneme)
    raise VeriHatasi("Supabase isteği başarısız.")


def ilanlari_cek(supabase_url: str, anahtar: str, bugun: date) -> list[dict[str, Any]]:
    """Zenginleştirmesi bitmiş ve son başvurusu son 60 günden yeni ilanlar."""
    if not supabase_url.startswith("https://"):
        raise VeriHatasi("SUPABASE_URL https:// ile başlamalı.")
    sinir = (bugun - timedelta(days=SURESI_GECMIS_GUN)).isoformat()
    satirlar: list[dict[str, Any]] = []
    kaydirma = 0
    toplam: int | None = None
    while True:
        sorgu = urllib.parse.urlencode(
            {
                "select": SUTUNLAR,
                "enrichment_durum": "eq.islendi",
                "basvuru_bitis": f"gte.{sinir}",
                "order": "id.asc",
                "limit": SAYFA_BOYUTU,
                "offset": kaydirma,
            }
        )
        parca, toplam = _istek(f"{supabase_url.rstrip('/')}/rest/v1/ilanlar?{sorgu}", anahtar)
        satirlar.extend(parca)
        if not parca or (toplam is None and len(parca) < SAYFA_BOYUTU):
            break
        if toplam is not None and len(satirlar) >= toplam:
            break
        kaydirma += len(parca)
    # Sunucu max-rows ile sessizce kırparsa eksik veriyle yayın yapılmasın.
    if toplam is not None and len(satirlar) != toplam:
        raise VeriHatasi(f"Eksik veri: {len(satirlar)} satır çekildi, beklenen {toplam}.")
    return satirlar
