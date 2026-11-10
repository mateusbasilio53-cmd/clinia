"""Pandas, parte 2: aplica o protocolo a cada paciente → ELEGÍVEL / NÃO ELEGÍVEL / REVISAR.

Como cada leitura do texto é tratada (docs/PARA_O_MATEUS.md, seção 3):

    leitura           exclusão (neoplasia, gestação)   inclusão (metformina)
    afirmado          NÃO ELEGÍVEL                     atende
    negado            atende                           NÃO ELEGÍVEL
    nao_mencionado    atende                           REVISAR
    incerto           REVISAR                          REVISAR
    confiança baixa   REVISAR                          REVISAR

Número não encontrado no texto → REVISAR.
Ordem de decisão: algum limitante → NÃO ELEGÍVEL (os motivos de revisão vão junto
nos limitantes); senão, algo a revisar → REVISAR; senão ELEGÍVEL.

Uso:
    py -m ia.regras.criterios --planilha dados/pacientes_ficticios_PAC201-300.xlsx --extracoes entregas/extracoes_base2.json
"""

from __future__ import annotations

import argparse
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

import pandas as pd

from ia.regras.protocolo import PROTOCOLO_DEMO, Protocolo

ELEGIVEL, NAO_ELEGIVEL, REVISAR = "ELEGÍVEL", "NÃO ELEGÍVEL", "REVISAR"

# Como o diagnóstico exigido aparece escrito na coluna diagnostico.
SINONIMOS_DIAGNOSTICO = {
    "DM2": ("dm2", "dm 2", "dm tipo 2", "dm tipo ii", "diabetes tipo 2", "diabetes tipo ii",
            "diabetes mellitus tipo 2", "diabetes mellitus tipo ii"),
}

ROTULOS = {
    "neoplasia_ativa": "Neoplasia ativa",
    "gestacao": "Gestação",
    "uso_metformina": "Metformina",
}


@dataclass
class Avaliacao:
    resultado: str = ""
    atendidos: list[str] = field(default_factory=list)
    limitantes: list[str] = field(default_factory=list)
    revisar: list[str] = field(default_factory=list)
    evidencias: list[str] = field(default_factory=list)


def _vazio(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _num(v: float) -> str:
    return f"{v:g}".replace(".", ",")


def _faixa(a: Avaliacao, p: Mapping, nome: str, rotulo: str, unidade: str, minimo, maximo) -> None:
    if minimo is None and maximo is None:
        return
    v = p.get(nome)
    if _vazio(v):
        a.revisar.append(f"{rotulo}: não encontrado no texto")
        return
    if minimo is not None and v < minimo:
        a.limitantes.append(f"{rotulo} {_num(v)}{unidade} abaixo do mínimo de {_num(minimo)}{unidade}")
    elif maximo is not None and v > maximo:
        a.limitantes.append(f"{rotulo} {_num(v)}{unidade} acima do máximo de {_num(maximo)}{unidade}")
    else:
        a.atendidos.append(f"{rotulo} {_num(v)}{unidade}")
    if p.get(f"{nome}_evidencia"):
        a.evidencias.append(f'{rotulo} ← "{p[f"{nome}_evidencia"]}"')


def _motivo(p: Mapping, campo: str, padrao: str) -> str:
    problemas = p.get(f"{campo}_problemas") or []
    return f"{ROTULOS[campo]}: {'; '.join(problemas) if problemas else padrao}"


def _leitura(a: Avaliacao, p: Mapping, campo: str, exclusao: bool) -> None:
    status, confianca = p.get(f"{campo}_status"), p.get(f"{campo}_confianca")
    rotulo = ROTULOS[campo]
    if p.get(f"{campo}_evidencia"):
        a.evidencias.append(f'{rotulo} ← "{p[f"{campo}_evidencia"]}"')
    if status is None or (isinstance(status, float) and math.isnan(status)):
        a.revisar.append(f"{rotulo}: sem leitura do texto")
    elif status == "incerto":
        a.revisar.append(_motivo(p, campo, "leitura incerta"))
    elif confianca == "baixa":
        a.revisar.append(_motivo(p, campo, "confiança baixa"))
    elif exclusao:
        if status == "afirmado":
            a.limitantes.append(f"{rotulo} presente")
        else:  # negado ou nao_mencionado
            a.atendidos.append(f"Sem {rotulo.lower()}")
    elif status == "afirmado":
        a.atendidos.append(f"Usa {rotulo.lower()}")
    elif status == "negado":
        a.limitantes.append(f"Não usa {rotulo.lower()}")
    else:  # nao_mencionado: sem prova de uso
        a.revisar.append(f"{rotulo}: uso não mencionado no texto")


def _normalizar_diagnostico(texto) -> str:
    """'diabetes_mellitus_tipo_2' e 'diabetes_tipo2' -> 'diabetes mellitus tipo 2' e 'diabetes tipo 2'."""
    t = re.sub(r"[_\-]+", " ", str(texto).lower())
    t = re.sub(r"tipo(?=(2|ii)\b)", "tipo ", t)
    return re.sub(r"\s+", " ", t)


def _diagnostico(a: Avaliacao, p: Mapping, exigido: str) -> None:
    texto = p.get("diagnostico")
    if _vazio(texto) or not str(texto).strip():
        a.revisar.append("Diagnóstico: não informado")
        return
    termos = SINONIMOS_DIAGNOSTICO.get(exigido, (exigido.lower(),))
    if any(t in _normalizar_diagnostico(texto) for t in termos):
        a.atendidos.append(f"Diagnóstico {exigido}")
    else:  # texto não reconhecido não prova que o paciente não tem o diagnóstico
        a.revisar.append(f"Diagnóstico: {exigido} não reconhecido em \"{texto}\"")


def avaliar(paciente: Mapping, protocolo: Protocolo = PROTOCOLO_DEMO) -> Avaliacao:
    """Camada 1 (D7): decisão por regras fixas para um paciente (uma linha de ia.dados.juntar)."""
    a, pr = Avaliacao(), protocolo
    if pr.diagnostico_exigido:
        _diagnostico(a, paciente, pr.diagnostico_exigido)
    _faixa(a, paciente, "idade", "Idade", " anos", pr.idade_min, pr.idade_max)
    _faixa(a, paciente, "hba1c", "HbA1c", "%", pr.hba1c_min, pr.hba1c_max)
    _faixa(a, paciente, "imc", "IMC", " kg/m²", pr.imc_min, pr.imc_max)
    _faixa(a, paciente, "creatinina", "Creatinina", " mg/dL", None, pr.creatinina_max)
    _faixa(a, paciente, "glicemia_jejum", "Glicemia de jejum", " mg/dL", None, pr.glicemia_jejum_max)
    if pr.permite_neoplasia_ativa is False:
        _leitura(a, paciente, "neoplasia_ativa", exclusao=True)
    if pr.permite_gestacao is False:
        _leitura(a, paciente, "gestacao", exclusao=True)
    if pr.exige_metformina:
        _leitura(a, paciente, "uso_metformina", exclusao=False)

    if a.limitantes:
        # Decisão do Mateus (18/10): o número já exclui com certeza; a dúvida vira motivo extra.
        a.resultado = NAO_ELEGIVEL
        a.limitantes += [f"também a revisar: {m}" for m in a.revisar]
    elif a.revisar:
        a.resultado = REVISAR
    else:
        a.resultado = ELEGIVEL
    return a


def aplicar(df: pd.DataFrame, protocolo: Protocolo = PROTOCOLO_DEMO) -> pd.DataFrame:
    """Acrescenta resultado, critérios atendidos/limitantes, motivos de revisão e evidências."""
    avaliacoes = [avaliar(linha, protocolo) for linha in df.to_dict("records")]
    out = df.copy()
    out["resultado"] = [a.resultado for a in avaliacoes]
    out["criterios_atendidos"] = ["; ".join(a.atendidos) for a in avaliacoes]
    out["criterios_limitantes"] = ["; ".join(a.limitantes) for a in avaliacoes]
    out["motivo_revisar"] = ["; ".join(a.revisar) if a.resultado == REVISAR else "" for a in avaliacoes]
    out["evidencias_texto"] = [" | ".join(a.evidencias) for a in avaliacoes]
    return out


def main(argv: list[str] | None = None) -> int:
    from ia.dados.juntar import carregar

    p = argparse.ArgumentParser(description="Aplica o protocolo da demo a uma base.")
    p.add_argument("--planilha", required=True)
    p.add_argument("--extracoes", required=True)
    args = p.parse_args(argv)
    df = aplicar(carregar(args.planilha, args.extracoes))
    print(df["resultado"].value_counts().to_string(), "\n")
    for _, r in df.head(5).iterrows():
        print(f"{r.id_paciente}  {r.resultado}\n  atende: {r.criterios_atendidos}\n"
              f"  limita: {r.criterios_limitantes}\n  revisar: {r.motivo_revisar}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
