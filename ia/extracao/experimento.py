"""Compara modelos de IA nas mesmas bases e guarda o histórico em avaliacao/historico.csv.

Uso:
    python -m ia.extracao.experimento --modelos qwen2.5:3b,qwen2.5:7b --conjunto prova
    python -m ia.extracao.experimento --modelos qwen2.5:7b --conjunto casos --prompt prompts/extrator_v2.md
    python -m ia.extracao.experimento --modelos qwen2.5:3b --conjunto prova --offline   # só o que já está no cache

Conjuntos (avaliacao/README.md explica cada um):
    prova   100 pacientes, texto variado — só para MEDIR (D25)
    casos   15 casos difíceis escritos à mão
    base1   200 pacientes da planilha original (fácil)
    estudo  base para ajustar prompt/regras (avaliacao/estudo/; ainda vazia)

Cada execução gera avaliacao/resultados/<data>_<conjunto>_<modelo>.json e uma linha no histórico.
O cache é por modelo + prompt + texto: rodar de novo não repete o trabalho.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from ia.entrada.planilha import ler_planilha, textos_para_extracao
from ia.extracao.avaliar import avaliar, avaliar_dados, gabarito_casos, gabarito_planilha
from ia.extracao.cache import CacheExtracoes
from ia.extracao.extrator import PROMPT_PADRAO_OLLAMA, carregar_casos, carregar_prompt, executar
from ia.extracao.provedores import ProvedorOllama
from ia.extracao.schema import CAMPOS

PASTA = Path("avaliacao")
CONJUNTOS = {
    "prova": ("planilha", Path("dados/pacientes_ficticios_PAC201-300.xlsx")),
    "casos": ("casos", Path("prompts/casos_teste_v1.json")),
    "base1": ("planilha", Path("dados/Base_ficticia_DM2_CLINIA.xlsx")),
    "estudo": ("planilha", Path("avaliacao/estudo/base_estudo.xlsx")),
}
COLUNAS_HISTORICO = [
    "data", "conjunto", "modelo", "prompt", "dupla_checagem", "pacientes", "segundos", "s_por_paciente",
    *[f"acerto_{c}" for c in CAMPOS], "erros_perigosos", "pacientes_revisar", "falhas",
]


def carregar_conjunto(nome: str):
    tipo, caminho = CONJUNTOS[nome]
    if not caminho.exists():
        raise SystemExit(f"Conjunto '{nome}' não encontrado em {caminho}. Veja avaliacao/README.md.")
    if tipo == "casos":
        return carregar_casos(caminho), gabarito_casos(caminho), None
    df = ler_planilha(caminho)
    return textos_para_extracao(df), gabarito_planilha(df), df


def rodar(modelo: str, conjunto: str, prompt: Path, dupla: bool, offline: bool) -> dict:
    from ia.extracao.relatorio import contar_perigosos  # import tardio: evita ciclo

    itens, gab, df = carregar_conjunto(conjunto)
    texto_prompt, versao = carregar_prompt(prompt)
    provedor = ProvedorOllama(modelo, texto_prompt)
    resultado, resumo = executar(itens, provedor, versao, CacheExtracoes(), offline=offline, dupla_checagem=dupla)

    acertos = avaliar(resultado, gab)
    perigosos = sum(contar_perigosos(resultado, gab, c) for c in CAMPOS)
    revisar = sum(
        any(getattr(i.campos, c).status == "incerto" or getattr(i.campos, c).confianca == "baixa" for c in CAMPOS)
        for i in resultado
    )
    registro = {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "conjunto": conjunto,
        "modelo": modelo,
        "prompt": versao,
        "dupla_checagem": dupla,
        "pacientes": len(itens),
        "segundos": resumo["segundos"],
        "s_por_paciente": round(resumo["segundos"] / max(resumo["chamadas_api"], 1), 1) if resumo["chamadas_api"] else "cache",
        **{f"acerto_{c}": acertos[c]["acuracia"] for c in CAMPOS},
        "erros_perigosos": perigosos,
        "pacientes_revisar": revisar,
        "falhas": len(resumo["falhas"]),
    }
    detalhe = {"registro": registro, "acertos": acertos, "resumo_execucao": resumo}
    if df is not None:
        detalhe["dados_lidos"] = avaliar_dados(resultado, df)

    pasta = PASTA / "resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"{datetime.now():%Y-%m-%d_%H%M}_{conjunto}_{modelo.replace(':', '-')}{'' if dupla else '_sem-dupla'}.json"
    (pasta / nome).write_text(json.dumps(detalhe, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    historico = PASTA / "historico.csv"
    novo = not historico.exists()
    with historico.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS_HISTORICO, delimiter=";")
        if novo:
            w.writeheader()
        w.writerow(registro)
    return registro


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description="Compara modelos e guarda o histórico de avaliação.")
    p.add_argument("--modelos", required=True, help="separados por vírgula, ex.: qwen2.5:3b,qwen2.5:7b")
    p.add_argument("--conjunto", choices=list(CONJUNTOS), default="prova")
    p.add_argument("--prompt", type=Path, default=PROMPT_PADRAO_OLLAMA)
    p.add_argument("--sem-dupla-checagem", action="store_true")
    p.add_argument("--offline", action="store_true", help="só usa o cache")
    args = p.parse_args(argv)

    linhas = [
        rodar(m.strip(), args.conjunto, args.prompt, not args.sem_dupla_checagem, args.offline)
        for m in args.modelos.split(",")
    ]

    print(f"\n{'modelo':<16}{'neoplasia':>10}{'gestação':>10}{'metformina':>11}{'perigosos':>11}{'revisar':>9}{'s/pac':>7}")
    for r in linhas:
        acc = [f"{r[f'acerto_{c}']:.0%}" for c in CAMPOS]
        print(f"{r['modelo']:<16}{acc[0]:>10}{acc[1]:>10}{acc[2]:>11}{r['erros_perigosos']:>11}{r['pacientes_revisar']:>9}{str(r['s_por_paciente']):>7}")
    print(f"\nHistórico: {PASTA / 'historico.csv'} · detalhes: {PASTA / 'resultados'}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
