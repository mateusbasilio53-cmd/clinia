# CLINIA

Triagem inteligente de pacientes para pesquisa clínica. MVP previsto para 04/12/2026.

- Plano e regras de trabalho: [CLINIA_MVP_PLAYBOOK.md](CLINIA_MVP_PLAYBOOK.md)
- Quem faz o quê: [CLINIA_DIVISAO_TAREFAS.md](CLINIA_DIVISAO_TAREFAS.md)
- Decisões: [docs/DECISOES.md](docs/DECISOES.md)
- Estado atual: [docs/AUDITORIA.md](docs/AUDITORIA.md)

## Como preparar o ambiente (Windows)

Pré-requisito: Python 3.14 (no Windows, o comando é `py`).

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Para testar se funcionou:

```powershell
python -c "import pandas, openpyxl; print('ok')"
```

Depois copie `.env.example` para `.env` e preencha o caminho da planilha (e a chave da API, se for rodar a LLM).

## Como rodar

```powershell
# testes
python -m pytest

# 1. validar a planilha
python -m ia.entrada.validar

# 2. extração sem custo (regex), gera saidas/<data>/extracoes_regras.json
python -m ia.extracao.extrator --provedor regras

# 3a. extração pela LLM local (grátis; precisa do Ollama aberto e do modelo baixado)
#     instalar: https://ollama.com  ·  baixar o modelo: ollama pull qwen2.5:3b
python -m ia.extracao.extrator --provedor ollama --casos prompts/casos_teste_v1.json

# 3b. extração pelo Claude (pago): primeiro mostra quantas chamadas pagas fará
python -m ia.extracao.extrator --provedor claude --casos prompts/casos_teste_v1.json
python -m ia.extracao.extrator --provedor claude --casos prompts/casos_teste_v1.json --confirmar

# 4. medir contra o gabarito (colunas escondidas da planilha ou casos de teste)
python -m ia.extracao.avaliar --extracoes saidas/<data>/extracoes_claude.json
python -m ia.extracao.avaliar --extracoes saidas/<data>/extracoes_claude.json --casos prompts/casos_teste_v1.json

# demo sem internet: usa só o cache
python -m ia.extracao.extrator --provedor claude --offline
```

| Pasta | Dono | O quê |
|---|---|---|
| `ia/entrada/` | Paulo | leitura e validação da planilha |
| `ia/extracao/` | Paulo | LLM, verificação de evidência, cache, avaliação |
| `prompts/` | Paulo | prompt do extrator (versionado) e casos de teste |
| `contratos/` | Paulo + Mateus | schema e exemplos de `extracoes.json` (mudança só com OK dos dois) |

> Só dados fictícios neste repositório. Chaves de API ficam em `.env`, que nunca vai para o git.
