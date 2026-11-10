"""Leitura dos dados numéricos do texto corrido: idade, sexo, HbA1c, creatinina, glicemia, IMC (D27).

Números e siglas seguem padrões fixos ("HbA1c 9,0%", "Cr 0,9", "76a"), então regras
leem com precisão, de graça e na hora. A IA fica com o que exige interpretação
(negação, histórico, familiar). Cada valor vem com o trecho literal do texto.
"""

from __future__ import annotations

import re

from ia.extracao.schema import DadosLidos, ValorLido

_NUM = r"(\d{1,3}(?:[.,]\d{1,2})?)"

_PADROES = {
    # "46 anos", "76a"; ignora "há 10 anos" (tempo de doença)
    "idade": re.compile(r"(?<!há\s)(?<!ha\s)\b(\d{2,3})\s*(?:anos\b|a\b)", re.I),
    "hba1c": re.compile(r"\b(?:hba1c|a1c)\s*(?:de\s*)?[:=]?\s*(\d{1,2}[.,]\d)", re.I),
    # "glicemia de jejum 185", "glic jejum 214", "GJ 231" (e o erro "glicemai")
    "glicemia_jejum": re.compile(r"\b(?:glicemia|glicemai|glic|gj)\b[^0-9|;.]{0,20}?(\d{2,3})\b", re.I),
    # "creatinina 1,1", "creat 1,2", "Cr 0,9"
    "creatinina": re.compile(r"\b(?:creatinina|creat|cr)\b\.?\s*(?:de\s*)?[:=]?\s*(\d[.,]\d{1,2})", re.I),
    "imc": re.compile(r"\bimc\s*(?:de\s*)?[:=]?\s*(\d{2}(?:[.,]\d)?)\b", re.I),
}

# "sexo M", "masculino", "Masc", "Fem", "Pcte F", "Sra.", "homem", "mulher"
_SEXO = re.compile(
    r"\bsexo\s*(masculino|feminino|m|f)\b"
    r"|\b(masc|fem)(?:ino|inino)?\b"
    r"|\b(?:pcte|pct|paciente)\.?\s+(m|f)\b"
    r"|\b(sra|sr|homem|mulher)\b\.?",
    re.I,
)
_SEXO_PALAVRA = {"sra": "F", "mulher": "F", "sr": "M", "homem": "M"}


def _numero(texto: str) -> float:
    return float(texto.replace(",", "."))


def ler_dados(texto: str) -> DadosLidos:
    valores: dict[str, ValorLido] = {}
    for campo, padrao in _PADROES.items():
        m = padrao.search(texto)
        valores[campo] = (
            ValorLido(valor=_numero(m.group(1)), evidencia=m.group(0).strip())
            if m else ValorLido(valor=None, evidencia=None)
        )

    m = _SEXO.search(texto)
    if m:
        palavra = (m.group(4) or "").lower()
        letra = _SEXO_PALAVRA.get(palavra) or (m.group(1) or m.group(2) or m.group(3))[0].upper()
        valores["sexo"] = ValorLido(valor=letra, evidencia=m.group(0).strip())
    else:
        valores["sexo"] = ValorLido(valor=None, evidencia=None)

    return DadosLidos(**valores)
