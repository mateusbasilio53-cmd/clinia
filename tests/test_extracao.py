import json
from pathlib import Path

import pytest

from ia.extracao.cache import CacheExtracoes, hash_texto
from ia.extracao.extrator import carregar_casos, carregar_prompt, executar
from ia.extracao.provedores import ProvedorRegras
from ia.extracao.schema import CampoExtraido, RespostaLLM, schema_resposta_llm
from ia.extracao.verificacao import evidencia_existe, verificar_campo

TEXTO = "Paciente com DM2. Nega história de neoplasia.  Em uso de Metformina 850 mg 2x/dia."
CASOS = Path("prompts/casos_teste_v1.json")


def campo(status, valor, evidencia, confianca="alta"):
    return CampoExtraido(status=status, valor=valor, evidencia=evidencia, confianca=confianca)


# --- verificação de evidência -------------------------------------------------

def test_evidencia_literal_ignora_maiusculas_e_espacos():
    assert evidencia_existe("nega história   de NEOPLASIA.", TEXTO)


def test_evidencia_inventada_nao_passa():
    assert not evidencia_existe("sem câncer", TEXTO)


def test_evidencia_vazia_nao_passa():
    assert not evidencia_existe("  . ", TEXTO)


def test_campo_com_evidencia_inventada_vira_baixa():
    c = verificar_campo(campo("negado", False, "nega câncer"), TEXTO)
    assert not c.evidencia_verificada
    assert c.confianca == "baixa"


def test_campo_coerente_mantem_confianca():
    c = verificar_campo(campo("afirmado", True, "Em uso de Metformina 850 mg"), TEXTO)
    assert c.evidencia_verificada and c.confianca == "alta" and not c.problemas


def test_valor_incoerente_com_status_vira_baixa():
    c = verificar_campo(campo("negado", True, "Nega história de neoplasia"), TEXTO)
    assert c.confianca == "baixa"
    assert any("incoerente" in p for p in c.problemas)


def test_nao_mencionado_sem_evidencia_e_valido():
    c = verificar_campo(campo("nao_mencionado", None, None), TEXTO)
    assert c.evidencia_verificada and c.confianca == "alta"


def test_afirmado_sem_evidencia_vira_baixa():
    c = verificar_campo(campo("afirmado", True, None), TEXTO)
    assert not c.evidencia_verificada and c.confianca == "baixa"


# --- schema enviado à API ------------------------------------------------------

def test_schema_llm_sem_ref_e_fechado():
    schema = schema_resposta_llm()
    texto = json.dumps(schema)
    assert "$ref" not in texto and "$defs" not in texto
    assert schema["additionalProperties"] is False
    assert schema["properties"]["gestacao"]["additionalProperties"] is False


# --- cache ---------------------------------------------------------------------

def test_cache_ida_e_volta(tmp_path):
    cache = CacheExtracoes(tmp_path)
    resposta, _ = ProvedorRegras().extrair(TEXTO)
    h = hash_texto(TEXTO)
    assert cache.obter("modelo-x", "v1", h) is None
    cache.guardar("modelo-x", "v1", h, resposta)
    assert cache.obter("modelo-x", "v1", h) == resposta
    assert cache.obter("modelo-x", "v2", h) is None  # versão de prompt separa o cache


# --- provedor de regras --------------------------------------------------------

@pytest.mark.parametrize(
    "texto, campo_, status",
    [
        ("Nega história de neoplasia.", "neoplasia_ativa", "negado"),
        ("Sem Ca.", "neoplasia_ativa", "negado"),
        ("Há registro de neoplasia em atividade.", "neoplasia_ativa", "afirmado"),
        ("Mãe falecida por Ca de mama.", "neoplasia_ativa", "nao_mencionado"),
        ("Suspeita de gestação, aguarda beta-HCG.", "gestacao", "incerto"),
        ("Gestação atual registrada em prontuário.", "gestacao", "afirmado"),
        ("Metformina suspensa há 2 meses.", "uso_metformina", "negado"),
        ("Não há metformina entre as medicações em uso.", "uso_metformina", "negado"),
        ("Em uso de Metformina 1.000 mg 2x/dia.", "uso_metformina", "afirmado"),
    ],
)
def test_regras_status(texto, campo_, status):
    resposta, _ = ProvedorRegras().extrair(texto)
    assert getattr(resposta, campo_).status == status


def test_regras_evidencia_sempre_verificada_nos_casos():
    itens = carregar_casos(CASOS)
    resultado, resumo = executar(itens, ProvedorRegras(), "regras-v1", cache=None)
    assert len(resultado) == 15
    assert resumo["evidencias_nao_verificadas"] == 0


# --- trava de custo ------------------------------------------------------------

class ProvedorFalso:
    nome = "falso"

    def __init__(self):
        self.chamadas = 0

    def extrair(self, texto):
        self.chamadas += 1
        return ProvedorRegras().extrair(texto)


def test_sem_confirmar_nao_chama_api(tmp_path):
    provedor = ProvedorFalso()
    with pytest.raises(SystemExit, match="2 chamada"):
        executar([("A", "texto a"), ("B", "texto b")], provedor, "v1", CacheExtracoes(tmp_path))
    assert provedor.chamadas == 0


def test_segunda_rodada_usa_cache(tmp_path):
    provedor, cache = ProvedorFalso(), CacheExtracoes(tmp_path)
    itens = [("A", "Sem Ca."), ("B", "Metformina 850 mg.")]
    executar(itens, provedor, "v1", cache, confirmar=True)
    _, resumo = executar(itens, provedor, "v1", cache)  # sem --confirmar: tudo vem do cache
    assert provedor.chamadas == 2
    assert resumo["chamadas_api"] == 0 and resumo["do_cache"] == 2


def test_offline_sem_cache_falha(tmp_path):
    with pytest.raises(SystemExit, match="offline"):
        executar([("A", "x")], ProvedorFalso(), "v1", CacheExtracoes(tmp_path), offline=True)


def test_prompt_v1_carrega():
    texto, versao = carregar_prompt(Path("prompts/extrator_v1.md"))
    assert versao == "extrator_v1"
    assert "neoplasia_ativa" in texto and "```" not in texto
