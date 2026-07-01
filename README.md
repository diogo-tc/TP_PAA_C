# Trabalho PAA - Mochila 0-1 com duas restricoes

Implementacao em C++ para comparar tres algoritmos para a mochila 0-1 sem repeticao com restricoes de peso e volume:

- Programacao dinamica
- Backtracking com poda
- Branch-and-bound

## Compilacao no WSL

```bash
cd /mnt/c/docsw/PAA/Trabalho_PAA_C
make
```

Para limpar arquivos gerados:

```bash
make clean
```

## Formato da instancia

A primeira linha contem a capacidade de peso `W` e volume `V`. As linhas seguintes contem `peso volume valor`.

```txt
10 9
6 3 10
3 4 14
4 2 16
2 5 9
```

## Executaveis

```bash
./build/mochila_dp exemplo.txt
./build/mochila_bt exemplo.txt
./build/mochila_bb exemplo.txt
```

Saida:

```txt
Algoritmo: Programacao Dinamica
Lucro maximo: 30
Itens escolhidos: 2 3
Tempo: 0.000023777 segundos
```

Os itens sao exibidos com indice iniciando em 1.

## Interface simples

Depois de compilar, voce pode abrir um menu no terminal:

```bash
./build/menu
```

Se voce alterar o codigo ou receber uma versao nova do projeto, recompile antes:

```bash
make
```

Opcoes disponiveis:

- Gerar uma instancia informando quantidade de itens, peso maximo, volume maximo e limites dos itens
- Rodar um algoritmo especifico:
  - Algoritmo 1: programacao dinamica
  - Algoritmo 2: backtracking com poda
  - Algoritmo 3: branch-and-bound
- Rodar os tres algoritmos sobre a mesma instancia
- Rodar os experimentos e gerar o CSV com 10 instancias aleatorias por combinacao

A interface apenas chama os executaveis existentes. Ela nao altera o formato do CSV.

## Gerador de instancias

```bash
./build/gerador_instancias instances/teste.txt 50 100 100 42
```

Parametros:

```txt
./build/gerador_instancias <saida.txt> <n> <W> <V> [seed] [peso_item_max] [volume_item_max] [valor_max]
```

## Experimentos com CSV

```bash
./build/run_experiments --n 10,20,30 --w 50,100 --v 50,100 --reps 10 --out results/resultados.csv
```

Teste minimo para verificar se o CSV esta sendo criado:

```bash
make
./build/run_experiments --n 5 --w 20 --v 20 --reps 1 --out results/teste.csv
ls -l results
cat results/teste.csv
```

Quando `--seed` nao e informado, as instancias sao geradas aleatoriamente. O menu usa esse modo por padrao e sempre gera 10 instancias para cada combinacao de `n`, `W` e `V`. A seed e usada apenas internamente e nao aparece no CSV.

O CSV gerado contem:

```txt
n,W,V,rep,instance,algorithm,profit,chosen_items,time_seconds,time_unit,status
```

Cada execucao de algoritmo tem limite de 2 horas. Se ultrapassar esse tempo, o processo e interrompido, a coluna `status` recebe `timeout`, e o runner continua para o proximo algoritmo ou instancia.

## Analise estatistica, graficos e dashboard

Instale as dependencias Python no WSL:

```bash
python3 -m pip install -r requirements.txt
```

Analise completa para um ou mais CSVs:

```bash
python3 scripts/full_analysis.py Teste_100a500.csv 500itens_1milhaoPW.csv --out-dir analysis_output
```

Saidas principais:

- `analysis_output/dashboard.html`: dashboard estatico com tabelas e graficos
- `analysis_output/tables/summary_by_combination.csv`: media, mediana, desvio padrao, minimo e maximo por combinacao
- `analysis_output/tables/summary_global.csv`: resumo geral por algoritmo
- `analysis_output/tables/mean_time_ratios.csv`: razoes de tempo entre algoritmos
- `analysis_output/tables/fastest_by_combination.csv`: algoritmo mais rapido por combinacao
- `analysis_output/tables/profit_consistency.csv`: verificacao se os algoritmos chegaram ao mesmo lucro
- `analysis_output/tables/statistical_tests.csv`: testes Friedman e Wilcoxon
- `analysis_output/plots/*.png`: graficos em escala logaritmica

As tabelas geradas pela analise usam cabecalhos em portugues do Brasil, como `tempo_medio`, `tempo_mediano`, `desvio_padrao_tempo`, `algoritmo_mais_rapido` e `valor_p`.

Tambem e possivel analisar todos os CSVs de um diretorio:

```bash
python3 scripts/full_analysis.py . --out-dir analysis_output
```

## Observacao sobre branch-and-bound

O branch-and-bound sempre retorna uma solucao 0-1. A estimativa fracionaria e usada apenas como limite superior para poda, isto e, para descartar ramos que nao conseguem superar a melhor solucao inteira encontrada.
