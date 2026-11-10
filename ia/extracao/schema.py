"""Formato da extração: o que a LLM devolve e o que vai para o Mateus (contrato).

Para regenerar contratos/extracao.schema.json depois de mudar este arquivo:
    py -m ia.extracao.schema
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

Status = Literal["afirmado", "negado", "nao_mencionado", "incerto"]
Confianca = Literal["alta", "media", "baixa"]

CAMPOS = ("neoplasia_ativa", "gestacao", "uso_metformina")


class CampoExtraido(BaseModel):
    """Um campo como a LLM devolve."""

    model_config = ConfigDict(extra="forbid")

    valor: bool | None
    status: Status
    evidencia: str | None
    confianca: Confianca


class RespostaLLM(BaseModel):
    """Resposta completa da LLM para uma anotação."""

    model_config = ConfigDict(extra="forbid")

    neoplasia_ativa: CampoExtraido
    gestacao: CampoExtraido
    uso_metformina: CampoExtraido
    diagnosticos_mencionados: list[str]
    observacoes_relevantes: str | None


class CampoVerificado(CampoExtraido):
    """Campo depois da verificação pelo código (evidência literal e coerência)."""

    evidencia_verificada: bool
    problemas: list[str]


class CamposVerificados(BaseModel):
    model_config = ConfigDict(extra="forbid")

    neoplasia_ativa: CampoVerificado
    gestacao: CampoVerificado
    uso_metformina: CampoVerificado


class ValorLido(BaseModel):
    """Um dado lido do texto pelas regras (número ou sexo), com o trecho literal."""

    model_config = ConfigDict(extra="forbid")

    valor: float | str | None
    evidencia: str | None


class DadosLidos(BaseModel):
    """Ficha numérica montada só a partir do texto corrido (D27). null = não está no texto."""

    model_config = ConfigDict(extra="forbid")

    idade: ValorLido
    sexo: ValorLido
    hba1c: ValorLido
    creatinina: ValorLido
    glicemia_jejum: ValorLido
    imc: ValorLido


CAMPOS_LIDOS = ("idade", "sexo", "hba1c", "creatinina", "glicemia_jejum", "imc")


class ExtracaoPaciente(BaseModel):
    """Um item de extracoes.json: a passagem do Paulo para o Mateus."""

    model_config = ConfigDict(extra="forbid")

    id_paciente: str
    dados_lidos: DadosLidos
    campos: CamposVerificados
    diagnosticos_mencionados: list[str]
    observacoes_relevantes: str | None
    evidencia_verificada: bool
    modelo_llm: str
    versao_prompt: str
    hash_texto: str
    extraido_em: str


def _inline_refs(schema: dict) -> dict:
    """Troca $ref por definições inline e remove títulos, para enviar à API um schema simples."""
    defs = schema.pop("$defs", {})

    def resolver(no):
        if isinstance(no, dict):
            if "$ref" in no:
                return resolver(copy.deepcopy(defs[no["$ref"].split("/")[-1]]))
            return {k: resolver(v) for k, v in no.items() if k != "title"}
        if isinstance(no, list):
            return [resolver(v) for v in no]
        return no

    return resolver(schema)


def schema_resposta_llm() -> dict:
    return _inline_refs(RespostaLLM.model_json_schema())


def schema_contrato() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "extracoes.json — contrato entre extração (Paulo) e regras/RF (Mateus)",
        "type": "array",
        "items": _inline_refs(ExtracaoPaciente.model_json_schema()),
    }


if __name__ == "__main__":
    destino = Path("contratos/extracao.schema.json")
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(schema_contrato(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gerado {destino}")
