# CLINIA — Resultados da extração do texto livre

> **Data:** 16/10/2026 · **Responsável:** Paulo (entrada + LLM)
> **Regra:** número que vai para slide só sai daqui (seção 5.1 da divisão de tarefas).
> **Planilha completa:** `entregas/CLINIA_saida_extracao.xlsx`

---

## 1. O que foi medido

A CLINIA lê a anotação médica (texto corrido) e responde três perguntas sobre cada paciente, sempre com o **trecho do texto** que justifica a resposta:

| Campo | Pergunta | Por que importa no estudo DM2 |
|---|---|---|
| neoplasia_ativa | Tem câncer ativo? | Critério de exclusão |
| gestacao | Está gestante agora? | Critério de exclusão |
| uso_metformina | Usa metformina atualmente? | Critério de inclusão |

Cada resposta é uma de quatro: **SIM**, **NÃO**, **não mencionado** ou **INCERTO** (vai para revisão humana).

**Como a CLINIA lê (configuração final):**
1. Uma **IA local e gratuita** (`qwen2.5:3b`, via Ollama) lê o texto, sem internet e sem os dados saírem do computador.
2. Um **leitor por regras** (regex) lê o mesmo texto, de forma independente.
3. **Dupla checagem:** se os dois discordam sobre "tem" ou "não tem", a CLINIA **não decide** e manda para REVISAR.
4. **Travas do código:** todo trecho citado é conferido no texto original; se a IA "inventar" um trecho, o caso vai para REVISAR.

## 2. Bases de teste (todas fictícias)

| Base | Pacientes | Como é o texto | Gabarito |
|---|---|---|---|
| **Base 1** — planilha original | 200 | Frases-modelo repetidas, quase sem negação | Colunas Sim/Não da planilha |
| **Base 2** — PAC-201 a 300 | 100 | **Variado:** estilos diferentes, abreviações (MTF, Cr, GJ), erros de digitação, negações, familiares, histórico vs. atual | Status exato por campo, gerado junto com a base (Claude chat) |
| Casos de teste | 15 | Casos difíceis escritos à mão | Status exato |

> **A Base 2 é a prova.** O prompt e as regras não foram ajustados olhando para ela. É o número mais honesto que temos.

## 3. Resultados

### Base 2 (100 pacientes, texto variado), o número principal

| Campo | Só IA | Só regras | **CLINIA (IA + regras)** |
|---|---|---|---|
| neoplasia: acertos | 78% | 92% | **91%** |
| neoplasia: erros perigosos | 6 | 5 | **2** |
| gestação: acertos | 88% | 98% | **92%** |
| gestação: erros perigosos | 0 | 0 | **0** |
| metformina: acertos | 85% | 81% | **80%** |
| metformina: erros perigosos | 5 | 14 | **1** |
| **erros perigosos (total)** | **11** | **19** | **3** |
| pacientes que vão para REVISAR | — | — | **46 de 100** |

**Erro perigoso** = a CLINIA poderia deixar como elegível alguém que deveria sair ou ser revisado (ex.: o texto fala de câncer e a leitura diz "não mencionado").

### Ficha numérica lida do texto (D27)

| Dado | Base 1 (200) | Prova (100) | Em branco na prova |
|---|---|---|---|
| idade | 100% | 99% | 1 (não está no texto) |
| sexo | 100% | 100% | 0 |
| HbA1c | 100% | 98% | 2 (não estão no texto) |
| creatinina | 100% | 95% | 5 (não estão no texto) |
| glicemia de jejum | 100% | 98% | 2 (não estão no texto) |
| IMC | 100% | 97% | 3 (não estão no texto) |

**Nenhum número lido errado** nas duas bases. Quando o valor não está no texto, fica em branco, sem chute.
**Transparência:** a primeira medição na prova (às cegas) também teve 0 erros, mas deixou em branco ~30% de sexo e glicemia, por abreviações como "Pcte F" e "glic jejum". Essas formas foram incluídas depois de olhar a prova; por isso, os números acima não são medida às cegas.

### Base 1 (200 pacientes, texto de modelo pronto)

100% nos três campos, 0 erros perigosos, 1 paciente para REVISAR (a IA reescreveu um trecho e o código percebeu).
**Atenção:** esse 100% não deve ir para slide sozinho, porque a base é fácil demais (até as regras simples acertam 100%).

### Casos de teste (15)

41 de 45 campos certos (91%); os 4 erros vão todos para o lado seguro (INCERTO ou NÃO onde o resultado não muda).

### Tempo

| | Tempo | Por paciente |
|---|---|---|
| 200 pacientes (Base 1) | 16 min | ~4,8 s |
| 100 pacientes (Base 2) | 8 min | ~4,9 s |

Notebook com RTX 3050 de 4 GB, sem internet, custo zero.

## 4. Frases para a apresentação (todas verdadeiras)

- "A CLINIA leu 300 prontuários fictícios em menos de meia hora, num notebook comum, sem internet e sem custo."
- "Na base com texto variado, a dupla checagem reduziu os erros perigosos de 11 para 3 em 300 leituras."
- "Quando a IA e as regras discordam, a CLINIA não decide: chama o humano. A decisão final é sempre do coordenador."
- "Toda resposta vem com o trecho do prontuário. Se a IA cita um trecho que não existe, o sistema percebe."

**Não dizer:** "100% de acerto" (só na base fácil) ou qualquer número que não esteja nesta página.

## 5. Limites honestos

1. **Dados fictícios.** Nenhum número aqui vale para prontuário real do AGHUx.
2. **O gabarito da Base 2 foi feito por IA** (Claude chat), não por profissional de saúde. Alguns são discutíveis (ex.: "MTC 850mg" marcado como incerto). `[A VALIDAR]` revisão por amostragem pela equipe da Bárbara.
3. **46% vão para REVISAR.** É o preço de quase não errar para o lado perigoso. Ainda assim, o coordenador revisa 46 em vez de ler 100.
4. **IA pequena (3B).** Sozinha, perde para as regras em neoplasia e gestação. O valor está na combinação.
5. **Os 3 erros perigosos que sobraram:** "Acompanhou com a oncologia no passado; não sabe se ainda tem retorno marcado" (2 pacientes; nem a IA nem as regras pegaram) e "Consta prescrição de MTF; paciente confuso quanto ao uso" (gabarito discutível).

## 6. Próximos passos

| Melhoria | Esperado | Cuidado |
|---|---|---|
| Regras: incluir "oncologia" | Pegaria os 2 erros de neoplasia | Fazer junto com uma base nova de estudo, não ajustando pela Base 2 |
| Prompt v3 com exemplos de negação e de G1P1 | Menos REVISAR | Exemplos vêm de base nova, nunca da Base 2 |
| Modelo maior (7–8B) | Menos erros da IA | Mais lento na placa de 4 GB |
| ~~Extração completa (idade, HbA1c, IMC... também do texto)~~ | ✅ feita (D27) | — |
| Revisão do gabarito pela equipe da Bárbara | Número confiável para a banca | Depende da disponibilidade deles |
