# ia/saida — a planilha final ranqueada

**Dono:** Mateus Basílio · **Seção do playbook:** 7.3

**Entrega:** `planilha_resultado.xlsx` com: posição, id, resultado (ELEGÍVEL / NÃO ELEGÍVEL / REVISAR), probabilidade, critérios atendidos, critérios limitantes, **evidências do texto**, **motivo do REVISAR**, e a frase "A decisão final é sempre humana".

Na versão de avaliação, incluir `rotulo_esperado` e `acertou`.

Referência de formato e de como mostrar evidências: `entregas/CLINIA_saida_extracao.xlsx` (gerada por `ia/extracao/relatorio.py`).

## Como rodar

```powershell
py -m ia.saida.planilha --planilha dados/pacientes_ficticios_PAC201-300.xlsx --extracoes entregas/extracoes_base2.json
# sai em saidas/planilha_resultado.xlsx (use --saida para outro caminho)
py -m pytest tests/test_saida.py
```

Código: `planilha.py`. Abas: `lista` (ranqueada, colorida por resultado, com filtro), `resumo`, `criterios`, `como_ler`.
O RF é treinado sem os pacientes da planilha que está sendo gerada. Se a planilha tiver rótulo, saem também `rotulo_esperado` e `acertou`.
