# ia/modelo — camada 2: Random Forest (ordenar a lista)

**Dono:** Mateus Basílio · **Decisão:** D8 · **Fase do playbook:** 4

**Recebe:** as features dos pacientes (saída de `ia/dados`) e o rótulo.
**Entrega:** `probabilidade_elegibilidade` por paciente, usada **só para ordenar** dentro de cada resultado. **Nunca muda a decisão das regras.**

**Dados:** 300 pacientes (Base 1 + Base 2). Ler o ponto crítico 6.4 do playbook antes de treinar: o rótulo da Base 1 é a própria fórmula das regras, então o RF tende a só copiá-la. Medir a distribuição das probabilidades e, se ficar tudo em 0 e 1, considerar o score de "margem até o limite".

## Como a lista é ordenada (10/11/2026)

A análise mostrou que o rótulo concorda 99,3% com a regra: dentro de ELEGÍVEL e de NÃO ELEGÍVEL todo mundo tem o mesmo rótulo, então o RF não tem o que aprender ali.

| Grupo | Ordenado por | Por quê |
|---|---|---|
| ELEGÍVEL | **margem até o limite** (`margem.py`), maior primeiro | mais "folgado" no topo; explicável |
| REVISAR | **probabilidade do RF**, maior primeiro | único grupo em que o rótulo varia |
| NÃO ELEGÍVEL | **margem até o limite**, maior primeiro | "quase elegível" no topo |

Margem = menor folga normalizada entre os critérios numéricos (`min(v - mín, máx - v) / (máx - mín)`). Positiva = dentro de todas as faixas; negativa = fora de alguma. A coluna `criterio_ordem` diz qual dos dois foi usado.

Número não lido do texto fica vazio (NaN) com a coluna `<nome>_ausente`, em vez do antigo `-1`.

O número principal do relatório é **treina Base 1 → testa Base 2**. A validação cruzada misturando as duas bases fica só como referência (é otimista porque a Base 1 é gerada por template).

## Como rodar

```powershell
py -m ia.modelo.random_forest      # validação cruzada + distribuição das probabilidades
py -m pytest tests/test_modelo.py
```

Código: `random_forest.py`. Usa as peças oficiais (`ia.dados.juntar`, `ia.regras.criterios.aplicar`, `ia.dados.rotulos`), então treina sobre a mesma decisão da planilha final. Substitui o `experimentos/treino_basico.py`, que tinha uma cópia própria das regras (sem o critério de diagnóstico).

`[A VALIDAR]` Números exploratórios até a equipe da Bárbara validar a amostra da Base 2 (ponto 6.4). Não vão para slide.
