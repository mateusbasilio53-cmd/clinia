import pandas as pd

from ia.entrada.planilha import textos_para_extracao, validar


def base(**alteracoes):
    linha = {
        "id_paciente": "PAC-001", "idade": 50, "sexo": "F", "diagnostico": "DM2",
        "hba1c": 8.0, "creatinina": 1.0, "glicemia_jejum": 150, "imc": 30.0,
        "medicamentos": "Metformina 850 mg", "neoplasia_ativa": "Não", "gestacao": "Não",
        "anotacao_medica": "Texto fictício.",
    }
    linha.update(alteracoes)
    return pd.DataFrame([linha])


def test_base_valida():
    assert validar(base()).ok


def test_coluna_ausente_bloqueia():
    assert not validar(base().drop(columns=["anotacao_medica"])).ok


def test_id_duplicado_bloqueia():
    df = pd.concat([base(), base()])
    assert any("duplicados" in e for e in validar(df).erros)


def test_valor_fora_da_faixa_bloqueia():
    assert any("hba1c" in e for e in validar(base(hba1c=25)).erros)


def test_texto_vazio_bloqueia():
    assert not validar(base(anotacao_medica="  ")).ok


def test_cpf_no_texto_bloqueia():
    assert any("CPF" in e for e in validar(base(anotacao_medica="CPF 123.456.789-00")).erros)


def test_gestacao_em_homem_bloqueia():
    assert not validar(base(sexo="M", gestacao="Sim")).ok


def test_extracao_recebe_so_id_e_texto():
    assert textos_para_extracao(base()) == [("PAC-001", "Texto fictício.")]
