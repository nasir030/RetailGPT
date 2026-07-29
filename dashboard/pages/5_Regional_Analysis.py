import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.services.data_service import load_data, apply_filters

st.set_page_config(page_title="Regional Analysis", page_icon="🌍", layout="wide")
st.title("🌍 Regional Analysis")

df = load_data()
filters = st.session_state.get("filters", {})
filtered = apply_filters(df, **filters) if filters else df

col1, col2 = st.columns(2)
with col1:
    st.subheader("Sales by Region")
    region = filtered.groupby("Region")["Sales"].sum().sort_values(ascending=False).reset_index()
    st.plotly_chart(px.bar(region, x="Region", y="Sales"), use_container_width=True)

with col2:
    st.subheader("Profit by Region")
    region_p = filtered.groupby("Region")["Profit"].sum().sort_values(ascending=False).reset_index()
    st.plotly_chart(px.bar(region_p, x="Region", y="Profit"), use_container_width=True)

st.subheader("Top States by Sales")
state = filtered.groupby("State")["Sales"].sum().sort_values(ascending=False).head(15).reset_index()
st.plotly_chart(px.bar(state, x="Sales", y="State", orientation="h"), use_container_width=True)

st.subheader("Top Cities by Sales")
city = filtered.groupby("City")["Sales"].sum().sort_values(ascending=False).head(15).reset_index()
st.plotly_chart(px.bar(city, x="Sales", y="City", orientation="h"), use_container_width=True)

st.subheader("US Sales Map (by State)")
state_full = filtered.groupby("State")["Sales"].sum().reset_index()
fig_map = px.choropleth(
    state_full, locations="State", locationmode="USA-states", color="Sales",
    scope="usa", color_continuous_scale="Blues", title="Sales by State"
)
st.plotly_chart(fig_map, use_container_width=True)
