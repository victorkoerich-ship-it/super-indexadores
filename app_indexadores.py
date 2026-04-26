"""
Dashboard Streamlit — Indexadores Econômicos (20 anos)
Execução: streamlit run app.py

Requer: streamlit, pandas, numpy, plotly (pip install streamlit pandas numpy plotly)
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import json
import time
import uuid
import os

# ==== CONFIG ====
st.set_page_config(
    page_title="Indexadores — 20 anos",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    h1, h2, h3 { letter-spacing: -0.01em; }
    .idx-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 14px;
        margin: 8px 0 4px 0;
    }
    .idx-card {
        border-radius: 14px;
        padding: 16px 18px;
        background: #ffffff;
        border: 1px solid #ececec;
        border-left: 6px solid var(--accent, #1F4E78);
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .idx-card .idx-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #6c757d;
        font-weight: 600;
    }
    .idx-card .idx-value {
        font-size: 26px;
        font-weight: 700;
        color: #111;
        margin-top: 6px;
        line-height: 1.1;
    }
    .idx-card .idx-sub {
        font-size: 12px;
        color: #495057;
        margin-top: 6px;
    }
    .idx-card .idx-sub b { color: #111; }
    .rank-pill {
        display:inline-block; padding:2px 8px; border-radius:999px;
        font-size:11px; font-weight:600; color:#fff; margin-left:6px;
    }
    .rank-top { background:#198754; }
    .rank-low { background:#6c757d; }
    </style>
    """,
    unsafe_allow_html=True,
)

COLS = ["CUB_SC", "INCC", "IGPM", "IPCA", "INPC", "SELIC", "USD"]
NICE = {
    "CUB_SC": "CUB-SC",
    "INCC":   "INCC-M",
    "IGPM":   "IGP-M",
    "IPCA":   "IPCA",
    "INPC":   "INPC",
    "SELIC":  "SELIC",
    "USD":    "Dólar (PTAX)",
}
CORES = {
    "CUB_SC": "#1F4E78",
    "INCC":   "#2E75B6",
    "IGPM":   "#70AD47",
    "IPCA":   "#C00000",
    "INPC":   "#ED7D31",
    "SELIC":  "#7030A0",
    "USD":    "#595959",
}

DEBUG_LOG_PATH = Path(
    os.environ.get(
        "DEBUG_LOG_PATH",
        str(Path(__file__).resolve().parent / ".cursor" / "debug-1e7101.log"),
    )
)
DEBUG_SESSION_ID = "1e7101"
DEBUG_RUN_ID = "pre-fix"

# ==== DATA LOAD ====
@st.cache_data
def load_data():
    df = pd.read_csv("indexadores_mensal.csv", index_col=0, parse_dates=True)
    df.index.name = "Data"
    return df

def acum_12m(s):
    return ((1 + s/100).rolling(12).apply(np.prod, raw=True) - 1) * 100

def variacao_anual(df):
    # Composição mensal -> variação do ano (%). Anos parciais incluídos.
    return df.resample("YE").apply(lambda x: ((1 + x/100).prod() - 1) * 100)

def fmt_br(v, casas=2, sinal=False):
    if pd.isna(v):
        return "—"
    s = f"{v:+.{casas}f}" if sinal else f"{v:.{casas}f}"
    return s.replace(".", ",")

def fmt_moeda_br(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def debug_log(hypothesis_id, location, message, data):
    payload = {
        "sessionId": DEBUG_SESSION_ID,
        "runId": DEBUG_RUN_ID,
        "hypothesisId": hypothesis_id,
        "id": f"log_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}",
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        # Never break app rendering due to debug instrumentation.
        pass

def num_indice(df, base_date=None):
    if base_date is None:
        return (1 + df/100).cumprod() * 100 / (1 + df.iloc[0]/100) * (1 + df.iloc[0]/100)
    # Base em base_date -> 100
    return (1 + df.loc[base_date:]/100).cumprod() * 100

df = load_data()
# region agent log
debug_log(
    "H1",
    "app_indexadores.py:145",
    "Loaded dataframe from CSV",
    {"rows": int(df.shape[0]), "cols": int(df.shape[1]), "columns": list(df.columns)},
)
# endregion

# ==== SIDEBAR ====
st.sidebar.title("⚙️ Filtros")

data_min = df.index.min().date()
data_max = df.index.max().date()

periodo = st.sidebar.date_input(
    "Período",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max,
    format="DD/MM/YYYY",
)

if isinstance(periodo, tuple) and len(periodo) == 2:
    d_ini, d_fim = periodo
else:
    d_ini, d_fim = data_min, data_max

selecionados = st.sidebar.multiselect(
    "Indexadores",
    options=COLS,
    default=COLS,
    format_func=lambda x: NICE[x],
)

visualizacao = st.sidebar.radio(
    "Visualização",
    ["Variação anual", "Acumulado ao longo dos anos", "Tabela anual"],
)
# region agent log
debug_log(
    "H2",
    "app_indexadores.py:180",
    "Sidebar selections captured",
    {
        "d_ini": str(d_ini),
        "d_fim": str(d_fim),
        "selecionados_count": len(selecionados),
        "visualizacao": visualizacao,
    },
)
# endregion

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Fontes**  \n"
    "• CUB-SC: Sinduscon-SC  \n"
    "• IPCA/INPC: IBGE  \n"
    "• IGP-M/INCC-M: FGV  \n"
    "• SELIC/Dólar: Bacen"
)

# ==== MAIN ====
st.title("📊 Indexadores Econômicos — 20 anos")
st.caption(f"Série de {df.index.min():%m/%Y} a {df.index.max():%m/%Y} (mensal, por mês de competência)")

if not selecionados:
    st.warning("Selecione ao menos um indexador na barra lateral.")
    st.stop()

# Filtrar período
mask = (df.index >= pd.Timestamp(d_ini)) & (df.index <= pd.Timestamp(d_fim))
df_f = df.loc[mask, selecionados].copy()
df_anual = variacao_anual(df_f)
df_anual.index = df_anual.index.year
# region agent log
debug_log(
    "H3",
    "app_indexadores.py:211",
    "Filtered frames built",
    {
        "df_f_rows": int(df_f.shape[0]),
        "df_f_cols": int(df_f.shape[1]),
        "df_anual_rows": int(df_anual.shape[0]),
        "df_anual_cols": int(df_anual.shape[1]),
    },
)
# endregion

# ==== CARDS DE RESUMO ====
st.subheader("📌 Resumo do período selecionado")

resumo = []
for col in selecionados:
    s = df_f[col]
    acum_total = ((1 + s/100).prod() - 1) * 100
    anos = df_anual[col].dropna()
    media_anual = anos.mean() if not anos.empty else np.nan
    ult_ano_val = anos.iloc[-1] if not anos.empty else np.nan
    ult_ano_lbl = anos.index[-1] if not anos.empty else ""
    resumo.append((col, acum_total, media_anual, ult_ano_val, ult_ano_lbl))

ordenado = sorted(resumo, key=lambda x: x[1], reverse=True)
top_key = ordenado[0][0]
low_key = ordenado[-1][0]

cards_html = ['<div class="idx-grid">']
for col, acum_total, media_anual, ult_ano_val, ult_ano_lbl in resumo:
    pill = ""
    if col == top_key and len(resumo) > 1:
        pill = '<span class="rank-pill rank-top">#1</span>'
    elif col == low_key and len(resumo) > 1:
        pill = '<span class="rank-pill rank-low">último</span>'
    ult_txt = (
        f"{fmt_br(ult_ano_val, 2, sinal=True)}%" if not pd.isna(ult_ano_val) else "—"
    )
    cards_html.append(
        f'<div class="idx-card" style="--accent:{CORES[col]}">'
        f'  <div class="idx-label">{NICE[col]}{pill}</div>'
        f'  <div class="idx-value">{fmt_br(acum_total, 2, sinal=True)}%</div>'
        f'  <div class="idx-sub">média anual <b>{fmt_br(media_anual, 2, sinal=True)}%</b></div>'
        f'  <div class="idx-sub">{ult_ano_lbl} <b>{ult_txt}</b></div>'
        f'</div>'
    )
cards_html.append("</div>")
st.markdown("\n".join(cards_html), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==== VISUALIZAÇÕES ====
if visualizacao == "Variação anual":
    # region agent log
    debug_log("H4", "app_indexadores.py:261", "Rendering annual variation view", {})
    # endregion
    df_plot = df_anual.rename(columns=NICE)
    fig = go.Figure()
    for col in selecionados:
        fig.add_trace(go.Bar(
            x=df_anual.index, y=df_anual[col],
            name=NICE[col],
            marker_color=CORES[col],
            hovertemplate="%{x}<br>%{y:.2f}%<extra>"+NICE[col]+"</extra>",
        ))
    fig.update_layout(
        title="Variação Anual (%)",
        xaxis_title="Ano",
        yaxis_title="Variação no ano (%)",
        barmode="group",
        height=520,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_yaxes(ticksuffix="%")
    fig.update_xaxes(type="category")
    st.plotly_chart(fig, use_container_width=True)

    # Estatísticas anuais
    st.subheader("Estatísticas anuais (no período selecionado)")
    est = pd.DataFrame({
        NICE[c]: {
            "Média anual": df_anual[c].mean(),
            "Mediana": df_anual[c].median(),
            "Melhor ano": df_anual[c].max(),
            "Pior ano": df_anual[c].min(),
            "Desvio padrão": df_anual[c].std(),
            "Acum. no período": ((1 + df_f[c]/100).prod() - 1) * 100,
        }
        for c in selecionados
    }).T
    st.dataframe(
        est.style.format(lambda v: f"{fmt_br(v, 2, sinal=True)}%").background_gradient(cmap="RdYlGn_r", axis=0),
        use_container_width=True,
    )

elif visualizacao == "Acumulado ao longo dos anos":
    # region agent log
    debug_log("H4", "app_indexadores.py:306", "Rendering cumulative view", {})
    # endregion
    # Base 100 ao fim do primeiro ano exibido; mostra crescimento cumulativo ano a ano.
    fatores_anuais = 1 + df_anual/100
    # inclui ponto inicial = 100 antes do primeiro ano
    acum = fatores_anuais.cumprod() * 100
    ano_ini = df_anual.index.min()
    acum.loc[ano_ini - 1] = 100
    acum = acum.sort_index()
    # também em % acumulado
    acum_pct = acum - 100

    fig = go.Figure()
    for col in selecionados:
        fig.add_trace(go.Scatter(
            x=acum.index, y=acum[col],
            mode="lines+markers",
            name=NICE[col],
            line=dict(color=CORES[col], width=2.2),
            marker=dict(size=6),
            hovertemplate="%{x}<br>Índice %{y:.2f}<extra>"+NICE[col]+"</extra>",
        ))
    fig.add_hline(y=100, line_dash="dot", line_color="gray", opacity=0.5)
    fig.update_layout(
        title=f"Acumulado ao longo dos anos (base 100 em {ano_ini - 1})",
        xaxis_title="Ano",
        yaxis_title="Índice (base 100)",
        height=520,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(type="category")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Quanto R$ 100,00 viraria?")
    last = acum.iloc[-1]
    html = ['<div class="idx-grid">']
    for col in selecionados:
        html.append(
            f'<div class="idx-card" style="--accent:{CORES[col]}">'
            f'  <div class="idx-label">{NICE[col]}</div>'
            f'  <div class="idx-value">{fmt_moeda_br(last[col])}</div>'
            f'  <div class="idx-sub">acumulado <b>{fmt_br(last[col]-100, 2, sinal=True)}%</b></div>'
            f'</div>'
        )
    html.append("</div>")
    st.markdown("\n".join(html), unsafe_allow_html=True)

else:  # Tabela anual
    # region agent log
    debug_log("H4", "app_indexadores.py:357", "Rendering annual table view", {})
    # endregion
    st.subheader("Tabela anual — variação (%) e acumulado")
    tab = df_anual.rename(columns=NICE).copy()
    acum_tab = ((1 + df_anual/100).cumprod() - 1) * 100
    acum_tab = acum_tab.rename(columns={c: f"{NICE[c]} (acum.)" for c in selecionados})
    tab_final = pd.concat([tab, acum_tab], axis=1)
    # reorder: variação e acumulado lado a lado
    ordem = []
    for c in selecionados:
        ordem.append(NICE[c])
        ordem.append(f"{NICE[c]} (acum.)")
    tab_final = tab_final[ordem]

    st.dataframe(
        tab_final.style.format(lambda v: f"{fmt_br(v, 2, sinal=True)}%").background_gradient(cmap="RdYlGn_r", axis=None),
        use_container_width=True,
        height=520,
    )

    # Download
    csv = df_anual.to_csv(index=True).encode("utf-8")
    st.download_button(
        label="⬇️ Baixar CSV (anual)",
        data=csv,
        file_name=f"indexadores_anual_{d_ini}_{d_fim}.csv",
        mime="text/csv",
    )

# ==== COMPARATIVO EM DESTAQUE ====
st.markdown("---")
st.subheader("🔥 Acumulado no período selecionado")
acum_periodo = pd.Series({
    NICE[c]: ((1 + df_f[c]/100).prod() - 1) * 100
    for c in selecionados
}).sort_values(ascending=True)

nice_to_key = {NICE[k]: k for k in COLS}
cores_bar = [CORES[nice_to_key[nm]] for nm in acum_periodo.index]
fig_bar = go.Figure(go.Bar(
    x=acum_periodo.values,
    y=acum_periodo.index,
    orientation="h",
    marker_color=cores_bar,
    text=[f"{fmt_br(v, 1, sinal=True)}%" for v in acum_periodo.values],
    textposition="outside",
))
fig_bar.update_layout(
    title=f"Acumulado de {d_ini:%b/%Y} a {d_fim:%b/%Y}",
    xaxis_title="Variação acumulada (%)",
    height=max(300, 50*len(selecionados)),
    template="plotly_white",
    showlegend=False,
)
fig_bar.update_xaxes(ticksuffix="%")
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.caption(
    "💡 **Dica:** CUB-SC, IPCA e INPC tipicamente divergem de IGP-M em ciclos onde o câmbio e atacado pressionam os IGPs, "
    "sem se refletir no consumidor final. Para avaliação de contratos imobiliários, o INCC-M e o CUB-SC tendem a refletir "
    "melhor os custos de construção, enquanto o IGP-M captura a pressão cambial/atacadista."
)
