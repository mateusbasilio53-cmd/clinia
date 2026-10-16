# Base de estudo — para melhorar a IA

Esta pasta é onde vocês podem **olhar os erros e ajustar** o prompt (`prompts/extrator_vN.md`) e as regras (`ia/extracao/provedores.py`, `ia/extracao/estruturados.py`). A prova (`dados/pacientes_ficticios_PAC201-300.xlsx`) fica intocada.

## Como criar a base de estudo

1. Abra o Claude chat (claude.ai) e cole o prompt abaixo.
2. Salve o arquivo gerado aqui como **`base_estudo.xlsx`**.
3. Rode `python -m ia.entrada.validar --planilha avaliacao/estudo/base_estudo.xlsx` (checa formato e sinais de dado real).
4. Meça: `python -m ia.extracao.experimento --modelos qwen2.5:3b --conjunto estudo`.

## Ciclo de melhoria

```
olhar erros na base de estudo → mudar prompt (nova versão) ou regra → medir na estudo
        → ficou melhor? → medir UMA vez na prova → registrar em avaliacao/README.md
```

Mudou o texto do prompt? Crie `extrator_v3.md` (não edite o v2): o cache e o histórico são separados por versão.

## Prompt para gerar a base (cole no Claude chat)

```text
Preciso de uma planilha Excel (.xlsx) com 100 pacientes FICTÍCIOS para treinar um sistema de triagem de pesquisa clínica em diabetes tipo 2. Nada de dados reais: sem nomes, CPF, telefone ou endereço.

Colunas (nesta ordem):
id_paciente (PAC-301 a PAC-400), idade, sexo (M/F), diagnostico, hba1c, creatinina, glicemia_jejum, imc, medicamentos, neoplasia_ativa, gestacao, anotacao_medica, gab_neoplasia, gab_gestacao, gab_metformina

Regras para a coluna anotacao_medica (a mais importante):
- Texto corrido como um médico brasileiro escreve no prontuário, de 2 a 6 frases, com estilos bem diferentes entre pacientes (formal, telegráfico, com abreviações, com erros de digitação). Use estilos e frases DIFERENTES de uma base anterior que tinha frases como "Acompanhou com a oncologia no passado" e "Veio acompanhada do filho".
- Os valores de idade, sexo, HbA1c, creatinina, glicemia, IMC e medicamentos devem aparecer no texto e bater com as colunas. Em uns 15% dos pacientes, deixe algum desses valores fora do texto.
- NÃO escreva frases que citem protocolo, critério, faixa ou limite de inclusão.
- Distribua estes casos difíceis (pelo menos 6 de cada):
  negação explícita com palavras variadas ("nega", "sem", "afastado", "descartado", "negativo");
  neoplasia em remissão vs. em tratamento atual (QT, RT, hormonioterapia, cirurgia recente);
  histórico de neoplasia ou acompanhamento oncológico sem dizer se está ativa;
  suspeita de gestação aguardando exame; histórico obstétrico (G2P1A1) sem gestação atual; gestação confirmada;
  metformina suspensa, trocada, prescrita e não iniciada, ou uso irregular;
  abreviações e siglas variadas e erros de digitação em nomes de remédio;
  doença de familiar, que não é do paciente;
  outros antidiabéticos sem metformina (sitagliptina, empagliflozina, gliclazida, insulina);
  texto que não fala de neoplasia, gestação ou metformina.

Colunas de gabarito (o que um leitor humano concluiria SÓ lendo o texto):
gab_neoplasia, gab_gestacao, gab_metformina, cada uma com exatamente um destes valores:
afirmado, negado, nao_mencionado, incerto
("incerto" = suspeita, aguardando exame, ou não dá para saber se é atual).

As colunas neoplasia_ativa e gestacao ficam Sim/Não, coerentes com o texto (Não quando o texto não fala).
Gere o arquivo para download. Ao final, mostre uma tabela com quantos casos de cada tipo difícil você incluiu.
```
