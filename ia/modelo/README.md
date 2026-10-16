# ia/modelo — camada 2: Random Forest (ordenar a lista)

**Dono:** Mateus Basílio · **Decisão:** D8 · **Fase do playbook:** 4

**Recebe:** as features dos pacientes (saída de `ia/dados`) e o rótulo.
**Entrega:** `probabilidade_elegibilidade` por paciente, usada **só para ordenar** dentro de cada resultado. **Nunca muda a decisão das regras.**

**Dados:** 300 pacientes (Base 1 + Base 2). Ler o ponto crítico 6.4 do playbook antes de treinar: o rótulo da Base 1 é a própria fórmula das regras, então o RF tende a só copiá-la. Medir a distribuição das probabilidades e, se ficar tudo em 0 e 1, considerar o score de "margem até o limite".
