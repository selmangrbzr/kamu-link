"""pdf_arsivi için birim testleri (ağ gerektirmez; indirici sahte)."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from uretec.model import Ilan
from uretec.pdf_arsivi import (
    PAGES_ONEKI,
    ArsivHatasi,
    arsivle,
    izinli_mi,
)

SUPABASE = "https://ornek.supabase.co"
SIMDI = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)
ID_A = "a" * 32
ID_B = "b" * 32
PDF = b"%PDF-1.7 ornek icerik"


def storage(ilan_id: str) -> str:
    return f"{SUPABASE}/storage/v1/object/public/ilanlar-pdf/{ilan_id}.pdf"


class SahteIndirici:
    """Adres -> bayt eşlemesi; her çağrıyı kaydeder."""

    def __init__(self, yanitlar: dict[str, bytes] | None = None):
        self.yanitlar = yanitlar or {}
        self.cagrilar: list[str] = []

    def __call__(self, adres: str) -> bytes | None:
        self.cagrilar.append(adres)
        return self.yanitlar.get(adres)


def _arsivle(tmp_path: Path, satirlar, indirici):
    return arsivle(
        satirlar,
        onbellek=tmp_path / "onbellek",
        cikti=tmp_path / "site",
        supabase_url=SUPABASE,
        simdi=SIMDI,
        indirici=indirici,
    )


def test_onbellekte_olan_dosya_icin_hic_indirme_yapilmaz(tmp_path):
    (tmp_path / "onbellek").mkdir()
    (tmp_path / "onbellek" / f"{ID_A}.pdf").write_bytes(PDF)
    indirici = SahteIndirici()

    sonuc = _arsivle(tmp_path, [{"id": ID_A, "pdf_url": storage(ID_A)}], indirici)

    assert sonuc == [ID_A]
    assert indirici.cagrilar == []
    assert (tmp_path / "site" / "pdf" / f"{ID_A}.pdf").read_bytes() == PDF


def test_eksik_dosya_once_yayindaki_siteden_sonra_storagedan_indirilir(tmp_path):
    indirici = SahteIndirici({storage(ID_A): PDF})

    sonuc = _arsivle(tmp_path, [{"id": ID_A, "pdf_url": storage(ID_A)}], indirici)

    assert sonuc == [ID_A]
    assert indirici.cagrilar == [f"{PAGES_ONEKI}{ID_A}.pdf", storage(ID_A)]
    # Sonraki build için önbelleğe de yazılır.
    assert (tmp_path / "onbellek" / f"{ID_A}.pdf").read_bytes() == PDF


def test_yayindaki_siteden_alinabilen_dosya_icin_supabasee_gidilmez(tmp_path):
    indirici = SahteIndirici({f"{PAGES_ONEKI}{ID_A}.pdf": PDF})

    _arsivle(tmp_path, [{"id": ID_A, "pdf_url": storage(ID_A)}], indirici)

    assert indirici.cagrilar == [f"{PAGES_ONEKI}{ID_A}.pdf"]


def test_pdf_imzasi_olmayan_yanit_reddedilir_ve_siradaki_kaynak_denenir(tmp_path):
    indirici = SahteIndirici({f"{PAGES_ONEKI}{ID_A}.pdf": b"<html>404</html>", storage(ID_A): PDF})

    sonuc = _arsivle(tmp_path, [{"id": ID_A, "pdf_url": storage(ID_A)}], indirici)

    assert sonuc == [ID_A]
    assert (tmp_path / "site" / "pdf" / f"{ID_A}.pdf").read_bytes() == PDF


def test_bozuk_onbellek_dosyasi_yeniden_indirilir(tmp_path):
    (tmp_path / "onbellek").mkdir()
    (tmp_path / "onbellek" / f"{ID_A}.pdf").write_bytes(b"yarim")
    indirici = SahteIndirici({storage(ID_A): PDF})

    _arsivle(tmp_path, [{"id": ID_A, "pdf_url": storage(ID_A)}], indirici)

    assert (tmp_path / "onbellek" / f"{ID_A}.pdf").read_bytes() == PDF


def test_hicbir_kaynaktan_alinamayan_supabase_adresli_dosya_atlanir(tmp_path):
    indirici = SahteIndirici({storage(ID_B): PDF})
    satirlar = [{"id": ID_A, "pdf_url": storage(ID_A)}, {"id": ID_B, "pdf_url": storage(ID_B)}]

    sonuc = _arsivle(tmp_path, satirlar, indirici)

    # Adresi hâlâ Supabase'te: uygulama oradan açmaya devam eder, kırılma yok.
    assert sonuc == [ID_B]


def test_adresi_zaten_sitede_olan_dosya_alinamazsa_build_durur(tmp_path):
    # Yayınlansaydı bu ilanın PDF'i 404 verirdi; önceki yayın yerinde kalmalı.
    indirici = SahteIndirici()

    with pytest.raises(ArsivHatasi):
        _arsivle(tmp_path, [{"id": ID_A, "pdf_url": f"{PAGES_ONEKI}{ID_A}.pdf"}], indirici)


def test_adresi_sitede_olan_dosya_storagedan_kurtarilir(tmp_path):
    indirici = SahteIndirici({storage(ID_A): PDF})

    sonuc = _arsivle(tmp_path, [{"id": ID_A, "pdf_url": f"{PAGES_ONEKI}{ID_A}.pdf"}], indirici)

    assert sonuc == [ID_A]


def test_listede_olmayan_onbellek_dosyalari_budanir(tmp_path):
    (tmp_path / "onbellek").mkdir()
    (tmp_path / "onbellek" / f"{ID_B}.pdf").write_bytes(PDF)

    _arsivle(tmp_path, [], SahteIndirici())

    assert not (tmp_path / "onbellek" / f"{ID_B}.pdf").exists()


def test_gecersiz_id_dosya_yoluna_donusmez(tmp_path):
    indirici = SahteIndirici()

    sonuc = _arsivle(tmp_path, [{"id": "../../etc/passwd", "pdf_url": storage("x")}], indirici)

    assert sonuc == []
    assert indirici.cagrilar == []


def test_manifest_yayinlanan_idleri_sirali_listeler(tmp_path):
    indirici = SahteIndirici({storage(ID_A): PDF, storage(ID_B): PDF})
    satirlar = [{"id": ID_B, "pdf_url": storage(ID_B)}, {"id": ID_A, "pdf_url": storage(ID_A)}]

    _arsivle(tmp_path, satirlar, indirici)

    manifest = json.loads((tmp_path / "site" / "pdf" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest == {"sema": 1, "uretildi": SIMDI.isoformat(), "dosyalar": [ID_A, ID_B]}


@pytest.mark.parametrize(
    ("adres", "beklenen"),
    [
        (f"{PAGES_ONEKI}{ID_A}.pdf", True),
        (storage(ID_A), True),
        ("http://ornek.supabase.co/x.pdf", False),
        ("https://baska.supabase.co/x.pdf", False),
        ("https://kamuuygulama.me.kotu.com/x.pdf", False),
    ],
)
def test_yalnizca_iki_sunucudan_https_ile_indirilir(adres, beklenen):
    assert izinli_mi(adres, SUPABASE) is beklenen


def test_site_modeli_kamuuygulama_pdf_adresini_kabul_eder():
    # Adresler sitemize taşınınca ilan sayfasındaki "İlan metni (PDF)" düğmesi kaybolmamalı.
    temel = {
        "id": ID_A,
        "kurum": "ÖRNEK KURUM",
        "pozisyon": "ÖRNEK",
        "ilan_turu": "Sözleşmeli Personel",
        "basvuru_bitis": "2026-11-20",
        "eklenme_tarihi": "2026-10-03T12:26:41+00:00",
        "detay_link": "https://kamuilan.sbb.gov.tr/x",
        "pdf_url": f"{PAGES_ONEKI}{ID_A}.pdf",
    }

    assert Ilan.from_satir(temel).pdf_url == f"{PAGES_ONEKI}{ID_A}.pdf"
