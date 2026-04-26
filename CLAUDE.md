# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

A Python 3.9 venv already exists at `.venv/` with `streamlit`, `pandas`, `numpy`, and `plotly` installed.

```bash
# Run the dashboard (headless avoids Streamlit's first-run email prompt)
source .venv/bin/activate
streamlit run app_indexadores.py --server.headless=true
```

Default URL: `http://localhost:8501`. The app reads `indexadores_mensal.csv` from the working directory — it must be run from the repo root.

There are no tests, linters, or build steps configured.

## Architecture

Single-file Streamlit app ([app_indexadores.py](app_indexadores.py)) over a monthly time-series CSV. The whole pipeline is: load CSV → filter by period/selection from sidebar → compute derived series → render one of three views + a summary section.

### Data contract

[indexadores_mensal.csv](indexadores_mensal.csv) is the single source of truth. 240 rows (monthly, 2006-04 onward), indexed by `Data`, with 7 columns: `CUB_SC`, `INCC`, `IGPM`, `IPCA`, `INPC`, `SELIC`, `USD`. **Values are monthly percent changes (e.g. `0.36` = +0.36%), not index levels.** Every aggregation in the code assumes this — don't pass raw values to plotting without dividing by 100 first.

[indexadores_20_anos.xlsx](indexadores_20_anos.xlsx) is a presentation copy of the same data; the app does not read it.

The `COLS`, `NICE` (display labels), and `CORES` (brand colors per indexador) dicts at the top of the app are the canonical mapping — adding or renaming an indexador means updating all three plus the CSV schema.

### Compounding convention

Monthly returns are compounded multiplicatively throughout. The recurring idiom is:

```python
((1 + s/100).prod() - 1) * 100     # accumulated % over a window
(1 + s/100).rolling(12).apply(np.prod, raw=True)   # 12-month rolling
df.resample("YE").apply(lambda x: ((1 + x/100).prod() - 1) * 100)  # yearly variation
```

`variacao_anual()` uses `"YE"` (year-end) resampling, so partial years are included and labeled by their end year. Changes that touch aggregation must preserve this multiplicative composition — simple sums will silently produce wrong numbers.

### View modes

The sidebar radio switches between three mutually exclusive views, all driven off `df_f` (period-filtered) and `df_anual` (yearly-compounded):

1. **Variação anual** — grouped bar chart of yearly % + a stats table (mean, median, best/worst year, stdev, period accumulation).
2. **Acumulado ao longo dos anos** — base-100 cumulative line chart. Base point is inserted as `ano_ini - 1 = 100` so the first real year shows the first year's growth.
3. **Tabela anual** — yearly variation and cumulative side-by-side, with CSV download of `df_anual`.

Below the view, there's always a summary-cards block and a horizontal bar chart of total period accumulation (shared across all views).

### Formatting

Numbers are rendered in pt-BR format via `fmt_br()` (comma decimal) and `fmt_moeda_br()` (R$ with thousands separator). Don't use Python's default formatting when writing to the UI — users expect Brazilian conventions.

### Caching

`load_data()` is wrapped in `@st.cache_data`. If you modify the CSV during development, use Streamlit's "Rerun" (hamburger menu → Clear cache) or restart the process.
