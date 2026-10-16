"""Valida a planilha de pacientes antes de qualquer processamento.

Uso:
    py -m ia.entrada.validar --planilha "C:\\caminho\\Base_ficticia_DM2_CLINIA.xlsx"
    (ou defina CLINIA_PLANILHA no .env e rode sem argumentos)

Sai com código 1 se houver erro bloqueante.
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from ia.entrada.planilha import caminho_planilha, estatisticas, ler_planilha, validar


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Valida a planilha de pacientes fictícios.")
    parser.add_argument("--planilha", help="caminho do .xlsx (padrão: CLINIA_PLANILHA)")
    args = parser.parse_args(argv)

    caminho = caminho_planilha(args.planilha)
    df = ler_planilha(caminho)
    relatorio = validar(df)

    print(f"Planilha: {caminho.name}\n")
    print(estatisticas(df))
    print()
    for erro in relatorio.erros:
        print(f"[ERRO] {erro}")
    for aviso in relatorio.avisos:
        print(f"[AVISO] {aviso}")
    print(f"\n{'OK' if relatorio.ok else 'FALHOU'}: {len(relatorio.erros)} erro(s), {len(relatorio.avisos)} aviso(s)")
    return 0 if relatorio.ok else 1


if __name__ == "__main__":
    sys.exit(main())
