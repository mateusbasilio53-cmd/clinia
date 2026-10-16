"""Gera a planilha de saída da extração: dados estruturados + o que a IA leu + gabarito + acerto.

Uso:
    py -m ia.extracao.relatorio \
        --base "Base 1|dados/Base_ficticia_DM2_CLINIA.xlsx|entregas/extracoes_base1.json" \
        --base "Base 2|dados/pacientes_ficticios_PAC201-300.xlsx|entregas/extracoes_base2.json" \
        --saida entregas/CLINIA_saida_extracao.xlsx

Abas: Resumo (IA x regex por campo), uma aba por base (uma linha por paciente) e Erros.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from ia.entrada.planilha import ler_planilha, textos_para_extracao
from ia.extracao.avaliar import avaliar, gabarito_planilha
from ia.extracao.extrator import executar
from ia.extracao.provedores import ProvedorRegras
from ia.extracao.schema import CAMPOS, ExtracaoPaciente

ROTULO = {"neoplasia_ativa": "neoplasia", "gestacao": "gestação", "uso_metformina": "metformina"}
LEGIVEL = {"afirmado": "SIM", "negado": "NÃO", "nao_mencionado": "não mencionado", "incerto": "INCERTO"}
ESTRUTURADAS = ["idade", "sexo", "diagnostico", "hba1c", "creatinina", "glicemia_jejum", "imc"]

# Erro perigoso: pode deixar elegível quem deveria sair ou ser revisado.
# Neoplasia e gestação são critérios de exclusão; metformina é de inclusão.
_EXCLUSAO = lambda esp, obt: esp in {"afirmado", "incerto"} and obt in {"negado", "nao_mencionado"}  # noqa: E731
PERIGOSO = {
    "neoplasia_ativa": _EXCLUSAO,
    "gestacao": _EXCLUSAO,
    "uso_metformina": lambda esp, obt: esp in {"negado", "incerto", "nao_mencionado"} and obt == "afirmado",
}


def erro_perigoso(campo: str, esperado: set[str], obtido: str) -> bool:
    return all(PERIGOSO[campo](e, obtido) for e in esperado)


def contar_perigosos(extracoes: list[ExtracaoPaciente], gab: dict, campo: str) -> int:
    return sum(
        erro_perigoso(campo, gab[i.id_paciente][campo], getattr(i.campos, campo).status)
        for i in extracoes if i.id_paciente in gab
    )


def contar_revisar(extracoes: list[ExtracaoPaciente], campo: str) -> int:
    return sum(
        getattr(i.campos, campo).status == "incerto" or getattr(i.campos, campo).confianca == "baixa"
        for i in extracoes
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Planilha de saída da extração.")
    p.add_argument("--base", action="append", required=True, help='"Nome|planilha.xlsx|extracoes.json"')
    p.add_argument("--saida", type=Path, default=Path("entregas/CLINIA_saida_extracao.xlsx"))
    args = p.parse_args(argv)

    resumo, erros, abas = [], [], {}
    for spec in args.base:
        nome, planilha, arquivo = spec.split("|")
        df = ler_planilha(planilha)
        gab = gabarito_planilha(df)
        ia = [ExtracaoPaciente.model_validate(i) for i in json.loads(Path(arquivo).read_text(encoding="utf-8"))]
        regex, _ = executar(textos_para_extracao(df), ProvedorRegras(), "regras-v1", cache=None)
        r_ia, r_rx = avaliar(ia, gab), avaliar(regex, gab)

        for campo in CAMPOS:
            resumo.append({
                "base": nome,
                "campo": ROTULO[campo],
                "gabarito": "exato (gab_*)" if "gab_neoplasia" in df.columns else "Sim/Não da coluna",
                "CLINIA: acertos": f"{r_ia[campo]['acertos']}/{r_ia[campo]['total']} ({r_ia[campo]['acuracia']:.0%})",
                "CLINIA: erros perigosos": contar_perigosos(ia, gab, campo),
                "CLINIA: vão para REVISAR": contar_revisar(ia, campo),
                "só regex: acertos": f"{r_rx[campo]['acertos']}/{r_rx[campo]['total']} ({r_rx[campo]['acuracia']:.0%})",
                "só regex: erros perigosos": contar_perigosos(regex, gab, campo),
            })

        por_id = {i.id_paciente: i for i in ia}
        linhas = []
        for _, pac in df.iterrows():
            pid = str(pac["id_paciente"])
            item = por_id[pid]
            linha = {"id_paciente": pid, **{c: pac[c] for c in ESTRUTURADAS if c in df.columns}}
            motivos = []
            for campo in CAMPOS:
                c = getattr(item.campos, campo)
                esperado = gab[pid][campo]
                linha[f"CLINIA: {ROTULO[campo]}"] = LEGIVEL[c.status]
                linha[f"evidência {ROTULO[campo]}"] = c.evidencia or ""
                linha[f"gabarito {ROTULO[campo]}"] = "/".join(LEGIVEL[s] for s in sorted(esperado))
                linha[f"acertou {ROTULO[campo]}"] = "✔" if c.status in esperado else "✘"
                if c.status == "incerto" or c.confianca == "baixa":
                    motivos.append(f"{ROTULO[campo]}: {'; '.join(c.problemas) or 'leitura incerta'}")
                if c.status not in esperado:
                    erros.append({
                        "base": nome, "id_paciente": pid, "campo": ROTULO[campo],
                        "gabarito": linha[f"gabarito {ROTULO[campo]}"], "CLINIA leu": LEGIVEL[c.status],
                        "perigoso?": "SIM" if erro_perigoso(campo, esperado, c.status) else "",
                        "evidência": c.evidencia or "", "problemas": "; ".join(c.problemas),
                        "texto": pac["anotacao_medica"],
                    })
            linha["vai para REVISAR?"] = "SIM" if motivos else ""
            linha["motivo do REVISAR"] = " | ".join(motivos)
            linha["anotacao_medica (entrada)"] = pac["anotacao_medica"]
            linhas.append(linha)
        abas[nome] = pd.DataFrame(linhas)

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(args.saida) as w:
        pd.DataFrame(resumo).to_excel(w, sheet_name="Resumo", index=False)
        for nome, tabela in abas.items():
            tabela.to_excel(w, sheet_name=nome[:31], index=False)
        pd.DataFrame(erros).to_excel(w, sheet_name="Erros", index=False)

    pd.set_option("display.width", 250)
    print(pd.DataFrame(resumo).to_string(index=False))
    for nome, tabela in abas.items():
        print(f"{nome}: {(tabela['vai para REVISAR?'] == 'SIM').sum()} de {len(tabela)} pacientes vão para REVISAR")
    print(f"Gerado {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
