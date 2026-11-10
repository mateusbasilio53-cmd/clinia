"""Planilha às cegas para a equipe da Bárbara validar uma amostra da Base 2.

A planilha mostra só o texto, os números e os critérios do estudo: nada do que a
CLINIA concluiu nem do rótulo calculado, para não influenciar quem revisa.
As nossas respostas ficam em chave_amostra.csv, para comparar quando voltar.

Amostra: todos com "incerto" no gabarito + todos calculados como elegíveis
+ todos os indefinidos + não elegíveis sorteados (no mínimo 3) até o tamanho pedido.

Uso:
    py -m ia.saida.amostra_validacao
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from ia.dados.juntar import juntar
from ia.dados.rotulos import ELEGIVEL_ROT, GABARITO, INDEFINIDO, rotulo_por_gabarito
from ia.entrada.planilha import ler_planilha
from ia.regras.criterios import aplicar

PLANILHA = Path("dados/pacientes_ficticios_PAC201-300.xlsx")
EXTRACOES = Path("entregas/extracoes_base2.json")
PASTA = Path("avaliacao/validacao_clinica")

CRITERIOS = [
    ("Diagnóstico", "Diabetes mellitus tipo 2 confirmado"),
    ("Idade", "30 a 70 anos, inclusive"),
    ("HbA1c", "7,0% a 10,5%, inclusive"),
    ("Metformina", "Em uso"),
    ("IMC", "25 a 45 kg/m², inclusive"),
    ("Creatinina", "Excluir se > 1,5 mg/dL"),
    ("Neoplasia ativa", "Excluir se Sim"),
    ("Gestação", "Excluir se Sim"),
]
INSTRUCOES = [
    "CLINIA — validação clínica de uma amostra (pacientes 100% FICTÍCIOS)",
    "",
    "Para cada paciente, leia a anotação e os exames e preencha as colunas em amarelo:",
    "  • neoplasia_ativa / gestacao_atual / usa_metformina: Sim, Não, Não mencionado ou Não dá para saber",
    "  • elegivel: Sim, Não ou Precisa de mais informação — considerando os critérios da aba 'criterios'",
    "  • comentario: livre (ex.: 'histórico de câncer de 2015 sem status atual: eu consideraria inelegível')",
    "",
    "Não existe resposta certa esperada: queremos o julgamento clínico de vocês.",
    "Os casos foram escolhidos de propósito, vários são difíceis.",
]
OPCOES_CAMPO = '"Sim,Não,Não mencionado,Não dá para saber"'
OPCOES_ELEGIVEL = '"Sim,Não,Precisa de mais informação"'
MIN_CONTROLES = 3  # sempre alguns "fáceis", para ver se a equipe concorda também nos óbvios
A_PREENCHER = ["neoplasia_ativa", "gestacao_atual", "usa_metformina", "elegivel", "comentario"]


def escolher(rotulos: pd.DataFrame, gab: pd.DataFrame, tamanho: int, semente: int) -> pd.DataFrame:
    """Devolve id_paciente + motivo da escolha, na ordem sorteada (não agrupada por motivo)."""
    incerto = gab.loc[(gab[list(GABARITO.values())] == "incerto").any(axis=1), "id_paciente"]
    elegivel = rotulos.loc[rotulos.rotulo == ELEGIVEL_ROT, "id_paciente"]
    escolha = {i: "gabarito incerto" for i in incerto}
    indefinido = rotulos.loc[rotulos.rotulo == INDEFINIDO, "id_paciente"]
    escolha.update({i: "calculado elegível" for i in elegivel if i not in escolha})
    escolha.update({i: "indefinido (ex.: metformina não mencionada)" for i in indefinido if i not in escolha})
    resto = rotulos.loc[~rotulos.id_paciente.isin(escolha), "id_paciente"]
    faltam = max(MIN_CONTROLES, tamanho - len(escolha))
    escolha.update({i: "controle (não elegível)" for i in resto.sample(min(faltam, len(resto)), random_state=semente)})
    out = pd.DataFrame({"id_paciente": list(escolha), "motivo_escolha": list(escolha.values())})
    return out.sample(frac=1, random_state=semente).reset_index(drop=True)


def gerar(tamanho: int = 25, semente: int = 42, pasta: Path = PASTA) -> tuple[Path, Path]:
    pacientes = ler_planilha(PLANILHA)
    rotulos = rotulo_por_gabarito(pacientes)
    escolhidos = escolher(rotulos, pacientes, tamanho, semente)
    escolhidos.insert(0, "caso", [f"CASO-{n:02d}" for n in range(1, len(escolhidos) + 1)])

    base = escolhidos.merge(pacientes, on="id_paciente")
    folha = base[["caso", "id_paciente", "sexo", "idade", "diagnostico", "hba1c", "creatinina",
                  "glicemia_jejum", "imc", "anotacao_medica"]].copy()
    for c in A_PREENCHER:
        folha[c] = ""

    clinia = aplicar(juntar(pacientes, json.loads(EXTRACOES.read_text(encoding="utf-8"))))
    chave = (escolhidos.merge(rotulos, on="id_paciente")
             .merge(pacientes[["id_paciente", *GABARITO.values()]], on="id_paciente")
             .merge(clinia[["id_paciente", "resultado", "criterios_limitantes", "motivo_revisar"]], on="id_paciente")
             .rename(columns={"resultado": "resultado_clinia"}))

    pasta.mkdir(parents=True, exist_ok=True)
    xlsx, csv = pasta / "amostra_base2_para_equipe_clinica.xlsx", pasta / "chave_amostra.csv"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as w:
        pd.DataFrame({"": INSTRUCOES}).to_excel(w, sheet_name="como_preencher", index=False, header=False)
        pd.DataFrame(CRITERIOS, columns=["Critério", "Regra"]).to_excel(w, sheet_name="criterios", index=False)
        folha.to_excel(w, sheet_name="pacientes", index=False)
        _formatar(w.book, len(folha))
    chave.to_csv(csv, index=False, encoding="utf-8-sig")
    return xlsx, csv


def _formatar(book, n: int) -> None:
    book["como_preencher"]["A1"].font = Font(bold=True, size=13)
    book["como_preencher"].column_dimensions["A"].width = 110
    book["criterios"].column_dimensions["A"].width = 18
    book["criterios"].column_dimensions["B"].width = 40
    ws = book["pacientes"]
    larguras = {"A": 9, "B": 10, "J": 70, "K": 16, "L": 16, "M": 16, "N": 20, "O": 45}
    for col, larg in larguras.items():
        ws.column_dimensions[col].width = larg
    amarelo = PatternFill("solid", fgColor="FFF2CC")
    for linha in ws.iter_rows(min_row=2, max_row=n + 1):
        linha[9].alignment = Alignment(wrap_text=True, vertical="top")
        for cel in linha[10:15]:
            cel.fill = amarelo
    for cel in ws[1]:
        cel.font = Font(bold=True)
    campos = DataValidation(type="list", formula1=OPCOES_CAMPO, allow_blank=True)
    eleg = DataValidation(type="list", formula1=OPCOES_ELEGIVEL, allow_blank=True)
    ws.add_data_validation(campos)
    ws.add_data_validation(eleg)
    campos.add(f"K2:M{n + 1}")
    eleg.add(f"N2:N{n + 1}")
    ws.freeze_panes = "C2"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gera a amostra às cegas para validação clínica.")
    p.add_argument("--tamanho", type=int, default=25)
    p.add_argument("--semente", type=int, default=42)
    args = p.parse_args(argv)
    xlsx, csv = gerar(args.tamanho, args.semente)
    chave = pd.read_csv(csv)
    print(f"Gerado {xlsx} ({len(chave)} casos) e {csv} (não mandar: é a nossa chave)")
    print(chave["motivo_escolha"].value_counts().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
