import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.services.data_service import load_data, apply_filters

st.set_page_config(page_title="Product Analysis", page_icon="📦", layout="wide")
st.title("📦 Product Analysis")

df = load_data()
filters = st.session_state.get("filters", {})
filtered = apply_filters(df, **filters) if filters else df

top_n = st.slider("Show top N products", 5, 30, 10)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Best Selling Products (by Sales)")
    best = filtered.groupby("Product Name")["Sales"].sum().sort_values(ascending=False).head(top_n).reset_index()
    st.plotly_chart(px.bar(best, x="Sales", y="Product Name", orientation="h"), use_container_width=True)

with col2:
    st.subheader("Worst Selling Products (by Sales)")
    worst = filtered.groupby("Product Name")["Sales"].sum().sort_values().head(top_n).reset_index()
    st.plotly_chart(px.bar(worst, x="Sales", y="Product Name", orientation="h"), use_container_width=True)

st.subheader("Most Profitable Products")
profitable = filtered.groupby("Product Name")["Profit"].sum().sort_values(ascending=False).head(top_n).reset_index()
st.plotly_chart(px.bar(profitable, x="Profit", y="Product Name", orientation="h"), use_container_width=True)

st.subheader("Category Performance")
cat_perf = filtered.groupby("Category").agg(
    Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique")
).reset_index()
cat_perf["Margin %"] = (cat_perf["Profit"] / cat_perf["Sales"] * 100).round(2)
st.dataframe(cat_perf, use_container_width=True)
