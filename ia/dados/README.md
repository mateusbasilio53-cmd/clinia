# ia/dados — juntar a planilha com a leitura da CLINIA

**Dono:** Mateus Basílio · **Fase do playbook:** 2

**Recebe:**
- a planilha (`dados/*.xlsx`), lida com `ia.entrada.planilha.ler_planilha`;
- o `extracoes.json` do Paulo (`entregas/extracoes_base*.json`), formato em `contratos/extracao.schema.json`.

**Entrega:** um DataFrame por paciente, pronto para as regras, com:
- números: de `dados_lidos` (lidos do texto) ou das colunas da planilha;
- critérios do texto: `campos.neoplasia_ativa`, `campos.gestacao`, `campos.uso_metformina` (status, evidência, confiança, problemas).

**Atenção (D14):** as colunas `neoplasia_ativa`, `gestacao` e `medicamentos` da planilha são **gabarito**. Não entram na decisão.

Exemplo de junção: `docs/PARA_O_MATEUS.md`, seção 2.
