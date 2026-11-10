"""Divide uma base de pacientes em treino e teste (metade/metade), sempre da mesma forma.

Divisão estratificada: cada metade fica com a mesma proporção de
    origem (barbara_original / sintetica_ia) x grupo_simulacao x elegivel.
Assim treino e teste têm os mesmos tipos de caso (limítrofes, exclusões por texto...)
e o teste não fica "mais fácil" ou "mais difícil" por sorte.

A semente fixa (42) garante que rodar de novo gera exatamente a mesma divisão.
Regra: o TESTE só serve para medir no final. Não ajuste nada olhando para ele.

Uso:
    py -m ia.dados.dividir_treino_teste --entrada "C:/caminho/CLINIA_base_treino_400.xlsx"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ESTRATOS = ["origem", "grupo_simulacao", "elegivel"]
SEMENTE = 42


def dividir(df: pd.DataFrame, fracao_teste: float = 0.5, semente: int = SEMENTE) -> tuple[pd.DataFrame, pd.DataFrame]:
    colunas = [c for c in ESTRATOS if c in df.columns]
    estrato = df[colunas].astype(str).agg("|".join, axis=1) if colunas else None
    treino, teste = train_test_split(df, test_size=fracao_teste, stratify=estrato, random_state=semente)
    return treino.sort_index(), teste.sort_index()


def resumo(nome: str, df: pd.DataFrame) -> str:
    linhas = [f"{nome}: {len(df)} pacientes | elegíveis {int((df['elegivel'] == 1).sum())} "
              f"| não elegíveis {int((df['elegivel'] == 0).sum())}"]
    if "origem" in df.columns:
        linhas.append("  " + " | ".join(f"{k}: {v}" for k, v in df["origem"].value_counts().sort_index().items()))
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Divide a base em treino e teste (50/50 estratificado).")
    p.add_argument("--entrada", required=True)
    p.add_argument("--saida", default="dados/base_treino_400")
    args = p.parse_args(argv)

    entrada = Path(args.entrada)
    df = pd.read_excel(entrada)
    assert df["id_paciente"].is_unique, "id_paciente repetido na base"
    treino, teste = dividir(df)
    assert not set(treino["id_paciente"]) & set(teste["id_paciente"]), "paciente nos dois conjuntos"

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    treino.to_excel(saida / f"{entrada.stem}_treino.xlsx", index=False)
    teste.to_excel(saida / f"{entrada.stem}_teste.xlsx", index=False)
    print(resumo("Treino", treino))
    print(resumo("Teste ", teste))
    print(f"Salvo em {saida}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
