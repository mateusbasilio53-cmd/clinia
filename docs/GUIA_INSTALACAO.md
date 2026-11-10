# Guia de instalação — rodar a CLINIA no seu computador (Windows)

> Para: Mateus Basílio (e quem for rodar a demo em 04/12).
> Tempo: uns 30 a 60 minutos, a maior parte esperando download (cerca de 3,5 GB).
> Dúvida em algum passo: manda print para o Paulo.

---

## Passo 0 — Ver se o computador aguenta a IA local

Abra o **PowerShell** e cole:

```powershell
$cs=Get-CimInstance Win32_ComputerSystem; "RAM: {0:N1} GB" -f ($cs.TotalPhysicalMemory/1GB); (Get-CimInstance Win32_Processor).Name; Get-CimInstance Win32_VideoController | % { $_.Name }; "Disco C livre: {0:N0} GB" -f ((Get-PSDrive C).Free/1GB); py -0p
```

Mande o resultado para o Paulo. Referência:

| | Mínimo | Bom (igual ao do Paulo) |
|---|---|---|
| RAM | 8 GB | 16 GB |
| Placa de vídeo | qualquer (roda no processador, mais lento) | NVIDIA com 4 GB ou mais |
| Disco livre | 10 GB | — |

## Passo 1 — Python 3.14

Se o comando `py -0p` do passo 0 **não** mostrou `3.14`, instale pelo site <https://www.python.org/downloads/> (versão 3.14) e marque **"Add python.exe to PATH"** na instalação.

> No Windows, use sempre `py`, não `python`. O `python` pode abrir a Microsoft Store.

## Passo 2 — Baixar o projeto

```powershell
cd $HOME
git clone git@github.com:mateusbasilio53-cmd/clinia.git
cd clinia
git checkout paulo/extracao-llm
```

> Depois que os PRs entrarem na `develop`, troque a última linha por `git checkout develop`.

## Passo 3 — Ambiente Python e bibliotecas

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
```

O último comando tem que terminar com **`54 passed`** (ou mais). Se der erro de "execução de scripts desabilitada" no `Activate.ps1`, rode antes:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**Teste rápido, ainda sem IA** (usa as respostas que já estão no cache):

```powershell
python -m ia.entrada.validar
python -m ia.extracao.extrator --provedor ollama --offline
```

Se o segundo comando terminar com `"falhas": []` e `"do_cache": 200`, o projeto está funcionando. As extrações prontas (para não rodar nada) estão em `entregas/`; veja `docs/PARA_O_MATEUS.md`. A partir daqui você já consegue trabalhar no Pandas / regras / RF.

## Passo 4 — Ollama (a IA local)

1. Baixe e instale: <https://ollama.com/download> (botão **Download for Windows**, cerca de 1,5 GB).
2. Depois de instalar, o Ollama fica rodando perto do relógio do Windows (ícone de lhama).
3. Feche e abra o PowerShell, entre no projeto e veja qual modelo o seu PC aguenta:

```powershell
cd $HOME\clinia
.\.venv\Scripts\Activate.ps1
python -m ia.verificar_pc
```

4. Baixe o modelo recomendado **e** o `qwen2.5:3b` (o do Paulo, para comparar). Exemplo com 8 GB de VRAM:

```powershell
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b
ollama list
```

## Passo 5 — A IA lendo os textos no seu computador

Primeiro, um texto novo, ao vivo:

```powershell
python -m ia.demo --texto "Fem, 52a, DM2. Lab: A1c 8,1 | GJ 170 | Cr 0,9 | IMC 31. Nega Ca. Em uso de metformina 850mg 2x/dia."
```

Depois, a comparação de modelos na prova (100 pacientes). O `qwen2.5:3b` vem do cache (instantâneo); o modelo novo lê de verdade:

```powershell
python -m ia.extracao.experimento --modelos qwen2.5:3b,qwen2.5:7b --conjunto prova
```

O resultado fica guardado em `avaliacao/historico.csv`. Mande para o Paulo a tabela que aparece no fim (acerto, erros perigosos, revisar, segundos por paciente). Como ler: `avaliacao/README.md`.

---

## Problemas comuns

| Mensagem | O que fazer |
|---|---|
| `Ollama não respondeu em http://localhost:11434 (está aberto?)` | Abra o Ollama pelo menu Iniciar e rode de novo |
| `model "qwen2.5:3b" not found` | Rode `ollama pull qwen2.5:3b` |
| `Modo offline: N texto(s) sem extração no cache` | Normal com texto novo. Rode sem `--offline` (com o Ollama aberto) |
| `Planilha não encontrada` | Confira se existe `dados\Base_ficticia_DM2_CLINIA.xlsx` dentro da pasta `clinia` |
| Muito lento (mais de 30 s por paciente) | O computador está sem placa de vídeo compatível. Avise o Paulo: para a demo, use o modo `--offline` |
