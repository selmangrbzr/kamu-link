"""Komut satırı: python -m uretec [--cikti _site] [--json dosya] [--env-dosyasi .env]

Ortam değişkenleri: SUPABASE_URL, SUPABASE_ANON_KEY. --json verilirse Supabase
yerine yerel bir satır listesi (JSON dizi) kullanılır.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .derle import EN_AZ_ACIK_ILAN, KOK, DerlemeHatasi, derle, yaz
from .model import bugun_tr
from .veri import VeriHatasi, ilanlari_cek

log = logging.getLogger("uretec")


def _env_oku(dosya: Path) -> None:
    """KEY=VALUE satırlarını, ortamda zaten tanımlı değilse yükler."""
    for satir in dosya.read_text(encoding="utf-8").splitlines():
        if "=" not in satir or satir.lstrip().startswith("#"):
            continue
        ad, deger = satir.split("=", 1)
        os.environ.setdefault(ad.strip(), deger.strip().strip('"').strip("'"))


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ayr = argparse.ArgumentParser(prog="uretec", description="kamuuygulama.me statik site üreteci")
    ayr.add_argument("--cikti", type=Path, default=KOK / "_site")
    ayr.add_argument("--json", type=Path, help="Supabase yerine yerel satır dosyası")
    ayr.add_argument("--env-dosyasi", type=Path, help="SUPABASE_* değişkenlerini içeren .env")
    args = ayr.parse_args(argv)

    simdi = datetime.now(timezone.utc)
    try:
        if args.json:
            satirlar = json.loads(args.json.read_text(encoding="utf-8"))
            if not isinstance(satirlar, list):
                log.error("--json dosyası bir JSON dizisi olmalı.")
                return 2
        else:
            if args.env_dosyasi:
                _env_oku(args.env_dosyasi)
            url, anahtar = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY")
            if not url or not anahtar:
                log.error("SUPABASE_URL ve SUPABASE_ANON_KEY tanımlı olmalı.")
                return 2
            satirlar = ilanlari_cek(url, anahtar, bugun_tr(simdi))
        en_az = int(os.environ.get("URETEC_EN_AZ_ACIK_ILAN", EN_AZ_ACIK_ILAN))
        derleme = derle(satirlar, simdi, en_az_acik=en_az)
        yaz(derleme, args.cikti)
    except (DerlemeHatasi, VeriHatasi) as hata:
        log.error("%s", hata)
        return 1

    log.info(
        "%d satır, %d açık ilan, %d süresi dolmuş ilan sayfası, %d merkez (%d noindex), "
        "%d sitemap adresi -> %s",
        len(satirlar), derleme.acik, derleme.kapali, len(derleme.merkezler),
        len(derleme.noindex_merkezler), len(derleme.sitemap), args.cikti,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
