"""Google bildirimi: sitemap gönderimi ve ilan sayfaları için Indexing API (ağ gerektirmez)."""

import json

from uretec.google_bildir import (
    INDEXING_UC_NOKTA,
    SITEMAP_URL,
    bildirimler,
    main,
    sitemap_gonderim_adresi,
    yayinla,
)

ILAN_A = "https://kamuuygulama.me/ilan/a-11111111/"
ILAN_B = "https://kamuuygulama.me/ilan/b-22222222/"
ILAN_C = "https://kamuuygulama.me/ilan/c-33333333/"
MERKEZ = "https://kamuuygulama.me/memur-alimlari/"


class SahteYanit:
    def __init__(self, durum: int):
        self.status_code = durum


class SahteOturum:
    def __init__(self, durum: int = 200):
        self.istekler: list[tuple[str, str, dict | None]] = []
        self.durum = durum

    def request(self, yontem, adres, json=None, timeout=None):
        self.istekler.append((yontem, adres, json))
        return SahteYanit(self.durum)


def test_yalnizca_ilan_sayfalari_bildirilir():
    eski = {MERKEZ: "1"}
    yeni = {MERKEZ: "2", ILAN_A: "1"}
    assert bildirimler(eski, yeni, sinir=50) == [(ILAN_A, "URL_UPDATED")]


def test_yeni_degisen_ve_kalkan_ilanlar():
    eski = {ILAN_A: "1", ILAN_B: "1"}
    yeni = {ILAN_A: "2", ILAN_C: "1"}
    assert bildirimler(eski, yeni, sinir=50) == [
        (ILAN_A, "URL_UPDATED"),
        (ILAN_C, "URL_UPDATED"),
        (ILAN_B, "URL_DELETED"),
    ]


def test_degismeyen_ilan_bildirilmez():
    assert bildirimler({ILAN_A: "1"}, {ILAN_A: "1"}, sinir=50) == []


def test_sinir_asilinca_once_guncellemeler_kalir():
    eski = {ILAN_B: "1"}
    yeni = {ILAN_A: "1", ILAN_C: "1"}
    assert bildirimler(eski, yeni, sinir=2) == [(ILAN_A, "URL_UPDATED"), (ILAN_C, "URL_UPDATED")]


def test_onceki_sitemap_yoksa_silme_bildirilmez():
    assert bildirimler({}, {ILAN_A: "1"}, sinir=50) == [(ILAN_A, "URL_UPDATED")]


def test_sitemap_gonderim_adresi_kodlanir():
    adres = sitemap_gonderim_adresi()
    assert adres == (
        "https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Akamuuygulama.me"
        "/sitemaps/https%3A%2F%2Fkamuuygulama.me%2Fsitemap.xml"
    )
    assert SITEMAP_URL == "https://kamuuygulama.me/sitemap.xml"


def test_yayinla_istek_govdesi_ve_durumlar():
    oturum = SahteOturum()
    durumlar = yayinla(oturum, [(ILAN_A, "URL_UPDATED"), (ILAN_B, "URL_DELETED")])
    assert durumlar == [200, 200]
    assert oturum.istekler == [
        ("POST", INDEXING_UC_NOKTA, {"url": ILAN_A, "type": "URL_UPDATED"}),
        ("POST", INDEXING_UC_NOKTA, {"url": ILAN_B, "type": "URL_DELETED"}),
    ]


def test_kota_dolunca_kalanlar_gonderilmez():
    oturum = SahteOturum(durum=429)
    durumlar = yayinla(oturum, [(ILAN_A, "URL_UPDATED"), (ILAN_B, "URL_UPDATED")])
    assert durumlar == [429]
    assert len(oturum.istekler) == 1


def test_anahtar_yoksa_atlanir_ve_basarili_doner(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    yeni = tmp_path / "yeni.xml"
    yeni.write_text("<urlset></urlset>", encoding="utf-8")
    assert main(["--yeni", str(yeni)]) == 0


def test_kuru_calisma_ag_kullanmaz(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", json.dumps({"sahte": True}))
    eski = tmp_path / "eski.xml"
    yeni = tmp_path / "yeni.xml"
    eski.write_text("", encoding="utf-8")
    yeni.write_text(
        f"<urlset><url><loc>{ILAN_A}</loc><lastmod>1</lastmod></url></urlset>", encoding="utf-8"
    )
    assert main(["--eski", str(eski), "--yeni", str(yeni), "--kuru"]) == 0
    assert f"URL_UPDATED {ILAN_A}" in capsys.readouterr().out
