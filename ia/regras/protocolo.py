"""Protocolo do estudo: as colunas fixas da D6 (com hba1c_min e imc_min da D15).

Campo None = critério não usado.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Protocolo:
    nome: str
    idade_min: float | None = None
    idade_max: float | None = None
    hba1c_min: float | None = None
    hba1c_max: float | None = None
    imc_min: float | None = None
    imc_max: float | None = None
    creatinina_max: float | None = None
    glicemia_jejum_max: float | None = None
    permite_neoplasia_ativa: bool | None = None
    permite_gestacao: bool | None = None
    exige_metformina: bool | None = None
    diagnostico_exigido: str | None = None


# Aba Criterios da planilha da equipe da Bárbara (Base_ficticia_DM2_CLINIA.xlsx).
PROTOCOLO_DEMO = Protocolo(
    nome="Controle glicêmico em DM2 (estudo simulado)",
    idade_min=30,
    idade_max=70,
    hba1c_min=7.0,
    hba1c_max=10.5,
    imc_min=25,
    imc_max=45,
    creatinina_max=1.5,
    permite_neoplasia_ativa=False,
    permite_gestacao=False,
    exige_metformina=True,
    diagnostico_exigido="DM2",
)
