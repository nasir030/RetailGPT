import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.services.data_service import load_data, apply_filters

st.set_page_config(page_title="Profit Analysis", page_icon="📈", layout="wide")
st.title("📈 Profit Analysis")

df = load_data()
filters = st.session_state.get("filters", {})
filtered = apply_filters(df, **filters) if filters else df

col1, col2 = st.columns(2)
with col1:
    st.subheader("Monthly Profit Trend")
    trend = filtered.groupby("Year-Month")["Profit"].sum().reset_index()
    st.plotly_chart(px.line(trend, x="Year-Month", y="Profit", markers=True), use_container_width=True)

with col2:
    st.subheader("Profit Margin by Category")
    cat = filtered.groupby("Category").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum")).reset_index()
    cat["Margin %"] = cat["Profit"] / cat["Sales"] * 100
    st.plotly_chart(px.bar(cat, x="Category", y="Margin %"), use_container_width=True)

st.subheader("High vs Low Margin Products")
prod = filtered.groupby("Product Name").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum")).reset_index()
prod["Margin %"] = prod["Profit"] / prod["Sales"] * 100
top_margin = prod.sort_values("Margin %", ascending=False).head(10)
bottom_margin = prod.sort_values("Margin %").head(10)

c1, c2 = st.columns(2)
c1.write("**Highest Margin Products**")
c1.dataframe(top_margin, use_container_width=True)
c2.write("**Lowest Margin Products (biggest losses)**")
c2.dataframe(bottom_margin, use_container_width=True)

st.subheader("Discount vs Profit Relationship")
fig = px.scatter(filtered, x="Discount", y="Profit", color="Category", opacity=0.5)
st.plotly_chart(fig, use_container_width=True)
st.caption(
    f"Correlation between discount and profit: **{filtered['Discount'].corr(filtered['Profit']):.3f}** "
    "(negative means higher discounts tend to shrink profit)."
)
