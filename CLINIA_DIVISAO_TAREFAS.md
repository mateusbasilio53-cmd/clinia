# CLINIA — Divisão de Tarefas no Claude Code (VS Code)

> **Versão:** 2.0 — 16/10/2026 (substitui a v1.0 de três pessoas)
> **Complementa:** `CLINIA_MVP_PLAYBOOK.md` (leia o playbook primeiro)
> **Prazo do MVP:** 04/12/2026
> **Dupla:** Paulo e Mateus Basílio

---

## 1. A divisão em uma frase

**O Paulo cuida do começo do pipeline (entrada + LLM). O Mateus cuida do resto (Pandas + regras + Random Forest + saída final).**
O ponto de encontro entre os dois é um único arquivo: a **extração estruturada** que a LLM gera.

```
 PAULO                                         │  MATEUS BASÍLIO
                                               │
 planilha de pacientes                         │
      │                                        │
      ▼                                        │
 leitura + validação da entrada                │
      │                                        │
      ▼                                        │
 extração LLM do texto livre                   │
 (valor + status + evidência + confiança)      │
      │                                        │
      ▼                                        │
 ┌──────────────────────────────┐   PASSAGEM   │
 │ extracoes.json  (contrato)   │ ───────────▶ │  junta estruturado + extraído (Pandas)
 └──────────────────────────────┘              │       │
                                               │       ▼
                                               │  camada de regras (elegível / não / revisar)
                                               │       │
                                               │       ▼
                                               │  Random Forest (probabilidade / ranking)
                                               │       │
                                               │       ▼
                                               │  planilha de saída final + métricas
```

---

## 2. Quem é dono de quê

| | **Paulo** — Entrada e LLM | **Mateus Basílio** — Dados, decisão e saída |
|---|---|---|
| **Pastas** | `ia/entrada/`, `ia/extracao/`, `prompts/`, `contratos/`, `docs/DECISOES.md` | `ia/dados/`, `ia/regras/`, `ia/modelo/`, `ia/saida/`, `docs/RESULTADOS.md` |
| **Fases do playbook** | Fase 0 (auditoria), Fase 1 (contrato de dados), Fase 3 (extração LLM) | Fase 2 (regras), Fase 4 (Random Forest e métricas), saída final da Fase 5 |
| **Entrega para o outro** | `extracoes.json` no formato do contrato | — (consome o arquivo do Paulo) |
| **Tarefas** | Ler e validar a planilha; montar o prompt do extrator; testar 2 modelos; verificar que cada evidência existe no texto; cache; modo offline | Juntar dados com Pandas; regras com testes; critérios limitantes legíveis; treinar e avaliar o RF (ponto crítico 6.4); gerar a planilha de saída (seção 7.3); métricas da seção 8 |
| **Chave da API do LLM** | Fica com o Paulo | Não precisa: trabalha com o mock e depois com o arquivo gerado |

### Arquivos compartilhados (combinar antes de mexer)

| Arquivo | Regra |
|---|---|
| `contratos/extracao.schema.json` e `contratos/extracoes.example.json` | Mudança só com OK dos dois |
| `CLAUDE.md`, playbook, este arquivo | Paulo altera, avisando |
| `docs/DECISOES.md` | Os dois **acrescentam** no fim, nunca reescrevem |
| `dados/` (dataset fictício) | Somente leitura para os dois |

---

## 3. O contrato da passagem (o mais importante desta divisão)

Fechado **juntos na Semana 1**. Depois disso, cada um trabalha sem esperar o outro.

`contratos/extracoes.example.json` — um item por paciente:

```json
[
  {
    "id_paciente": "PAC-0001",
    "campos": {
      "neoplasia_ativa": { "valor": false, "status": "negado", "evidencia": "nega história de neoplasia", "confianca": "alta" },
      "gestacao":        { "valor": null,  "status": "nao_mencionado", "evidencia": null, "confianca": "alta" },
      "uso_metformina":  { "valor": true,  "status": "afirmado", "evidencia": "em uso de metformina 850mg", "confianca": "alta" }
    },
    "diagnosticos_mencionados": ["diabetes mellitus tipo 2"],
    "evidencia_verificada": true,
    "modelo_llm": "a definir",
    "versao_prompt": "extrator_v1"
  }
]
```

Regras do contrato:
- `status` ∈ { `afirmado`, `negado`, `nao_mencionado`, `incerto` }.
- `evidencia_verificada = false` quando o trecho não for encontrado literalmente no texto.
- Os campos exatos saem da Fase 1 (podem mudar em relação ao exemplo).
- **Os dados estruturados (idade, HbA1c etc.) não passam pela LLM.** O Mateus lê direto da planilha e junta com o `extracoes.json` pelo `id_paciente`.

**Como o Mateus trabalha antes da LLM ficar pronta:** usa o `extracoes.example.json` (ou um mock maior, com os 200 pacientes, gerado por script com valores plausíveis) para desenvolver e testar regras e RF. Quando o Paulo entregar o arquivo real, é só trocar o caminho.

---

## 4. Cronograma

| Semana | Paulo (entrada + LLM) | Mateus Basílio (Pandas + regras + RF + saída) |
|---|---|---|
| **S1** 16–23/10 | Fase 0 (auditoria). **Reunião de contrato com o Mateus.** Script de leitura e validação da planilha | **Reunião de contrato.** Mock de `extracoes.json` para os 200. Pandas: juntar planilha + mock |
| **S2** 24–30/10 | Prompt do extrator v1 + 15 anotações de teste com casos difíceis (negação, abreviação, histórico) | Camada de regras + testes; critérios limitantes em português legível |
| **S3** 31/10–06/11 | Experimento com 2 modelos; Paulo escolhe; roda nos 200; **entrega `extracoes.json` real** | Fecha regras; casos "incerto" → REVISAR; prepara features do RF |
| **S4** 07–13/11 | Conferência manual de 20 extrações; cache; modo offline | Random Forest + métricas + ponto crítico 6.4 (o RF agrega?) |
| **S5** 14–20/11 | **Integração**: um comando roda entrada → LLM → (Mateus) → saída | Planilha de saída final (seção 7.3); `docs/RESULTADOS.md` |
| **S6** 21–27/11 | Decide como mostrar a demo; revisão crítica (prompt 11.3) | Ajustes de métricas e dos limítrofes |
| **S7** 28/11–04/12 | **Congelamento**: checklist da seção 13; `MVP_RESUMO.md`; ensaio | Roda o pipeline 3× seguidas; corrige bugs |

---

## 5. Equipe de duas pessoas: o que muda no escopo

`[FATO]` Só Paulo e Mateus Basílio constroem o MVP. Pedro e Matheus Andrade não programam até 04/12: eles ficam com a **apresentação** (ver seção 5.1).

| Item | Antes | Com a dupla |
|---|---|---|
| **Camada de regras** | Frente Python | Fica com o **Mateus** (é Pandas e alimenta o RF). `[A CONFIRMAR]` |
| **Postgres + back-end Node (D1, D3)** | Paulo + Matheus Andrade | `[PROPOSTA — confirmar]` **O MVP roda só em Python**: planilha de entrada → LLM → regras → RF → planilha de saída. Node e Postgres vão para o backlog pós-MVP. |
| **Tela React (opção B)** | Front | Só se a opção A estiver pronta até 20/11. Se acontecer, alternativa mais leve que React: uma página simples em Python (ex.: Streamlit). Decidir na S6. |
| **Comando único da demo** | Matheus Andrade | **Paulo**, junto com a integração na S5 |

**Por que a proposta Python-only:**
- A demo definida (D11) já é planilha → planilha; Node e Postgres não aparecem para quem assiste.
- Com duas pessoas e 7 semanas, cada camada a mais é risco de não fechar.
- Nada se perde: o contrato `extracoes.json` e os módulos Python continuam válidos quando o Node e o banco entrarem depois.

**O que se perde:** o histórico de execuções no banco (tabelas `execucao` e `resultado_triagem`). Mitigação: salvar cada execução como arquivo com data e versão (`saidas/AAAA-MM-DD_HHMM/`), o que mantém a rastreabilidade para a demo.

**Ao confirmar:** registrar em `docs/DECISOES.md` que D1, D3 e D4 foram adiados para pós-MVP por causa do tamanho da equipe, não descartados.

### 5.1 Equipe de apresentação: Pedro e Matheus Andrade

`[FATO]` Pedro e Matheus Andrade apresentam o MVP em 04/12. Eles **não mexem no repositório** e não precisam de Claude Code: trabalham no Claude normal (chat) e com os documentos que a dupla técnica entrega.

**Risco principal:** quem apresenta não construiu. Se a banca perguntar "e se a IA errar?" ou "por que Random Forest?", a resposta tem que sair firme da boca deles, não do Paulo na plateia. Por isso eles entram **no meio do caminho**, não só na última semana.

| Semana | O que os apresentadores fazem | O que recebem da dupla técnica |
|---|---|---|
| **S1–S2** | Rascunho do roteiro da apresentação (problema → solução → demo → resultados → próximos passos), a partir dos documentos da CLINIA | Este arquivo e o playbook (seções 2, 6 e 9) |
| **S3** | Entendem o pipeline: o que a LLM faz, o que as regras fazem, o que o RF faz, por que a decisão final é humana | Explicação de 1 página (prompt 11.6 do playbook) |
| **S4** | Montam a lista de perguntas difíceis da banca e as respostas | Primeiras métricas (`docs/RESULTADOS.md` parcial) |
| **S5** | Fecham o roteiro da demo: quais 3–4 pacientes mostrar (um elegível, um não elegível com critério limitante, um REVISAR) | Saída de exemplo do pipeline |
| **S6** | Slides prontos; primeiro ensaio **com a demo rodando** | `docs/RESULTADOS.md` final |
| **S7** | Ensaios cronometrados; plano B se a demo falhar (vídeo gravado ou planilha já gerada) | `docs/MVP_RESUMO.md`; gravação da demo |

**Regras de passagem:**
- Toda sexta (merge na `main`), o Paulo manda aos apresentadores um resumo de 3 linhas do que mudou.
- Número que vai para slide só entra se estiver em `docs/RESULTADOS.md`. Nada de arredondar para cima ou citar métrica que ainda não foi medida.
- Quem roda a demo ao vivo no dia: **decidir até a S6** (sugestão: um apresentador opera, o Paulo fica de suporte ao lado).

**Prompt para os apresentadores (no Claude normal, com os documentos anexados):**

```text
Vamos apresentar o MVP da CLINIA em 04/12. Anexei o playbook, a divisão de tarefas e o resumo técnico da fase atual.
Somos os apresentadores, não construímos o código.
1. Explique o pipeline (LLM → regras → Random Forest) como se fosse para uma banca não técnica, com uma analogia.
2. Liste as 10 perguntas mais difíceis que uma banca de saúde digital faria e uma resposta curta e honesta para cada uma, sem prometer nada que o MVP não faz.
3. Proponha um roteiro de apresentação de 5 a 7 minutos, incluindo onde entra a demo.
Diferencie o que é fato (medido) do que é plano futuro.
```

---

## 6. Git: duas pessoas, dois Claude Code

> **Atualizado em 16/10/2026** (ver `docs/DECISOES.md`): o repositório já tinha `develop`, então o fluxo usa as duas branches.

- `main` = versão estável. Só recebe merge de `develop` na sexta, depois de rodarem juntos. Nada de commit direto.
- `develop` = integração do dia a dia. Todo PR vai para `develop`. Nada de commit direto.
- Branches com o nome da pessoa, saindo de `develop`: `paulo/extracao-llm`, `mateus/camada-regras`.
- Rotina diária:

```bash
git checkout develop && git pull
git checkout -b nome/tarefa        # ou entrar na branch e: git merge develop
# ... trabalha com o Claude Code ...
git add . && git commit -m "extracao: adiciona verificação de evidência"
git push -u origin nome/tarefa
# abre Pull Request para develop e marca o outro para revisar
```

- **Revisão cruzada:** o Paulo revisa o Mateus e vice-versa. Isso também faz cada um entender a parte do outro antes da banca.
- Como as pastas não se cruzam, conflito só deve acontecer em `contratos/` ou `docs/DECISOES.md`.

---

## 7. `CLAUDE.md` (raiz do projeto, compartilhado)

```markdown
# CLINIA — instruções para o Claude Code

Antes de qualquer tarefa:
1. Leia CLINIA_MVP_PLAYBOOK.md e siga as Regras de Trabalho da seção 1.
2. Leia CLINIA_DIVISAO_TAREFAS.md.
3. Pergunte se está trabalhando com o Paulo ou com o Mateus Basílio.
4. Edite somente as pastas dessa pessoa (seção 2). Se precisar mexer em outra pasta
   ou em arquivo compartilhado, PARE e avise.
5. Trabalhe numa branch nome/tarefa, nunca na main.
6. O contrato em contratos/ é a fronteira entre os dois. Não mude sem aprovação dos dois.
```

---

## 8. Prompts de abertura

### 8.1 Paulo

```text
Sou o Paulo. Na CLINIA cuido do começo do pipeline: entrada (leitura e validação da planilha) e extração por LLM do texto livre.
Leia CLAUDE.md, CLINIA_MVP_PLAYBOOK.md e CLINIA_DIVISAO_TAREFAS.md.
Minhas pastas: ia/entrada/, ia/extracao/, prompts/, contratos/.
Não altere nada nesta mensagem. Me diga:
1. Minhas tarefas desta semana pelo cronograma (seção 4).
2. O que preciso entregar ao Mateus e em qual formato (seção 3).
3. Sua proposta para a primeira tarefa, no formato da seção 1 do playbook.
Aguarde meu OK.
```

### 8.2 Mateus Basílio

```text
Sou o Mateus Basílio. Na CLINIA cuido de tudo depois da LLM: Pandas, camada de regras, Random Forest e a planilha de saída final.
Leia CLAUDE.md, CLINIA_MVP_PLAYBOOK.md e CLINIA_DIVISAO_TAREFAS.md.
Minhas pastas: ia/dados/, ia/regras/, ia/modelo/, ia/saida/.
A extração real do Paulo ainda não existe: vou trabalhar com o mock em contratos/.
Não altere nada nesta mensagem. Me diga:
1. Minhas tarefas desta semana pelo cronograma (seção 4).
2. Como gerar um mock de extracoes.json para os 200 pacientes e juntar com a planilha no Pandas.
3. Sua proposta para a primeira tarefa, explicando cada escolha em linguagem simples.
Aguarde meu OK.
```

### 8.3 Reunião de contrato (os dois, Semana 1)

```text
Estamos Paulo e Mateus Basílio fechando o contrato entre a LLM (Paulo) e o Pandas/regras/RF (Mateus).
Com base na planilha real e nas seções 7 do playbook e 3 desta divisão, proponha:
1. contratos/extracao.schema.json com os campos que a LLM vai extrair (status, evidência, confiança);
2. contratos/extracoes.example.json com 3 pacientes fictícios, incluindo 1 limítrofe e 1 com negação;
3. quais critérios da tabela protocolo vêm da planilha e quais vêm da extração.
Explique cada campo. Não crie os arquivos até aprovarmos.
```

---

## 9. Sincronização

| Quando | O quê |
|---|---|
| Todo dia | Mensagem rápida: fiz / vou fazer / estou travado |
| 2× por semana | Call de 20 min revisando PRs |
| Sexta de cada semana | Merge na `main` e rodar juntos o que já existe |
| **Fim da S3** | **Momento crítico:** trocar o mock pelo `extracoes.json` real e ver se nada quebra |

---

## 10. Decisões a confirmar

1. A camada de regras fica com o Mateus?
2. O MVP roda só em Python (planilha → planilha), com Node e Postgres adiados para pós-MVP? (seção 5)
3. Dia e horário da reunião de contrato.
4. Quem opera a demo ao vivo no dia 04/12? (seção 5.1)
