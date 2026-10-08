"""IndexNow bildirimi: yalnızca yeni ya da lastmod'u değişen adresleri gönderir.

Kullanım (site.yml, yayından sonra):
    python -m uretec.indexnow --eski onceki-sitemap.xml --yeni _site/sitemap.xml [--kuru]

Anahtar herkese açık olacak şekilde tasarlanmıştır; doğrulama dosyası
uretec/statik/<anahtar>.txt olarak yayınlanır.
"""

import argparse
import json
import logging
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

INDEXNOW_ANAHTARI = "f224f60e1d7fd8c09de9d1b7963ddf67"
SUNUCU = "kamuuygulama.me"
UC_NOKTA = "https://api.indexnow.org/IndexNow"
PARCA_BOYUTU = 10_000
ZAMAN_ASIMI = 30
_GIRDI = re.compile(r"<url>\s*<loc>([^<]+)</loc>\s*(?:<lastmod>([^<]+)</lastmod>)?", re.S)

log = logging.getLogger("uretec.indexnow")


def sitemap_oku(xml: str) -> dict[str, str]:
    """Sitemap metninden {url: lastmod}. Biçim bizim ürettiğimiz sitemap'tir; regex yeterli."""
    return {loc.strip(): (lastmod or "").strip() for loc, lastmod in _GIRDI.findall(xml)}


def degisen_adresler(eski: dict[str, str], yeni: dict[str, str]) -> list[str]:
    """Yeni eklenen ya da lastmod'u değişen adresler (kaldırılanlar bildirilmez)."""
    return sorted(url for url, lastmod in yeni.items() if eski.get(url) != lastmod)


def istek_govdesi(adresler: list[str]) -> dict[str, object]:
    return {
        "host": SUNUCU,
        "key": INDEXNOW_ANAHTARI,
        "keyLocation": f"https://{SUNUCU}/{INDEXNOW_ANAHTARI}.txt",
        "urlList": adresler,
    }


def gonder(adresler: list[str], uc_nokta: str = UC_NOKTA) -> list[int]:
    """Adresleri 10.000'lik parçalar halinde POST eder; HTTP durum kodlarını döner."""
    durumlar = []
    for bas in range(0, len(adresler), PARCA_BOYUTU):
        govde = json.dumps(istek_govdesi(adresler[bas:bas + PARCA_BOYUTU])).encode("utf-8")
        istek = urllib.request.Request(
            uc_nokta, data=govde, method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI) as yanit:
                durumlar.append(yanit.status)
        except urllib.error.HTTPError as hata:
            durumlar.append(hata.code)
    return durumlar


def _oku(yol: Path | None) -> dict[str, str]:
    if yol is None or not yol.exists() or yol.stat().st_size == 0:
        return {}
    return sitemap_oku(yol.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ayr = argparse.ArgumentParser(prog="uretec.indexnow")
    ayr.add_argument("--eski", type=Path, help="Yayından önceki sitemap.xml (yoksa hepsi yeni sayılır)")
    ayr.add_argument("--yeni", type=Path, required=True)
    ayr.add_argument("--kuru", action="store_true", help="Göndermeden yalnızca listele")
    args = ayr.parse_args(argv)

    adresler = degisen_adresler(_oku(args.eski), _oku(args.yeni))
    log.info("%d adres değişti", len(adresler))
    if not adresler:
        return 0
    if args.kuru:
        print("\n".join(adresler))
        return 0
    durumlar = gonder(adresler)
    log.info("IndexNow yanıtları: %s", durumlar)
    # 200 ve 202 kabul; diğerleri iş akışını düşürmez ama loglanır.
    return 0 if all(d in (200, 202) for d in durumlar) else 1


if __name__ == "__main__":
    sys.exit(main())
