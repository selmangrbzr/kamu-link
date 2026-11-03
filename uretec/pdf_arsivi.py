"""İlan PDF'lerini kamuuygulama.me/pdf/ altında yayınlanmak üzere toplar.

Neden: PDF'ler Supabase Storage'dan sunulduğunda her açılış Supabase'in egress
kotasından düşüyordu. Site yayınına konan kopya GitHub Pages'ten sunulur;
`pdf_url`'leri bu kopyaya çeviren adım ana repodaki enricher'dadır ve burada
yazılan manifest'i okur — yalnızca gerçekten yayınlanmış dosyaların adresi
değişir.

Her dosya Supabase'ten en fazla bir kez indirilir: önbellek (actions/cache)
build'ler arasında korunur, önbellek kaybolursa önce yayındaki siteden alınır.
"""

import json
import logging
import shutil
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from .model import _ID_KALIBI
from .veri import SAYFA_BOYUTU, VeriHatasi, _istek

log = logging.getLogger(__name__)

SITE_SUNUCUSU = "kamuuygulama.me"
PAGES_ONEKI = f"https://{SITE_SUNUCUSU}/pdf/"
STORAGE_YOLU = "/storage/v1/object/public/ilanlar-pdf/"
MANIFEST_ADI = "manifest.json"
# Storage bucket'ı 5 MB ile sınırlı; pay bırakıldı.
EN_FAZLA_BAYT = 10 * 1024 * 1024
# Pages yayını 1 GB ile sınırlı; yaklaşınca haber verilsin.
UYARI_TOPLAM_BAYT = 700 * 1024 * 1024
ZAMAN_ASIMI = 60

Indirici = Callable[[str], bytes | None]


class ArsivHatasi(RuntimeError):
    pass


def izinli_mi(adres: str, supabase_url: str) -> bool:
    """Yalnızca kendi sitemizden ve kendi Supabase projemizden, https ile."""
    parca = urllib.parse.urlsplit(adres)
    izinli = {SITE_SUNUCUSU, (urllib.parse.urlsplit(supabase_url).hostname or "").lower()}
    return parca.scheme == "https" and (parca.hostname or "").lower() in izinli


def pdf_mi(icerik: bytes | None) -> bool:
    return bool(icerik) and icerik.startswith(b"%PDF-")


def indir(adres: str) -> bytes | None:
    """Dosyayı indirir; yoksa, çok büyükse ya da ağ hatasında None."""
    try:
        with urllib.request.urlopen(adres, timeout=ZAMAN_ASIMI) as yanit:
            icerik = yanit.read(EN_FAZLA_BAYT + 1)
    except (urllib.error.URLError, OSError) as hata:
        log.info("PDF alınamadı (%s): %s", adres, hata)
        return None
    if len(icerik) > EN_FAZLA_BAYT:
        log.warning("PDF %d MB sınırını aşıyor, atlandı: %s", EN_FAZLA_BAYT // 2**20, adres)
        return None
    return icerik


def pdf_satirlari_cek(supabase_url: str, anahtar: str) -> list[dict[str, Any]]:
    """PDF adresi dolu tüm ilanlar (durumdan bağımsız: uygulama hepsini açıyor)."""
    taban = f"{supabase_url.rstrip('/')}/rest/v1/ilanlar"
    satirlar: list[dict[str, Any]] = []
    while True:
        sorgu = urllib.parse.urlencode(
            {
                "select": "id,pdf_url",
                "pdf_url": "not.is.null",
                "order": "id.asc",
                "limit": SAYFA_BOYUTU,
                "offset": len(satirlar),
            }
        )
        parca, toplam = _istek(f"{taban}?{sorgu}", anahtar)
        satirlar.extend(parca)
        if not parca or (toplam is not None and len(satirlar) >= toplam):
            break
        if toplam is None and len(parca) < SAYFA_BOYUTU:
            break
    if toplam is not None and len(satirlar) != toplam:
        raise VeriHatasi(f"Eksik PDF listesi: {len(satirlar)} satır, beklenen {toplam}.")
    return satirlar


def _kaynaklar(ilan_id: str, pdf_url: str, supabase_url: str) -> list[str]:
    """Denenecek adresler; Supabase en sona, çünkü egress oradan sayılıyor."""
    adresler = [
        f"{PAGES_ONEKI}{ilan_id}.pdf",
        pdf_url,
        f"{supabase_url.rstrip('/')}{STORAGE_YOLU}{ilan_id}.pdf",
    ]
    tekil = list(dict.fromkeys(adresler))
    return [a for a in tekil if izinli_mi(a, supabase_url)]


def _buda(onbellek: Path, tutulacak: set[str]) -> None:
    for dosya in onbellek.glob("*.pdf"):
        if dosya.stem not in tutulacak:
            dosya.unlink()


def arsivle(
    satirlar: Iterable[dict[str, Any]],
    *,
    onbellek: Path,
    cikti: Path,
    supabase_url: str,
    simdi: datetime,
    indirici: Indirici = indir,
) -> list[str]:
    """PDF'leri `cikti/pdf/` altına koyar, yayınlanan id'leri döndürür.

    Adresi zaten sitemizi gösteren bir dosya hiçbir kaynaktan alınamazsa
    ArsivHatasi: yayınlansaydı o ilanın PDF'i 404 verirdi, önceki yayın yerinde
    kalmalı. Adresi hâlâ Supabase'i gösteren dosya ise sessizce değil uyarıyla
    atlanır — uygulama oradan açmaya devam eder.
    """
    gecerli: dict[str, str] = {}
    for satir in satirlar:
        ilan_id = str(satir.get("id") or "").lower()
        pdf_url = satir.get("pdf_url")
        if _ID_KALIBI.fullmatch(ilan_id) and isinstance(pdf_url, str):
            gecerli[ilan_id] = pdf_url

    onbellek.mkdir(parents=True, exist_ok=True)
    _buda(onbellek, set(gecerli))
    hedef = cikti / "pdf"
    hedef.mkdir(parents=True, exist_ok=True)

    yayinlanan: list[str] = []
    indirilen = 0
    for ilan_id, pdf_url in sorted(gecerli.items()):
        dosya = onbellek / f"{ilan_id}.pdf"
        if not (dosya.exists() and pdf_mi(dosya.read_bytes()[:5])):
            icerik = next(
                (c for c in map(indirici, _kaynaklar(ilan_id, pdf_url, supabase_url)) if pdf_mi(c)),
                None,
            )
            if icerik is None:
                if pdf_url.startswith(PAGES_ONEKI):
                    raise ArsivHatasi(f"Yayındaki PDF hiçbir kaynaktan alınamadı: {ilan_id}")
                log.warning("PDF alınamadı, Supabase adresinde kalıyor: %s", ilan_id)
                continue
            dosya.write_bytes(icerik)
            indirilen += 1
        shutil.copy2(dosya, hedef / dosya.name)
        yayinlanan.append(ilan_id)

    toplam = sum(f.stat().st_size for f in hedef.glob("*.pdf"))
    if toplam > UYARI_TOPLAM_BAYT:
        log.warning("PDF arşivi %d MB; Pages 1 GB sınırına yaklaşıyor.", toplam // 2**20)
    (hedef / MANIFEST_ADI).write_text(
        json.dumps({"sema": 1, "uretildi": simdi.isoformat(), "dosyalar": yayinlanan}),
        encoding="utf-8",
    )
    log.info("%d PDF yayında (%d yeni indirildi, %d MB).", len(yayinlanan), indirilen, toplam // 2**20)
    return yayinlanan
