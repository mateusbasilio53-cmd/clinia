"""Margem até o limite: score explicável para ordenar DENTRO de ELEGÍVEL e NÃO ELEGÍVEL.

Para cada critério numérico do protocolo, a folga normalizada pela largura da faixa:
    faixa [min, max]  ->  min(v - min, max - v) / (max - min)
    só máximo         ->  (max - v) / max
A margem do paciente é a MENOR folga (o critério mais apertado).

    > 0  dentro de todas as faixas; quanto maior, mais "folgado"
    = 0  exatamente no limite
    < 0  fora de alguma faixa; quanto mais perto de 0, mais "quase elegível"

Por que existe: o rótulo de treino é a própria regra, então dentro de ELEGÍVEL e de
NÃO ELEGÍVEL o RF não tem o que aprender (todo mundo tem o mesmo rótulo). A margem
não depende de rótulo e se explica numa frase ("HbA1c 10,4%, a 0,1 do máximo").
Número não lido do texto é ignorado; sem nenhum número, a margem fica vazia (vai pro fim).
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import pandas as pd

from ia.regras.protocolo import PROTOCOLO_DEMO, Protocolo


def _faixas(protocolo: Protocolo) -> list[tuple[str, float | None, float | None]]:
    return [
        ("idade", protocolo.idade_min, protocolo.idade_max),
        ("hba1c", protocolo.hba1c_min, protocolo.hba1c_max),
        ("imc", protocolo.imc_min, protocolo.imc_max),
        ("creatinina", None, protocolo.creatinina_max),
        ("glicemia_jejum", None, protocolo.glicemia_jejum_max),
    ]


def folga(v: float, minimo: float | None, maximo: float | None) -> float | None:
    """Folga normalizada de um valor até o limite mais próximo (None se o critério não é usado)."""
    if minimo is not None and maximo is not None:
        return min(v - minimo, maximo - v) / (maximo - minimo)
    if maximo is not None:
        return (maximo - v) / maximo
    if minimo is not None:
        return (v - minimo) / minimo
    return None


def margem_paciente(p: Mapping, protocolo: Protocolo = PROTOCOLO_DEMO) -> float:
    folgas = []
    for nome, minimo, maximo in _faixas(protocolo):
        v = pd.to_numeric(p.get(nome), errors="coerce")
        if v is None or math.isnan(v):
            continue
        f = folga(float(v), minimo, maximo)
        if f is not None:
            folgas.append(f)
    return min(folgas) if folgas else math.nan


def margem(df: pd.DataFrame, protocolo: Protocolo = PROTOCOLO_DEMO) -> pd.Series:
    return pd.Series([margem_paciente(r, protocolo) for r in df.to_dict("records")], index=df.index, name="margem")
