# Como a CLINIA funciona — explicado do zero

> **Para quem:** toda a equipe (Paulo, Mateus, Pedro, Matheus Andrade) e quem chegar depois.
> **Objetivo:** depois de ler, você consegue explicar cada parte do sistema, por que ela existe e o que os números querem dizer, sem precisar abrir o código.
> **Atualizado em:** 16/10/2026

---

## Sumário

1. [A CLINIA em 1 minuto](#1-a-clinia-em-1-minuto)
2. [O caminho de um paciente](#2-o-caminho-de-um-paciente)
3. [Cada peça, explicada](#3-cada-peça-explicada)
4. [Mapa do projeto](#4-mapa-do-projeto)
5. [Comandos do dia a dia](#5-comandos-do-dia-a-dia)
6. [Como medimos e o que os números dizem](#6-como-medimos-e-o-que-os-números-dizem)
7. [As decisões mais importantes, e por quê](#7-as-decisões-mais-importantes-e-por-quê)
8. [O que falta até 04/12](#8-o-que-falta-até-0412)
9. [Perguntas que a banca pode fazer](#9-perguntas-que-a-banca-pode-fazer)
10. [Como usamos IA para construir a CLINIA](#10-como-usamos-ia-para-construir-a-clinia)

---

## 1. A CLINIA em 1 minuto

**O problema.** Nos hospitais universitários, o prontuário eletrônico (AGHUx) guarda boa parte da informação em **texto corrido**: evoluções, anamneses. Para achar pacientes para uma pesquisa clínica, o coordenador lê prontuário por prontuário. Pacientes elegíveis se perdem pelo volume.

**A solução.** O coordenador informa os critérios do estudo. A CLINIA **lê o texto de todos os pacientes**, monta uma ficha estruturada de cada um, aplica os critérios e devolve uma **lista ranqueada**, sempre com o **trecho do prontuário** que justifica cada conclusão.

**A regra que não muda.** A CLINIA não decide sozinha. Na dúvida, ela manda para **revisão humana**. A decisão final é sempre do coordenador ou do médico.

> *"Enquanto você lê um, a CLINIA leu todos."*

## 2. O caminho de um paciente

```
 TEXTO CORRIDO DO PRONTUÁRIO
 "Masc, 63a, DM2 + HAS. Lab: A1c 8,4 | GJ 190 | Cr 1,0 | IMC 30,1.
  Em QT para Ca de pulmão desde julho. MTF suspensa pela oncologia."
        │
        ├──────────────► (A) LEITURA DOS NÚMEROS — regras                    [Paulo]
        │                    idade 63 · sexo M · HbA1c 8,4 · glicemia 190
        │                    creatinina 1,0 · IMC 30,1   (cada um com o trecho)
        │
        ├──────────────► (B) LEITURA DOS CRITÉRIOS — IA local                [Paulo]
        │                    neoplasia ativa? · gestação? · usa metformina?
        │
        ├──────────────► (C) MESMA LEITURA — regras (regex)                  [Paulo]
        │
        ▼
 (D) DUPLA CHECAGEM E TRAVAS                                                 [Paulo]
     · IA e regras discordam sobre "tem" x "não tem"?  → INCERTO (revisão humana)
     · o trecho citado existe mesmo no texto?           → se não, revisão humana
     · "usa metformina" mas o trecho não fala de metformina? → revisão humana
        │
        ▼
 extracoes.json  ←── O CONTRATO: a passagem do Paulo para o Mateus
        │
        ▼
 (E) JUNTA OS DADOS (Pandas)                                                 [Mateus]
 (F) REGRAS DO PROTOCOLO → ELEGÍVEL / NÃO ELEGÍVEL / REVISAR + motivos       [Mateus]
 (G) RANDOM FOREST → probabilidade, só para ORDENAR a lista                   [Mateus]
 (H) PLANILHA FINAL RANQUEADA, com evidências                                [Mateus]
```

No exemplo acima, a IA errou ("QT para Ca de pulmão" virou "não tem câncer"), mas as regras discordaram e o paciente foi para **revisão humana**. É exatamente para isso que a dupla checagem existe. Para ver ao vivo: `python -m ia.demo --texto "..."`.

## 3. Cada peça, explicada

### LLM (modelo de linguagem)
Um programa treinado em muito texto, capaz de **ler e interpretar** linguagem: entende que "nega neoplasia" quer dizer "não tem câncer", e que "mãe com Ca de mama" é sobre a mãe, não sobre o paciente. Regras simples erram nisso.

**Na CLINIA, a LLM só lê. Ela não decide quem é elegível.** Uma decisão tomada por LLM seria difícil de auditar e poderia "inventar".

### Ollama e o modelo `qwen2.5:3b`
O **Ollama** é um programa gratuito que roda LLMs **no próprio computador**. O **qwen2.5:3b** é o modelo que usamos: "3b" quer dizer 3 bilhões de parâmetros, um modelo pequeno.

- **Por que local:** custo zero, funciona sem internet, e **os dados não saem do computador**. Isso é um argumento forte de LGPD.
- **Por que pequeno:** cabe na placa de vídeo de 4 GB do notebook do Paulo. Em PCs mais fortes, um modelo maior (`qwen2.5:7b`) deve errar menos. O comando `python -m ia.verificar_pc` diz qual cabe.
- **Não treinamos o modelo.** Ele vem pronto. O que fazemos é dar boas instruções (o prompt).

### Prompt e exemplos no prompt
O **prompt** é a instrução que mandamos para a IA junto com o texto: o que extrair, como responder, o que significa cada status. Fica em `prompts/extrator_v2.md`.

O v2 traz **3 exemplos resolvidos** (texto → resposta). Modelos pequenos aprendem muito mais com exemplos do que com regras escritas: nos 15 casos difíceis, o acerto **subiu de 78% para 87%** só com isso. É o "treino" possível sem mexer no modelo.

**Prompts são versionados.** Mudou o texto, vira `extrator_v3.md`. Assim os resultados de versões diferentes não se misturam.

### Saída estruturada (schema)
Em vez de deixar a IA responder em texto livre, mandamos um **molde em JSON** (o *schema*) e o Ollama obriga a resposta a seguir esse molde. Resultado: a resposta sempre tem os mesmos campos, no mesmo formato, e o código consegue ler sem adivinhar.

### Os 4 status de cada critério

| Status | Quer dizer | Exemplo |
|---|---|---|
| `afirmado` (SIM) | o texto diz que tem | "Em QT para Ca de mama" |
| `negado` (NÃO) | o texto diz que não tem | "Nega neoplasia", "metformina suspensa" |
| `nao_mencionado` | o texto não fala do assunto | — |
| `incerto` | ambíguo, suspeita, aguardando exame | "suspeita de gestação, aguarda beta-HCG" |

**Separar "negado" de "não mencionado" é essencial.** É o erro clássico de quem faz busca por palavra-chave: achar "neoplasia" em "nega neoplasia" e concluir que o paciente tem câncer.

### Evidência e verificação
Toda resposta vem com o **trecho literal** do texto que a justifica. O código **confere** se esse trecho existe de verdade no prontuário. Se a IA "inventar" uma frase, o código percebe e manda para revisão.

Isso já aconteceu nos testes: a IA escreveu "Nega metformina entre as medicações em uso", mas o texto dizia "Não há metformina...". O código pegou.

### Confiança
Cada campo vem com `alta`, `media` ou `baixa`. Qualquer problema (trecho não encontrado, divergência, valor incoerente) rebaixa para `baixa`. **Confiança baixa sempre vai para revisão humana.**

### Regras (regex) e leitura dos números
**Regex** é um jeito de descrever padrões de texto: por exemplo, "a palavra HbA1c, seguida de um número com vírgula". Usamos regras para duas coisas:

1. **Ler os números** (idade, sexo, HbA1c, creatinina, glicemia, IMC). Números seguem padrões fixos, então regras leem com precisão, na hora e de graça. Nas duas bases: **nenhum número lido errado**. Quando o valor não está no texto, fica em branco, sem chute.
2. **Ler os critérios de novo**, de forma independente da IA, para a dupla checagem.

### Dupla checagem
A IA e as regras leem o mesmo texto. Se elas **discordam** sobre o que importa ("tem" x "não tem"), a CLINIA **não escolhe**: marca INCERTO e chama o humano.

Na base de prova, isso derrubou os **erros perigosos de 11 (só IA) para 3**. O preço: mais pacientes vão para revisão (46 de 100). Para o coordenador, revisar um a mais é muito melhor do que perder um elegível ou incluir alguém que não poderia.

### Cache e modo offline
Toda resposta da IA fica guardada em `cache/`, identificada pelo texto, pelo modelo e pela versão do prompt. Consequências:
- rodar de novo **não repete o trabalho** (os 300 pacientes saem em menos de 1 segundo);
- o **modo `--offline`** funciona **sem Ollama e sem internet**, usando o que já foi lido. É o plano B da demo.

### Regras do protocolo (camada 1, Mateus)
Comparam a ficha do paciente com os critérios do estudo (idade 30–70, HbA1c 7,0–10,5, etc.) e decidem: **ELEGÍVEL**, **NÃO ELEGÍVEL** ou **REVISAR**, com o motivo em português ("HbA1c 10,8% acima do máximo de 10,5%"). São regras fixas: sempre dão o mesmo resultado e mostram o porquê.

### Random Forest (camada 2, Mateus)
Um modelo de *machine learning* que aprende com exemplos rotulados e dá uma **probabilidade**. Na CLINIA ele **só ordena** a lista dentro de cada grupo. **Nunca muda a decisão das regras.** O Random Forest é a única parte que é treinada de verdade com os nossos dados.

### Gabarito, prova e estudo
- **Gabarito:** a resposta certa de cada paciente, para medir a CLINIA.
- **Prova** (`dados/pacientes_ficticios_PAC201-300.xlsx`): só para **medir**. Não ajustamos nada olhando para ela, senão a nota deixa de valer (é como estudar com o gabarito).
- **Estudo** (`avaliacao/estudo/`): para **melhorar** prompt e regras à vontade.

### Erro perigoso
Uma leitura que pode deixar **elegível** alguém que deveria **sair** ou ser **revisado**. Exemplo: o texto diz "em QT para câncer" e a leitura diz "não mencionado". É a métrica mais importante, mais do que o acerto geral.

## 4. Mapa do projeto

```
clinica/
├── README.md                    porta de entrada
├── CLAUDE.md                    instruções para o Claude Code
├── CLINIA_MVP_PLAYBOOK.md       plano completo do MVP (fases, regras, riscos)
├── CLINIA_DIVISAO_TAREFAS.md    quem faz o quê
│
├── dados/                       planilhas de pacientes FICTÍCIOS (só leitura)
├── prompts/                     instruções da IA (versionadas) e 15 casos difíceis
├── contratos/                   formato do extracoes.json (Paulo ↔ Mateus)
├── entregas/                    resultados prontos para o Mateus usar
├── cache/                       respostas da IA já calculadas (modo offline)
├── avaliacao/                   bases de teste, histórico de medições, base de estudo
│
├── ia/
│   ├── demo.py                  demo: texto → ficha estruturada
│   ├── verificar_pc.py          qual modelo de IA o PC aguenta
│   ├── entrada/        [Paulo]  ler e validar a planilha
│   ├── extracao/       [Paulo]  IA, regras, verificação, cache, avaliação, relatório
│   ├── dados/          [Mateus] juntar planilha + extração (Pandas)
│   ├── regras/         [Mateus] decisão elegível / não / revisar
│   ├── modelo/         [Mateus] Random Forest
│   └── saida/          [Mateus] planilha final ranqueada
│
├── tests/                       testes automáticos (python -m pytest)
└── docs/                        este documento, decisões, resultados, guias
```

Dentro de `ia/extracao/`:

| Arquivo | Faz |
|---|---|
| `extrator.py` | o comando principal: lê as anotações e gera o `extracoes.json` |
| `provedores.py` | quem lê: regras (regex), Ollama (IA local) ou Claude (IA via internet) |
| `estruturados.py` | lê os números do texto |
| `combinacao.py` | dupla checagem e travas |
| `verificacao.py` | confere se cada trecho existe no texto |
| `schema.py` | o formato de tudo (o que a IA devolve e o que vai para o Mateus) |
| `cache.py` | guarda as respostas da IA |
| `avaliar.py` | compara com o gabarito |
| `relatorio.py` | gera a planilha de saída |
| `experimento.py` | compara modelos e guarda o histórico |

## 5. Comandos do dia a dia

> Antes: `.\.venv\Scripts\Activate.ps1` na pasta do projeto. Instalação completa: [GUIA_INSTALACAO.md](GUIA_INSTALACAO.md).

| Quero… | Comando |
|---|---|
| ver se está tudo funcionando | `python -m pytest` |
| ver a demo | `python -m ia.demo` |
| a IA ler um texto novo | `python -m ia.demo --texto "Fem, 45a, DM2. Nega Ca. MTF 850mg."` |
| saber qual modelo meu PC aguenta | `python -m ia.verificar_pc` |
| validar uma planilha | `python -m ia.entrada.validar --planilha dados/arquivo.xlsx` |
| ler uma planilha inteira | `python -m ia.extracao.extrator --provedor ollama --planilha dados/arquivo.xlsx` |
| o mesmo, sem IA (só cache) | adicionar `--offline` |
| medir contra o gabarito | `python -m ia.extracao.avaliar --extracoes entregas/extracoes_base2.json --planilha dados/pacientes_ficticios_PAC201-300.xlsx` |
| comparar modelos | `python -m ia.extracao.experimento --modelos qwen2.5:3b,qwen2.5:7b --conjunto prova` |
| gerar a planilha de saída | `python -m ia.extracao.relatorio --base "Base 2\|dados/pacientes_ficticios_PAC201-300.xlsx\|entregas/extracoes_base2.json"` |

## 6. Como medimos e o que os números dizem

Números oficiais: [RESULTADOS_EXTRACAO.md](RESULTADOS_EXTRACAO.md). Resumo da **prova** (100 pacientes, texto variado):

| | Só IA | Só regras | **CLINIA** |
|---|---|---|---|
| Erros perigosos | 11 | 19 | **3** |
| Acerto neoplasia / gestação / metformina | 78 / 88 / 85% | 92 / 98 / 81% | **91 / 92 / 80%** |
| Números lidos errados | — | — | **0** |
| Pacientes para revisão humana | — | — | 46 de 100 |
| Tempo | ~5 s por paciente, notebook comum, sem internet | | |

**Como interpretar:**
- Sozinha, a IA pequena **não é melhor** que as regras. O ganho está em **combinar as duas**: uma pega o erro da outra.
- O 100% da planilha original **não vale** como resultado, porque aquela base é fácil demais (até as regras simples acertam tudo).
- Tudo é com **dados fictícios** e com **gabarito feito por IA**. Serve para mostrar que o caminho funciona, não para afirmar acurácia clínica.

## 7. As decisões mais importantes, e por quê

Lista completa em [DECISOES.md](DECISOES.md).

| # | Decisão | Por quê |
|---|---|---|
| D13 | MVP só em Python (Node, Postgres e React depois) | Equipe de 2, 7 semanas, e a demo é planilha → planilha |
| D8 | O Random Forest só ordena, nunca decide | A decisão precisa ser auditável |
| D14 | A IA lê do texto o que no AGHUx só existe em texto | Senão a IA não teria papel real |
| D22 | IA local e gratuita (Ollama) | Custo zero, sem internet, dados não saem do computador |
| D23 | Prompt com exemplos | Modelo pequeno aprende com exemplos: 78% → 87% |
| D24 | Dupla checagem IA + regras | Erros perigosos: 11 → 3 |
| D25 | A prova não é usada para ajustar | Senão o número deixa de valer |
| D27 | Números lidos por regras, não pela IA | Precisos, instantâneos, 0 erros |

## 8. O que falta até 04/12

| Semana | O quê | Quem |
|---|---|---|
| até 23/10 | Mateus: instalar, rodar `verificar_pc`, testar modelo maior; fechar o contrato | Mateus + Paulo |
| 24/10–06/11 | Regras do protocolo, com testes e motivos legíveis | Mateus |
| 07–13/11 | Random Forest e métricas (ponto 6.4) | Mateus |
| 14–20/11 | Planilha final; comando único da demo ponta a ponta | Mateus + Paulo |
| 21–27/11 | Demo no PC do Mateus, 3 vezes seguidas; vídeo de plano B; ensaio com os apresentadores | todos |
| 28/11–04/12 | Congelamento: só correção e ensaio | todos |

Melhorias opcionais da extração: base de estudo + prompt v3; regra para "oncologia"; modelo maior.

## 9. Perguntas que a banca pode fazer

**"E se a IA errar?"**
Ela erra, e o sistema foi feito sabendo disso. Toda resposta vem com o trecho do prontuário, o código confere o trecho, e quando a IA e as regras discordam o caso vai para revisão humana. Na nossa base de teste, isso reduziu os erros perigosos de 11 para 3 em 300 leituras. E a decisão final é sempre humana.

**"Por que não deixar a IA decidir quem é elegível?"**
Porque uma decisão de IA é difícil de auditar. Na CLINIA, a IA só lê; quem decide são regras fixas e transparentes, que dizem exatamente qual critério foi atendido ou violado.

**"Os dados dos pacientes vão para a internet?"**
Não. A IA roda no próprio computador. No MVP usamos só dados fictícios; com dados reais, a arquitetura prevê desidentificação e o dado identificado nunca sai do hospital.

**"Qual a acurácia?"**
Com dados fictícios e texto variado: 91% em neoplasia, 92% em gestação e 80% em metformina, com 3 erros perigosos em 300 leituras e 46% dos pacientes indo para revisão. Não afirmamos acurácia clínica: falta validar com dados reais e com profissionais.

**"Por que um modelo tão pequeno?"**
Para provar que funciona num notebook comum, de graça e sem internet. Em computadores mais fortes, o mesmo sistema troca para um modelo maior sem mudar o código.

**"Por que Random Forest?"**
É um modelo simples, explicável (mostra quais dados mais pesam) e que funciona com poucos dados. E ele só ordena a lista, não decide.

**"Quanto tempo economiza?"**
A CLINIA leu 300 prontuários fictícios em menos de meia hora num notebook comum. O tempo de um coordenador fazendo isso à mão ainda precisa ser medido com uma coordenadora real.

## 10. Como usamos IA para construir a CLINIA

Usamos o **Claude Code** (um assistente de programação com IA) como par técnico, seguindo regras escritas em `CLINIA_MVP_PLAYBOOK.md`, seção 1:

- **Ele propõe e explica; nós decidimos.** Toda decisão de arquitetura foi apresentada com motivo e alternativas, e ficou registrada em `docs/DECISOES.md` com quem decidiu.
- **Nada de número inventado.** Todo resultado aqui foi medido por um comando que qualquer um pode rodar de novo.
- **Testes automáticos** (`python -m pytest`) conferem as peças principais a cada mudança.
- **Separação de fatos e hipóteses** nos documentos: `[FATO]`, `[HIPÓTESE]`, `[A VALIDAR]`.

O objetivo é que a equipe **entenda e consiga manter** o sistema, não só rodar. Se alguma parte deste documento não ficou clara, essa parte precisa ser melhorada.
