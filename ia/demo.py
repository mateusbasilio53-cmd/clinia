"""Demo da CLINIA: texto corrido entra, ficha estruturada sai, com o trecho que justifica cada campo.

Uso:
    python -m ia.demo                                  # 3 pacientes de exemplo (rápido, usa o cache)
    python -m ia.demo --id PAC-231                     # um paciente das bases
    python -m ia.demo --texto "Fem, 45a, DM2. Nega Ca. Em uso de MTF 850mg."   # IA lê ao vivo

Se o Ollama não estiver aberto, a leitura ao vivo cai para as regras e avisa.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

from dotenv import load_dotenv

from ia.entrada.planilha import ler_planilha, textos_para_extracao
from ia.extracao.cache import CacheExtracoes
from ia.extracao.extrator import OLLAMA_MODELO_PADRAO, PROMPT_PADRAO_OLLAMA, carregar_prompt, executar
from ia.extracao.provedores import ProvedorOllama, ProvedorRegras
from ia.extracao.schema import CAMPOS, CAMPOS_LIDOS, ExtracaoPaciente

BASES = [Path("dados/Base_ficticia_DM2_CLINIA.xlsx"), Path("dados/pacientes_ficticios_PAC201-300.xlsx")]
EXEMPLOS = ["PAC-201", "PAC-231", "PAC-204"]  # remissão; QT ativa; "nunca usou metformina"

NOME = {
    "idade": "Idade", "sexo": "Sexo", "hba1c": "HbA1c (%)", "creatinina": "Creatinina (mg/dL)",
    "glicemia_jejum": "Glicemia de jejum", "imc": "IMC",
    "neoplasia_ativa": "Neoplasia ativa", "gestacao": "Gestação atual", "uso_metformina": "Usa metformina",
}
LEGIVEL = {"afirmado": "SIM", "negado": "NÃO", "nao_mencionado": "não mencionado", "incerto": "INCERTO"}


def mostrar(item: ExtracaoPaciente, texto: str) -> None:
    linha = "═" * 78
    print(f"\n{linha}\n  CLINIA · {item.id_paciente}\n{linha}")
    print("  Texto do prontuário:")
    print(textwrap.indent(textwrap.fill(texto, 74), "    "))

    print("\n  Ficha lida do texto")
    for c in CAMPOS_LIDOS:
        v = getattr(item.dados_lidos, c)
        if v.valor is None:
            valor = "—  (não está no texto)"
        elif isinstance(v.valor, float) and v.valor.is_integer():
            valor = str(int(v.valor))
        else:
            valor = str(v.valor).replace(".", ",")
        trecho = f'   ← "{v.evidencia}"' if v.evidencia else ""
        print(f"    {NOME[c]:<20} {valor:<10}{trecho}")

    print("\n  Critérios lidos do texto")
    motivos = []
    for c in CAMPOS:
        campo = getattr(item.campos, c)
        marca = "✔ trecho conferido" if campo.evidencia_verificada and campo.evidencia else ""
        print(f"    {NOME[c]:<20} {LEGIVEL[campo.status]:<15}{marca}")
        if campo.evidencia:
            print(f'      ← "{campo.evidencia}"')
        if campo.status == "incerto" or campo.confianca == "baixa":
            motivos.append(f"{NOME[c]}: {'; '.join(campo.problemas) or 'leitura incerta'}")

    print()
    if motivos:
        print("  → VAI PARA REVISÃO HUMANA")
        for m in motivos:
            print(f"      · {m}")
    else:
        print("  → Leitura completa, sem dúvidas.")
    print(f"\n  Lido por: {item.modelo_llm} · prompt {item.versao_prompt}")
    print("  A decisão final é sempre do coordenador/médico.")


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description="Demo: texto corrido → ficha estruturada.")
    p.add_argument("--texto", help="anotação nova, lida ao vivo pela IA")
    p.add_argument("--id", help="paciente das bases (ex.: PAC-231)")
    args = p.parse_args(argv)

    prompt, versao = carregar_prompt(PROMPT_PADRAO_OLLAMA)
    ia = ProvedorOllama(OLLAMA_MODELO_PADRAO, prompt)
    cache = CacheExtracoes()

    if args.texto:
        itens = [("TEXTO-NOVO", args.texto)]
        resultado, resumo = executar(itens, ia, versao, cache, dupla_checagem=True)
        if resumo["falhas"]:  # o extrator transforma erro do Ollama em falha registrada
            print("\n  [aviso] Ollama indisponível: leitura feita só pelas regras.")
            resultado, _ = executar(itens, ProvedorRegras(), "regras-v1", cache=None)
    else:
        todos = dict(t for base in BASES if base.exists() for t in textos_para_extracao(ler_planilha(base)))
        ids = [args.id] if args.id else EXEMPLOS
        faltando = [i for i in ids if i not in todos]
        if faltando:
            raise SystemExit(f"Paciente não encontrado: {', '.join(faltando)}")
        itens = [(i, todos[i]) for i in ids]
        resultado, _ = executar(itens, ia, versao, cache, dupla_checagem=True)

    for item, (_, texto) in zip(resultado, itens):
        mostrar(item, texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
