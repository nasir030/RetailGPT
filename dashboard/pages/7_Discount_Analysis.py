import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.services.data_service import load_data, apply_filters

st.set_page_config(page_title="Discount Analysis", page_icon="🏷️", layout="wide")
st.title("🏷️ Discount Analysis")

df = load_data()
filters = st.session_state.get("filters", {})
filtered = apply_filters(df, **filters) if filters else df

filtered = filtered.copy()
bins = [-0.01, 0, 0.1, 0.2, 0.3, 0.5, 1.0]
labels = ["0%", "1-10%", "11-20%", "21-30%", "31-50%", "51-100%"]
filtered["Discount Band"] = pd.cut(filtered["Discount"], bins=bins, labels=labels)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Average Profit by Discount Band")
    band = filtered.groupby("Discount Band", observed=True)["Profit"].mean().reset_index()
    st.plotly_chart(px.bar(band, x="Discount Band", y="Profit"), use_container_width=True)

with col2:
    st.subheader("Order Volume by Discount Band")
    band_count = filtered.groupby("Discount Band", observed=True)["Order ID"].nunique().reset_index(name="Orders")
    st.plotly_chart(px.bar(band_count, x="Discount Band", y="Orders"), use_container_width=True)

st.subheader("Discount Impact by Category")
cat_disc = filtered.groupby(["Category", "Discount Band"], observed=True)["Profit"].mean().reset_index()
fig = px.bar(cat_disc, x="Discount Band", y="Profit", color="Category", barmode="group")
st.plotly_chart(fig, use_container_width=True)

st.warning(
    "Tip: look for discount bands where average profit turns negative — that's where "
    "discounting policy is actively losing money on the sale."
)
