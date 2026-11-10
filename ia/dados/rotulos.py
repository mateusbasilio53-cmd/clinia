"""Rótulo de elegibilidade para avaliação e treino (nunca entrada da decisão).

Base 1: coluna elegibilidade_calculada (equipe da Bárbara).
Base 2: não tem rótulo. Provisório (decisão 6, opção C, 18/10/2026): as regras
aplicadas aos números da planilha + colunas gab_* (leitura humana do texto).
Quando o gabarito diz "incerto", o rótulo fica "Indefinido" — são os casos que
a equipe da Bárbara revisa na amostra (ia/saida/amostra_validacao.py).

[A VALIDAR] as colunas gab_* foram feitas por IA, não por profissional de saúde.
"""

from __future__ import annotations

import pandas as pd

from ia.entrada.planilha import COLUNAS_NUMERICAS
from ia.regras.criterios import ELEGIVEL, NAO_ELEGIVEL, avaliar
from ia.regras.protocolo import PROTOCOLO_DEMO, Protocolo

GABARITO = {"neoplasia_ativa": "gab_neoplasia", "gestacao": "gab_gestacao", "uso_metformina": "gab_metformina"}
ELEGIVEL_ROT, NAO_ELEGIVEL_ROT, INDEFINIDO = "Elegível", "Não elegível", "Indefinido"


def rotulo_por_gabarito(pacientes: pd.DataFrame, protocolo: Protocolo = PROTOCOLO_DEMO) -> pd.DataFrame:
    """id_paciente, rotulo (Elegível / Não elegível / Indefinido) e o motivo."""
    linhas = []
    for r in pacientes.to_dict("records"):
        p = {"diagnostico": r["diagnostico"], **{c: r[c] for c in COLUNAS_NUMERICAS}}
        for campo, col in GABARITO.items():
            p[f"{campo}_status"], p[f"{campo}_confianca"] = r[col], "alta"
        a = avaliar(p, protocolo)
        rotulo = {ELEGIVEL: ELEGIVEL_ROT, NAO_ELEGIVEL: NAO_ELEGIVEL_ROT}.get(a.resultado, INDEFINIDO)
        motivo = "; ".join(a.limitantes if a.resultado == NAO_ELEGIVEL else a.revisar)
        linhas.append({"id_paciente": r["id_paciente"], "rotulo": rotulo, "motivo_rotulo": motivo})
    return pd.DataFrame(linhas)


def rotulo(pacientes: pd.DataFrame) -> pd.DataFrame:
    """Rótulo de qualquer base: o da equipe clínica se existir; senão, o provisório pelo gabarito."""
    if "elegibilidade_calculada" in pacientes.columns:
        out = pacientes[["id_paciente", "elegibilidade_calculada"]].rename(columns={"elegibilidade_calculada": "rotulo"})
        return out.assign(motivo_rotulo="", origem_rotulo="equipe clínica")
    return rotulo_por_gabarito(pacientes).assign(origem_rotulo="provisório: regras + gab_*")
