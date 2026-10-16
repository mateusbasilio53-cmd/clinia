# Para o Mateus — o que está pronto e como usar

> **De:** Paulo · **Data:** 16/10/2026
> **Resumo:** a parte de entrada e de IA está pronta e testada. Você **não precisa rodar a IA de novo**: os resultados estão em `entregas/`. Se quiser conferir, tudo roda em segundos a partir do cache.

---

## 1. O que usar (pasta `entregas/`)

| Arquivo | O que é |
|---|---|
| `extracoes_base1.json` | O que a CLINIA leu do texto dos 200 pacientes da planilha original |
| `extracoes_base2.json` | O mesmo para os 100 pacientes da base nova (PAC-201 a 300, texto variado) |
| `extracoes_casos_teste.json` | Os 15 casos difíceis |
| `CLINIA_saida_extracao.xlsx` | Tudo em planilha: dados + leitura + gabarito + acerto + motivo do REVISAR |

E as planilhas de entrada, em `dados/`:

| Arquivo | Pacientes |
|---|---|
| `dados/Base_ficticia_DM2_CLINIA.xlsx` | PAC-001 a PAC-200 (aba `Base_Pacientes`) |
| `dados/pacientes_ficticios_PAC201-300.xlsx` | PAC-201 a PAC-300 (aba `pacientes`) |

## 2. Como juntar no Pandas

```python
import json
import pandas as pd

from ia.entrada.planilha import ler_planilha

pacientes = ler_planilha("dados/pacientes_ficticios_PAC201-300.xlsx")
extracoes = json.load(open("entregas/extracoes_base2.json", encoding="utf-8"))

lidos = pd.json_normalize(extracoes)  # colunas como campos.neoplasia_ativa.status
base = pacientes.merge(lidos, on="id_paciente", how="left")
```

**Importante (D14):** na sua camada de regras, **não use** as colunas `neoplasia_ativa`, `gestacao` e `medicamentos` da planilha. Elas são o gabarito. Use o que a CLINIA leu (`campos.*`).

**Números (D27):** a CLINIA também lê do texto idade, sexo, HbA1c, creatinina, glicemia e IMC (`dados_lidos.<campo>.valor`, com o trecho em `.evidencia`). Na demo, use esses: é o que mostra a ficha montada **só a partir do texto**. Quando o valor não está no texto, vem `null` → trate como REVISAR no critério correspondente. Os números da planilha servem para conferência.

Formato completo: `contratos/extracao.schema.json`.

## 3. Como tratar cada leitura nas regras (sugestão, decidimos juntos)

| Leitura | `status` | Critério de exclusão (neoplasia, gestação) | Critério de inclusão (metformina) |
|---|---|---|---|
| tem | `afirmado` | NÃO ELEGÍVEL | atende |
| não tem | `negado` | atende | NÃO ELEGÍVEL |
| texto não fala | `nao_mencionado` | **atende** (sugestão: no prontuário, quem não tem câncer normalmente não tem isso escrito) | **REVISAR** (sem prova de uso) |
| dúvida | `incerto` | **REVISAR** | **REVISAR** |
| qualquer um com `confianca = "baixa"` | — | **REVISAR** | **REVISAR** |

Regra de ouro do playbook: **na dúvida, REVISAR. Nunca ELEGÍVEL automático.**

Todo REVISAR deve mostrar o motivo. Ele está em `campos.<campo>.problemas` (ex.: `"leituras divergentes: IA = tem, regras = não tem"`).

## 4. Random Forest

- **Use as duas bases (300 pacientes).** A Base 2 é a que tem variação de verdade.
- Rótulo da Base 1: `elegibilidade_calculada` (é a fórmula das regras; o RF tende a só copiar a regra, ponto 6.4 do playbook).
- A Base 2 **não tem** coluna de elegibilidade. Você pode calcular com as regras ou pedir à equipe da Bárbara.
- Lembre: o RF só **ordena**; nunca muda a decisão das regras (D8).

## 5. Planilha final (seção 7.3 do playbook)

Sugestão de colunas: posição, id, resultado (ELEGÍVEL / NÃO ELEGÍVEL / REVISAR), probabilidade, critérios atendidos, critérios limitantes, **evidências do texto** e **motivo do REVISAR**. A evidência é o que faz o coordenador confiar.

## 6. A IA no seu computador (testar um modelo melhor)

Siga `docs/GUIA_INSTALACAO.md`. Resumo:

```powershell
python -m pytest                    # tem que dar "54 passed"
python -m ia.demo                   # demo (funciona sem Ollama, vem do cache)
python -m ia.verificar_pc           # diz qual modelo seu PC aguenta
ollama pull qwen2.5:7b              # ou o que o verificar_pc recomendar
python -m ia.extracao.experimento --modelos qwen2.5:3b,qwen2.5:7b --conjunto prova
```

O experimento guarda o resultado em `avaliacao/historico.csv`. Regras da avaliação (prova x estudo): `avaliacao/README.md`.

Suas pastas já existem com um README cada (`ia/dados/`, `ia/regras/`, `ia/modelo/`, `ia/saida/`), dizendo o que recebe e o que entrega.

## 7. Resultados

Ver `docs/RESULTADOS_EXTRACAO.md`. Resumo: na base com texto variado, **3 erros perigosos em 300 leituras**, e 46 de 100 pacientes vão para REVISAR.

## 8. O que eu preciso de você

1. OK no formato do `extracoes.json` (é o nosso contrato).
2. A saída do `python -m ia.verificar_pc` e a tabela do `experimento` com o modelo recomendado, para sabermos se a demo ao vivo roda aí e qual modelo usar.
3. Concordar (ou não) com a tabela da seção 3.
