"""Treina o RF só na metade de TREINO da base de 400 e mede UMA vez no TESTE e na Base 2.

    treino  -> dados/base_treino_400/CLINIA_base_treino_400_treino.xlsx (+ extracoes_treino.json)
    teste   -> mesma base, metade separada: parecida com o treino (nota otimista)
    Base 2  -> PAC-201–300, texto variado e escrito de outro jeito: o número que vale

Ajuste de hiperparâmetros, se precisar, só com validação cruzada DENTRO do treino.
Não mexa em nada olhando para o teste ou para a Base 2.

[A VALIDAR] o rótulo continua vindo da regra (Base 1 e sintéticos) ou é provisório (Base 2).

Uso:
    py -m ia.modelo.treino_teste
"""

from __future__ import annotations

import argparse

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score

from ia.modelo.random_forest import alvo, carregar_bases, features, novo_modelo, treinaveis

PASTA = "dados/base_treino_400"
TREINO = [(1, f"{PASTA}/CLINIA_base_treino_400_treino.xlsx", f"{PASTA}/extracoes_treino.json")]
TESTE = [(1, f"{PASTA}/CLINIA_base_treino_400_teste.xlsx", f"{PASTA}/extracoes_teste.json")]
BASE2 = [(2, "dados/pacientes_ficticios_PAC201-300.xlsx", "entregas/extracoes_base2.json")]


def medir(nome: str, df, modelo) -> list[str]:
    t = treinaveis(df).reset_index(drop=True)
    X, y = features(t), alvo(t)
    p = modelo.predict_proba(X)[:, 1]
    regra = (t["resultado"] == "ELEGÍVEL").astype(int).to_numpy()
    tn, fp, fn, tp = confusion_matrix(y, (p >= 0.5).astype(int), labels=[0, 1]).ravel()
    auc = roc_auc_score(y, p) if len(set(y)) > 1 else float("nan")
    linhas = [
        f"{nome}: {len(t)} pacientes ({len(df) - len(t)} Indefinidos fora) | elegíveis {y.sum()}",
        f"  RF:    AUC {auc:.3f} | acurácia {accuracy_score(y, p >= 0.5):.1%} | VP={tp} FN={fn} FP={fp} VN={tn}",
        f"  Regra: acurácia {accuracy_score(y, regra):.1%} | resultados {t['resultado'].value_counts().to_dict()}",
    ]
    if "origem_rotulo" in t.columns and t["origem_rotulo"].nunique() > 1:
        for origem, g in t.assign(p=p, y=y).groupby("origem_rotulo"):
            linhas.append(f"    {origem:18s} n={len(g):3d} acurácia RF {((g.p >= .5) == g.y).mean():.1%}")
    return linhas


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="Treina na metade de treino e mede no teste e na Base 2.").parse_args(argv)
    treino = treinaveis(carregar_bases(TREINO)).reset_index(drop=True)
    X, y = features(treino), alvo(treino)

    cv = StratifiedKFold(5, shuffle=True, random_state=42)
    auc_cv = cross_val_score(novo_modelo(), X, y, cv=cv, scoring="roc_auc")
    modelo = novo_modelo().fit(X, y)
    auc_treino = roc_auc_score(y, modelo.predict_proba(X)[:, 1])

    print(f"Treino: {len(treino)} pacientes | elegíveis {y.sum()}")
    print(f"  AUC no próprio treino {auc_treino:.3f} | validação cruzada dentro do treino "
          f"{np.mean(auc_cv):.3f} ± {np.std(auc_cv):.3f}\n")
    print("\n".join(medir("TESTE (metade separada)", carregar_bases(TESTE), modelo)), "\n")
    print("\n".join(medir("BASE 2 (texto variado, o número que vale)", carregar_bases(BASE2), modelo)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
