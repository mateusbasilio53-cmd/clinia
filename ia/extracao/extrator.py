"""Roda a extração e gera extracoes.json (o arquivo que vai para o Mateus).

Exemplos:
    # grátis, sem chave: provedor de regras nos 200 pacientes
    py -m ia.extracao.extrator --provedor regras

    # LLM nos 15 casos de teste: primeiro mostra quantas chamadas pagas vai fazer
    py -m ia.extracao.extrator --provedor claude --casos prompts/casos_teste_v1.json
    py -m ia.extracao.extrator --provedor claude --casos prompts/casos_teste_v1.json --confirmar

    # demo sem internet: só usa o que já está no cache
    py -m ia.extracao.extrator --provedor claude --offline

O texto clínico nunca é impresso no terminal; só ids e contagens.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from ia.entrada.planilha import caminho_planilha, ler_planilha, textos_para_extracao
from ia.extracao.cache import CacheExtracoes, hash_texto
from ia.extracao.combinacao import combinar
from ia.extracao.provedores import ErroExtracao, Provedor, ProvedorClaude, ProvedorOllama, ProvedorRegras
from ia.extracao.schema import CAMPOS, CampoVerificado, CamposVerificados, ExtracaoPaciente, RespostaLLM
from ia.extracao.verificacao import verificar_resposta

PROMPT_PADRAO = Path("prompts/extrator_v1.md")
PROMPT_PADRAO_OLLAMA = Path("prompts/extrator_v2.md")  # com exemplos, para modelo pequeno (D23)
MODELO_PADRAO = "claude-opus-5-5"
OLLAMA_MODELO_PADRAO = "qwen2.5:3b"


def carregar_prompt(caminho: Path) -> tuple[str, str]:
    """Devolve (texto do prompt, versão). O prompt é o primeiro bloco ```text do arquivo."""
    conteudo = caminho.read_text(encoding="utf-8")
    achado = re.search(r"```text\n(.*?)\n```", conteudo, re.S)
    if not achado:
        raise SystemExit(f"Nenhum bloco ```text em {caminho}")
    return achado.group(1).strip(), caminho.stem


def carregar_casos(caminho: Path) -> list[tuple[str, str]]:
    casos = json.loads(caminho.read_text(encoding="utf-8"))
    return [(c["id"], c["anotacao_medica"]) for c in casos]


def _falha(id_paciente: str, motivo: str, modelo: str, versao: str, hash_: str) -> ExtracaoPaciente:
    """Extração que falhou: todos os campos incertos e com confiança baixa, para cair em REVISAR."""
    campo = CampoVerificado(
        valor=None, status="incerto", evidencia=None, confianca="baixa",
        evidencia_verificada=False, problemas=[f"falha na extração: {motivo}"],
    )
    return ExtracaoPaciente(
        id_paciente=id_paciente,
        campos=CamposVerificados(**{nome: campo for nome in CAMPOS}),
        diagnosticos_mencionados=[], observacoes_relevantes=None, evidencia_verificada=False,
        modelo_llm=modelo, versao_prompt=versao, hash_texto=hash_, extraido_em=datetime.now().isoformat(timespec="seconds"),
    )


def montar_item(
    id_paciente: str, texto: str, resposta: RespostaLLM, modelo: str, versao: str,
    notas: dict[str, list[str]] | None = None,
) -> ExtracaoPaciente:
    campos = verificar_resposta(resposta, texto, notas)
    return ExtracaoPaciente(
        id_paciente=id_paciente,
        campos=campos,
        diagnosticos_mencionados=resposta.diagnosticos_mencionados,
        observacoes_relevantes=resposta.observacoes_relevantes,
        evidencia_verificada=all(getattr(campos, nome).evidencia_verificada for nome in CAMPOS),
        modelo_llm=modelo,
        versao_prompt=versao,
        hash_texto=hash_texto(texto),
        extraido_em=datetime.now().isoformat(timespec="seconds"),
    )


def executar(
    itens: list[tuple[str, str]],
    provedor: Provedor,
    versao: str,
    cache: CacheExtracoes | None,
    confirmar: bool = False,
    offline: bool = False,
    dupla_checagem: bool = False,
) -> tuple[list[ExtracaoPaciente], dict]:
    pendentes = [i for i, (_, t) in enumerate(itens) if cache is None or cache.obter(provedor.nome, versao, hash_texto(t)) is None]
    if cache is not None and pendentes:
        if offline:
            raise SystemExit(f"Modo offline: {len(pendentes)} texto(s) sem extração no cache. Rode online antes.")
        if provedor.pago and not confirmar:
            raise SystemExit(
                f"{len(pendentes)} chamada(s) paga(s) ao modelo {provedor.nome} "
                f"({len(itens) - len(pendentes)} já no cache). Rode de novo com --confirmar para executar."
            )

    resultado, falhas, chamadas = [], [], 0
    inicio = time.perf_counter()
    for n, (id_paciente, texto) in enumerate(itens, 1):
        h = hash_texto(texto)
        resposta = cache.obter(provedor.nome, versao, h) if cache else None
        modelo_usado = provedor.nome
        if resposta is None:
            try:
                resposta, modelo_usado = provedor.extrair(texto)
                chamadas += cache is not None
            except (ErroExtracao, ValueError) as e:
                falhas.append(id_paciente)
                print(f"  [{n}/{len(itens)}] {id_paciente}: FALHA ({e})", file=sys.stderr)
                resultado.append(_falha(id_paciente, str(e), provedor.nome, versao, h))
                continue
            if cache is not None:
                cache.guardar(provedor.nome, versao, h, resposta)
                print(f"  [{n}/{len(itens)}] {id_paciente}: extraído", file=sys.stderr)
        notas = None
        if dupla_checagem:
            resposta, notas = combinar(resposta, ProvedorRegras().extrair(texto)[0])
            modelo_usado = f"{modelo_usado}+{ProvedorRegras.nome}"
        resultado.append(montar_item(id_paciente, texto, resposta, modelo_usado, versao, notas))

    baixa =sum(getattr(r.campos, c).confianca == "baixa" for r in resultado for c in CAMPOS)
    resumo = {
        "pacientes": len(itens),
        "chamadas_api": chamadas,
        "do_cache": len(itens) - chamadas - len(falhas) if cache else 0,
        "falhas": falhas,
        "campos_confianca_baixa": baixa,
        "evidencias_nao_verificadas": sum(
            not getattr(r.campos, c).evidencia_verificada for r in resultado for c in CAMPOS
        ),
        "segundos": round(time.perf_counter() - inicio, 2),
        "dupla_checagem": dupla_checagem,
        "campos_divergentes": sum(
            any(p.startswith(("leituras divergentes", "IA disse")) for p in getattr(r.campos, c).problemas)
            for r in resultado for c in CAMPOS
        ),
    }
    return resultado, resumo


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description="Extrai campos estruturados do texto livre.")
    origem = p.add_mutually_exclusive_group()
    origem.add_argument("--planilha", help="caminho do .xlsx (padrão: CLINIA_PLANILHA)")
    origem.add_argument("--casos", type=Path, help="arquivo JSON de casos de teste")
    p.add_argument("--provedor", choices=["regras", "ollama", "claude"], default="regras")
    p.add_argument("--modelo", help=f"padrão: CLINIA_MODELO; senão {OLLAMA_MODELO_PADRAO} (ollama) ou {MODELO_PADRAO} (claude)")
    p.add_argument("--effort", default=os.getenv("CLINIA_EFFORT", "medium"), choices=["low", "medium", "high"])
    p.add_argument("--prompt", type=Path, help=f"padrão: {PROMPT_PADRAO_OLLAMA} (ollama) ou {PROMPT_PADRAO} (claude)")
    p.add_argument("--ids", help="só estes ids, separados por vírgula")
    p.add_argument("--limite", type=int, help="só os N primeiros")
    p.add_argument("--saida", type=Path, help="padrão: saidas/AAAA-MM-DD_HHMM/extracoes_<provedor>.json")
    p.add_argument("--confirmar", action="store_true", help="autoriza as chamadas pagas")
    p.add_argument("--offline", action="store_true", help="usa só o cache, sem chamar a API")
    p.add_argument("--sem-dupla-checagem", action="store_true", help="usa só a IA, sem conferir com as regras (D24)")
    args = p.parse_args(argv)

    itens = carregar_casos(args.casos) if args.casos else textos_para_extracao(ler_planilha(caminho_planilha(args.planilha)))
    if args.ids:
        escolhidos = {i.strip() for i in args.ids.split(",")}
        itens = [it for it in itens if it[0] in escolhidos]
    if args.limite:
        itens = itens[: args.limite]

    if args.provedor == "regras":
        provedor, versao, cache = ProvedorRegras(), "regras-v1", None
    else:
        padrao = PROMPT_PADRAO_OLLAMA if args.provedor == "ollama" else PROMPT_PADRAO
        prompt, versao = carregar_prompt(args.prompt or padrao)
        # CLINIA_CACHE permite usar outra pasta (ex.: medir a velocidade sem as respostas prontas)
        cache = CacheExtracoes(Path(os.getenv("CLINIA_CACHE", "cache/extracoes")))
        if args.provedor == "ollama":
            modelo = args.modelo or os.getenv("CLINIA_MODELO_OLLAMA", OLLAMA_MODELO_PADRAO)
            provedor = ProvedorOllama(modelo, prompt, os.getenv("OLLAMA_URL", "http://localhost:11434"))
        else:
            modelo = args.modelo or os.getenv("CLINIA_MODELO", MODELO_PADRAO)
            provedor = ProvedorClaude(modelo, prompt, args.effort)

    dupla = args.provedor != "regras" and not args.sem_dupla_checagem
    resultado, resumo = executar(itens, provedor, versao, cache, args.confirmar, args.offline, dupla)

    saida = args.saida or Path("saidas") / datetime.now().strftime("%Y-%m-%d_%H%M") / f"extracoes_{args.provedor}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(
        json.dumps([r.model_dump() for r in resultado], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(f"Gerado {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
