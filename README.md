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

> Só dados fictícios neste repositório. Chaves de API ficam em `.env`, que nunca vai para o git.
