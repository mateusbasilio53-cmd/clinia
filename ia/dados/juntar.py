"""Pandas, parte 1: junta a planilha com as fichas do extracoes.json (1 linha por paciente).

Uso:
    py -m ia.dados.juntar --planilha dados/pacientes_ficticios_PAC201-300.xlsx --extracoes entregas/extracoes_base2.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ia.entrada.planilha import COLUNAS_GABARITO, COLUNAS_NUMERICAS, ler_planilha
from ia.extracao.schema import CAMPOS

# Da planilha só entram o id e o diagnóstico (estruturado no AGHUx). Os números
# vêm do texto (D27) e os critérios do texto também (D14).
COLUNAS_DA_PLANILHA = ["id_paciente", "diagnostico"]


def ficha(extracao: dict) -> dict:
    """Achata uma extração do contrato numa linha."""
    linha = {"id_paciente": extracao["id_paciente"]}
    lidos = extracao.get("dados_lidos") or {}
    for nome in [*COLUNAS_NUMERICAS, "sexo"]:
        lido = lidos.get(nome) or {}
        linha[nome] = lido.get("valor")
        linha[f"{nome}_evidencia"] = lido.get("evidencia")
    for campo in CAMPOS:
        c = extracao["campos"][campo]
        linha[f"{campo}_status"] = c["status"]
        linha[f"{campo}_confianca"] = c["confianca"]
        linha[f"{campo}_evidencia"] = c.get("evidencia")
        linha[f"{campo}_problemas"] = list(c.get("problemas") or [])
    return linha


def juntar(pacientes: pd.DataFrame, extracoes: list[dict]) -> pd.DataFrame:
    """Uma linha por paciente da planilha. Quem não tem extração fica com os campos vazios."""
    fichas = pd.DataFrame([ficha(e) for e in extracoes])
    base = pacientes[COLUNAS_DA_PLANILHA].merge(fichas, on="id_paciente", how="left", validate="one_to_one")
    assert not set(COLUNAS_GABARITO) & set(base.columns), "coluna de gabarito entrou na tabela (D14)"
    return base


def carregar(planilha: str | Path, extracoes: str | Path) -> pd.DataFrame:
    return juntar(ler_planilha(planilha), json.loads(Path(extracoes).read_text(encoding="utf-8")))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Junta planilha + extracoes.json numa tabela.")
    p.add_argument("--planilha", required=True)
    p.add_argument("--extracoes", required=True)
    args = p.parse_args(argv)
    df = carregar(args.planilha, args.extracoes)
    print(df.drop(columns=[c for c in df.columns if c.endswith(("_evidencia", "_problemas"))]).head(10).to_string())
    print(f"\n{len(df)} pacientes, {df['hba1c'].isna().sum()} sem HbA1c no texto")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
