import pytest

from ia.extracao.estruturados import ler_dados
from ia.extracao.verificacao import evidencia_existe

FORMAL = (
    "Paciente do sexo masculino, 46 anos, DM2 há 10 anos. Exames recentes: HbA1c de 9,0%, "
    "glicemia de jejum 185 mg/dL e creatinina 1,1 mg/dL; IMC de 23,9 kg/m²."
)
TELEGRAFICO = "Fem, 21a, DM2 + HAS. Lab: HbA1c 9,6 | GJ 231 | creat 1,1 | IMC 32,2."
MODELO_PRONTO = (
    "36 anos, sexo M. Exames recentes: HbA1c 9.5%, glicemia de jejum 171 mg/dL, "
    "creatinina 0.87 mg/dL. IMC 32.6 kg/m²."
)


@pytest.mark.parametrize(
    "texto, esperado",
    [
        (FORMAL, {"idade": 46, "sexo": "M", "hba1c": 9.0, "glicemia_jejum": 185, "creatinina": 1.1, "imc": 23.9}),
        (TELEGRAFICO, {"idade": 21, "sexo": "F", "hba1c": 9.6, "glicemia_jejum": 231, "creatinina": 1.1, "imc": 32.2}),
        (MODELO_PRONTO, {"idade": 36, "sexo": "M", "hba1c": 9.5, "glicemia_jejum": 171, "creatinina": 0.87, "imc": 32.6}),
    ],
)
def test_le_valores_em_estilos_diferentes(texto, esperado):
    dados = ler_dados(texto)
    for campo, valor in esperado.items():
        assert getattr(dados, campo).valor == valor, campo


@pytest.mark.parametrize(
    "texto, sexo",
    [("Pcte F, 56 anos.", "F"), ("Sra. 38 anos.", "F"), ("Sr. João não", "M"), ("Homem, 60 anos.", "M")],
)
def test_sexo_abreviado(texto, sexo):
    assert ler_dados(texto).sexo.valor == sexo


def test_a1c_glic_e_imc_inteiro():
    dados = ler_dados("Últimos exames: A1c 9,3%; glic jejum 214; IMC 41")
    assert (dados.hba1c.valor, dados.glicemia_jejum.valor, dados.imc.valor) == (9.3, 214, 41)


def test_tempo_de_doenca_nao_vira_idade():
    assert ler_dados("DM2 há 10 anos, sem outras queixas.").idade.valor is None


def test_valor_ausente_fica_nulo():
    dados = ler_dados("Fem, 40a. Sem exames recentes.")
    assert dados.hba1c.valor is None and dados.hba1c.evidencia is None


def test_cr_abreviado():
    assert ler_dados("Lab: Cr 0,9 | HbA1c 11,1").creatinina.valor == 0.9


def test_evidencias_sao_trechos_do_texto():
    dados = ler_dados(FORMAL)
    for campo in ("idade", "sexo", "hba1c", "creatinina", "glicemia_jejum", "imc"):
        assert evidencia_existe(getattr(dados, campo).evidencia, FORMAL), campo
