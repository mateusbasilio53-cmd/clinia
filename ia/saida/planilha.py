"""Etapa ④: a planilha final de elegibilidade, ranqueada e com o porquê de cada paciente.

Junta as peças oficiais:
    ia.dados.juntar        -> uma linha por paciente (o que a CLINIA leu do texto)
    ia.regras.criterios    -> ELEGÍVEL / NÃO ELEGÍVEL / REVISAR + critérios e evidências (decide)
    ia.modelo.random_forest -> ordem dentro de cada grupo (margem; RF só no REVISAR). Não decide.

O RF é treinado com as bases rotuladas (ia.modelo.random_forest.BASES), SEM os pacientes
da planilha que está sendo gerada, para a probabilidade nunca vir de um paciente que o
modelo já viu.

Se a planilha tiver rótulo (elegivel, elegibilidade_calculada ou gab_*), sai a versão
de avaliação, com rotulo_esperado e acertou (seção 7.3 do playbook).

Uso:
    py -m ia.saida.planilha --planilha dados/pacientes_ficticios_PAC201-300.xlsx --extracoes entregas/extracoes_base2.json
    (padrão de saída: saidas/planilha_resultado.xlsx)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill

from ia.dados.juntar import juntar
from ia.dados.rotulos import ELEGIVEL_ROT, INDEFINIDO, NAO_ELEGIVEL_ROT, rotulo
from ia.entrada.planilha import ler_planilha
from ia.modelo.random_forest import BASES, alvo, carregar_bases, features, novo_modelo, ordenar, treinaveis
from ia.regras.criterios import ELEGIVEL, NAO_ELEGIVEL, REVISAR, aplicar
from ia.regras.protocolo import PROTOCOLO_DEMO, Protocolo

FRASE = "A decisão final é sempre humana. A CLINIA organiza a lista e mostra o porquê; quem decide é o coordenador/médico."

COLUNAS = {  # coluna interna -> nome na planilha (seção 7.3)
    "posicao": "posicao",
    "id_paciente": "id_paciente",
    "resultado": "resultado",
    "criterios_limitantes": "criterios_limitantes",
    "motivo_revisar": "motivo_revisar",
    "criterios_atendidos": "criterios_atendidos",
    "evidencias_texto": "evidencias_texto",
    "margem": "margem_ate_o_limite",
    "probabilidade_elegibilidade": "probabilidade",
    "criterio_ordem": "ordenado_por",
}
CORES = {ELEGIVEL: "C6EFCE", REVISAR: "FFEB9C", NAO_ELEGIVEL: "F4CCCC"}
LARGURAS = {"posicao": 8, "id_paciente": 11, "resultado": 15, "criterios_limitantes": 45, "motivo_revisar": 45,
            "criterios_atendidos": 45, "evidencias_texto": 70, "margem_ate_o_limite": 12, "probabilidade": 12,
            "ordenado_por": 20, "rotulo_esperado": 15, "acertou": 10}

COMO_LER = [
    "CLINIA — planilha de elegibilidade (pacientes 100% FICTÍCIOS)",
    "",
    FRASE,
    "",
    "resultado: ELEGÍVEL (atende tudo) · REVISAR (falta informação ou a leitura do texto ficou em dúvida) · "
    "NÃO ELEGÍVEL (algum critério barrou)",
    "criterios_limitantes: o que barrou o paciente (ex.: 'HbA1c 10,8% acima do máximo de 10,5%')",
    "motivo_revisar: por que a CLINIA não decidiu sozinha e chamou um humano",
    "evidencias_texto: o trecho do prontuário que justifica cada leitura",
    "",
    "Como a lista é ordenada (não muda o resultado):",
    "  • ELEGÍVEL e NÃO ELEGÍVEL: margem_ate_o_limite, maior primeiro. Margem = folga até o limite mais próximo",
    "    (0,50 = no meio da faixa; 0 = no limite; negativo = fora). Nos NÃO ELEGÍVEIS, quem está 'quase lá' vem antes.",
    "  • REVISAR: probabilidade do Random Forest, maior primeiro (quem mais se parece com os elegíveis).",
    "  • probabilidade aparece para todos, mas é informativa: o modelo foi treinado com rótulos ainda não validados",
    "    pela equipe clínica.",
]


def treinar(excluir_ids: set[str], bases=BASES):
    """RF treinado nas bases rotuladas, sem os pacientes da planilha que vai sair."""
    t = treinaveis(carregar_bases(bases))
    t = t[~t["id_paciente"].isin(excluir_ids)]
    return novo_modelo().fit(features(t), alvo(t)), len(t)


def _tem_rotulo(pacientes: pd.DataFrame) -> bool:
    return any(c in pacientes.columns for c in ["elegivel", "elegibilidade_calculada", "gab_neoplasia"])


def acertou(resultado: str, esperado: str) -> str:
    if esperado not in (ELEGIVEL_ROT, NAO_ELEGIVEL_ROT):
        return ""
    if resultado == REVISAR:
        return "revisar"
    return "✔" if (resultado == ELEGIVEL) == (esperado == ELEGIVEL_ROT) else "✘"


def montar(pacientes: pd.DataFrame, extracoes: list[dict], protocolo: Protocolo = PROTOCOLO_DEMO,
           modelo=None) -> pd.DataFrame:
    df = aplicar(juntar(pacientes, extracoes), protocolo)
    if modelo is None:
        modelo, _ = treinar(set(df["id_paciente"]))
    out = ordenar(df, modelo)
    tabela = out[list(COLUNAS)].rename(columns=COLUNAS)
    tabela["probabilidade"] = tabela["probabilidade"].round(2)
    tabela["margem_ate_o_limite"] = tabela["margem_ate_o_limite"].round(2)
    if _tem_rotulo(pacientes):
        r = rotulo(pacientes).set_index("id_paciente")["rotulo"]
        tabela["rotulo_esperado"] = tabela["id_paciente"].map(r).fillna(INDEFINIDO)
        tabela["acertou"] = [acertou(a, b) for a, b in zip(tabela["resultado"], tabela["rotulo_esperado"])]
    return tabela


def resumo(tabela: pd.DataFrame, protocolo: Protocolo, origem: str, n_treino: int) -> pd.DataFrame:
    linhas = [("Gerado em", datetime.now().strftime("%d/%m/%Y %H:%M")), ("Base", origem),
              ("Protocolo", protocolo.nome), ("Pacientes", len(tabela))]
    for res in (ELEGIVEL, REVISAR, NAO_ELEGIVEL):
        linhas.append((res, int((tabela["resultado"] == res).sum())))
    if "acertou" in tabela.columns:
        decididos = tabela[tabela["acertou"].isin(["✔", "✘"])]
        if len(decididos):
            linhas.append(("Acerto nos decididos (avaliação)", f"{(decididos['acertou'] == '✔').mean():.1%} "
                                                               f"de {len(decididos)}"))
        perigosos = ((tabela["resultado"] == ELEGIVEL) & (tabela["rotulo_esperado"] == NAO_ELEGIVEL_ROT)).sum()
        linhas.append(("Não elegível marcado ELEGÍVEL (perigoso)", int(perigosos)))
        perdidos = ((tabela["resultado"] == NAO_ELEGIVEL) & (tabela["rotulo_esperado"] == ELEGIVEL_ROT)).sum()
        linhas.append(("Elegível descartado como NÃO ELEGÍVEL", int(perdidos)))
    linhas.append(("Random Forest treinado com", f"{n_treino} pacientes (nenhum desta planilha)"))
    linhas.append(("", ""))
    linhas.append(("Lembrete", FRASE))
    return pd.DataFrame(linhas, columns=["Item", "Valor"])


def criterios(protocolo: Protocolo) -> pd.DataFrame:
    def faixa(mi, ma, un=""):
        if mi is not None and ma is not None:
            return f"{mi:g} a {ma:g}{un}, inclusive".replace(".", ",")
        return f"no máximo {ma:g}{un}".replace(".", ",") if ma is not None else ""
    p = protocolo
    linhas = [("Diagnóstico", p.diagnostico_exigido), ("Idade", faixa(p.idade_min, p.idade_max, " anos")),
              ("HbA1c", faixa(p.hba1c_min, p.hba1c_max, "%")), ("IMC", faixa(p.imc_min, p.imc_max, " kg/m²")),
              ("Creatinina", faixa(None, p.creatinina_max, " mg/dL")),
              ("Glicemia de jejum", faixa(None, p.glicemia_jejum_max, " mg/dL")),
              ("Metformina", "em uso" if p.exige_metformina else ""),
              ("Neoplasia ativa", "exclui" if p.permite_neoplasia_ativa is False else ""),
              ("Gestação", "exclui" if p.permite_gestacao is False else "")]
    return pd.DataFrame([(a, b) for a, b in linhas if b], columns=["Critério", "Regra"])


def salvar(tabela: pd.DataFrame, caminho: Path, protocolo: Protocolo, origem: str, n_treino: int) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(caminho, engine="openpyxl") as w:
        tabela.to_excel(w, sheet_name="lista", index=False)
        resumo(tabela, protocolo, origem, n_treino).to_excel(w, sheet_name="resumo", index=False)
        criterios(protocolo).to_excel(w, sheet_name="criterios", index=False)
        pd.DataFrame({"": COMO_LER}).to_excel(w, sheet_name="como_ler", index=False, header=False)
        _formatar(w.book, tabela)
    return caminho


def _formatar(book, tabela: pd.DataFrame) -> None:
    ws = book["lista"]
    for i, nome in enumerate(tabela.columns, start=1):
        ws.cell(1, i).font = Font(bold=True)
        ws.column_dimensions[ws.cell(1, i).column_letter].width = LARGURAS.get(nome, 14)
    col_res = list(tabela.columns).index("resultado")
    for linha in ws.iter_rows(min_row=2, max_row=len(tabela) + 1):
        cor = CORES.get(linha[col_res].value)
        if cor:
            linha[col_res].fill = PatternFill("solid", fgColor=cor)
        for cel in linha:
            cel.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = ws.dimensions
    for nome, larg in [("resumo", (42, 90)), ("criterios", (20, 35))]:
        book[nome].column_dimensions["A"].width, book[nome].column_dimensions["B"].width = larg
        for cel in book[nome][1]:
            cel.font = Font(bold=True)
    book["como_ler"]["A1"].font = Font(bold=True, size=13)
    book["como_ler"]["A3"].font = Font(bold=True)
    book["como_ler"].column_dimensions["A"].width = 120


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gera a planilha final de elegibilidade (etapa ④).")
    p.add_argument("--planilha", required=True)
    p.add_argument("--extracoes", required=True)
    p.add_argument("--saida", type=Path, default=Path("saidas/planilha_resultado.xlsx"))
    args = p.parse_args(argv)

    pacientes = ler_planilha(args.planilha)
    extracoes = json.loads(Path(args.extracoes).read_text(encoding="utf-8"))
    modelo, n_treino = treinar(set(pacientes["id_paciente"].astype(str)))
    tabela = montar(pacientes, extracoes, modelo=modelo)
    salvar(tabela, args.saida, PROTOCOLO_DEMO, Path(args.planilha).name, n_treino)

    print(resumo(tabela, PROTOCOLO_DEMO, Path(args.planilha).name, n_treino).to_string(index=False, header=False))
    print(f"\nGerado {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
