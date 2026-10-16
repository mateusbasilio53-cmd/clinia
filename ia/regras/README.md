# ia/regras — camada 1: a decisão (elegível / não elegível / revisar)

**Dono:** Mateus Basílio · **Decisões:** D6, D7, D15 · **Fase do playbook:** 2

**Recebe:** um paciente (saída de `ia/dados`) e um protocolo (colunas da D6, com `hba1c_min` e `imc_min` da D15).

**Entrega:** `ELEGÍVEL` / `NÃO ELEGÍVEL` / `REVISAR` + lista de critérios atendidos + lista de critérios limitantes em português (ex.: "HbA1c 10,8% acima do máximo de 10,5%").

**Regras de ouro:**
- `incerto` ou `confianca = "baixa"` nunca vira ELEGÍVEL automático → REVISAR, com o motivo (`problemas`).
- Coluna do protocolo vazia (NULL) = critério ignorado.
- Tabela sugerida de como tratar cada leitura: `docs/PARA_O_MATEUS.md`, seção 3.

**Protocolo da demo** (aba `Criterios` da planilha original): DM2; idade 30–70; HbA1c 7,0–10,5; metformina em uso; IMC 25–45; creatinina ≤ 1,5; sem neoplasia ativa; sem gestação.
