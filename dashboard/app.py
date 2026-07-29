"""
RetailGPT - main Streamlit entry point.

Run with:
    streamlit run dashboard/app.py

This is the landing page. Use the sidebar to navigate to the other
dashboard pages (Sales, Product, Customer, Regional, Profit, Discount,
AI Assistant).
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.data_service import load_data, kpi_summary, apply_filters

st.set_page_config(page_title="RetailGPT", page_icon="📊", layout="wide")

st.title("📊 RetailGPT — AI-Powered Retail Business Intelligence")
st.caption("Ask questions in plain English. Explore KPIs, trends, and AI-generated insights.")

df = load_data()

# ---------------------------------------------------------------------------
# Global filters (sidebar) - shared across pages via session_state
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")
region = st.sidebar.selectbox("Region", ["All"] + sorted(df["Region"].unique().tolist()))
category = st.sidebar.selectbox("Category", ["All"] + sorted(df["Category"].unique().tolist()))
segment = st.sidebar.selectbox("Segment", ["All"] + sorted(df["Segment"].unique().tolist()))
year = st.sidebar.selectbox("Year", ["All"] + sorted(df["Year"].unique().tolist(), reverse=True))

st.session_state["filters"] = {
    "region": region,
    "category": category,
    "segment": segment,
    "year": year,
}

filtered = apply_filters(df, region=region, category=category, segment=segment, year=year)
st.session_state["filtered_df"] = filtered

kpis = kpi_summary(filtered)

st.subheader("Executive Snapshot")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"${kpis['total_revenue']:,.0f}")
c2.metric("Total Profit", f"${kpis['total_profit']:,.0f}")
c3.metric("Profit Margin", f"{kpis['profit_margin_pct']:.1f}%")
c4.metric("Total Orders", f"{kpis['total_orders']:,}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Total Customers", f"{kpis['total_customers']:,}")
c6.metric("Avg Order Value", f"${kpis['avg_order_value']:,.2f}")
c7.metric("Best Region", kpis["best_performing_region"])
c8.metric("Monthly Growth", f"{kpis['monthly_growth_pct']:.1f}%")

st.info(
    "Use the **pages in the left sidebar** to explore Sales, Product, Customer, Regional, "
    "Profit, and Discount analysis — or open **AI Assistant** to ask questions in plain English."
)

with st.expander("Preview filtered data"):
    st.dataframe(filtered.head(100), use_container_width=True)
