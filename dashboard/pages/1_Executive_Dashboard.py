import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.services.data_service import load_data, kpi_summary, apply_filters

st.set_page_config(page_title="Executive Dashboard", page_icon="📊", layout="wide")
st.title("📊 Executive Dashboard")

df = load_data()
filters = st.session_state.get("filters", {})
filtered = apply_filters(df, **filters) if filters else df
kpis = kpi_summary(filtered)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${kpis['total_revenue']:,.0f}")
col2.metric("Total Profit", f"${kpis['total_profit']:,.0f}")
col3.metric("Profit Margin", f"{kpis['profit_margin_pct']:.1f}%")
col4.metric("Monthly Growth", f"{kpis['monthly_growth_pct']:.1f}%")

st.divider()

left, right = st.columns(2)
with left:
    monthly = filtered.groupby("Year-Month")["Sales"].sum().reset_index()
    fig = px.line(monthly, x="Year-Month", y="Sales", markers=True, title="Monthly Sales Trend")
    st.plotly_chart(fig, use_container_width=True)

with right:
    cat = filtered.groupby("Category")[["Sales", "Profit"]].sum().reset_index()
    fig2 = px.bar(cat, x="Category", y=["Sales", "Profit"], barmode="group", title="Sales & Profit by Category")
    st.plotly_chart(fig2, use_container_width=True)

left2, right2 = st.columns(2)
with left2:
    region = filtered.groupby("Region")["Sales"].sum().reset_index()
    fig3 = px.pie(region, names="Region", values="Sales", title="Revenue Share by Region", hole=0.4)
    st.plotly_chart(fig3, use_container_width=True)

with right2:
    seg = filtered.groupby("Segment")["Profit"].sum().reset_index()
    fig4 = px.bar(seg, x="Segment", y="Profit", title="Profit by Customer Segment")
    st.plotly_chart(fig4, use_container_width=True)
