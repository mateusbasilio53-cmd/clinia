# CLINIA — Playbook de Construção do MVP com Claude Code

> **Versão:** 1.0 — 16/10/2026
> **Prazo do MVP:** sexta-feira, **04/12/2026** (≈ 7 semanas a partir de hoje)
> **Responsável pelas decisões:** Paulo Francisco de Moura Neto (Gaibu)
> **Para quem é este documento:** para o Claude Code (e qualquer IA de apoio) que vai ajudar a equipe a construir o MVP, e para a própria equipe como roteiro.

---

## 0. Como usar este documento

### 0.1 Para o Paulo (humano)

1. Coloque este arquivo na raiz da pasta/repositório da CLINIA.
2. **Dica importante:** o Claude Code lê automaticamente um arquivo chamado `CLAUDE.md` na raiz do projeto em toda sessão. Duas opções:
   - renomear este arquivo para `CLAUDE.md`; **ou**
   - criar um `CLAUDE.md` curto que diga: *"Leia `CLINIA_MVP_PLAYBOOK.md` antes de qualquer tarefa e siga as Regras de Trabalho da seção 1."*
   A segunda opção é melhor: mantém o `CLAUDE.md` enxuto e o playbook completo separado.
3. Abra o Claude Code na pasta e cole o **Prompt de Abertura** (seção 11.1).
4. Avance **uma fase por vez** (seção 10). Cada fase tem um prompt pronto. Não pule para a próxima sem o "critério de pronto" da fase atual estar cumprido.
5. Sempre que o Claude Code propuser uma decisão, ele deve explicar o porquê e esperar seu OK. Se ele não fizer isso, lembre-o da seção 1.

### 0.2 Expectativa realista para hoje (16/10)

Terminar o MVP hoje não é viável — e nem é o objetivo. O que **dá** para fazer hoje:

- **Fase 0** completa (auditoria do que já existe + plano confirmado);
- começar a **Fase 1** (contrato de dados e checagem do dataset).

Se isso sair hoje, vocês terão começado muito bem.

---

## 1. Regras de Trabalho para o Claude Code (OBRIGATÓRIAS)

Você, Claude Code, está atuando como **engenheiro sênior e par técnico** da equipe CLINIA. Siga estas regras em todas as sessões:

1. **Pergunte antes de decidir.** Toda decisão de arquitetura, biblioteca, provedor de LLM, estrutura de pastas, esquema de dados ou mudança no que já existe deve ser **proposta**, nunca executada direto. Formato obrigatório da proposta:
   - **O que proponho**
   - **Por que** (motivo técnico/estratégico)
   - **Alternativas consideradas** (pelo menos uma) e por que ficaram de fora
   - **Riscos / impactos** em outras partes do projeto
   - **Pergunta de confirmação** ao Paulo
2. **Respeite as decisões já tomadas** (seção 3). Se achar que alguma está errada, **argumente**, mas não mude sem aprovação.
3. **Diferencie fatos de hipóteses.** Use os rótulos: `[FATO]`, `[HIPÓTESE]`, `[SUGESTÃO]`, `[A VALIDAR]`.
4. **Não invente.** Se faltar informação (ex.: colunas da planilha, regras de um protocolo), **pergunte**. Não preencha lacunas com suposições silenciosas.
5. **Nada de dados reais de pacientes.** O MVP usa apenas dados fictícios. Se algum arquivo parecer conter dados reais (nomes, CPF, nº de prontuário real), **pare e avise**.
6. **Segredos fora do código.** Chaves de API só em `.env`, e `.env` no `.gitignore`. Nunca imprima chaves no terminal ou em logs.
7. **Passos pequenos e verificáveis.** Prefira mudanças pequenas, com teste ou comando de verificação ao final de cada uma. Mostre como rodar.
8. **Explique para quem está aprendendo.** A equipe é de ADS (Senac PE). Ao introduzir algo novo (ex.: FastAPI, structured outputs, validação cruzada), explique em 2–4 frases o que é e por que importa.
9. **Documente enquanto constrói.** Ao fim de cada fase, atualize `docs/DECISOES.md` (decisão, data, motivo) e o `README.md` (como rodar).
10. **Escopo do MVP é sagrado.** Se surgir ideia fora do escopo (seção 4.2), registre em `docs/BACKLOG_POS_MVP.md` e siga em frente.
11. **Pare em comandos destrutivos.** Antes de apagar arquivos, rodar migrações que destroem dados, `git reset --hard`, `docker volume rm` etc., peça permissão explícita.

---

## 2. Contexto da CLINIA (resumo para a IA)

- **O que é:** HealthTech brasileira de triagem inteligente de pacientes para pesquisa clínica.
- **Problema:** em hospitais universitários federais, o prontuário eletrônico é o **AGHUx**, que não oferece busca eficaz por diagnóstico/critério dentro do **texto livre** (evoluções, anamneses, laudos). Coordenadores de pesquisa revisam prontuário por prontuário; pacientes elegíveis são perdidos por volume.
- **Solução:** o coordenador informa os critérios do protocolo; o sistema lê os dados do paciente (estruturados + texto livre), aplica os critérios e devolve uma **lista ranqueada** de pacientes, com **justificativa auditável** (qual critério foi atendido/violado e qual trecho do prontuário embasou). **A decisão final é sempre humana.**
- **Mote:** *"Enquanto você lê um, a CLINIA leu todos."*
- **Origem:** 2º lugar no Ideathon do 3º ConSaúde (UFPE + HC-UFPE, abril/2026). Pré-incubação na i.de.i.a.S (Senac PE) e jornada Sebrae PE.
- **Insight de usuário mais importante:** o coordenador **só confia na lista se enxergar o porquê** de cada sinalização. Explicabilidade não é enfeite: é o que faz o produto ser usado.
- **Equipe que constrói o MVP:** só **Paulo** (entrada + extração LLM) e **Mateus Basílio** (Pandas, regras, Random Forest e saída). **Pedro e Matheus Andrade apresentam** o MVP e não mexem no código. Ver `CLINIA_DIVISAO_TAREFAS.md`.
- **Dados de treino:** planilha fictícia de **200 pacientes** (115 elegíveis, 85 não elegíveis, dos quais 30 casos limítrofes), produzida manualmente pela equipe de pesquisa clínica da Bárbara — **não** gerada por IA.

---

## 3. Decisões já tomadas (NÃO alterar sem aprovação)

| # | Decisão | Status |
|---|---|---|
| ⚠️ | **Proposta pendente (equipe de 2):** MVP roda só em Python (planilha → planilha); D1, D3 e D4 **adiados para pós-MVP**, não descartados. Ver seção 5 de `CLINIA_DIVISAO_TAREFAS.md`. Claude Code: confirme com o Paulo antes de criar qualquer coisa em Node, Postgres ou React. | `[A CONFIRMAR]` |
| D1 | Back-end em **Node.js (Express)** | `[FATO]` decidido |
| D2 | Serviço separado de IA/dados em **Python (Pandas + scikit-learn)**, chamado via HTTP | `[FATO]` decidido |
| D3 | Banco **PostgreSQL**, rodando via **docker-compose** (já existe) | `[FATO]` decidido |
| D4 | Front-end em **React** | `[FATO]` decidido |
| D5 | Java foi descartado em favor de Node.js | `[FATO]` decidido |
| D6 | Tabela `protocolo` com **colunas fixas** espelhando os campos do paciente: `idade_min`, `idade_max`, `hba1c_max`, `creatinina_max`, `glicemia_jejum_max`, `imc_max`, `permite_neoplasia_ativa`, `permite_gestacao`, `exige_metformina`, `diagnostico_exigido` (NULL = critério não usado). **Não** usar modelo EAV/uma-linha-por-critério. | `[FATO]` decidido |
| D7 | **Camada 1 (regras fixas)** decide a elegibilidade binária `elegibilidade_calculada` comparando paciente × colunas do protocolo. | `[FATO]` decidido |
| D8 | **Camada 2 (Random Forest)**, treinada nos casos rotulados, gera `probabilidade_elegibilidade`, usada **apenas para ordenar** pacientes dentro de cada resultado binário. **O RF nunca sobrescreve a regra.** | `[FATO]` decidido |
| D9 | Todo paciente real tem texto livre (`anotacao_medica`) — portanto a **extração por LLM não é opcional**: todo registro passa por ela. | `[FATO]` confirmado em campo no HC-UFPE |
| D10 | Fine-tuning de Llama 3 8B **descartado para o MVP** (poucos dados rotulados, limite de GPU, risco de prazo). Usar LLM via **API**. Reavaliar pós-MVP. | `[FATO]` decidido |
| D11 | **Escopo da demo:** entrada = planilha simulando o AGHUx (campos estruturados + campo de texto livre); saída = planilha marcando cada paciente como elegível/não elegível **com os critérios limitantes**. Sem tela de cadastro de protocolo e sem integração real com AGHUx no MVP. | `[FATO]` decidido |
| D12 | ~~Divisão de frentes: Paulo + Matheus Andrade → PostgreSQL + CRUD Node; Pedro + Mateus Basílio → estruturação de dados com Pandas.~~ **Substituída em 16/10/2026:** Paulo (entrada + LLM) e Mateus Basílio (Pandas, regras, RF, saída) constroem; Pedro e Matheus Andrade apresentam. | `[FATO]` atualizado |

### 3.1 Arquitetura de privacidade (visão de produto, 4 camadas)

1. Dados identificados ficam no hospital.
2. Desidentificação do texto clínico antes de sair do hospital.
3. Dados pseudonimizados + ranking por IA do lado da CLINIA.
4. "Cofre" de revelação de identidade com RBAC e log imutável.

> **Para o MVP:** só dados fictícios, então as camadas 2–4 **não precisam ser implementadas**. Mas o código deve **nascer compatível** com elas: usar `id_paciente` pseudônimo (ex.: `PAC-0001`), nunca nome, e manter o texto livre separado dos identificadores. Ver seção 9.

---

## 4. Escopo do MVP (04/12/2026)

### 4.1 Dentro do escopo

- [ ] Leitura de planilha (CSV/XLSX) de pacientes fictícios com campos estruturados + `anotacao_medica`.
- [ ] Cadastro de **1 a 3 protocolos** direto no banco (seed/SQL), sem tela.
- [ ] **Extração por LLM** do texto livre → campos estruturados + **trecho de evidência** de cada campo.
- [ ] **Camada de regras** → `elegibilidade_calculada` + lista de **critérios limitantes**.
- [ ] **Random Forest** → `probabilidade_elegibilidade` para ordenação (ver ponto crítico na seção 6.4).
- [ ] **Saída**: planilha ranqueada com: id, elegível (sim/não/revisar), probabilidade, critérios atendidos, critérios limitantes, evidências do texto.
- [ ] **Métricas** comparando a saída com os rótulos da equipe da Bárbara.
- [ ] Um jeito simples e confiável de **rodar a demo** de ponta a ponta (script único ou botão).

### 4.2 Fora do escopo (vai para `docs/BACKLOG_POS_MVP.md`)

- Integração real com AGHUx.
- Tela de cadastro de protocolo / leitura de protocolo em PDF por LLM.
- Login, RBAC, Cofre de identidade, log imutável com hash.
- Dados reais de pacientes.
- Fine-tuning de modelo próprio.
- Deploy em nuvem/intranet de hospital.

### 4.3 Decisão em aberto sobre a interface da demo

`[A VALIDAR com o Paulo]` A D11 diz "saída em planilha". Há três níveis possíveis:

| Opção | O que é | Prós | Contras |
|---|---|---|---|
| A | Só script → gera planilha de saída | Mais rápido e seguro para o prazo | Demo menos visual |
| B | A + uma **tela React simples** com a lista ranqueada e um painel "por quê?" ao clicar no paciente | Mostra a explicabilidade, que é o diferencial; aproveita o React já decidido | ~1 semana a mais |
| C | Front completo com upload, cadastro de protocolo etc. | Visual de produto | Alto risco de não fechar até 04/12 |

**Sugestão:** fazer **A primeiro** (garante a entrega) e **B só se A estiver pronto até ~20/11**. Claude Code: confirme com o Paulo antes de começar o front.

---

## 5. Arquitetura proposta para o MVP

```
                ┌──────────────────────────────────────────┐
 planilha.xlsx  │  Node.js (Express)                        │
 ─────────────▶ │  - recebe/importa planilha                │
                │  - grava pacientes e protocolos no Postgres│
                │  - dispara a triagem                      │
                │  - devolve planilha/JSON de resultado     │
                └───────────────┬──────────────────────────┘
                                │ HTTP (JSON)
                                ▼
                ┌──────────────────────────────────────────┐
                │  Serviço Python (IA/dados)                │
                │  1. Extração LLM do texto livre  ──────▶ API do LLM
                │     (JSON validado + evidências)          │
                │  2. Junta estruturado + extraído (Pandas) │
                │  3. Camada de regras (decisão binária)    │
                │  4. Random Forest (probabilidade/ranking) │
                │  5. Monta justificativas                  │
                └───────────────┬──────────────────────────┘
                                ▼
                ┌──────────────────────────────────────────┐
                │  PostgreSQL (docker-compose)              │
                │  paciente | protocolo | extracao |        │
                │  resultado_triagem | execucao             │
                └──────────────────────────────────────────┘
                                ▼
                 planilha_resultado.xlsx  (+ tela React opcional)
```

### 5.1 Decisões em aberto da arquitetura

| Tema | Opções | Sugestão | Status |
|---|---|---|---|
| Framework do serviço Python | FastAPI / Flask | **FastAPI**: valida JSON com Pydantic (útil para a saída do LLM) e gera documentação automática da API | `[A VALIDAR]` |
| Quem chama o LLM | Serviço Python / Node | **Python**: concentra toda a IA num lugar só e facilita testar a extração junto com o Pandas | `[A VALIDAR]` |
| Guardar extrações no banco? | Sim / Não | **Sim**, numa tabela `extracao`: evita pagar o LLM duas vezes pelo mesmo texto e dá rastreabilidade | `[A VALIDAR]` |
| Rodar tudo via Docker? | Só Postgres (atual) / tudo | **Manter só Postgres no Docker** até o MVP (decisão D3 atual); dockerizar o resto é pós-MVP | `[SUGESTÃO]` |

---

## 6. A grande pergunta: "Vamos precisar de LLM ou de quê?"

### 6.1 Resposta curta

`[FATO]` Já foi decidido: **sim, LLM via API para ler o texto livre**, **regras fixas para decidir** e **Random Forest para ordenar**. Cada peça faz uma coisa:

| Peça | Faz | Não faz |
|---|---|---|
| **LLM** | Lê `anotacao_medica` e transforma em campos estruturados (ex.: `neoplasia_ativa: false`, evidência: "nega história de câncer") | **Não decide** elegibilidade |
| **Regras** | Compara paciente × protocolo e decide elegível / não elegível / revisar | Não ordena por "quão bom" é o candidato |
| **Random Forest** | Dá uma probabilidade para ordenar a lista | **Nunca muda** a decisão das regras |

Por que dividir assim: um LLM decidindo sozinho a elegibilidade seria difícil de auditar e poderia "inventar". Usar o LLM **só para extrair, sempre com a citação do trecho**, mantém a decisão em regras transparentes — e isso é exatamente o diferencial de auditabilidade da CLINIA.

### 6.2 Alternativas ao LLM (para registro e para responder à banca)

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| Regex / palavras-chave | Barato, rápido, determinístico | Erra negação ("nega DM"), sinônimos, abreviações médicas | Usar só como **checagem auxiliar/fallback** |
| NER clínico em português (modelos BERT) | Roda local | Precisa de dado rotulado e ajuste; pouco tempo | Pós-MVP |
| LLM local (ex.: via Ollama) | Dados não saem da máquina (bom para LGPD) | Qualidade menor em modelos pequenos; exige hardware | Pós-MVP / argumento de roadmap |
| Fine-tuning Llama 3 8B | Modelo próprio | Já descartado (D10) | Pós-MVP |
| **LLM via API com saída estruturada** | Melhor qualidade, rápido de integrar | Custo por chamada; dado sai da máquina | **Escolhido para o MVP** (dados fictícios eliminam o risco de LGPD agora) |

### 6.3 Escolha do provedor/modelo — `[A VALIDAR com o Paulo]`

A equipe já usa Claude, GPT e Gemini. Critérios para escolher:

1. **Suporte a saída estruturada/JSON confiável** (tool use, JSON schema ou equivalente).
2. **Qualidade em português clínico** — testar com 10–15 anotações reais do dataset fictício antes de decidir.
3. **Custo** para 200 pacientes × algumas rodadas (deve ser pequeno, mas confirmar na página de preços oficial do provedor no dia).
4. **Facilidade de chave/créditos** para a equipe.

**Sugestão de processo:** na Fase 3, o Claude Code roda o mesmo conjunto de 15 anotações em 2 modelos (um "rápido/barato" e um "mais forte") e apresenta tabela de acertos. O Paulo escolhe.

Configuração recomendada independentemente do provedor: `temperature = 0`, schema JSON obrigatório, validação com Pydantic, cache por hash do texto.

### 6.4 ⚠️ Ponto crítico para discutir: o Random Forest vai agregar?

`[HIPÓTESE / A VALIDAR]` Se o rótulo "elegível" dos 200 pacientes foi definido **exatamente pelas mesmas regras** da Camada 1, o Random Forest tende a só reaprender as regras e devolver probabilidades perto de 0 ou 1. Aí a ordenação **dentro** de cada grupo fica quase aleatória e não ajuda o coordenador.

O Claude Code deve, na Fase 4:

1. Verificar como os rótulos foram feitos (perguntar ao Paulo / equipe da Bárbara): são **só regras** ou têm **julgamento clínico** (ex.: os 30 casos limítrofes)?
2. Mostrar a distribuição de `probabilidade_elegibilidade` gerada. Se estiver tudo concentrado em 0 e 1, avisar.
3. Propor (sem implementar sem OK) uma alternativa ou complemento simples e explicável, por exemplo:
   - **margem até o limite** (ex.: HbA1c 7,9 com limite 8,0 está "na borda"; 6,5 está "folgado");
   - **nº de critérios atendidos com folga** / **completude dos dados**.

Isso não muda a decisão D8 — só garante que ela entregue valor real. Se o RF for mantido, ótimo; se não agregar, a equipe precisa saber **antes** da banca perguntar.

---

## 7. Contrato de dados

> `[A VALIDAR]` As colunas abaixo foram **deduzidas** do esquema da tabela `protocolo` (D6). O Claude Code deve **conferir com a planilha real** na Fase 1 e ajustar este contrato com aprovação do Paulo.

### 7.1 Entrada — planilha de pacientes

| Coluna | Tipo | Origem | Observação |
|---|---|---|---|
| `id_paciente` | texto | estruturado | Pseudônimo (ex.: `PAC-0001`). Nunca nome. |
| `idade` | inteiro | estruturado | |
| `sexo` | texto | estruturado | Se existir |
| `diagnostico` | texto/CID | estruturado | Comparar com `diagnostico_exigido` |
| `hba1c` | decimal | estruturado | % |
| `creatinina` | decimal | estruturado | mg/dL |
| `glicemia_jejum` | decimal | estruturado | mg/dL |
| `imc` | decimal | estruturado | kg/m² |
| `anotacao_medica` | texto livre | não estruturado | Vai para o LLM |
| `elegivel_rotulo` | booleano | rótulo da equipe da Bárbara | **Só para treino/avaliação**, nunca usado como entrada da decisão |

### 7.2 Campos extraídos pelo LLM (de `anotacao_medica`)

Cada campo volta com **valor + evidência + confiança**:

```json
{
  "id_paciente": "PAC-0001",
  "neoplasia_ativa": {
    "valor": false,
    "status": "negado",
    "evidencia": "nega história de neoplasia",
    "confianca": "alta"
  },
  "gestacao": {
    "valor": null,
    "status": "nao_mencionado",
    "evidencia": null,
    "confianca": "alta"
  },
  "uso_metformina": {
    "valor": true,
    "status": "afirmado",
    "evidencia": "em uso de metformina 850mg 2x/dia",
    "confianca": "alta"
  },
  "diagnosticos_mencionados": ["diabetes mellitus tipo 2", "hipertensão arterial"],
  "observacoes_relevantes": "Paciente relata episódios de hipoglicemia."
}
```

**Regras do contrato:**

- `status` ∈ { `afirmado`, `negado`, `nao_mencionado`, `incerto` }. **Diferenciar "negado" de "não mencionado" é essencial** — é o erro clássico de quem faz busca por palavra-chave.
- `evidencia` deve ser um **trecho literal** da anotação (permite auditoria). O código deve **verificar** que o trecho existe de fato no texto; se não existir, marcar `confianca: baixa` e mandar para revisão.
- Campo `incerto` ou `confianca: baixa` **nunca** vira "elegível" automático — vira **"revisar"**.

### 7.3 Saída — planilha de resultado

| Coluna | Descrição |
|---|---|
| `posicao` | Ordem na lista |
| `id_paciente` | Pseudônimo |
| `resultado` | `ELEGÍVEL` / `NÃO ELEGÍVEL` / `REVISAR` |
| `probabilidade` | Da Camada 2 (ou score alternativo, ver 6.4) |
| `criterios_atendidos` | Lista legível |
| `criterios_limitantes` | Lista legível (ex.: "HbA1c 9,2 > máx. 8,0") |
| `evidencias_texto` | Trechos da anotação usados |
| `rotulo_esperado` | Só na versão de avaliação |
| `acertou` | Só na versão de avaliação |

### 7.4 Proposta de tabelas novas — `[A VALIDAR]`

- `extracao` (id_paciente, hash_texto, json_extraido, modelo_llm, criado_em)
- `execucao` (id, protocolo_id, data, modelo_llm, versao_regras, versao_modelo_rf)
- `resultado_triagem` (execucao_id, id_paciente, resultado, probabilidade, criterios_atendidos, criterios_limitantes, evidencias)

Motivo: rastreabilidade — saber **qual versão** do sistema gerou **qual resultado**. Isso conversa com auditabilidade e LGPD, que são diferenciais da CLINIA.

---

## 8. Métricas de sucesso do MVP

`[FATO]` Do Canvas do MVP já documentado: **identificar corretamente mais de 80% dos pacientes elegíveis nos testes internos.**

O Claude Code deve calcular e mostrar, comparando com `elegivel_rotulo`:

| Métrica | Pergunta que responde | Meta sugerida |
|---|---|---|
| **Sensibilidade (recall) dos elegíveis** | Dos elegíveis de verdade, quantos encontramos? | **> 80%** (meta oficial) |
| Precisão | Dos que marcamos elegíveis, quantos eram mesmo? | registrar |
| Desempenho nos **30 limítrofes** | O sistema manda os casos difíceis para "REVISAR"? | registrar e discutir |
| Acurácia da extração LLM | O LLM extraiu certo cada campo? (amostra conferida à mão) | registrar por campo |
| Tempo total para 200 pacientes | "Enquanto você lê um, a CLINIA leu todos" em números | registrar (vai para o pitch) |

> **Por que sensibilidade em primeiro lugar:** para o coordenador, perder um paciente elegível é pior do que revisar um a mais. O sistema deve errar para o lado do "REVISAR", não do "NÃO ELEGÍVEL".

Cuidados:
- Separar dados de **treino e teste** do Random Forest (ou validação cruzada). Com 200 linhas, explicar à equipe o porquê.
- Registrar a matriz de confusão em `docs/RESULTADOS.md`.
- **Medir o tempo** da triagem automática: esse número é ouro para o pitch e para subir o item "proposta de valor" no diagnóstico da incubadora.

---

## 9. LGPD e segurança no MVP

| Regra | Como aplicar |
|---|---|
| Só dados fictícios | Checar na Fase 1; avisar se algo parecer real |
| Pseudônimo desde já | `id_paciente` tipo `PAC-0001`; nada de nome/CPF em nenhuma tabela |
| Segredos | `.env` + `.gitignore`; `.env.example` sem valores |
| Logs | Não logar texto clínico completo nem chaves |
| Texto separado da identidade | Já preparar o caminho das camadas 2–4 (seção 3.1) |
| Discurso correto | Pseudonimização ≠ criptografia; desidentificação do texto é uma camada a mais |
| Envio para API externa | Aceitável **só** com dados fictícios. Com dados reais, isso precisa de base legal, acordo com o hospital e desidentificação antes — registrar no backlog |

---

## 10. Roteiro por fases (com prompts prontos)

> Cada fase: **objetivo → entregáveis → critério de pronto → prompt**. Cole o prompt no Claude Code. Ele deve **propor antes de executar**.

### Cronograma sugerido até 04/12

| Semana | Datas | Fase(s) |
|---|---|---|
| S1 | 16–23/10 | Fase 0 (auditoria) + Fase 1 (contrato de dados) |
| S2 | 24–30/10 | Fase 2 (camada de regras) |
| S3 | 31/10–06/11 | Fase 3 (extração LLM) |
| S4 | 07–13/11 | Fase 4 (Random Forest + avaliação) |
| S5 | 14–20/11 | Fase 5 (integração Node ↔ Python + saída) |
| S6 | 21–27/11 | Fase 6 (demo: script e, se der, tela React) |
| S7 | 28/11–04/12 | Fase 7 (congelamento, testes, ensaio, folga) |

**Regra de ouro do cronograma:** a partir de **28/11, nada de funcionalidade nova** — só correção e ensaio.

---

### Fase 0 — Auditoria do que já existe e alinhamento

**Objetivo:** o Claude Code entender o repositório atual antes de mexer em qualquer coisa.
**Entregáveis:** `docs/AUDITORIA.md` com o estado atual; lista de lacunas; plano da Fase 1.
**Critério de pronto:** Paulo leu e aprovou a auditoria.

```text
Leia o arquivo CLINIA_MVP_PLAYBOOK.md inteiro e siga as Regras de Trabalho da seção 1.

Tarefa (Fase 0 — Auditoria, SOMENTE LEITURA, não altere nenhum arquivo ainda):
1. Mapeie a estrutura do repositório: pastas, linguagens, dependências (package.json, requirements.txt etc.), docker-compose, scripts.
2. Verifique o que já existe de cada decisão da seção 3 (D1 a D12): Express rodando? Postgres no docker-compose? Tabela protocolo criada com as colunas da D6? CRUD em Node? Código Pandas? Dataset de 200 pacientes?
3. Localize a planilha de pacientes fictícios e me diga: nome do arquivo, colunas reais, nº de linhas, se existe a coluna de texto livre e a coluna de rótulo.
4. Compare o que encontrou com o Contrato de Dados da seção 7 e liste as diferenças.
5. Liste riscos e lacunas que você vê para cumprir o prazo de 04/12.

Entregue um relatório em tópicos, marcando [FATO]/[HIPÓTESE]/[A VALIDAR]. Depois proponha o conteúdo de docs/AUDITORIA.md e só crie o arquivo quando eu aprovar.
Termine com as perguntas que você precisa que eu responda antes da Fase 1.
```

---

### Fase 1 — Contrato de dados e qualidade do dataset

**Objetivo:** fechar exatamente quais colunas entram, quais o LLM extrai e quais saem.
**Entregáveis:** contrato de dados atualizado (seção 7 ajustada), `docs/DECISOES.md` iniciado, script de validação do dataset.
**Critério de pronto:** contrato aprovado; script aponta zero erro bloqueante no dataset.

```text
Fase 1 — Contrato de dados.

1. Com base na planilha real encontrada na Fase 0, proponha a versão final do Contrato de Dados (seção 7 do playbook): colunas de entrada, campos que o LLM deve extrair de anotacao_medica, e colunas de saída.
2. Para cada critério da tabela protocolo (D6), diga se ele vem de campo estruturado ou do texto livre. Exemplo: permite_gestacao provavelmente vem do texto.
3. Escreva (após minha aprovação) um script Python de validação do dataset que verifique: colunas obrigatórias, tipos, valores fora de faixa plausível (ex.: idade negativa, HbA1c > 20), textos vazios, ids duplicados, e qualquer sinal de dado real (nomes próprios, CPF, nº de telefone).
4. Mostre estatísticas: distribuição de idade, HbA1c etc., e quantos elegíveis/não elegíveis/limítrofes.
5. Crie docs/DECISOES.md com as decisões já tomadas (seção 3) e as novas desta fase.

Proponha antes de criar arquivos. Explique cada escolha em linguagem simples.
```

---

### Fase 2 — Camada de regras (decisão binária)

**Objetivo:** implementar a Camada 1 (D7) de forma transparente e testada.
**Entregáveis:** módulo de regras em Python; testes unitários; 1–3 protocolos de exemplo no banco (seed).
**Critério de pronto:** testes passando; cada "não elegível" vem com o critério limitante legível.

```text
Fase 2 — Camada de regras.

Implemente (após aprovação do desenho) a Camada 1 descrita nas decisões D6 e D7:
- Entrada: um paciente (campos estruturados + campos extraídos do texto) e um protocolo (linha da tabela protocolo).
- Saída: resultado (ELEGÍVEL / NÃO ELEGÍVEL / REVISAR), lista de critérios atendidos e lista de critérios limitantes em português legível (ex.: "HbA1c 9,2% acima do máximo de 8,0%").
- Coluna NULL no protocolo = critério ignorado.
- Campo necessário com status "incerto", "nao_mencionado" quando o critério exige confirmação, ou confiança baixa => REVISAR, nunca ELEGÍVEL automático. Discuta comigo os casos de "nao_mencionado" um a um (ex.: gestação não mencionada num homem de 60 anos vs. numa mulher de 30).

Antes de codar, me mostre:
1. A tabela de decisão (critério × situação → resultado).
2. Os casos de borda que você identificou.
3. Os testes que pretende escrever.

Também proponha um seed SQL com 1 a 3 protocolos de exemplo coerentes com o dataset (ex.: um estudo de DM2). Não invente critérios clínicos sem me perguntar — se precisar, sugira e marque como [SUGESTÃO] para eu validar com a equipe clínica.
```

---

### Fase 3 — Extração do texto livre com LLM

**Objetivo:** transformar `anotacao_medica` em campos estruturados com evidência.
**Entregáveis:** módulo de extração; prompt do extrator versionado em `prompts/`; cache; relatório comparando 2 modelos.
**Critério de pronto:** extração conferida à mão em ≥ 20 pacientes, com acurácia por campo registrada; nenhuma evidência "inventada" passa sem ser marcada.

```text
Fase 3 — Extração por LLM.

1. Proponha a estrutura do módulo de extração em Python: chamada à API, schema de saída validado com Pydantic, verificação de que cada "evidencia" existe literalmente no texto, cache por hash do texto (tabela extracao ou arquivo local — me pergunte), retry com limite, e tratamento de erro.
2. Use como base o prompt do extrator da seção 12 do playbook. Melhore-o se achar necessário, explicando cada mudança. Salve em prompts/extrator_v1.md (versionado).
3. Configuração: temperature 0, saída estruturada obrigatória, chave em .env.
4. Experimento de escolha de modelo: rode as mesmas 15 anotações em 2 modelos (um rápido/barato e um mais forte, do provedor que eu escolher). Monte uma tabela de acertos por campo, com atenção especial a NEGAÇÕES ("nega", "sem", "ausência de") e a abreviações médicas (DM2, HAS, IRC, Ca).
5. Depois que eu escolher o modelo, rode nos 200 e gere uma planilha para conferência manual de uma amostra de 20.

Antes de qualquer chamada paga à API, me diga quantas chamadas vai fazer e peça confirmação.
```

---

### Fase 4 — Random Forest e avaliação

**Objetivo:** implementar a Camada 2 (D8) e medir o sistema inteiro.
**Entregáveis:** treino do RF com separação treino/teste; `docs/RESULTADOS.md` com métricas da seção 8; discussão do ponto crítico 6.4.
**Critério de pronto:** sensibilidade dos elegíveis medida (meta > 80%); o Paulo decidiu manter o RF, ajustar ou complementar com score alternativo.

```text
Fase 4 — Random Forest e avaliação.

1. Leia a seção 6.4 do playbook (ponto crítico). Antes de treinar, me pergunte como os rótulos dos 200 pacientes foram definidos (só regras ou julgamento clínico).
2. Proponha: features (estruturadas + extraídas), separação treino/teste ou validação cruzada (explique por que com 200 linhas), e hiperparâmetros iniciais simples.
3. Treine e mostre: distribuição das probabilidades, importância das features, e se as probabilidades estão concentradas em 0 e 1.
4. Rode o pipeline completo (extração → regras → RF) e calcule as métricas da seção 8: sensibilidade, precisão, matriz de confusão, comportamento nos 30 limítrofes, tempo total.
5. Se o RF não agregar à ordenação, proponha (sem implementar) uma alternativa explicável, como margem até o limite, e compare as duas ordenações comigo.
6. Escreva docs/RESULTADOS.md em linguagem que eu possa usar no pitch.

Lembre: o RF NUNCA muda a decisão da camada de regras (D8).
```

---

### Fase 5 — Integração Node ↔ Python e saída

**Objetivo:** juntar as frentes do Paulo (entrada + LLM) e do Mateus Basílio (Pandas, regras, RF, saída) num comando único. Se a proposta Python-only for confirmada, ignore as partes de Node/Postgres abaixo e use arquivos com data e versão no lugar das tabelas.
**Entregáveis:** endpoint no Python; rota no Express que importa a planilha, chama a triagem, grava resultados e gera a planilha de saída.
**Critério de pronto:** um comando roda tudo de ponta a ponta e gera `planilha_resultado.xlsx` igual à seção 7.3.

```text
Fase 5 — Integração.

1. Proponha o contrato HTTP entre Node e Python: endpoint, formato do request/response (JSON), códigos de erro, timeout.
2. Proponha as tabelas extracao, execucao e resultado_triagem (seção 7.4) como migração SQL — só aplique após minha aprovação.
3. Implemente a rota no Express: importa planilha → grava pacientes → chama o serviço Python → grava resultado → gera planilha de saída (colunas da seção 7.3).
4. Crie um comando único para a demo (ex.: npm run demo ou script) e documente no README como rodar do zero: subir o Postgres, instalar dependências, configurar .env, rodar.
5. Teste em uma máquina "limpa" mentalmente: liste tudo que alguém precisaria instalar.

Respeite a divisão de frentes (D12 atualizada): explique quais partes o Paulo e o Mateus devem revisar um do outro.
```

---

### Fase 6 — Demo (script e, se der tempo, tela React)

**Objetivo:** tornar a explicabilidade visível.
**Entregáveis:** demo por script estável; opcionalmente uma tela React com lista ranqueada + painel "por quê?".
**Critério de pronto:** demo roda 3 vezes seguidas sem erro, em menos de alguns minutos, com dados de exemplo.

```text
Fase 6 — Demo.

1. Garanta que a demo por script (Fase 5) roda 3 vezes seguidas sem erro. Se a API do LLM cair na hora da apresentação, a demo precisa continuar: proponha um modo "offline" usando o cache das extrações.
2. SÓ SE eu aprovar (ver seção 4.3, opção B): proponha uma tela React simples com
   - lista ranqueada (posição, id, resultado com cor, probabilidade);
   - ao clicar no paciente, painel "Por quê?" mostrando critérios atendidos, limitantes e os TRECHOS do texto destacados;
   - aviso fixo: "A decisão final é do coordenador/médico."
   Nada de login, upload complexo ou cadastro de protocolo.
3. Liste o que mostrar na demo em até 3 minutos, na ordem.
```

---

### Fase 7 — Congelamento, testes e ensaio (28/11 a 04/12)

**Objetivo:** chegar no dia 04/12 com algo que funciona sempre.
**Entregáveis:** checklist da seção 13 cumprido; tag de versão `mvp-v1.0` no git.
**Critério de pronto:** ensaio completo feito pela equipe sem o Claude Code.

```text
Fase 7 — Congelamento.

1. Não adicione funcionalidades. Revise bugs, mensagens de erro, README e docs.
2. Rode o checklist da seção 13 do playbook item por item e me diga o status de cada um.
3. Gere um resumo de 1 página (docs/MVP_RESUMO.md) com: o que o MVP faz, arquitetura em uma figura, métricas obtidas, limitações honestas e próximos passos pós-MVP. Linguagem para banca não técnica.
4. Proponha a tag de versão mvp-v1.0 e me peça confirmação antes de criá-la.
```

---

## 11. Prompts utilitários

### 11.1 Prompt de abertura (cole na primeira sessão)

```text
Você vai me ajudar a construir o MVP da CLINIA até 04/12/2026.
Antes de tudo, leia CLINIA_MVP_PLAYBOOK.md por completo.
Regras: siga a seção 1 (perguntar antes de decidir, explicar o porquê, alternativas, não inventar, só dados fictícios).
Não altere nenhum arquivo nesta primeira mensagem.
Me responda:
1. Um resumo de 5 linhas do que você entendeu do projeto.
2. As decisões já tomadas que você vai respeitar.
3. As decisões em aberto que vamos precisar fechar (com sua recomendação inicial para cada uma).
4. Qualquer inconsistência ou risco que você viu no playbook.
Depois disso, aguarde meu OK para iniciar a Fase 0.
```

### 11.2 Retomar uma sessão

```text
Retomando o trabalho da CLINIA. Leia CLINIA_MVP_PLAYBOOK.md, docs/DECISOES.md e o git log recente.
Me diga: em que fase estamos, o que foi feito por último, o que falta para o critério de pronto desta fase e qual o próximo passo que você propõe. Aguarde meu OK.
```

### 11.3 Pedir revisão crítica

```text
Faça uma revisão crítica do que construímos até agora como se fosse um engenheiro sênior e um avaliador de banca de saúde digital. Aponte: bugs prováveis, riscos de LGPD, pontos frágeis da explicabilidade, o que pode quebrar na demo e o que uma banca perguntaria. Não altere nada; só liste, ordenado por gravidade.
```

### 11.4 Quando travar num erro

```text
Estou com este erro: [colar erro]. Antes de corrigir: explique em linguagem simples o que está acontecendo, a causa mais provável, como confirmar, e as opções de correção. Aguarde minha escolha.
```

### 11.5 Registrar decisão

```text
Registre em docs/DECISOES.md: decisão, data de hoje, motivo, alternativas descartadas e impacto em outras partes. Mostre o texto antes de salvar.
```

### 11.6 Explicar para a equipe

```text
Explique o que fizemos nesta fase para o Pedro e o Matheus Andrade, que vão APRESENTAR o MVP mas não programaram: o que foi construído, por que, o que isso significa para quem usa (coordenador de pesquisa), o que ainda não funciona e que perguntas uma banca faria sobre esta parte. Linguagem não técnica, máximo 1 página.
```

---

## 12. Rascunho do prompt do extrator LLM (v0 — melhorar na Fase 3)

> `[SUGESTÃO]` Rascunho inicial. O Claude Code deve testar, medir e propor melhorias. Os campos devem ser ajustados ao contrato final da Fase 1.

```text
Você é um assistente de extração de informações clínicas para triagem de pesquisa clínica.
Sua única tarefa é LER a anotação médica e EXTRAIR informações. Você NÃO decide se o paciente é elegível.

Regras:
1. Extraia apenas o que está escrito. Não deduza, não complete, não use conhecimento externo sobre o paciente.
2. Para cada campo, classifique o status:
   - "afirmado": o texto diz que existe/está presente;
   - "negado": o texto diz explicitamente que NÃO existe ("nega", "sem", "ausência de", "descarta");
   - "nao_mencionado": o texto não fala sobre isso;
   - "incerto": o texto é ambíguo, condicional ou contraditório ("suspeita de", "a esclarecer", "investigar").
3. Em "evidencia", copie o TRECHO EXATO do texto que justifica a classificação (até ~20 palavras). Se o status for "nao_mencionado", evidencia = null.
4. Atenção a abreviações médicas brasileiras (ex.: DM2 = diabetes mellitus tipo 2, HAS = hipertensão arterial sistêmica, IRC = insuficiência renal crônica, Ca = câncer/neoplasia, G1P1 = gestações/partos).
5. Atenção a tempo verbal e temporalidade: "neoplasia tratada em 2015, em remissão" não é neoplasia ATIVA → marque "incerto" se não estiver claro.
6. Responda SOMENTE com o JSON no formato definido, sem texto adicional.

Campos a extrair:
- neoplasia_ativa
- gestacao
- uso_metformina
- diagnosticos_mencionados (lista de textos)
- observacoes_relevantes (texto curto ou null)

Anotação médica:
"""
{anotacao_medica}
"""
```

Casos de teste obrigatórios para esse prompt (o Claude Code deve criar exemplos fictícios de cada um):

- negação explícita ("nega neoplasia");
- negação com abreviação ("sem Ca");
- história passada vs. ativa ("Ca de mama tratado em 2018");
- suspeita ("suspeita de gestação, aguarda beta-HCG");
- medicação suspensa ("metformina suspensa há 2 meses");
- texto sem menção ao campo;
- texto com erro de digitação/abreviação incomum.

---

## 13. Checklist da demo (04/12)

- [ ] Demo roda do zero seguindo o README.
- [ ] Demo roda 3× seguidas sem erro.
- [ ] Modo offline (cache) funciona sem internet/API.
- [ ] Nenhum dado real em lugar nenhum do repositório.
- [ ] `.env` fora do git; `.env.example` presente.
- [ ] Métricas em `docs/RESULTADOS.md` (sensibilidade, precisão, limítrofes, tempo).
- [ ] Cada paciente "NÃO ELEGÍVEL" tem critério limitante legível.
- [ ] Cada campo extraído do texto tem trecho de evidência verificado.
- [ ] Casos "REVISAR" aparecem destacados.
- [ ] Frase "a decisão final é humana" visível na saída/tela.
- [ ] `docs/MVP_RESUMO.md` pronto para a banca.
- [ ] Limitações honestas listadas (sem integração AGHUx, dados fictícios, protocolos cadastrados manualmente).
- [ ] Tag `mvp-v1.0` criada.
- [ ] Ensaio feito pelos apresentadores (Pedro e Matheus Andrade), cronometrado, com a demo rodando.
- [ ] Vídeo gravado da demo como plano B.
- [ ] Apresentadores respondem sem ajuda às perguntas difíceis da banca.

---

## 14. Riscos e mitigação

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Prazo apertado (7 semanas) | Alta | Alto | Fases curtas; congelamento em 28/11; opção A antes da B |
| LLM extrai errado negações/abreviações | Média | Alto | Status "negado" vs "não mencionado"; casos de teste; conferência manual de 20 |
| LLM "inventa" evidência | Média | Alto | Verificar trecho literal no texto; senão → REVISAR |
| RF não agrega (6.4) | Média | Médio | Medir na Fase 4; score alternativo explicável |
| API do LLM fora do ar na apresentação | Baixa | Alto | Modo offline com cache |
| Frentes Node e Python não se encaixam | Média | Médio | Contrato HTTP definido cedo (Fase 5 pode ser antecipada se necessário) |
| Equipe depender da IA sem entender o código | Média | Médio | Prompt 11.6 ao fim de cada fase; revisão cruzada Paulo ↔ Mateus |
| Apresentadores não dominam o sistema na banca | Média | Alto | Entram na S3 (seção 5.1 da divisão); prompt 11.6 a cada fase; ensaios com a demo rodando a partir da S6 |
| Demo falha ao vivo | Média | Alto | Modo offline + vídeo gravado da demo + planilha de saída já gerada como plano B |
| Escopo crescer | Alta | Alto | Backlog pós-MVP (seção 4.2) |
| Custo de API acima do esperado | Baixa | Baixo | Cache + pedir confirmação antes de lotes pagos |

---

## 15. Perguntas que o Paulo precisa responder (o Claude Code deve cobrar)

1. Qual provedor de LLM e qual conta/chave a equipe vai usar? Há orçamento definido para API?
2. Onde está a planilha dos 200 pacientes e ela tem a coluna `anotacao_medica` e a coluna de rótulo?
3. Os rótulos foram definidos só por regras ou com julgamento clínico (ver 6.4)?
4. Quais 1–3 protocolos de exemplo usar na demo? A equipe clínica (Bárbara) pode validar os critérios?
5. Demo só por planilha (opção A) ou com tela React (opção B)?
6. Para quem é a demo de 04/12 (incubadora, banca, hospital)? Isso muda o que mostrar.
7. O repositório está no GitHub? Quem tem acesso?
8. Quanto tempo por semana cada membro consegue dedicar até 04/12?

---

## 16. O que registrar na Base de Conhecimento da CLINIA ao fim do MVP

- Decisões finais de arquitetura e o porquê (`docs/DECISOES.md`).
- Métricas obtidas e limitações (`docs/RESULTADOS.md`).
- Versão final do prompt do extrator e o desempenho por campo.
- Aprendizados sobre o Random Forest vs. score alternativo.
- Lista do backlog pós-MVP priorizada.
- O número de **tempo de triagem** (manual vs. CLINIA), se for medido com uma coordenadora — ele alimenta o pitch e o diagnóstico da incubadora (item "proposta de valor" nível 4).
