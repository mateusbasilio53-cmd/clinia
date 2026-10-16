"""Quem lê o texto: o provedor de regras (regex, grátis) ou a LLM (Claude via API).

O provedor de regras é o "fallback/checagem auxiliar" da seção 6.2 do playbook:
serve de linha de base no experimento e de mock para o Mateus trabalhar sem chave.
Trocar de provedor de LLM = escrever outra classe com o mesmo método `extrair`.
"""

from __future__ import annotations

import re
from typing import Protocol

from ia.extracao.schema import CampoExtraido, RespostaLLM


class ErroExtracao(Exception):
    pass


class Provedor(Protocol):
    nome: str

    def extrair(self, texto: str) -> tuple[RespostaLLM, str]:
        """Devolve a resposta e o modelo que de fato respondeu."""
        ...


# ---------------------------------------------------------------------------
# Provedor de regras (sem LLM)
# ---------------------------------------------------------------------------

_FAMILIAR = re.compile(r"\b(m[ãa]e|pai|irm[ãa]o?|av[óô]|tio|tia|filh[oa])\b", re.I)

# Para cada campo: termo que identifica o assunto e, em ordem, os padrões de status.
_REGRAS = {
    "neoplasia_ativa": {
        "termo": re.compile(r"neoplasia|c[âa]ncer|\bca\b|oncol[óo]gic|\bqt\b|quimioterapia", re.I),
        "negado": re.compile(r"\bnega\b|\bsem\b|aus[êe]ncia|descart|remiss|curad", re.I),
        "incerto": re.compile(r"suspeita|a esclarecer|investiga|hist[óo]ria de|seguimento", re.I),
    },
    "gestacao": {
        "termo": re.compile(r"gesta|gr[áa]vida|beta[- ]?hcg", re.I),
        "negado": re.compile(r"\bnega\b|\bsem\b|negativo|n[ãa]o gestante|descart", re.I),
        "incerto": re.compile(r"suspeita|aguarda|a esclarecer|atraso menstrual", re.I),
    },
    "uso_metformina": {
        "termo": re.compile(r"metfo?r?mina|\bmtf\b", re.I),
        "negado": re.compile(r"suspens|suspend|n[ãa]o h[áa]|\bsem\b|n[ãa]o iniciou|trocad|substitu", re.I),
        "incerto": re.compile(r"a esclarecer|irregular", re.I),
    },
}

_DIAGNOSTICOS = {
    "diabetes mellitus tipo 2": re.compile(r"\bdm2\b|\bdm tipo i{1,2}\b|diabetes( mellitus)? tipo (2|ii)\b", re.I),
    "hipertensão arterial sistêmica": re.compile(r"\bhas\b|hipertens[ãa]o", re.I),
}


def _frases(texto: str) -> list[str]:
    return [f.strip().rstrip(".") for f in re.split(r"(?<=[.;])\s+", texto) if f.strip()]


def _campo_por_regras(regras: dict, texto: str) -> CampoExtraido:
    for frase in _frases(texto):
        if not regras["termo"].search(frase) or _FAMILIAR.search(frase):
            continue
        for status, valor in (("negado", False), ("incerto", None)):
            if regras[status].search(frase):
                return CampoExtraido(valor=valor, status=status, evidencia=frase, confianca="media")
        return CampoExtraido(valor=True, status="afirmado", evidencia=frase, confianca="media")
    return CampoExtraido(valor=None, status="nao_mencionado", evidencia=None, confianca="media")


class ProvedorRegras:
    nome = "regras-v1"

    def extrair(self, texto: str) -> tuple[RespostaLLM, str]:
        campos = {nome: _campo_por_regras(regras, texto) for nome, regras in _REGRAS.items()}
        diagnosticos = [nome for nome, padrao in _DIAGNOSTICOS.items() if padrao.search(texto)]
        resposta = RespostaLLM(**campos, diagnosticos_mencionados=diagnosticos, observacoes_relevantes=None)
        return resposta, self.nome


# ---------------------------------------------------------------------------
# Provedor Claude (API da Anthropic)
# ---------------------------------------------------------------------------

# Modelos com fallback no servidor: se o modelo recusar, a API tenta outro na mesma chamada.
_COM_FALLBACK = ("claude-opus", "claude-sonnet", "claude-fable")


class ProvedorClaude:
    def __init__(self, modelo: str, prompt_sistema: str, effort: str = "medium"):
        import anthropic

        from ia.extracao.schema import schema_resposta_llm

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(max_retries=3)  # chave vem de ANTHROPIC_API_KEY (.env)
        self.modelo = modelo
        self.nome = modelo
        self.prompt_sistema = prompt_sistema
        self.effort = effort
        self.schema = schema_resposta_llm()

    def extrair(self, texto: str) -> tuple[RespostaLLM, str]:
        parametros = dict(
            model=self.modelo,
            max_tokens=16000,
            system=self.prompt_sistema,
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": self.schema}},
            messages=[{"role": "user", "content": f'Anotação médica:\n"""\n{texto}\n"""'}],
        )
        try:
            if self.modelo.startswith(_COM_FALLBACK):
                resposta = self.client.beta.messages.create(
                    **parametros, betas=["server-side-fallback-2026-07-01"], fallbacks="default"
                )
            else:
                resposta = self.client.messages.create(**parametros)
        except self._anthropic.APIStatusError as e:
            raise ErroExtracao(f"API respondeu {e.status_code}: {e.message}") from e
        except self._anthropic.APIConnectionError as e:
            raise ErroExtracao("sem conexão com a API") from e

        if resposta.stop_reason == "refusal":
            raise ErroExtracao("o modelo recusou a extração")
        if resposta.stop_reason == "max_tokens":
            raise ErroExtracao("resposta cortada por max_tokens")

        texto_json = next((b.text for b in resposta.content if b.type == "text"), None)
        if texto_json is None:
            raise ErroExtracao("resposta sem bloco de texto")
        return RespostaLLM.model_validate_json(texto_json), resposta.model
