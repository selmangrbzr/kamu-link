"""Google bildirimi: sitemap'i Search Console'a gönderir, ilan sayfalarını Indexing API'ye bildirir.

Google IndexNow'u desteklemez ve sitemap "ping" adresi kaldırılmıştır; bu yüzden
yayından sonra iki resmî API kullanılır:
  1. Search Console API sitemaps.submit: sitemap'in yeniden okunmasını ister.
  2. Indexing API: yalnızca JobPosting içeren /ilan/ sayfaları için (API'nin izin
     verdiği kullanım). Yeni ya da lastmod'u değişen ilan URL_UPDATED, siteden
     kalkan ilan URL_DELETED olarak bildirilir.

Kimlik: GOOGLE_SERVICE_ACCOUNT_JSON (hizmet hesabı anahtarı, JSON metni). Hesap
Search Console mülkünde "Sahip" olmalıdır. Değişken yoksa adım atlanır.

Kullanım (site.yml, yayından sonra):
    python -m uretec.google_bildir --eski onceki-sitemap.xml --yeni _site/sitemap.xml [--kuru]
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote

from .indexnow import degisen_adresler, sitemap_oku

GSC_MULKU = "sc-domain:kamuuygulama.me"
SITEMAP_URL = "https://kamuuygulama.me/sitemap.xml"
INDEXING_UC_NOKTA = "https://indexing.googleapis.com/v3/urlNotifications:publish"
KAPSAMLAR = (
    "https://www.googleapis.com/auth/webmasters",
    "https://www.googleapis.com/auth/indexing",
)
ANAHTAR_DEGISKENI = "GOOGLE_SERVICE_ACCOUNT_JSON"
# Indexing API varsayılan kotası günde 200 yayın; site günde 4 kez üretilir.
CALISMA_BASI_SINIR = 50
ZAMAN_ASIMI = 30
_ILAN_YOLU = "/ilan/"

log = logging.getLogger("uretec.google_bildir")


class Oturum(Protocol):
    def request(self, method: str, url: str, json: Any = None, timeout: int | None = None) -> Any: ...


def sitemap_gonderim_adresi() -> str:
    return (
        "https://www.googleapis.com/webmasters/v3/sites/"
        f"{quote(GSC_MULKU, safe='')}/sitemaps/{quote(SITEMAP_URL, safe='')}"
    )


def bildirimler(eski: dict[str, str], yeni: dict[str, str], sinir: int) -> list[tuple[str, str]]:
    """İlan sayfaları için (adres, tür) listesi; sınır aşılırsa önce güncellemeler kalır."""
    guncellenen = [u for u in degisen_adresler(eski, yeni) if _ILAN_YOLU in u]
    kalkan = sorted(u for u in eski if _ILAN_YOLU in u and u not in yeni)
    liste = [(u, "URL_UPDATED") for u in guncellenen] + [(u, "URL_DELETED") for u in kalkan]
    return liste[:sinir]


def yayinla(oturum: Oturum, liste: list[tuple[str, str]]) -> list[int]:
    """Bildirimleri sırayla gönderir; kota dolunca (429) kalanları bırakır."""
    durumlar = []
    for adres, tur in liste:
        yanit = oturum.request(
            "POST", INDEXING_UC_NOKTA, json={"url": adres, "type": tur}, timeout=ZAMAN_ASIMI
        )
        durumlar.append(yanit.status_code)
        if yanit.status_code == 429:
            log.warning("Indexing API kotası doldu; %d bildirim gönderilmedi.", len(liste) - len(durumlar))
            break
    return durumlar


def sitemap_gonder(oturum: Oturum) -> int:
    return oturum.request("PUT", sitemap_gonderim_adresi(), timeout=ZAMAN_ASIMI).status_code


def _oturum(anahtar_json: str) -> Oturum:
    # Yalnızca gerçek gönderimde gerekir; site üretimi ve testler google-auth'a bağlı değil.
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2 import service_account

    kimlik = service_account.Credentials.from_service_account_info(
        json.loads(anahtar_json), scopes=list(KAPSAMLAR)
    )
    return AuthorizedSession(kimlik)


def _oku(yol: Path | None) -> dict[str, str]:
    if yol is None or not yol.exists() or yol.stat().st_size == 0:
        return {}
    return sitemap_oku(yol.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ayr = argparse.ArgumentParser(prog="uretec.google_bildir")
    ayr.add_argument("--eski", type=Path, help="Yayından önceki sitemap.xml (yoksa silme bildirilmez)")
    ayr.add_argument("--yeni", type=Path, required=True)
    ayr.add_argument("--kuru", action="store_true", help="Göndermeden yalnızca listele")
    args = ayr.parse_args(argv)

    anahtar = os.environ.get(ANAHTAR_DEGISKENI, "").strip()
    if not anahtar:
        log.warning("%s tanımlı değil; Google bildirimi atlandı.", ANAHTAR_DEGISKENI)
        return 0

    liste = bildirimler(_oku(args.eski), _oku(args.yeni), CALISMA_BASI_SINIR)
    log.info("%d ilan bildirimi hazır.", len(liste))
    if args.kuru:
        print("\n".join(f"{tur} {adres}" for adres, tur in liste))
        return 0

    oturum = _oturum(anahtar)
    sitemap_durumu = sitemap_gonder(oturum)
    log.info("Sitemap gönderimi: %s", sitemap_durumu)
    durumlar = yayinla(oturum, liste)
    log.info("Indexing API yanıtları: %s", durumlar)
    basarili = sitemap_durumu in (200, 204) and all(d == 200 for d in durumlar)
    return 0 if basarili else 1


if __name__ == "__main__":
    sys.exit(main())
