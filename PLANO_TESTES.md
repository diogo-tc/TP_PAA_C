# Plano de testes - Mochila 0-1 com duas restricoes

Este roteiro foi pensado para comparar programacao dinamica, backtracking com poda e branch-and-bound variando:

- quantidade de itens `n`
- peso maximo suportado `W`
- volume maximo suportado `V`

O experimento deve gerar 10 instancias aleatorias para cada combinacao `n x W x V`, rodar os tres algoritmos e salvar os tempos no CSV.

## Ideia geral

A programacao dinamica tende a crescer principalmente com `n * W * V`.

O backtracking e o branch-and-bound tendem a crescer principalmente com `n`, mas a capacidade da mochila tambem influencia a poda. Quando a mochila e muito restrita, muitos ramos sao cortados cedo. Quando a mochila e mais permissiva, ha mais combinacoes viaveis e a busca pode demorar mais.

Por isso, use tres blocos de testes:

1. Instancias pequenas, para validar que tudo funciona.
2. Instancias medias, para comecar a enxergar diferencas.
3. Instancias grandes/controladas, para evidenciar o crescimento assintotico sem deixar tudo inviavel.

## Bloco 1 - Validacao pequena

Objetivo: conferir se todos os algoritmos rodam rapido e retornam o mesmo lucro.

```bash
./build/run_experiments --n 8,10,12 --w 20,40 --v 20,40 --reps 10 --out results/bloco1_validacao.csv
```

Combinacoes: `3 x 2 x 2 = 12`

Execucoes: `12 x 10 x 3 = 360`

Resultado esperado: todos devem rodar muito rapido.

## Bloco 2 - Crescimento por quantidade de itens

Objetivo: mostrar o impacto de aumentar `n` mantendo `W` e `V` moderados.

```bash
./build/run_experiments --n 15,20,25,30,35,40 --w 80 --v 80 --reps 10 --out results/bloco2_itens.csv
```

Combinacoes: `6 x 1 x 1 = 6`

Execucoes: `6 x 10 x 3 = 180`

Resultado esperado:

- DP deve crescer de forma relativamente controlada.
- Backtracking deve piorar bastante conforme `n` aumenta.
- Branch-and-bound deve ficar entre os dois ou muito melhor que backtracking quando a poda funcionar bem.

## Bloco 3 - Crescimento por peso e volume

Objetivo: evidenciar que a programacao dinamica depende fortemente de `W * V`.

```bash
./build/run_experiments --n 25 --w 40,80,160,320 --v 40,80,160,320 --reps 10 --out results/bloco3_capacidades.csv
```

Combinacoes: `1 x 4 x 4 = 16`

Execucoes: `16 x 10 x 3 = 480`

Resultado esperado:

- DP deve ficar mais lenta quando `W` e `V` aumentam.
- Backtracking e branch-and-bound podem variar, mas nao crescem diretamente por tabela `W * V`.
- Este bloco ajuda muito nos graficos de tempo por capacidade.

## Bloco 4 - Instancias medias comparativas

Objetivo: combinar crescimento de `n`, `W` e `V` em um conjunto bom para o relatorio.

```bash
./build/run_experiments --n 20,30,40 --w 80,160,320 --v 80,160,320 --reps 10 --out results/bloco4_comparativo.csv
```

Combinacoes: `3 x 3 x 3 = 27`

Execucoes: `27 x 10 x 3 = 810`

Resultado esperado: deve produzir graficos ricos e mostrar diferencas claras entre os algoritmos.

## Bloco 5 - Estresse controlado

Objetivo: buscar instancias que mostrem diferencas grandes, mas sem necessariamente passar de uma hora.

Rode primeiro:

```bash
./build/run_experiments --n 45,50 --w 200,400 --v 200,400 --reps 10 --out results/bloco5_estresse_a.csv
```

Se ainda estiver rapido, rode:

```bash
./build/run_experiments --n 55,60 --w 300,600 --v 300,600 --reps 10 --out results/bloco5_estresse_b.csv
```

Se ficar muito demorado, pare e use apenas o bloco `5A`.

## Bloco 6 - DP grande, busca moderada

Objetivo: forcar a programacao dinamica pelo aumento de capacidade, sem aumentar demais `n`.

```bash
./build/run_experiments --n 20,25 --w 500,1000 --v 500,1000 --reps 10 --out results/bloco6_dp_grande.csv
```

Resultado esperado:

- DP deve sentir bastante o aumento de `W` e `V`.
- Backtracking e branch-and-bound podem nao piorar tanto quanto a DP neste caso.

## Ordem recomendada de execucao

1. Rode o bloco 1.
2. Rode o bloco 2.
3. Rode o bloco 3.
4. Rode o bloco 4.
5. Rode o bloco 5A.
6. Rode o bloco 5B apenas se o tempo ainda estiver aceitavel.
7. Rode o bloco 6 se quiser destacar o custo da DP com capacidades grandes.

## Comando para analisar cada CSV

Depois de gerar um CSV:

```bash
python3 scripts/analyze_results.py results/bloco1_validacao.csv --out-dir results/analysis_bloco1
```

Repita trocando o nome do CSV e o diretorio de saida.

## Sugestao para o relatorio

Use pelo menos estes arquivos no relatorio:

- `bloco2_itens.csv`: mostra crescimento com `n`
- `bloco3_capacidades.csv`: mostra crescimento com `W` e `V`
- `bloco4_comparativo.csv`: mostra comparacao geral
- `bloco5_estresse_a.csv`: mostra diferencas em instancias maiores

Se algum bloco passar de uma hora, registre isso como evidência experimental de inviabilidade para aquela faixa e use os resultados parciais anteriores.
