# Avaliação — onde medimos a CLINIA

Aqui ficam as bases de teste, o histórico de cada medição e o espaço para melhorar a IA sem "colar na prova".

## As bases e para que serve cada uma

| Conjunto | Arquivo | Pacientes | Para quê | Pode ajustar prompt/regras olhando para ela? |
|---|---|---|---|---|
| `prova` | `dados/pacientes_ficticios_PAC201-300.xlsx` | 100 | **Medir.** Texto variado, gabarito exato | ❌ **Não** (D25). É o número oficial |
| `casos` | `prompts/casos_teste_v1.json` | 15 | Casos difíceis escritos à mão | ⚠️ Já foi usada para criar o prompt v2 |
| `base1` | `dados/Base_ficticia_DM2_CLINIA.xlsx` | 200 | Checar que nada quebrou (é fácil) | ✅ Sim |
| `estudo` | `avaliacao/estudo/base_estudo.xlsx` | — | **Melhorar** prompt e regras | ✅ Sim. É para isso que ela existe |

> **Por que separar prova de estudo?** Se você ajusta o prompt olhando os erros da prova, a nota sobe mas não quer dizer nada: é como estudar com o gabarito da prova. A base de estudo serve para treinar; a prova, só para medir.

A base de estudo ainda não existe. Para criar: [estudo/README.md](estudo/README.md).

## Como medir

```powershell
# qual modelo o seu PC aguenta
python -m ia.verificar_pc

# um ou mais modelos na prova (resultado vai para o histórico)
python -m ia.extracao.experimento --modelos qwen2.5:3b,qwen2.5:7b --conjunto prova

# nos casos difíceis, com outro prompt
python -m ia.extracao.experimento --modelos qwen2.5:7b --conjunto casos --prompt prompts/extrator_v2.md

# sem a dupla checagem (só a IA), para ver o quanto ela ajuda
python -m ia.extracao.experimento --modelos qwen2.5:7b --conjunto prova --sem-dupla-checagem
```

Rodar de novo o mesmo modelo + prompt + texto **não repete o trabalho**: vem do cache.

## O que fica guardado

| Onde | O quê |
|---|---|
| `avaliacao/historico.csv` | Uma linha por medição: data, conjunto, modelo, prompt, acerto por campo, erros perigosos, pacientes para REVISAR, tempo. Abre no Excel (separador `;`) |
| `avaliacao/resultados/*.json` | Detalhe de cada medição, inclusive cada erro |

## Como ler os números

| Coluna | Significado | Queremos |
|---|---|---|
| `acerto_<campo>` | % de pacientes em que a leitura bate com o gabarito | alto |
| `erros_perigosos` | leituras que podem deixar elegível quem deveria sair (ex.: texto fala de câncer e a leitura diz "não mencionado") | **zero** |
| `pacientes_revisar` | quantos vão para revisão humana | baixo, mas **nunca às custas de erro perigoso** |
| `s_por_paciente` | segundos por paciente (`cache` = não chamou a IA) | baixo |

**Ordem de importância:** erros perigosos > acerto > pacientes para revisar > tempo.

## Roteiro sugerido de testes (PC do Mateus)

1. `python -m ia.verificar_pc` → baixe o modelo recomendado.
2. Prova com o 3b (deve dar o mesmo do PC do Paulo, vindo do cache) e com o recomendado:
   `python -m ia.extracao.experimento --modelos qwen2.5:3b,qwen2.5:7b --conjunto prova`
3. Repita com `--sem-dupla-checagem` para ver se o modelo maior precisa menos das regras.
4. Anote no fim deste arquivo o que concluiu (data, modelo escolhido, por quê).

## Conclusões registradas

| Data | Conclusão |
|---|---|
| 16/10/2026 | `qwen2.5:3b` + dupla checagem na prova: 91% / 92% / 80%, 3 erros perigosos, 46 pacientes para REVISAR (PC do Paulo, ~5 s/paciente) |
