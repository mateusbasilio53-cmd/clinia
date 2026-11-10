"""Camada 2 (D8): ordenar a lista DENTRO de cada resultado, sem nunca mudar o resultado.

Como cada grupo é ordenado (análise de 10/11/2026):
    ELEGÍVEL e NÃO ELEGÍVEL -> margem até o limite (ia.modelo.margem).
        O rótulo de treino é a própria regra: dentro desses grupos todo mundo tem o
        mesmo rótulo, então o RF não tem o que aprender ali. A margem é explicável.
    REVISAR -> probabilidade_elegibilidade do Random Forest.
        É o único grupo em que o rótulo varia (a regra não decidiu), então é onde
        o RF pode separar quem tende a ser elegível.

A probabilidade do RF continua na planilha para todos (coluna informativa).

Usa as mesmas peças oficiais do pipeline, para o RF nunca treinar em cima de uma
decisão diferente da que vai para a planilha final:
    ia.dados.juntar.carregar  -> uma linha por paciente (números e leituras do texto)
    ia.regras.criterios.aplicar -> resultado das regras (Camada 1)
    ia.dados.rotulos.rotulo   -> rótulo para treino/avaliação (nunca entrada da decisão)

[A VALIDAR] ponto 6.4: o rótulo da Base 1 é a fórmula das regras e o da Base 2 é
provisório (regras + gab_* feitos por IA). Até a equipe da Bárbara validar a amostra,
os números deste módulo são exploratórios, não vão para slide.

Uso:
    py -m ia.modelo.random_forest
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from ia.dados.juntar import juntar
from ia.dados.rotulos import ELEGIVEL_ROT, INDEFINIDO, rotulo
from ia.entrada.planilha import COLUNAS_NUMERICAS, ler_planilha
from ia.extracao.schema import CAMPOS
from ia.modelo.margem import margem
from ia.regras.criterios import aplicar

BASES = [
    (1, "dados/Base_ficticia_DM2_CLINIA.xlsx", "entregas/extracoes_base1.json"),
    (2, "dados/pacientes_ficticios_PAC201-300.xlsx", "entregas/extracoes_base2.json"),
]
STATUS = ["afirmado", "negado", "nao_mencionado", "incerto"]
ORDEM_RESULTADO = {"ELEGÍVEL": 0, "REVISAR": 1, "NÃO ELEGÍVEL": 2}


def carregar_bases(bases=BASES) -> pd.DataFrame:
    """Junta as bases: ficha oficial + resultado das regras + rótulo (Indefinido fica de fora do treino)."""
    partes = []
    for n, planilha, extracoes in bases:
        pacientes = ler_planilha(planilha)
        df = aplicar(juntar(pacientes, json.loads(Path(extracoes).read_text(encoding="utf-8"))))
        df = df.merge(rotulo(pacientes), on="id_paciente", how="left", validate="one_to_one")
        partes.append(df.assign(base=n))
    return pd.concat(partes, ignore_index=True)


def features(df: pd.DataFrame) -> pd.DataFrame:
    """Só o que a CLINIA leu do texto. Nada de gabarito, rótulo ou resultado das regras.

    Número não lido do texto fica vazio (NaN, o RF do scikit-learn >= 1.4 aceita) e ganha
    uma coluna <nome>_ausente. Antes era -1, que a árvore confundia com "valor baixo"
    (idade -1 parecia abaixo do mínimo de 30).
    """
    X = pd.DataFrame(index=df.index)
    for c in COLUNAS_NUMERICAS:
        X[c] = pd.to_numeric(df[c], errors="coerce")
        X[f"{c}_ausente"] = X[c].isna().astype(int)
    X["sexo_F"] = (df["sexo"] == "F").astype(int)
    for campo in CAMPOS:
        for s in STATUS:
            X[f"{campo}={s}"] = (df[f"{campo}_status"] == s).astype(int)
        X[f"{campo}_conf_baixa"] = (df[f"{campo}_confianca"] == "baixa").astype(int)
    return X


def novo_modelo() -> RandomForestClassifier:
    return RandomForestClassifier(n_estimators=300, min_samples_leaf=3, class_weight="balanced", random_state=42)


def treinaveis(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["rotulo"].notna() & (df["rotulo"] != INDEFINIDO)]


def alvo(df: pd.DataFrame) -> np.ndarray:
    return (df["rotulo"] == ELEGIVEL_ROT).astype(int).to_numpy()


def ordenar(df: pd.DataFrame, modelo: RandomForestClassifier) -> pd.DataFrame:
    """Acrescenta probabilidade_elegibilidade e margem e ordena DENTRO de cada resultado (D8).

    ELEGÍVEL e NÃO ELEGÍVEL: maior margem primeiro (mais folgado / mais perto de ser elegível).
    REVISAR: maior probabilidade do RF primeiro. Margem vazia vai para o fim do grupo.
    """
    out = df.copy()
    out["probabilidade_elegibilidade"] = modelo.predict_proba(features(out))[:, 1]
    out["margem"] = margem(out)
    revisar = out["resultado"] == "REVISAR"
    out["criterio_ordem"] = np.where(revisar, "probabilidade RF", "margem até o limite")
    chave = out["margem"].where(~revisar, out["probabilidade_elegibilidade"])
    out = (out.assign(_grupo=out["resultado"].map(ORDEM_RESULTADO), _chave=chave)
              .sort_values(["_grupo", "_chave"], ascending=[True, False], na_position="last", kind="stable")
              .drop(columns=["_grupo", "_chave"]))
    out.insert(0, "posicao", range(1, len(out) + 1))
    return out.reset_index(drop=True)


def relatorio(df: pd.DataFrame) -> str:
    """Número principal: treina Base 1 -> testa Base 2 (bases diferentes, sem vazamento de template)."""
    t = treinaveis(df).reset_index(drop=True)
    X, y = features(t), alvo(t)
    linhas = [f"Pacientes no treino: {len(t)} (fora: {len(df) - len(t)} Indefinidos)  | elegíveis: {y.sum()}"]

    m1 = (t.base == 1).to_numpy()
    if m1.any() and (~m1).any() and len(set(y[~m1])) > 1:
        p2 = novo_modelo().fit(X[m1], y[m1]).predict_proba(X[~m1])[:, 1]
        tn, fp, fn, tp = confusion_matrix(y[~m1], (p2 >= 0.5).astype(int), labels=[0, 1]).ravel()
        linhas += [
            "",
            "PRINCIPAL — treina Base 1 -> testa Base 2 (texto variado, nunca visto)",
            f"  AUC {roc_auc_score(y[~m1], p2):.3f} | matriz (corte 0,5): VP={tp} FN={fn} FP={fp} VN={tn}",
        ]

    cv = StratifiedKFold(5, shuffle=True, random_state=42)
    proba = cross_val_predict(novo_modelo(), X, y, cv=cv, method="predict_proba")[:, 1]
    regra = (t["resultado"] == "ELEGÍVEL").astype(int)
    linhas += [
        "",
        "Referência — validação cruzada 5 dobras com as duas bases misturadas (otimista)",
        f"  AUC {roc_auc_score(y, proba):.3f} | acurácia RF {((proba >= .5) == y).mean():.1%} "
        f"| acurácia da regra sozinha {(regra == y).mean():.1%}",
        f"  Concordância regra x rótulo: {(regra == y).mean():.1%}  (perto de 100% = o RF só imita a regra)",
        "",
        "Ordenação dentro de cada grupo:",
    ]
    t = t.assign(prob=proba, margem=margem(t))
    for res in ORDEM_RESULTADO:
        d = t[t.resultado == res]
        if d.empty:
            continue
        yy = alvo(d)
        sinal = (f"AUC do RF dentro do grupo {roc_auc_score(yy, d.prob):.3f}" if len(set(yy)) > 1
                 else "rótulo igual para todos: o RF não tem o que ordenar -> usa margem")
        linhas.append(f"  {res:13s} n={len(d):3d}  elegíveis={yy.sum():3d}  margem {d.margem.min():+.2f} a "
                      f"{d.margem.max():+.2f}  | {sinal}")
    n_rev = int((t.resultado == "REVISAR").sum())
    if n_rev < 30:
        linhas.append(f"  Atenção: só {n_rev} pacientes REVISAR com rótulo. O número do RF ali ainda não é confiável.")
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="Random Forest da CLINIA (exploratório até validar o rótulo).").parse_args(argv)
    print(relatorio(carregar_bases()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
