import json
from pathlib import Path

import pandas as pd
import pytest

from ia.dados.rotulos import ELEGIVEL_ROT, INDEFINIDO, NAO_ELEGIVEL_ROT
from ia.entrada.planilha import ler_planilha
from ia.regras.criterios import aplicar
from ia.dados.juntar import juntar
from ia.saida.planilha import acertou, montar, salvar, treinar
from ia.regras.protocolo import PROTOCOLO_DEMO

PLANILHA = Path("dados/pacientes_ficticios_PAC201-300.xlsx")
EXTRACOES = Path("entregas/extracoes_base2.json")


def test_acertou():
    assert acertou("ELEGÍVEL", ELEGIVEL_ROT) == "✔"
    assert acertou("NÃO ELEGÍVEL", NAO_ELEGIVEL_ROT) == "✔"
    assert acertou("ELEGÍVEL", NAO_ELEGIVEL_ROT) == "✘"
    assert acertou("REVISAR", ELEGIVEL_ROT) == "revisar"
    assert acertou("ELEGÍVEL", INDEFINIDO) == ""


@pytest.fixture(scope="module")
def base2():
    if not (PLANILHA.exists() and EXTRACOES.exists()):
        pytest.skip("Base 2 não está no repositório")
    pacientes = ler_planilha(PLANILHA)
    extracoes = json.loads(EXTRACOES.read_text(encoding="utf-8"))
    modelo, n = treinar(set(pacientes["id_paciente"]))
    return pacientes, extracoes, montar(pacientes, extracoes, modelo=modelo), n


def test_planilha_tem_as_colunas_da_secao_7_3(base2):
    _, _, tabela, _ = base2
    for c in ["posicao", "id_paciente", "resultado", "probabilidade", "criterios_atendidos",
              "criterios_limitantes", "evidencias_texto", "rotulo_esperado", "acertou"]:
        assert c in tabela.columns, c
    assert list(tabela["posicao"]) == list(range(1, len(tabela) + 1))


def test_planilha_nao_muda_a_decisao_das_regras(base2):
    pacientes, extracoes, tabela, _ = base2
    regras = aplicar(juntar(pacientes, extracoes)).set_index("id_paciente")["resultado"]
    assert tabela.set_index("id_paciente")["resultado"].sort_index().equals(regras.sort_index())


def test_rf_nao_treina_com_os_pacientes_da_planilha(base2):
    pacientes, _, _, n = base2
    _, n_com_todos = treinar(set())
    assert n < n_com_todos  # os 100 da Base 2 saíram do treino


def test_salvar_gera_as_abas(base2, tmp_path):
    _, _, tabela, n = base2
    caminho = salvar(tabela, tmp_path / "saida.xlsx", PROTOCOLO_DEMO, "Base 2", n)
    assert pd.ExcelFile(caminho).sheet_names == ["lista", "resumo", "criterios", "como_ler"]
