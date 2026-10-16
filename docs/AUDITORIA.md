# CLINIA — Auditoria inicial (Fase 0)

> **Data:** 16/10/2026
> **Responsável:** Paulo (com apoio do Claude Code)
> **Fonte de verdade:** `CLINIA_MVP_PLAYBOOK.md` e `CLINIA_DIVISAO_TAREFAS.md`. Os docx/pdf/txt das pastas de histórico são materiais antigos.
> **Rótulos:** `[FATO]` verificado nos arquivos · `[SUGESTÃO]` proposta, ainda não decidida · `[A VALIDAR]` depende de alguém da equipe

---

## 1. O que existe

| Onde | O quê |
|---|---|
| `OneDrive\Documents\CLINIA\` (sem git) | Playbook, divisão de tarefas, `Base_ficticia_DM2_CLINIA.xlsx`, pastas 01–06 (história, problema, solução, validações, branding, pitch) |
| Este repositório (remote `mateusbasilio53-cmd/clinia`) | Só `README.md` até esta auditoria. Branches `main`, `develop` e `feature/estrutura-inicial` apontando para o mesmo commit |
| Histórico do git | `clinia_dados_pandas.ipynb` (Mateus, Colab, 15/09), apagado em 16/10. Padroniza diagnóstico, medicamentos e Sim/Não e salva um CSV tratado. Recuperável com `git show 6e52d73:clinia_dados_pandas.ipynb` |

## 2. O que ainda não existe

`[FATO]` Não encontrados em nenhuma das duas pastas:

- código Node/Express, CRUD;
- `docker-compose`, Postgres, tabela `protocolo`, seed SQL (a D3 diz que o docker-compose "já existe": `[A VALIDAR]` onde está);
- pastas `ia/`, `contratos/`, `prompts/`;
- `requirements.txt`, `.env.example`;
- Python instalado na máquina do Paulo (só o atalho da Microsoft Store).

## 3. A planilha de pacientes fictícios

**Arquivo:** `Base_ficticia_DM2_CLINIA.xlsx` (pasta do OneDrive). Dados fictícios feitos pela equipe da Bárbara para construir e testar o pipeline e para o aprendizado da equipe, já que dados reais não podem ser usados.

### 3.1 Abas

- **Base_Pacientes:** 200 linhas, 200 ids únicos (`PAC-001` a `PAC-200`), 17 colunas.
- **Criterios:** protocolo do estudo simulado *"Controle Glicêmico em Pacientes com DM2"* (terapia adjuvante à Metformina).
- **Resumo:** contagens por grupo e por motivo, com gráfico.

### 3.2 Colunas de `Base_Pacientes`

| Coluna | Conteúdo observado |
|---|---|
| `id_paciente` | `PAC-001` … `PAC-200` |
| `idade` | 21 a 82 |
| `sexo` | M (104) / F (96) |
| `diagnostico` | 5 grafias: "DM tipo II", "Diabetes mellitus tipo 2", "Diabetes tipo 2", "Diabetes mellitus tipo II", "DM2" |
| `diagnostico_secundario` | comorbidades (HAS, dislipidemia, esteatose…) |
| `hba1c` | 5,9 a 12,6 |
| `creatinina` | 0,65 a 2,35 |
| `glicemia_jejum` | 137 a 214 |
| `imc` | 21,1 a 51,7 |
| `medicamentos` | texto livre curto; 197 com Metformina, 3 sem |
| `neoplasia_ativa` | Sim (8) / Não (192) |
| `gestacao` | Sim (8, todas F) / Não (192) |
| `data_atendimento` | data serial do Excel |
| `anotacao_medica` | texto livre, 321–482 caracteres, nenhum vazio |
| `grupo_simulacao` | Elegível (100) / Não elegível (70) / Limítrofe (30) |
| `marcador_caso` | motivo do caso (ex.: "HbA1c acima da faixa") |
| `elegibilidade_calculada` | **fórmula do Excel** com as regras do protocolo → Elegível (115) / Não elegível (85) |

Os 30 limítrofes se dividem em 15 logo dentro e 15 logo fora dos critérios.

### 3.3 Critérios do protocolo (aba `Criterios`)

| Critério | Regra |
|---|---|
| Diagnóstico | DM2 confirmado |
| Idade | 30 a 70 anos, inclusive |
| HbA1c | 7,0% a 10,5%, inclusive |
| Metformina | em uso |
| IMC | 25 a 45 kg/m², inclusive |
| Creatinina | excluir se > 1,5 mg/dL |
| Neoplasia ativa | excluir se Sim |
| Gestação | excluir se Sim |

`[FATO]` Nenhum sinal de dado real: ids pseudônimos, sem nomes nem CPF.

## 4. Diferenças em relação ao Contrato de Dados (playbook, seção 7)

1. **Rótulo.** Não existe `elegivel_rotulo`. O rótulo disponível é `elegibilidade_calculada`, que é a própria fórmula das regras. Além disso, o nome coincide com a saída da Camada 1 (D7).
2. **Formato do id.** `PAC-001` (3 dígitos), não `PAC-0001`.
3. **Colunas não previstas no contrato:** `diagnostico_secundario`, `medicamentos`, `neoplasia_ativa`, `gestacao`, `data_atendimento`, `grupo_simulacao`, `marcador_caso`.
4. **Tabela `protocolo` (D6).** O protocolo usa faixas, então faltam `hba1c_min` e `imc_min`. `glicemia_jejum_max` não é critério deste protocolo.
5. **Contagem.** O playbook diz "85 não elegíveis, dos quais 30 limítrofes". Na planilha, os 30 limítrofes se dividem 15/15 entre os dois lados.

## 5. Limites da base para o que queremos medir

A base cumpre bem o objetivo de construir e testar o pipeline. Os pontos abaixo são limites do que ela consegue **provar**, não defeitos:

1. **O RF vai reaprender as regras.** Como o rótulo é a fórmula, a tendência é que as probabilidades fiquem concentradas em 0 e 1 (ponto crítico 6.4).
2. **O texto repete o estruturado.** Todos os valores de HbA1c, creatinina e IMC do texto batem com as colunas. Neoplasia, gestação e medicamentos também já estão em colunas.
3. **O texto entrega o motivo.** 81 anotações têm frases como "HbA1c acima da faixa definida para inclusão" ou "Caso construído próximo a um ponto de corte do protocolo". Isso infla métricas da LLM.
4. **Faltam casos difíceis.** Não há negações ("nega neoplasia", "sem Ca"), suspeitas, medicação suspensa ou abreviações além de DM2. Neoplasia e gestação só aparecem no texto quando são "Sim".
5. `[A VALIDAR]` Há gestantes de 54, 61 e 63 anos, o que a equipe clínica pode questionar.

## 6. Riscos para o prazo de 04/12

| Risco | Mitigação proposta |
|---|---|
| Python não instalado | Instalar Python 3.12 antes da Fase 1 |
| Métricas infladas pela base (seção 5) | `[SUGESTÃO]` 15 anotações difíceis num arquivo separado (S2); deixar claro na apresentação o que foi medido com quê |
| LLM sem papel real, já que as colunas existem | `[SUGESTÃO]` Esconder `neoplasia_ativa`, `gestacao` e `medicamentos` do pipeline; a LLM extrai do texto e as colunas viram gabarito automático da extração |
| D6 sem `hba1c_min` / `imc_min` | `[SUGESTÃO]` Incluir as duas colunas |
| Duas cópias dos .md (OneDrive e repositório) | `[SUGESTÃO]` Repositório como fonte oficial a partir desta auditoria |
| Fluxo de git (repositório usa `develop`/`feature/*`; a divisão manda `main` + `nome/tarefa`) | `[A VALIDAR]` Escolher um e ajustar o outro |

## 7. Perguntas abertas antes da Fase 1

1. MVP só em Python (D1, D3, D4 adiados)? Regras com o Mateus?
2. Onde está o docker-compose citado na D3 (ou ele deixa de importar)?
3. Os rótulos são só a regra ou têm julgamento clínico?
4. A planilha entra no repositório (em `dados/`)?
5. Qual provedor de LLM e qual orçamento de API?
6. Aprovar as sugestões da seção 6 (esconder colunas, `hba1c_min`/`imc_min`, casos difíceis).
