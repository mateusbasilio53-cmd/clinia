"""Leitura e validação da planilha de pacientes fictícios (simulação do AGHUx)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ABA_PACIENTES = "Base_Pacientes"

COLUNAS_OBRIGATORIAS = [
    "id_paciente",
    "idade",
    "sexo",
    "diagnostico",
    "hba1c",
    "creatinina",
    "glicemia_jejum",
    "imc",
    "anotacao_medica",
]

# D14: no AGHUx estas informações estariam só no texto livre. Elas não entram
# no pipeline; servem de gabarito para medir a extração da LLM.
COLUNAS_GABARITO = ["neoplasia_ativa", "gestacao", "medicamentos"]

# Rótulos da equipe clínica: só para avaliação e treino, nunca entrada da decisão.
COLUNAS_ROTULO = ["grupo_simulacao", "marcador_caso", "elegibilidade_calculada"]

COLUNAS_NUMERICAS = ["idade", "hba1c", "creatinina", "glicemia_jejum", "imc"]

# Faixas fisiologicamente plausíveis (não são os critérios do protocolo).
FAIXAS_PLAUSIVEIS = {
    "idade": (0, 120),
    "hba1c": (3, 20),
    "creatinina": (0.1, 15),
    "glicemia_jejum": (30, 800),
    "imc": (10, 80),
}

PADRAO_ID = re.compile(r"^PAC-\d{3,4}$")

# Sinais de dado real (regra 5 do playbook). Qualquer ocorrência é bloqueante.
SINAIS_DADO_REAL = {
    "CPF": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-\d{2}\b"),
    "telefone": re.compile(r"\(?\b\d{2}\)?\s?9?\d{4}-\d{4}\b"),
    "e-mail": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
}
# Sinal mais fraco: pode ser falso positivo, então vira só aviso.
PADRAO_NOME = re.compile(r"\b(?:Sr|Sra|Dr|Dra)\.?\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+")


@dataclass
class RelatorioValidacao:
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.erros


def caminho_planilha(caminho: str | None = None) -> Path:
    """Resolve o caminho da planilha: argumento ou variável CLINIA_PLANILHA do .env."""
    valor = caminho or os.getenv("CLINIA_PLANILHA")
    if not valor:
        raise SystemExit("Informe --planilha ou defina CLINIA_PLANILHA no .env")
    p = Path(valor)
    if not p.exists():
        raise SystemExit(f"Planilha não encontrada: {p}")
    return p


def ler_planilha(caminho: str | Path) -> pd.DataFrame:
    return pd.read_excel(caminho, sheet_name=ABA_PACIENTES)


def textos_para_extracao(df: pd.DataFrame) -> list[tuple[str, str]]:
    """Só o que vai para a LLM: id pseudônimo + texto livre. Nada de colunas de gabarito."""
    return list(zip(df["id_paciente"].astype(str), df["anotacao_medica"].astype(str)))


def validar(df: pd.DataFrame) -> RelatorioValidacao:
    r = RelatorioValidacao()

    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltando:
        r.erros.append(f"Colunas obrigatórias ausentes: {', '.join(faltando)}")
        return r

    ids = df["id_paciente"].astype(str)
    duplicados = sorted(ids[ids.duplicated()].unique())
    if duplicados:
        r.erros.append(f"ids duplicados: {', '.join(duplicados)}")
    fora_padrao = sorted(i for i in ids if not PADRAO_ID.match(i))
    if fora_padrao:
        r.avisos.append(f"ids fora do padrão PAC-NNN: {', '.join(fora_padrao[:10])}")

    for col in COLUNAS_OBRIGATORIAS:
        vazios = df.loc[df[col].isna() | (df[col].astype(str).str.strip() == ""), "id_paciente"]
        if len(vazios):
            r.erros.append(f"{col} vazio em {len(vazios)} linha(s): {', '.join(map(str, vazios[:10]))}")

    for col in COLUNAS_NUMERICAS:
        numeros = pd.to_numeric(df[col], errors="coerce")
        nao_numericos = df.loc[numeros.isna() & df[col].notna(), "id_paciente"]
        if len(nao_numericos):
            r.erros.append(f"{col} não numérico em: {', '.join(map(str, nao_numericos[:10]))}")
        minimo, maximo = FAIXAS_PLAUSIVEIS[col]
        fora = df.loc[(numeros < minimo) | (numeros > maximo), "id_paciente"]
        if len(fora):
            r.erros.append(f"{col} fora da faixa plausível {minimo}–{maximo} em: {', '.join(map(str, fora[:10]))}")

    sexos = set(df["sexo"].dropna().astype(str)) - {"M", "F"}
    if sexos:
        r.avisos.append(f"valores de sexo inesperados: {', '.join(sorted(sexos))}")

    if "gestacao" in df.columns:
        gestantes = df[df["gestacao"].astype(str).str.strip() == "Sim"]
        homens = gestantes.loc[gestantes["sexo"] == "M", "id_paciente"]
        if len(homens):
            r.erros.append(f"gestação = Sim em paciente do sexo M: {', '.join(map(str, homens))}")
        idosas = gestantes.loc[pd.to_numeric(gestantes["idade"], errors="coerce") > 50, ["id_paciente", "idade"]]
        if len(idosas):
            lista = ", ".join(f"{i} ({int(a)} anos)" for i, a in idosas.itertuples(index=False))
            r.avisos.append(f"gestação acima de 50 anos (plausibilidade clínica a validar): {lista}")

    # pandas 3 usa o tipo "str" para texto, não mais "object"; aceitar os dois.
    colunas_texto = [c for c in df.columns if pd.api.types.is_string_dtype(df[c]) or df[c].dtype == object]
    for nome, padrao in SINAIS_DADO_REAL.items():
        for col in colunas_texto:
            achados = df.loc[df[col].astype(str).str.contains(padrao, na=False), "id_paciente"]
            if len(achados):
                r.erros.append(f"possível {nome} real na coluna {col}: {', '.join(map(str, achados[:10]))}")
    for col in colunas_texto:
        achados = df.loc[df[col].astype(str).str.contains(PADRAO_NOME, na=False), "id_paciente"]
        if len(achados):
            r.avisos.append(f"possível nome próprio na coluna {col}: {', '.join(map(str, achados[:10]))}")

    return r


def estatisticas(df: pd.DataFrame) -> str:
    linhas = [f"Pacientes: {len(df)}"]
    resumo = df[COLUNAS_NUMERICAS].apply(pd.to_numeric, errors="coerce").describe().T
    linhas.append(resumo[["min", "mean", "max"]].round(2).to_string())
    for col in ["sexo", "grupo_simulacao", "elegibilidade_calculada"]:
        if col in df.columns:
            contagem = df[col].value_counts().to_dict()
            linhas.append(f"{col}: {contagem}")
    tamanho = df["anotacao_medica"].astype(str).str.len()
    linhas.append(f"anotacao_medica: {tamanho.min()}–{tamanho.max()} caracteres (média {tamanho.mean():.0f})")
    return "\n".join(linhas)
