"""Verificação feita pelo código, nunca pela LLM: a evidência existe no texto? valor e status batem?

Qualquer problema rebaixa a confiança para "baixa", o que manda o caso para REVISAR.
"""

from __future__ import annotations

import re
import unicodedata

from ia.extracao.schema import CAMPOS, CampoExtraido, CampoVerificado, CamposVerificados, RespostaLLM

_ASPAS = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})

VALOR_DO_STATUS = {"afirmado": True, "negado": False, "nao_mencionado": None, "incerto": None}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto).translate(_ASPAS).casefold()
    return re.sub(r"\s+", " ", texto).strip()


def evidencia_existe(evidencia: str, texto: str) -> bool:
    """O trecho aparece literalmente no texto? Ignora só maiúsculas, espaços e pontuação nas pontas."""
    trecho = normalizar(evidencia).strip(" .,;:\"'")
    return bool(trecho) and trecho in normalizar(texto)


def verificar_campo(campo: CampoExtraido, texto: str) -> CampoVerificado:
    problemas: list[str] = []

    if campo.status == "nao_mencionado":
        verificada = campo.evidencia is None
        if not verificada:
            problemas.append("evidência informada para campo não mencionado")
    elif campo.evidencia is None:
        verificada = False
        problemas.append("sem evidência")
    else:
        verificada = evidencia_existe(campo.evidencia, texto)
        if not verificada:
            problemas.append("evidência não encontrada literalmente no texto")

    if campo.valor != VALOR_DO_STATUS[campo.status]:
        problemas.append(f"valor {campo.valor} incoerente com status {campo.status}")

    dados = campo.model_dump()
    if problemas:
        dados["confianca"] = "baixa"
    return CampoVerificado(**dados, evidencia_verificada=verificada, problemas=problemas)


def verificar_resposta(resposta: RespostaLLM, texto: str, notas: dict[str, list[str]] | None = None) -> CamposVerificados:
    """Verifica cada campo; `notas` (da dupla checagem) entram como problemas e rebaixam a confiança."""
    campos = {}
    for nome in CAMPOS:
        campo = verificar_campo(getattr(resposta, nome), texto)
        extras = (notas or {}).get(nome, [])
        if extras:
            campo = campo.model_copy(update={"problemas": [*extras, *campo.problemas], "confianca": "baixa"})
        campos[nome] = campo
    return CamposVerificados(**campos)
