import math

import pandas as pd

from ia.dados.rotulos import ELEGIVEL_ROT, INDEFINIDO, NAO_ELEGIVEL_ROT
from ia.entrada.planilha import COLUNAS_GABARITO, COLUNAS_ROTULO
from ia.modelo.margem import folga, margem_paciente
from ia.modelo.random_forest import features, novo_modelo, ordenar, treinaveis


def linha(id_, resultado, rotulo, hba1c=8.0, met="afirmado", idade=50):
    return {
        "id_paciente": id_, "idade": idade, "sexo": "F", "hba1c": hba1c, "creatinina": 1.0,
        "glicemia_jejum": 150, "imc": 30.0,
        "neoplasia_ativa_status": "negado", "neoplasia_ativa_confianca": "alta",
        "gestacao_status": "nao_mencionado", "gestacao_confianca": "alta",
        "uso_metformina_status": met, "uso_metformina_confianca": "alta",
        "resultado": resultado, "rotulo": rotulo,
    }


def base():
    return pd.DataFrame(
        [linha(f"PAC-{i:03d}", "ELEGÍVEL", ELEGIVEL_ROT, hba1c=7.5 + i * 0.1) for i in range(10)]
        + [linha(f"PAC-{i:03d}", "NÃO ELEGÍVEL", NAO_ELEGIVEL_ROT, hba1c=10.6 + (i - 10) * 0.2, met="negado")
           for i in range(10, 20)]
        + [linha("PAC-020", "REVISAR", INDEFINIDO, hba1c=None, met="incerto"),
           linha("PAC-021", "REVISAR", INDEFINIDO, met="incerto")]
    )


def test_features_nao_usam_gabarito_rotulo_nem_resultado():
    X = features(base())
    proibidas = {*COLUNAS_GABARITO, *COLUNAS_ROTULO, "rotulo", "resultado"}
    assert not proibidas & set(X.columns)


def test_numero_ausente_fica_vazio_com_indicador():
    X = features(base())
    assert math.isnan(X.loc[20, "hba1c"]) and X.loc[20, "hba1c_ausente"] == 1
    assert X.loc[0, "hba1c_ausente"] == 0


def test_indefinido_fica_fora_do_treino():
    assert len(treinaveis(base())) == 20


def test_folga_e_margem():
    assert folga(8.75, 7.0, 10.5) == 0.5          # meio da faixa
    assert folga(10.5, 7.0, 10.5) == 0.0          # no limite
    assert folga(11.2, 7.0, 10.5) < 0             # fora
    assert folga(1.2, None, 1.5) == (1.5 - 1.2) / 1.5
    p = {"idade": 50, "hba1c": 10.4, "imc": 30, "creatinina": 1.0}
    assert margem_paciente(p) == folga(10.4, 7.0, 10.5)  # o critério mais apertado manda
    assert math.isnan(margem_paciente({}))


def _ordenado():
    df = base()
    t = treinaveis(df)
    modelo = novo_modelo().fit(features(t), (t["rotulo"] == ELEGIVEL_ROT).astype(int))
    return df, ordenar(df, modelo)


def test_rf_so_ordena_nao_muda_o_resultado_das_regras():
    df, out = _ordenado()
    antes = df.set_index("id_paciente")["resultado"]
    depois = out.set_index("id_paciente")["resultado"]
    assert depois.sort_index().equals(antes.sort_index())  # D8
    assert list(out["resultado"].drop_duplicates()) == ["ELEGÍVEL", "REVISAR", "NÃO ELEGÍVEL"]
    assert list(out["posicao"]) == list(range(1, len(out) + 1))


def test_elegivel_e_nao_elegivel_ordenam_por_margem_revisar_por_rf():
    _, out = _ordenado()
    for res in ["ELEGÍVEL", "NÃO ELEGÍVEL"]:
        g = out[out.resultado == res]
        assert g["margem"].is_monotonic_decreasing
        assert set(g["criterio_ordem"]) == {"margem até o limite"}
    rev = out[out.resultado == "REVISAR"]
    assert rev["probabilidade_elegibilidade"].is_monotonic_decreasing
    assert set(rev["criterio_ordem"]) == {"probabilidade RF"}
    # NÃO ELEGÍVEL "quase elegível" (HbA1c 10,6, logo acima de 10,5) vem primeiro
    assert out[out.resultado == "NÃO ELEGÍVEL"].iloc[0]["hba1c"] == 10.6
