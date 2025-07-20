"""
Streamlit dashboard - Customer Lifetime Value (CLV) Explorer
-----------------------------------------------------------
• Heatmap de retención por cohorte (datos transaccionales)
• Distribución de CLV a 6 m (tabla de predicciones)
• Filtro de país
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CLV Dashboard", layout="wide")
st.title("Customer Lifetime Value — Cohort Explorer")

# ─── Rutas de datos ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[1] / "data/processed"
TX_FILE   = BASE_DIR / "clv.parquet"               # transacciones limpias
PRED_FILE = BASE_DIR / "clv_predictions.parquet"   # CLV por cliente

tx_df   = pd.read_parquet(TX_FILE)    # transacción-level  (InvoiceDate, Country…)
pred_df = pd.read_parquet(PRED_FILE)  # RFM + clv_6m

# Añadimos Country a pred_df para permitir filtro
pred_df = pred_df.merge(
    tx_df[["Customer ID", "Country"]].drop_duplicates(),
    on="Customer ID",
    how="left",
)

# ─── Sidebar filtros ──────────────────────────────────────────────────────
st.sidebar.header("Filtros")

country_opts = ["Todos"] + sorted(tx_df["Country"].unique())
country_sel = st.sidebar.selectbox("País", country_opts)

if country_sel != "Todos":
    tx_df   = tx_df[tx_df["Country"] == country_sel]
    pred_df = pred_df[pred_df["Country"] == country_sel]

# ─── Heatmap de cohortes ──────────────────────────────────────────────────
st.subheader("Retención por cohorte · Clientes activos")

tx_df["cohort"] = (
    tx_df.groupby("Customer ID")["InvoiceDate"]
         .transform("min")
         .dt.to_period("M")
)
tx_df["period"] = tx_df["InvoiceDate"].dt.to_period("M")

heat = (
    tx_df.groupby(["cohort", "period"])["Customer ID"]
         .nunique()
         .unstack(fill_value=0)
         .sort_index()
)

palettes = {
    "Viridis": "Viridis",
    "Blues": "Blues",
    "TealGrn": "Tealgrn",
    "Hot": "Hot",
    "Cividis": "Cividis",
    "Jet": "Jet",
    "Magma": "Magma",
    "Plasma": "Plasma",
    "Inferno": "Inferno",
    "Rainbow": "Rainbow",
    "Greens": "Greens",
    "Reds": "Reds",
}
palette_sel = st.sidebar.selectbox("Paleta de color", list(palettes.keys()))

fig_heat = px.imshow(
    heat,
    x=heat.columns.astype(str),
    y=heat.index.astype(str),
    labels=dict(x="Mes de compra", y="Cohorte de alta", color="Clientes"),
    color_continuous_scale=palettes[palette_sel],   
    aspect="auto",
)
st.plotly_chart(fig_heat, use_container_width=True)

# ─── Distribución de CLV ──────────────────────────────────────────────────
st.subheader("Distribución CLV (6 meses)")

fig_box = px.box(
    pred_df,
    y="clv_6m",
    points="all",
    labels={"clv_6m": "CLV (6 m)"},
)
st.plotly_chart(fig_box, use_container_width=True)

# ─── Métrica resumen ──────────────────────────────────────────────────────
clv_mean = pred_df["clv_6m"].mean()
st.metric(label="CLV promedio (6 m)", value=f"£{clv_mean:,.2f}")