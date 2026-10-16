"""Cache das respostas da LLM em arquivo local.

Cada texto é enviado uma vez por modelo e versão de prompt. Serve para não pagar
de novo e para o modo offline da demo (playbook, Fase 6).

Estrutura: cache/extracoes/<modelo>/<versao_prompt>/<sha256 do texto>.json
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from ia.extracao.schema import RespostaLLM

RAIZ_PADRAO = Path("cache/extracoes")


def hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


class CacheExtracoes:
    def __init__(self, raiz: Path = RAIZ_PADRAO):
        self.raiz = Path(raiz)

    def _caminho(self, modelo: str, versao_prompt: str, hash_: str) -> Path:
        pasta_modelo = re.sub(r"[^\w.-]", "_", modelo)
        return self.raiz / pasta_modelo / versao_prompt / f"{hash_}.json"

    def obter(self, modelo: str, versao_prompt: str, hash_: str) -> RespostaLLM | None:
        caminho = self._caminho(modelo, versao_prompt, hash_)
        if not caminho.exists():
            return None
        return RespostaLLM.model_validate_json(caminho.read_text(encoding="utf-8"))

    def guardar(self, modelo: str, versao_prompt: str, hash_: str, resposta: RespostaLLM) -> None:
        caminho = self._caminho(modelo, versao_prompt, hash_)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(resposta.model_dump_json(indent=2), encoding="utf-8")
