import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.services.data_service import load_data, apply_filters

st.set_page_config(page_title="Sales Analysis", page_icon="💰", layout="wide")
st.title("💰 Sales Analysis")

df = load_data()
filters = st.session_state.get("filters", {})
filtered = apply_filters(df, **filters) if filters else df

st.subheader("Sales Over Time")
granularity = st.radio("Granularity", ["Monthly", "Quarterly", "Yearly"], horizontal=True)
if granularity == "Monthly":
    trend = filtered.groupby("Year-Month")["Sales"].sum().reset_index()
    fig = px.line(trend, x="Year-Month", y="Sales", markers=True)
elif granularity == "Quarterly":
    trend = filtered.groupby(["Year", "Quarter"])["Sales"].sum().reset_index()
    trend["Period"] = trend["Year"].astype(str) + "-Q" + trend["Quarter"].astype(str)
    fig = px.line(trend, x="Period", y="Sales", markers=True)
else:
    trend = filtered.groupby("Year")["Sales"].sum().reset_index()
    fig = px.bar(trend, x="Year", y="Sales")
st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Sales by Ship Mode")
    ship = filtered.groupby("Ship Mode")["Sales"].sum().reset_index()
    st.plotly_chart(px.bar(ship, x="Ship Mode", y="Sales"), use_container_width=True)

with col2:
    st.subheader("Sales by Sub-Category")
    subcat = filtered.groupby("Sub-Category")["Sales"].sum().sort_values(ascending=False).reset_index()
    st.plotly_chart(px.bar(subcat, x="Sub-Category", y="Sales"), use_container_width=True)

st.subheader("Year-over-Year Comparison")
years = sorted(filtered["Year"].unique().tolist())
if len(years) >= 2:
    y1, y2 = st.columns(2)
    year_a = y1.selectbox("Year A", years, index=len(years) - 2)
    year_b = y2.selectbox("Year B", years, index=len(years) - 1)
    sales_a = filtered[filtered["Year"] == year_a]["Sales"].sum()
    sales_b = filtered[filtered["Year"] == year_b]["Sales"].sum()
    change = ((sales_b - sales_a) / sales_a * 100) if sales_a else 0
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Sales {year_a}", f"${sales_a:,.0f}")
    c2.metric(f"Sales {year_b}", f"${sales_b:,.0f}")
    c3.metric("Change", f"{change:.1f}%")
