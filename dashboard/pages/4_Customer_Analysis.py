import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.services.data_service import load_data, apply_filters

st.set_page_config(page_title="Customer Analysis", page_icon="👥", layout="wide")
st.title("👥 Customer Analysis")

df = load_data()
filters = st.session_state.get("filters", {})
filtered = apply_filters(df, **filters) if filters else df

col1, col2 = st.columns(2)
with col1:
    st.subheader("Top Customers by Sales")
    top = filtered.groupby("Customer Name")["Sales"].sum().sort_values(ascending=False).head(10).reset_index()
    st.plotly_chart(px.bar(top, x="Sales", y="Customer Name", orientation="h"), use_container_width=True)

with col2:
    st.subheader("Customers by Segment")
    seg = filtered.groupby("Segment")["Customer ID"].nunique().reset_index(name="Customers")
    st.plotly_chart(px.pie(seg, names="Segment", values="Customers", hole=0.4), use_container_width=True)

st.subheader("Customer Segmentation (Order Frequency vs Avg Order Value)")
cust = filtered.groupby("Customer Name").agg(
    orders=("Order ID", "nunique"), avg_order_value=("Sales", "mean"), total_sales=("Sales", "sum")
).reset_index()

# Simple RFM-lite segmentation using quantiles (no ML model needed for this view)
cust["Segment Tier"] = "Standard"
cust.loc[cust["total_sales"] >= cust["total_sales"].quantile(0.9), "Segment Tier"] = "VIP (Top 10%)"
cust.loc[
    (cust["total_sales"] < cust["total_sales"].quantile(0.9)) & (cust["total_sales"] >= cust["total_sales"].quantile(0.5)),
    "Segment Tier",
] = "Loyal"
cust.loc[cust["total_sales"] < cust["total_sales"].quantile(0.5), "Segment Tier"] = "At Risk / New"

fig = px.scatter(
    cust, x="orders", y="avg_order_value", size="total_sales", color="Segment Tier",
    hover_name="Customer Name", title="Customer Segmentation"
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("View segmentation table"):
    st.dataframe(cust.sort_values("total_sales", ascending=False), use_container_width=True)

st.subheader("Repeat Customers")
repeat_rate = (cust["orders"] > 1).mean() * 100
st.metric("Repeat Customer Rate", f"{repeat_rate:.1f}%")
