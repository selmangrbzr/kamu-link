"""uygulama_verisi ve veri.sayfali_cek için birim testleri (ağ gerektirmez)."""

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from uretec import uygulama_verisi as uv
from uretec import veri
from uretec.veri import VeriHatasi, sayfali_cek

SIMDI = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)
ORNEKLER = json.loads(
    (Path(__file__).parent / "fixtures" / "alt_pozisyon_ornekleri.json").read_text(encoding="utf-8")
)


def satir(**alanlar):
    temel = {
        "id": "a" * 32,
        "kurum": "ÖRNEK KURUM",
        "pozisyon": "MEMUR ALIMI",
        "ilan_turu": "Memur",
        "detay_link": "https://kamuilan.sbb.gov.tr/x",
        "eklenme_tarihi": "2026-11-01T10:00:00+00:00",
        "basvuru_bitis": "2026-11-20",
        "kontenjan": [{"pozisyon": "Memur", "nitelik": "uzun metin " * 50}],
        "ozel_sartlar": "uzun",
        "basvuru_belgeleri": "uzun",
        "basvuru_yeri": "uzun",
        "kpss_puan_turu": None,
    }
    return {**temel, **alanlar}


# --- alt pozisyonlar: uygulamadaki Dart mantığıyla aynı örnekler -------------


@pytest.mark.parametrize("ornek", ORNEKLER, ids=[o["ad"] for o in ORNEKLER])
def test_alt_pozisyonlar_uygulamayla_ayni_sonucu_verir(ornek):
    assert uv.alt_pozisyonlar(ornek["kontenjan"]) == ornek["beklenen"]


def test_ortak_ornek_dosyasi_ana_repodakiyle_ayni():
    ana = Path(__file__).resolve().parents[2] / "proje" / "test" / "fixtures" / "alt_pozisyon_ornekleri.json"
    if not ana.exists():
        pytest.skip("Ana repo yanda değil (CI).")
    assert json.loads(ana.read_text(encoding="utf-8")) == ORNEKLER


# --- liste satırı ------------------------------------------------------------


def test_liste_satiri_agir_alanlari_tasimaz_ve_alt_pozisyon_ekler():
    sonuc = uv.liste_satiri(satir())

    assert sonuc["alt_pozisyonlar"] == ["Memur"]
    for agir in ("kontenjan", "ozel_sartlar", "basvuru_belgeleri", "basvuru_yeri"):
        assert agir not in sonuc


def test_liste_satiri_bos_alanlari_yazmaz():
    assert "kpss_puan_turu" not in uv.liste_satiri(satir())


def test_zorunlu_alani_eksik_satir_listeye_girmez():
    # Uygulamada Ilan.fromMap bu alanları `as String` ile okuyor; tek bozuk
    # satır tüm listeyi düşürürdü.
    for alan in uv.ZORUNLU_ALANLAR:
        assert uv.liste_satiri(satir(**{alan: None})) is None


# --- liste JSON'u -----------------------------------------------------------


def test_liste_json_semasi_sirasi_korur_ve_bozuk_satiri_atar():
    satirlar = [satir(id="c" * 32), satir(id="d" * 32, detay_link=None), satir(id="b" * 32)]

    veri_ = json.loads(uv.liste_json(satirlar, SIMDI))

    assert veri_["sema"] == uv.LISTE_SEMA == 1
    assert veri_["uretildi"] == SIMDI.isoformat()
    assert [s["id"] for s in veri_["ilanlar"]] == ["c" * 32, "b" * 32]


def test_liste_cek_aktif_ve_gecmisi_dogru_sorgular(monkeypatch):
    cagrilar = []

    def sahte(url, anahtar, parametreler, en_fazla=None):
        cagrilar.append((parametreler, en_fazla))
        return []

    monkeypatch.setattr(uv, "sayfali_cek", sahte)
    uv.liste_cek("https://ornek.supabase.co", "k", date(2026, 11, 3))

    (aktif, aktif_sinir), (gecmis, gecmis_sinir) = cagrilar
    assert aktif["or"] == "(basvuru_bitis.gte.2026-11-03,basvuru_bitis.is.null)"
    assert aktif["order"].startswith("eklenme_tarihi.desc")
    assert aktif_sinir is None
    assert gecmis["basvuru_bitis"] == "lt.2026-11-03"
    assert gecmis["order"].startswith("basvuru_bitis.desc")
    assert gecmis_sinir == uv.GECMIS_SINIRI
    assert "kontenjan" in aktif["select"].split(",")


# --- sürüm JSON'u -----------------------------------------------------------


def test_surum_json_api_adresi_ve_platformlar():
    veri_ = json.loads(uv.surum_json())

    assert veri_["sema"] == 1
    assert veri_["api"]["url"].startswith("https://")
    for platform in ("android", "ios"):
        assert isinstance(veri_[platform]["min_build"], int)
        assert veri_[platform]["magaza"].startswith("https://")


def test_yaz_aktif_gecmis_ve_surum_dosyalarini_uretir(tmp_path):
    uv.yaz(tmp_path, [satir(id="b" * 32)], [satir(id="c" * 32)], SIMDI)

    def oku(yol):
        return json.loads((tmp_path / yol).read_text(encoding="utf-8"))

    assert [s["id"] for s in oku(uv.LISTE_YOLU)["ilanlar"]] == ["b" * 32]
    assert [s["id"] for s in oku(uv.GECMIS_YOLU)["ilanlar"]] == ["c" * 32]
    assert oku(uv.SURUM_YOLU)["api"]


# --- veri.sayfali_cek -------------------------------------------------------


def _sahte_istek(monkeypatch, toplam, gercek=None):
    """Sunucu `toplam` satır bildirir ama yalnızca `gercek` kadarını verir."""
    gercek = toplam if gercek is None else gercek
    istenenler = []

    def sahte(url, anahtar):
        sorgu = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))
        limit, offset = int(sorgu["limit"]), int(sorgu["offset"])
        istenenler.append((limit, offset))
        adet = max(0, min(limit, gercek - offset))
        return [{"id": offset + i} for i in range(adet)], toplam

    monkeypatch.setattr(veri, "_istek", sahte)
    return istenenler


def test_sayfali_cek_tum_sayfalari_toplar(monkeypatch):
    istenenler = _sahte_istek(monkeypatch, toplam=2500)

    satirlar = sayfali_cek("https://ornek.supabase.co", "k", {"select": "id"})

    assert len(satirlar) == 2500
    assert istenenler == [(1000, 0), (1000, 1000), (1000, 2000)]


def test_sayfali_cek_en_fazla_ile_durur(monkeypatch):
    istenenler = _sahte_istek(monkeypatch, toplam=600)

    satirlar = sayfali_cek("https://ornek.supabase.co", "k", {"select": "id"}, en_fazla=200)

    assert len(satirlar) == 200
    assert istenenler == [(200, 0)]


def test_sayfali_cek_eksik_veride_hata_verir(monkeypatch):
    _sahte_istek(monkeypatch, toplam=500, gercek=300)

    with pytest.raises(VeriHatasi):
        sayfali_cek("https://ornek.supabase.co", "k", {"select": "id"})


def test_sayfali_cek_https_ister():
    with pytest.raises(VeriHatasi):
        sayfali_cek("http://ornek.supabase.co", "k", {"select": "id"})
