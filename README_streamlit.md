# Dashboard Streamlit — Indexadores Econômicos

## Como rodar

```bash
pip install streamlit pandas numpy plotly
streamlit run app_indexadores.py
```

O app precisa do arquivo `indexadores_mensal.csv` na mesma pasta que o `app_indexadores.py`.

## O que tem no app

- **Filtros na sidebar**: período e indexadores a exibir
- **4 visualizações**:
  1. Variação mensal (% mês a mês)
  2. Acumulado 12 meses (rolling)
  3. Número índice (base 100 configurável — padrão = início do período)
  4. Tabela completa com download em CSV
- **Cards de resumo** no topo (acumulado e média mensal por indexador)
- **Gráfico comparativo** no rodapé (barras horizontais com acumulado do período)

## Estrutura

```
app_indexadores.py          # código do app
indexadores_mensal.csv      # dados (240 linhas × 7 indexadores)
indexadores_20_anos.xlsx    # mesmo dataset em Excel, com abas e formatação
```
