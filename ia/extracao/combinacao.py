"""Dupla checagem (D24): a leitura da IA é conferida pelas regras (regex) e por travas do código.

Quando as duas leituras discordam sobre o que importa para a decisão ("tem" x "não tem"),
o campo vira "incerto" com confiança baixa: a CLINIA não decide, chama o humano.

"negado" e "nao_mencionado" contam como a mesma conclusão ("não tem"). Se uma leitura
diz "negado" com trecho e a outra "nao_mencionado", fica o "negado", que tem evidência.
"""

from __future__ import annotations

import re

from ia.extracao.schema import CAMPOS, CampoExtraido, RespostaLLM

_TERMO_METFORMINA = re.compile(r"metfo?r?mina|\bmtf\b", re.I)

NOME_LEGIVEL = {"afirmado": "tem", "negado": "não tem", "nao_mencionado": "não mencionado", "incerto": "incerto"}


def _conclusao(status: str) -> str:
    return "nao" if status in ("negado", "nao_mencionado") else status


def _incerto(base: CampoExtraido) -> CampoExtraido:
    return CampoExtraido(valor=None, status="incerto", evidencia=base.evidencia, confianca="baixa")


def combinar(ia: RespostaLLM, regras: RespostaLLM) -> tuple[RespostaLLM, dict[str, list[str]]]:
    """Devolve a resposta final e, por campo, as notas que explicam cada ajuste."""
    campos: dict[str, CampoExtraido] = {}
    notas: dict[str, list[str]] = {c: [] for c in CAMPOS}

    for nome in CAMPOS:
        a, r = getattr(ia, nome), getattr(regras, nome)
        final = a

        # Trava: "usa metformina" só vale se o trecho citado fala de metformina.
        if nome == "uso_metformina" and a.status == "afirmado" and not _TERMO_METFORMINA.search(a.evidencia or ""):
            notas[nome].append("IA disse que usa metformina, mas o trecho citado não fala de metformina")
            final = _incerto(a)
        elif _conclusao(a.status) != _conclusao(r.status):
            notas[nome].append(
                f"leituras divergentes: IA = {NOME_LEGIVEL[a.status]}, regras = {NOME_LEGIVEL[r.status]}"
            )
            final = _incerto(a if a.evidencia else r)
        elif a.status == "nao_mencionado" and r.status == "negado":
            final = r  # mesma conclusão, mas as regras acharam o trecho da negação

        campos[nome] = final

    resposta = RespostaLLM(
        **campos,
        diagnosticos_mencionados=ia.diagnosticos_mencionados,
        observacoes_relevantes=ia.observacoes_relevantes,
    )
    return resposta, notas
