# CLINIA — Registro de decisões

> As decisões D1–D12 estão na seção 3 do `CLINIA_MVP_PLAYBOOK.md`.
> Este arquivo registra as decisões novas. **Regra:** os dois só acrescentam no fim, nunca reescrevem.

---

## D13 — MVP só em Python

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo e Mateus Basílio
- **Decisão:** o MVP roda só em Python: planilha de entrada → LLM → regras → RF → planilha de saída. Node.js (D1), PostgreSQL (D3) e React (D4) ficam **adiados para pós-MVP, não descartados**.
- **Motivo:** equipe de duas pessoas e 7 semanas; a demo (D11) já é planilha → planilha, e Node e Postgres não aparecem para quem assiste.
- **Alternativa descartada:** manter a arquitetura completa da seção 5 do playbook (risco alto de não fechar até 04/12).
- **Impacto:**
  - não há chamada HTTP entre serviços; o pipeline é um conjunto de módulos Python e um comando único;
  - a tabela `protocolo` (D6) vira um arquivo de configuração com as mesmas colunas;
  - as tabelas `extracao`, `execucao` e `resultado_triagem` viram arquivos com data e versão em `saidas/AAAA-MM-DD_HHMM/`;
  - o cache das extrações da LLM fica em arquivo local, indexado pelo hash do texto.

## D14 — A LLM extrai do texto o que hoje está em colunas

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo
- **Decisão:** as colunas `neoplasia_ativa`, `gestacao` e `medicamentos` **não entram** no pipeline. A LLM lê `anotacao_medica` e extrai essas informações (com status, evidência e confiança). As colunas originais viram **gabarito** para medir a acurácia da extração nos 200 pacientes.
- **Motivo:** no AGHUx essas informações estão no texto livre, não em colunas. Se o pipeline usasse as colunas, a LLM não teria papel real (a D9 diz que a extração é obrigatória).
- **Alternativa descartada:** usar todas as colunas e a LLM só como complemento (a demo não mostraria o valor da LLM).
- **Impacto:** os dados numéricos (`idade`, `hba1c`, `creatinina`, `imc` etc.) continuam vindo direto da planilha, sem passar pela LLM. A lista exata de campos fecha na reunião de contrato.

## D15 — `hba1c_min` e `imc_min` no protocolo

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo
- **Decisão:** o protocolo (D6) ganha as colunas `hba1c_min` e `imc_min`.
- **Motivo:** o protocolo da aba `Criterios` da planilha usa faixas (HbA1c 7,0–10,5%; IMC 25–45 kg/m²). Sem essas colunas, ele não pode ser representado.
- **Alternativa descartada:** manter só os máximos (perderia os critérios de mínimo).
- **Impacto:** a camada de regras (Mateus) compara mínimo e máximo nos dois campos.

## D16 — Fluxo de git

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo delegou ao Claude Code
- **Decisão:** `main` = estável (merge de `develop` na sexta); `develop` = integração (todo PR vai para ela); branches `nome/tarefa` saindo de `develop`.
- **Motivo:** o repositório já tinha `develop` como branch padrão, e a seção 6 da divisão pedia `main` sempre funcionando. Usar as duas mantém o que já existe e protege a `main`.
- **Alternativa descartada:** só `main` + `nome/tarefa` (exigiria apagar ou ignorar a `develop`, que já é a padrão no GitHub).
- **Impacto:** seção 6 do `CLINIA_DIVISAO_TAREFAS.md` e `CLAUDE.md` atualizados.

## D17 — Repositório é a fonte oficial dos documentos

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo delegou ao Claude Code
- **Decisão:** a partir de hoje, a versão oficial do playbook, da divisão de tarefas e dos docs é a do repositório. As cópias do OneDrive ficam como histórico.
- **Motivo:** evitar duas versões divergentes; o Claude Code do Mateus só enxerga o que está no repositório.
- **Impacto:** quem alterar um documento faz isso no repositório, por PR.

## D18 — Ambiente Python

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo delegou ao Claude Code
- **Decisão:** ambiente virtual `.venv` no repositório, com as versões fixadas em `requirements.txt`. Bibliotecas entram só na fase que as usa.
- **Motivo:** Paulo e Mateus rodam exatamente as mesmas versões.
- **Impacto:** o Mateus precisa de Python 3.14 (`[A VALIDAR]` a versão que ele usa).

## D19 — Sem `temperature = 0`; repetibilidade pelo cache

- **Data:** 16/10/2026 · **Quem decidiu:** Claude Code (ajuste técnico, a validar pelo Paulo)
- **Decisão:** o extrator não envia `temperature`. A repetibilidade vem de: saída estruturada obrigatória (schema), cache por hash do texto + modelo + versão do prompt, e verificação da evidência pelo código.
- **Motivo:** nos modelos Claude atuais o parâmetro `temperature` foi removido; enviá-lo dá erro 400. O playbook (seção 6.3) foi escrito antes disso.
- **Impacto:** com o cache, rodar duas vezes o mesmo texto devolve exatamente a mesma extração (e não paga de novo).

## D20 — Provedor de regras (regex) como linha de base e mock

- **Data:** 16/10/2026 · **Quem decidiu:** Claude Code (Paulo delegou)
- **Decisão:** além da LLM, o extrator tem um provedor `regras` (regex, grátis, sem chave), no mesmo formato do contrato.
- **Motivo:** (1) o Mateus trabalha já com `contratos/extracoes.mock_200.json`, no formato real; (2) é a "checagem auxiliar" da seção 6.2 e a linha de base do experimento: a LLM precisa ganhar dela nos casos difíceis para se justificar.
- **Impacto:** o regex acertou 100% nos 200 da planilha e nos 15 casos de teste. Isso **não** prova que o regex é bom: a planilha é fácil (seção 5 da auditoria) e os 15 casos e as regras foram escritos juntos. Para uma comparação justa, os casos precisam vir de alguém que não viu as regras (`[A VALIDAR]` equipe da Bárbara).

## D21 — Provedor da LLM: Claude, modelo configurável

- **Data:** 16/10/2026 · **Status:** `[A VALIDAR]` com o Paulo
- **Proposta:** Claude via API, modelo em `CLINIA_MODELO` (padrão `claude-opus-5-5`). No experimento da Fase 3, comparar com `claude-haiku-5-5` (rápido e barato).
- **Motivo:** saída estruturada com schema garantido pela API; troca de modelo sem mexer no código. Trocar de provedor = escrever outra classe em `ia/extracao/provedores.py`.
- **Impacto:** o extrator nunca faz chamada paga sem `--confirmar`, e antes disso mostra quantas chamadas vai fazer.

## D22 — LLM local e pequena (Ollama), grátis

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo
- **Decisão:** por enquanto, a extração usa uma LLM pequena rodando no próprio computador, via Ollama (padrão `qwen2.5:3b`). O Claude (D21) fica como opção, sem custo enquanto não for usado.
- **Motivo:** custo zero; os dados não saem da máquina (argumento de LGPD para a banca, seção 6.2 do playbook); funciona sem internet. O notebook do Paulo tem RTX 3050 com 4 GB, onde um modelo de 3B cabe inteiro.
- **Alternativas descartadas:** API paga (custo); API com plano gratuito (limites mudam, dados saem da máquina); agente de IA (várias chamadas para uma tarefa que se resolve com uma, e mais difícil de auditar).
- **Impacto:**
  - modelo pequeno erra mais em negação e abreviação; medir nos 15 casos contra o regex antes de decidir;
  - aqui o `temperature = 0` existe e é usado;
  - quem rodar a demo precisa do Ollama e do modelo instalados, ou usar `--offline` com o cache.

## D23 — Prompt v2 (com exemplos) para o modelo local

- **Data:** 16/10/2026 · **Quem decidiu:** Claude Code (Paulo delegou), a validar pelo Paulo
- **Decisão:** com Ollama, o prompt padrão é `prompts/extrator_v2.md`, que traz 3 exemplos resolvidos. O Claude continua com o v1.
- **Motivo (medido nos 15 casos de teste, `qwen2.5:3b`):**

  | | v1 | v2 |
  |---|---|---|
  | neoplasia_ativa | 14/15 | 12/15 |
  | gestacao | 12/15 | 13/15 |
  | uso_metformina | 9/15 | 14/15 |
  | total | 35/45 (78%) | 39/45 (87%) |
  | campos com confiança baixa | 26 | 1 |
  | tempo | 178 s | 71 s |

  No v1, o modelo pequeno desistia e respondia "nao_mencionado" para tudo. Com exemplos, isso parou.
- **Erro perigoso que sobrou:** CT-04 ("História de Ca de próstata, em seguimento") saiu "negado" em vez de "incerto". Esse tipo de erro pode deixar elegível alguém que deveria ir para revisão.
- **Limite da medida:** os exemplos cobrem os mesmos tipos de dificuldade dos 15 casos, então 87% é otimista. Precisa de casos escritos por outra pessoa (D20).

## D24 — Dupla checagem: IA + regras

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo
- **Decisão:** com IA (Ollama ou Claude), a leitura final passa por `ia/extracao/combinacao.py`:
  - se IA e regras discordam sobre "tem" ou "não tem" → INCERTO, confiança baixa (vai para REVISAR), com a nota da divergência;
  - "negado" e "nao_mencionado" contam como a mesma conclusão; se uma diz "negado" com trecho, fica o "negado";
  - trava: "usa metformina" só vale se o trecho citado fala de metformina ou MTF.
  Desligável com `--sem-dupla-checagem`.
- **Motivo (Base 2, 100 pacientes):** erros perigosos 11 (só IA) e 19 (só regras) → **3** (combinado).
- **Custo:** 46 de 100 pacientes vão para REVISAR.
- **Alternativa descartada:** só IA (mais erros perigosos) ou só regras (14 erros perigosos em metformina).

## D25 — A Base 2 é a prova, não material de ajuste

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo
- **Decisão:** `dados/pacientes_ficticios_PAC201-300.xlsx` (100 pacientes, gerada no Claude chat) serve só para **medir**. O prompt e as regras não são ajustados olhando para ela. Melhorias futuras usam outra base de estudo.
- **Motivo:** se ajustarmos pela prova, o número deixa de valer. Exemplo: as regras não pegam "oncologia"; isso fica anotado para corrigir junto com uma base nova.
- **Impacto:** `docs/RESULTADOS_EXTRACAO.md` é a fonte dos números para a apresentação.

## D26 — Pasta `entregas/` e demo no computador do Mateus

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo
- **Decisão:**
  - `entregas/` guarda o que o Paulo entrega ao Mateus: as extrações prontas e a planilha de saída. O Mateus não precisa rodar a IA para trabalhar.
  - A demo de 04/12 roda no computador do Mateus, **com Ollama instalado**, para ler textos ao vivo. O cache (`--offline`) é o plano B.
- **Impacto:** testar a demo completa no computador do Mateus na S6 (21–27/11), 3 vezes seguidas. Guia em `docs/GUIA_INSTALACAO.md`.

## D27 — Ficha numérica lida do texto, por regras

- **Data:** 16/10/2026 · **Quem decidiu:** Claude Code (Paulo delegou)
- **Decisão:** a extração também lê do texto idade, sexo, HbA1c, creatinina, glicemia de jejum e IMC (`ia/extracao/estruturados.py`), cada um com o trecho literal. Vai no campo `dados_lidos` do `extracoes.json`. Quem faz é **regex, não a IA**.
- **Motivo:** no AGHUx só existe o texto; a ficha completa precisa vir dele. Números seguem padrões fixos: regras leem com precisão, na hora e de graça, sem rodar a IA de novo.
- **Resultado:** Base 1, 100%. Prova, medido às cegas: **0 números errados**, mas sexo e glicemia ficavam em branco em ~30% (formas como "Pcte F", "Sra.", "glic jejum", "A1c"). Depois de incluir essas formas (ajuste feito **olhando a prova**, então não é medida às cegas): 0 errados, e só ficam em branco os valores que de fato não estão no texto.
- **Impacto:** o contrato **ganha** o campo `dados_lidos`; nada do que existia muda. O Mateus pode usar os números lidos ou os da planilha.

## D28 — Espaço de avaliação e escolha de modelo por PC

- **Data:** 16/10/2026 · **Quem decidiu:** Paulo
- **Decisão:**
  - `python -m ia.verificar_pc` analisa RAM e placa de vídeo e recomenda o modelo (8 GB de VRAM ou mais → `qwen2.5:7b`);
  - `python -m ia.extracao.experimento` compara modelos nas mesmas bases e guarda cada medição em `avaliacao/historico.csv`;
  - `avaliacao/estudo/` é o lugar para melhorar prompt e regras, com o prompt pronto para gerar a base de estudo no Claude chat.
- **Motivo:** o PC do Mateus deve aguentar um modelo maior; precisamos comparar com números guardados, sem misturar prova e estudo (D25).

## D29 — Demo por comando e correção da trava de metformina

- **Data:** 16/10/2026 · **Quem decidiu:** Claude Code (Paulo delegou)
- **Decisão:**
  - `python -m ia.demo` mostra texto → ficha estruturada → motivo da revisão. Com `--texto`, a IA lê ao vivo; se o Ollama estiver fechado, cai para as regras e avisa.
  - A trava da D24 passou a aceitar qualquer palavra que começa com "metf" (pega erros como "metformia"). Antes só aceitava "metformina" exata e mandava para revisão casos certos.
- **Transparência:** o defeito da trava foi visto ao olhar a prova. Os números da prova não mudaram com a correção.

---

## Pendentes

- **Dono da camada de regras:** o Mateus ainda não entendeu o que ela é. Explicar antes da reunião de contrato.
- **Rótulos:** são só a regra (fórmula) ou têm julgamento clínico? (ponto crítico 6.4)
- **A planilha entra no repositório** (em `dados/`)?
- **Provedor de LLM e orçamento.**
