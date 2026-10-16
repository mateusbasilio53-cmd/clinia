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

---

## Pendentes

- **Dono da camada de regras:** o Mateus ainda não entendeu o que ela é. Explicar antes da reunião de contrato.
- **Rótulos:** são só a regra (fórmula) ou têm julgamento clínico? (ponto crítico 6.4)
- **A planilha entra no repositório** (em `dados/`)?
- **Provedor de LLM e orçamento.**
