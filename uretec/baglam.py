"""Sayfa üretiminde paylaşılan derleme bağlamı."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .model import TR_SAAT
from .sablon import SayfaBasi, sayfa

YENI_SAAT = 48  # "Yeni" işareti: son 48 saatte eklenen ilanlar


@dataclass(frozen=True)
class Baglam:
    simdi: datetime
    bugun: date
    mevcut_yollar: frozenset[str]
    il_yollari: dict[str, str] = field(default_factory=dict)
    kurum_yollari: dict[str, str] = field(default_factory=dict)
    acik_sayisi: int = 0

    @property
    def yil(self) -> int:
        return self.simdi.astimezone(TR_SAAT).year

    @property
    def yeni_sinir(self) -> datetime:
        return self.simdi - timedelta(hours=YENI_SAAT)

    @property
    def saat(self) -> str:
        return f"{self.simdi.astimezone(TR_SAAT):%H:%M}"

    def sayfa(self, bas: SayfaBasi, govde: str, jsonld: tuple[dict, ...] = ()) -> str:
        return sayfa(
            bas, govde, self.simdi, self.mevcut_yollar, jsonld,
            kunye_alt=f"{self.acik_sayisi} açık ilan",
        )
