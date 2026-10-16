from ia.extracao.combinacao import combinar
from ia.extracao.schema import CampoExtraido, RespostaLLM
from ia.extracao.verificacao import verificar_resposta

NM = CampoExtraido(valor=None, status="nao_mencionado", evidencia=None, confianca="alta")


def resposta(**campos):
    base = {"neoplasia_ativa": NM, "gestacao": NM, "uso_metformina": NM}
    base.update(campos)
    return RespostaLLM(**base, diagnosticos_mencionados=[], observacoes_relevantes=None)


def campo(status, valor, evidencia):
    return CampoExtraido(valor=valor, status=status, evidencia=evidencia, confianca="alta")


def test_concordancia_mantem_leitura_da_ia():
    ia = resposta(uso_metformina=campo("afirmado", True, "metformina 850 mg"))
    final, notas = combinar(ia, ia)
    assert final == ia and not any(notas.values())


def test_divergencia_vira_incerto_com_nota():
    ia = resposta()  # IA: não mencionado
    regras = resposta(neoplasia_ativa=campo("afirmado", True, "Em QT para Ca de cólon"))
    final, notas = combinar(ia, regras)
    assert final.neoplasia_ativa.status == "incerto"
    assert final.neoplasia_ativa.confianca == "baixa"
    assert final.neoplasia_ativa.evidencia == "Em QT para Ca de cólon"  # usa o trecho de quem achou
    assert "divergentes" in notas["neoplasia_ativa"][0]


def test_negado_e_nao_mencionado_nao_divergem_e_fica_o_negado():
    ia = resposta()
    regras = resposta(neoplasia_ativa=campo("negado", False, "Nega neoplasias"))
    final, notas = combinar(ia, regras)
    assert final.neoplasia_ativa.status == "negado"
    assert not notas["neoplasia_ativa"]


def test_trava_metformina_com_evidencia_de_outro_remedio():
    ia = resposta(uso_metformina=campo("afirmado", True, "Em uso de empagliflozina 25mg/dia"))
    final, notas = combinar(ia, ia)
    assert final.uso_metformina.status == "incerto"
    assert "não fala de metformina" in notas["uso_metformina"][0]


def test_mtf_conta_como_metformina():
    ia = resposta(uso_metformina=campo("afirmado", True, "MTF 850mg 12/12h"))
    final, notas = combinar(ia, ia)
    assert final.uso_metformina.status == "afirmado" and not notas["uso_metformina"]


def test_notas_viram_problemas_e_confianca_baixa():
    texto = "Em QT para Ca de cólon."
    final, notas = combinar(resposta(), resposta(neoplasia_ativa=campo("afirmado", True, "Em QT para Ca de cólon")))
    campos = verificar_resposta(final, texto, notas)
    assert campos.neoplasia_ativa.confianca == "baixa"
    assert any("divergentes" in p for p in campos.neoplasia_ativa.problemas)
