# ia/regras — Pandas, parte 2: aplicar os critérios do estudo (elegível / não elegível / revisar)

**Dono:** Mateus Basílio · **Decisões:** D6, D7, D15 · **Fase do playbook:** 2

**Recebe:** um paciente (saída de `ia/dados`) e um protocolo (colunas da D6, com `hba1c_min` e `imc_min` da D15).

**Entrega:** `ELEGÍVEL` / `NÃO ELEGÍVEL` / `REVISAR` + lista de critérios atendidos + lista de critérios limitantes em português (ex.: "HbA1c 10,8% acima do máximo de 10,5%").

**Regras de ouro:**
- `incerto` ou `confianca = "baixa"` nunca vira ELEGÍVEL automático → REVISAR, com o motivo (`problemas`).
- Coluna do protocolo vazia (NULL) = critério ignorado.
- Tabela sugerida de como tratar cada leitura: `docs/PARA_O_MATEUS.md`, seção 3.

**Protocolo da demo** (aba `Criterios` da planilha original): DM2; idade 30–70; HbA1c 7,0–10,5; metformina em uso; IMC 25–45; creatinina ≤ 1,5; sem neoplasia ativa; sem gestação.

## Como rodar

```powershell
python -m ia.regras.criterios --planilha dados/pacientes_ficticios_PAC201-300.xlsx --extracoes entregas/extracoes_base2.json
python -m pytest tests/test_regras.py
```

Código: `protocolo.py` (colunas da D6/D15 + protocolo da demo) e `criterios.py` (decisão). A tabela vem de `ia/dados/juntar.py`.

## Decisões do Mateus (18/10/2026) — levar para o `docs/DECISOES.md` com o Paulo

- **Excluído por número + campo em dúvida → NÃO ELEGÍVEL.** O número já exclui com certeza; a dúvida não muda o resultado. Os dois motivos aparecem em `criterios_limitantes` (o da dúvida com o prefixo "também a revisar:").
- **Diagnóstico escrito de forma não reconhecida → REVISAR**, nunca NÃO ELEGÍVEL. A planilha escreve DM2 de 5 jeitos ("DM tipo II", "Diabetes mellitus tipo 2"…); a lista está em `SINONIMOS_DIAGNOSTICO`.
- **Rótulo da Base 2 (opção C):** provisório = regras sobre os números da planilha + colunas `gab_*` (`ia/dados/rotulos.py`): 12 Elegível, 77 Não elegível, 11 Indefinido. A equipe da Bárbara valida uma amostra **às cegas** de 40 casos: `py -m ia.saida.amostra_validacao` gera `avaliacao/validacao_clinica/amostra_base2_para_equipe_clinica.xlsx` (mandar) e `chave_amostra.csv` (não mandar: são as nossas respostas).

## Pendente `[A VALIDAR]` com o Paulo / equipe da Bárbara

- **Gestação "não mencionada" depende do sexo e da idade?** Proposta do Mateus: homem ou mulher fora da idade fértil → atende; mulher de ~15 a 50 anos → REVISAR (o silêncio do prontuário é uma lacuna real). **Ainda não está no código**: hoje "não mencionado" atende para todos.
