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

**Importante (D14):** na sua camada de regras, **não use** as colunas `neoplasia_ativa`, `gestacao` e `medicamentos` da planilha. Elas são o gabarito. Use o que a CLINIA leu (`campos.*`). Os números (idade, HbA1c, creatinina, IMC) vêm da planilha normalmente.

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

## 6. Se quiser rodar a extração você mesmo

Siga `docs/GUIA_INSTALACAO.md`. Resumo:

```powershell
python -m pytest                                   # tem que dar "41 passed"
python -m ia.extracao.extrator --provedor ollama --offline --planilha dados/pacientes_ficticios_PAC201-300.xlsx
```

Sem o Ollama, o `--offline` funciona para os 300 pacientes (usa o cache). Com o Ollama, roda também para textos novos.

## 7. Resultados

Ver `docs/RESULTADOS_EXTRACAO.md`. Resumo: na base com texto variado, **3 erros perigosos em 300 leituras**, e 46 de 100 pacientes vão para REVISAR.

## 8. O que eu preciso de você

1. OK no formato do `extracoes.json` (é o nosso contrato).
2. O resultado do passo 0 do guia (configuração do seu computador), para sabermos se a demo ao vivo roda aí.
3. Concordar (ou não) com a tabela da seção 3.
