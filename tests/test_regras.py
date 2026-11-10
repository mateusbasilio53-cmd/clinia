from ia.dados.juntar import ficha, juntar
from ia.regras.criterios import ELEGIVEL, NAO_ELEGIVEL, REVISAR, aplicar, avaliar
from ia.regras.protocolo import PROTOCOLO_DEMO, Protocolo

import pandas as pd


def paciente(**mudar):
    base = {
        "id_paciente": "PAC-001", "diagnostico": "DM2; HAS",
        "idade": 50, "hba1c": 8.5, "imc": 30.0, "creatinina": 1.0, "glicemia_jejum": 170,
        "neoplasia_ativa_status": "negado", "neoplasia_ativa_confianca": "alta",
        "gestacao_status": "nao_mencionado", "gestacao_confianca": "alta",
        "uso_metformina_status": "afirmado", "uso_metformina_confianca": "alta",
        "uso_metformina_evidencia": "metformina 850mg 2x/dia",
    }
    base.update(mudar)
    return base


def test_tudo_certo_e_elegivel():
    a = avaliar(paciente())
    assert a.resultado == ELEGIVEL and not a.limitantes and not a.revisar
    assert 'Metformina ← "metformina 850mg 2x/dia"' in a.evidencias


def test_limites_sao_inclusivos():
    assert avaliar(paciente(idade=30, hba1c=10.5, imc=45, creatinina=1.5)).resultado == ELEGIVEL
    assert avaliar(paciente(idade=70, hba1c=7.0, imc=25)).resultado == ELEGIVEL


def test_numero_fora_da_faixa_explica_em_portugues():
    a = avaliar(paciente(hba1c=10.8))
    assert a.resultado == NAO_ELEGIVEL
    assert a.limitantes == ["HbA1c 10,8% acima do máximo de 10,5%"]
    assert avaliar(paciente(creatinina=1.6)).limitantes == ["Creatinina 1,6 mg/dL acima do máximo de 1,5 mg/dL"]
    assert avaliar(paciente(idade=29)).limitantes == ["Idade 29 anos abaixo do mínimo de 30 anos"]


def test_numero_ausente_no_texto_vai_para_revisar():
    a = avaliar(paciente(hba1c=None))
    assert a.resultado == REVISAR and a.revisar == ["HbA1c: não encontrado no texto"]
    assert avaliar(paciente(imc=float("nan"))).resultado == REVISAR


def test_exclusao_afirmada_barra():
    assert avaliar(paciente(neoplasia_ativa_status="afirmado")).limitantes == ["Neoplasia ativa presente"]
    assert avaliar(paciente(gestacao_status="afirmado")).resultado == NAO_ELEGIVEL


def test_exclusao_nao_mencionada_atende():
    assert avaliar(paciente(neoplasia_ativa_status="nao_mencionado")).resultado == ELEGIVEL


def test_incerto_ou_confianca_baixa_nunca_vira_elegivel():
    p = paciente(neoplasia_ativa_status="incerto",
                 neoplasia_ativa_problemas=["leituras divergentes: IA = não tem, regras = tem"])
    a = avaliar(p)
    assert a.resultado == REVISAR
    assert a.revisar == ["Neoplasia ativa: leituras divergentes: IA = não tem, regras = tem"]
    assert avaliar(paciente(uso_metformina_confianca="baixa")).resultado == REVISAR
    assert avaliar(paciente(neoplasia_ativa_status="afirmado", neoplasia_ativa_confianca="baixa")).resultado == REVISAR


def test_metformina_negada_barra_e_nao_mencionada_revisa():
    assert avaliar(paciente(uso_metformina_status="negado")).limitantes == ["Não usa metformina"]
    a = avaliar(paciente(uso_metformina_status="nao_mencionado"))
    assert a.resultado == REVISAR and "não mencionado" in a.revisar[0]


def test_excluido_por_numero_com_duvida_fica_nao_elegivel_com_os_dois_motivos():
    a = avaliar(paciente(hba1c=12.0, neoplasia_ativa_status="incerto"))
    assert a.resultado == NAO_ELEGIVEL
    assert a.limitantes == ["HbA1c 12% acima do máximo de 10,5%", "também a revisar: Neoplasia ativa: leitura incerta"]


def test_diagnostico():
    for escrito in ["DM2", "Diabetes tipo 2", "DM tipo II", "Diabetes mellitus tipo II", "DM2; HAS; IRC",
                    "diabetes_mellitus_tipo_2", "diabetes_tipo2", "DM tipo2"]:
        assert avaliar(paciente(diagnostico=escrito)).resultado == ELEGIVEL, escrito
    assert avaliar(paciente(diagnostico="Diabetes tipo 1")).resultado == REVISAR
    assert avaliar(paciente(diagnostico=None)).resultado == REVISAR


def test_criterio_vazio_no_protocolo_e_ignorado():
    so_idade = Protocolo(nome="só idade", idade_min=18)
    assert avaliar(paciente(hba1c=None, uso_metformina_status="negado", diagnostico=None), so_idade).resultado == ELEGIVEL


def test_juntar_e_aplicar_sem_colunas_de_gabarito():
    planilha = pd.DataFrame([{"id_paciente": "PAC-001", "diagnostico": "DM2", "gestacao": "Sim",
                              "neoplasia_ativa": "Sim", "medicamentos": "Metformina", "hba1c": 99}])
    campo = {"valor": None, "status": "nao_mencionado", "evidencia": None, "confianca": "alta", "problemas": []}
    ext = {"id_paciente": "PAC-001",
           "dados_lidos": {"idade": {"valor": 50, "evidencia": "50 anos"}, "hba1c": {"valor": 8.0, "evidencia": "A1c 8"},
                           "imc": {"valor": 30, "evidencia": "IMC 30"}, "creatinina": {"valor": 1.0, "evidencia": "Cr 1"}},
           "campos": {"neoplasia_ativa": campo, "gestacao": campo,
                      "uso_metformina": {**campo, "valor": True, "status": "afirmado", "evidencia": "MTF 850"}}}
    df = juntar(planilha, [ext])
    assert "gestacao" not in df.columns and df.loc[0, "hba1c"] == 8.0  # número do texto, não da planilha
    assert ficha(ext)["glicemia_jejum"] is None
    assert aplicar(df, PROTOCOLO_DEMO).loc[0, "resultado"] == ELEGIVEL


def test_rotulo_por_gabarito_usa_numeros_da_planilha_e_gab():
    from ia.dados.rotulos import rotulo_por_gabarito

    linha = {"id_paciente": "PAC-201", "diagnostico": "DM2", "idade": 50, "hba1c": 8.0, "creatinina": 1.0,
             "glicemia_jejum": 150, "imc": 30, "gab_neoplasia": "negado", "gab_gestacao": "nao_mencionado",
             "gab_metformina": "afirmado"}
    df = pd.DataFrame([linha, {**linha, "id_paciente": "PAC-202", "hba1c": 11.0},
                       {**linha, "id_paciente": "PAC-203", "gab_neoplasia": "incerto"}])
    assert rotulo_por_gabarito(df)["rotulo"].tolist() == ["Elegível", "Não elegível", "Indefinido"]
