<div align="center">

# 🩺 CLINIA

### Triagem inteligente de pacientes para pesquisa clínica

*"Enquanto você lê um, a CLINIA leu todos."*

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![IA local](https://img.shields.io/badge/IA-local%20%C2%B7%20Ollama-000000)
![Testes](https://img.shields.io/badge/testes-54%20passando-2ea44f)
![Dados](https://img.shields.io/badge/dados-100%25%20fict%C3%ADcios-orange)
![MVP](https://img.shields.io/badge/MVP-04%2F12%2F2026-blue)

2º lugar no Ideathon do 3º ConSaúde (UFPE + HC-UFPE) · Pré-incubação i.de.i.a.S (Senac PE)

</div>

---

## O que é

Nos hospitais universitários, boa parte da informação do paciente está em **texto corrido** no prontuário (AGHUx). Para achar candidatos a uma pesquisa clínica, o coordenador lê prontuário por prontuário.

A **CLINIA lê o texto de todos os pacientes**, monta uma **ficha estruturada** de cada um, aplica os critérios do estudo e devolve uma **lista ranqueada**, com o **trecho do prontuário** que justifica cada conclusão.

> **A decisão final é sempre humana.** Na dúvida, a CLINIA não decide: manda para revisão.

## Veja funcionando

```text
$ python -m ia.demo --texto "Masc, 63a, DM2 + HAS. Lab: A1c 8,4 | GJ 190 | Cr 1,0 | IMC 30,1.
                             Em QT para Ca de pulmão desde julho. MTF suspensa pela oncologia."

  Ficha lida do texto
    Idade                63           ← "63a"
    Sexo                 M            ← "Masc"
    HbA1c (%)            8,4          ← "A1c 8,4"
    Creatinina (mg/dL)   1            ← "Cr 1,0"
    Glicemia de jejum    190          ← "GJ 190"
    IMC                  30,1         ← "IMC 30,1"

  Critérios lidos do texto
    Neoplasia ativa      INCERTO        ✔ trecho conferido
      ← "QT para Ca de pulmão desde julho"
    Gestação atual       não mencionado
    Usa metformina       NÃO            ✔ trecho conferido
      ← "MTF suspensa pela oncologia"

  → VAI PARA REVISÃO HUMANA
      · Neoplasia ativa: leituras divergentes: IA = não tem, regras = tem

  A decisão final é sempre do coordenador/médico.
```

Aqui a IA errou sozinha, as regras discordaram, e a CLINIA chamou o humano. **É assim que ela foi feita para funcionar.**

## Como funciona

```mermaid
flowchart LR
    T["📄 Texto corrido<br/>do prontuário"] --> N["🔢 Números<br/>(regras)"]
    T --> IA["🤖 IA local<br/>(qwen2.5)"]
    T --> R["📏 Regras<br/>(regex)"]
    IA --> D{"Dupla<br/>checagem"}
    R --> D
    N --> J["extracoes.json"]
    D -->|concordam| J
    D -->|discordam| REV["👤 Revisão humana"]
    J --> P["Regras do protocolo<br/>ELEGÍVEL · NÃO · REVISAR"]
    P --> RF["Random Forest<br/>(só ordena)"]
    RF --> S["📊 Planilha final<br/>ranqueada + evidências"]
```

Explicação completa, peça por peça: **[docs/COMO_FUNCIONA.md](docs/COMO_FUNCIONA.md)**.

## Resultados (dados fictícios)

Base de prova: 100 pacientes com texto variado (abreviações, erros de digitação, negações, histórico familiar).

| | Só IA | Só regras | **CLINIA (IA + regras)** |
|---|:---:|:---:|:---:|
| **Erros perigosos** | 11 | 19 | **3** |
| Acerto: neoplasia / gestação / metformina | 78 / 88 / 85% | 92 / 98 / 81% | **91 / 92 / 80%** |
| Números lidos errados (idade, HbA1c, IMC…) | — | — | **0** |

⏱️ ~5 s por paciente num notebook comum (RTX 3050), **sem internet e sem custo**.
Detalhes, limites e o que **não** afirmar: [docs/RESULTADOS_EXTRACAO.md](docs/RESULTADOS_EXTRACAO.md).

## Começar

```powershell
git clone git@github.com:mateusbasilio53-cmd/clinia.git
cd clinia
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python -m pytest          # 54 passed = tudo certo
python -m ia.demo         # demo com 3 pacientes (funciona mesmo sem a IA instalada)
python -m ia.verificar_pc # qual modelo de IA seu PC aguenta
```

Para a IA ler textos novos, instale o [Ollama](https://ollama.com) e rode `ollama pull qwen2.5:3b` (ou o modelo que o `verificar_pc` recomendar). Passo a passo: **[docs/GUIA_INSTALACAO.md](docs/GUIA_INSTALACAO.md)**.

## Comandos

| Quero… | Comando |
|---|---|
| ver a demo / a IA ler um texto novo | `python -m ia.demo` · `python -m ia.demo --texto "..."` |
| validar uma planilha | `python -m ia.entrada.validar --planilha dados/arquivo.xlsx` |
| ler uma planilha inteira | `python -m ia.extracao.extrator --provedor ollama --planilha dados/arquivo.xlsx` |
| …sem IA, só com o que já foi lido | adicionar `--offline` |
| medir contra o gabarito | `python -m ia.extracao.avaliar --extracoes <json> --planilha <xlsx>` |
| comparar modelos e guardar o histórico | `python -m ia.extracao.experimento --modelos qwen2.5:3b,qwen2.5:7b --conjunto prova` |
| gerar a planilha de saída | `python -m ia.extracao.relatorio --base "Nome\|<xlsx>\|<json>"` |

## Estrutura

| Pasta | O que tem | Dono |
|---|---|---|
| `ia/entrada/` | ler e validar a planilha | Paulo |
| `ia/extracao/` | IA, regras, dupla checagem, verificação, cache, avaliação | Paulo |
| `ia/dados/` · `ia/regras/` · `ia/modelo/` · `ia/saida/` | Pandas, decisão, Random Forest, planilha final | Mateus |
| `dados/` | planilhas de pacientes **fictícios** | os dois (só leitura) |
| `prompts/` | instruções da IA (versionadas) e casos difíceis | Paulo |
| `contratos/` | formato do `extracoes.json` (Paulo ↔ Mateus) | os dois |
| `entregas/` | resultados prontos para o Mateus | Paulo → Mateus |
| `avaliacao/` | bases de teste, histórico de medições, base de estudo | os dois |
| `cache/` | respostas da IA já calculadas (modo offline) | automático |
| `docs/` | explicações, decisões, resultados, guias | os dois |

## Documentação

| Documento | Para quê |
|---|---|
| 📘 [Como funciona](docs/COMO_FUNCIONA.md) | **comece por aqui:** o sistema explicado do zero |
| 📊 [Resultados](docs/RESULTADOS_EXTRACAO.md) | números oficiais e frases para a apresentação |
| 🛠️ [Guia de instalação](docs/GUIA_INSTALACAO.md) | do zero até a IA rodando no seu PC |
| 🤝 [Para o Mateus](docs/PARA_O_MATEUS.md) | o que está pronto e como usar na parte dele |
| 🧪 [Avaliação](avaliacao/README.md) | como medir, comparar modelos e melhorar sem "colar na prova" |
| 🧭 [Decisões](docs/DECISOES.md) | cada decisão, quando, por quem e por quê |
| 🗺️ [Playbook do MVP](CLINIA_MVP_PLAYBOOK.md) · [Divisão de tarefas](CLINIA_DIVISAO_TAREFAS.md) | o plano completo |

## Equipe

| | Papel |
|---|---|
| **Paulo Francisco de Moura Neto** | cofundador, líder técnico · entrada e IA |
| **Mateus Basílio** | dados, regras, Random Forest e saída |
| **Pedro** e **Matheus Andrade** | apresentação do MVP |
| Equipe de pesquisa clínica da **Bárbara** | validação clínica |

## Privacidade

- **Só dados fictícios** neste repositório. Nenhum dado real de paciente.
- A IA roda **no próprio computador**: o texto não vai para a internet.
- Pacientes são identificados por pseudônimo (`PAC-001`), nunca por nome.
- Chaves de API ficam em `.env`, que nunca vai para o git.
