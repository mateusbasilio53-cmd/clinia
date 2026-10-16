"""Mede a extração contra um gabarito.

Gabarito da planilha (D14): as colunas escondidas do pipeline.
    - neoplasia_ativa / gestacao "Sim" -> esperado "afirmado";
      "Não" -> aceita "negado" ou "nao_mencionado" (a coluna não distingue os dois).
    - uso_metformina: "metformina" em `medicamentos` -> "afirmado"; senão "negado" ou "nao_mencionado".
Gabarito explícito (colunas gab_neoplasia, gab_gestacao, gab_metformina): o status exato.
Gabarito dos casos de teste: o status exato em `esperado`.

Uso:
    py -m ia.extracao.avaliar --extracoes saidas/.../extracoes_claude.json
    py -m ia.extracao.avaliar --extracoes saidas/.../extracoes_claude.json --casos prompts/casos_teste_v1.json
    py -m ia.extracao.avaliar --extracoes ... --conferencia 20   # gera CSV para conferência manual
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from ia.entrada.planilha import caminho_planilha, ler_planilha
from ia.extracao.schema import CAMPOS, ExtracaoPaciente

NAO = {"negado", "nao_mencionado"}


COLUNAS_GAB = {"neoplasia_ativa": "gab_neoplasia", "gestacao": "gab_gestacao", "uso_metformina": "gab_metformina"}


def gabarito_planilha(df: pd.DataFrame) -> dict[str, dict[str, set[str]]]:
    # Bases com gabarito explícito por status (ex.: PAC-201 a 300): comparação exata.
    if all(c in df.columns for c in COLUNAS_GAB.values()):
        return {
            str(linha["id_paciente"]): {campo: {str(linha[col]).strip()} for campo, col in COLUNAS_GAB.items()}
            for _, linha in df.iterrows()
        }
    gab = {}
    for linha in df.itertuples(index=False):
        tem_metformina = "metformina" in str(linha.medicamentos).casefold()
        gab[str(linha.id_paciente)] = {
            "neoplasia_ativa": {"afirmado"} if str(linha.neoplasia_ativa).strip() == "Sim" else NAO,
            "gestacao": {"afirmado"} if str(linha.gestacao).strip() == "Sim" else NAO,
            "uso_metformina": {"afirmado"} if tem_metformina else NAO,
        }
    return gab


def gabarito_casos(caminho: Path) -> dict[str, dict[str, set[str]]]:
    casos = json.loads(caminho.read_text(encoding="utf-8"))
    return {c["id"]: {campo: {status} for campo, status in c["esperado"].items()} for c in casos}


def avaliar(extracoes: list[ExtracaoPaciente], gabarito: dict) -> dict:
    por_campo = {}
    for campo in CAMPOS:
        acertos, erros = 0, []
        for item in extracoes:
            if item.id_paciente not in gabarito:
                continue
            obtido = getattr(item.campos, campo)
            esperado = gabarito[item.id_paciente][campo]
            if obtido.status in esperado:
                acertos += 1
            else:
                erros.append({
                    "id": item.id_paciente,
                    "esperado": "/".join(sorted(esperado)),
                    "obtido": obtido.status,
                    "evidencia": obtido.evidencia,
                })
        total = acertos + len(erros)
        por_campo[campo] = {
            "acertos": acertos,
            "total": total,
            "acuracia": round(acertos / total, 3) if total else None,
            "erros": erros,
        }
    return por_campo


def imprimir(resultado: dict) -> None:
    print(f"{'campo':<18}{'acertos':>10}{'acurácia':>11}")
    for campo, r in resultado.items():
        acc = f"{r['acuracia']:.1%}" if r["acuracia"] is not None else "-"
        print(f"{campo:<18}{r['acertos']:>5}/{r['total']:<4}{acc:>11}")
    for campo, r in resultado.items():
        for e in r["erros"]:
            print(f"  ERRO {campo} {e['id']}: esperado {e['esperado']}, obtido {e['obtido']} | evidência: {e['evidencia']}")


def planilha_conferencia(extracoes: list[ExtracaoPaciente], textos: dict[str, str], n: int, destino: Path) -> None:
    """CSV para conferência manual (Fase 3): uma linha por paciente, coluna 'conferido_ok' em branco."""
    amostra = random.Random(42).sample(extracoes, min(n, len(extracoes)))
    linhas = []
    for item in sorted(amostra, key=lambda i: i.id_paciente):
        linha = {"id_paciente": item.id_paciente, "anotacao_medica": textos.get(item.id_paciente, "")}
        for campo in CAMPOS:
            c = getattr(item.campos, campo)
            linha[f"{campo}_status"] = c.status
            linha[f"{campo}_evidencia"] = c.evidencia
            linha[f"{campo}_verificada"] = c.evidencia_verificada
            linha[f"{campo}_conferido_ok"] = ""
        linhas.append(linha)
    pd.DataFrame(linhas).to_csv(destino, index=False, encoding="utf-8-sig", sep=";")


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description="Mede a extração contra o gabarito.")
    p.add_argument("--extracoes", type=Path, required=True)
    p.add_argument("--planilha", help="caminho do .xlsx (padrão: CLINIA_PLANILHA)")
    p.add_argument("--casos", type=Path, help="usar o gabarito dos casos de teste")
    p.add_argument("--conferencia", type=int, metavar="N", help="gera CSV com N pacientes para conferência manual")
    p.add_argument("--json", type=Path, help="salva o resultado em JSON")
    args = p.parse_args(argv)

    extracoes = [ExtracaoPaciente.model_validate(i) for i in json.loads(args.extracoes.read_text(encoding="utf-8"))]
    if args.casos:
        gabarito = gabarito_casos(args.casos)
        textos = {c["id"]: c["anotacao_medica"] for c in json.loads(args.casos.read_text(encoding="utf-8"))}
    else:
        df = ler_planilha(caminho_planilha(args.planilha))
        gabarito = gabarito_planilha(df)
        textos = dict(zip(df["id_paciente"].astype(str), df["anotacao_medica"].astype(str)))

    resultado = avaliar(extracoes, gabarito)
    imprimir(resultado)

    if args.json:
        args.json.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.conferencia:
        destino = args.extracoes.with_name(args.extracoes.stem + "_conferencia.csv")
        planilha_conferencia(extracoes, textos, args.conferencia, destino)
        print(f"Gerado {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
