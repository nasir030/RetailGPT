"""
visualization_agent.py
-----------------------
Decides which chart best represents the answer to a given question (intent),
and builds the actual Plotly figure so the dashboard/chatbot can render it
right next to the AI's text answer.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Maps analytics_agent intents -> a chart type name
INTENT_CHART_MAP = {
    "highest_sales_month": "monthly_line",
    "monthly_sales_trend": "monthly_line",
    "most_profitable_product": "product_bar",
    "products_to_promote": "product_bar",
    "best_region": "region_bar",
    "top_customers": "customer_bar",
    "lowest_profit_category": "category_bar",
    "category_sales": "category_bar",
    "profit_decline_analysis": "discount_scatter",
    "compare_years": "year_comparison_bar",
    "kpi_summary": "none",
}


def suggest_chart(intent: str) -> str:
    return INTENT_CHART_MAP.get(intent, "none")


def build_chart(chart_type: str, df: pd.DataFrame):
    """Build and return a Plotly figure object for the given chart type."""
    if chart_type == "monthly_line":
        grouped = df.groupby("Year-Month")["Sales"].sum().reset_index()
        fig = px.line(grouped, x="Year-Month", y="Sales", markers=True, title="Monthly Sales Trend")
        return fig

    if chart_type == "product_bar":
        grouped = df.groupby("Product Name")["Profit"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(grouped, x="Profit", y="Product Name", orientation="h", title="Top 10 Products by Profit")
        return fig

    if chart_type == "region_bar":
        grouped = df.groupby("Region")["Sales"].sum().sort_values(ascending=False).reset_index()
        fig = px.bar(grouped, x="Region", y="Sales", title="Sales by Region")
        return fig

    if chart_type == "customer_bar":
        grouped = df.groupby("Customer Name")["Sales"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(grouped, x="Sales", y="Customer Name", orientation="h", title="Top 10 Customers by Sales")
        return fig

    if chart_type == "category_bar":
        grouped = df.groupby("Category")["Profit"].sum().sort_values().reset_index()
        fig = px.bar(grouped, x="Category", y="Profit", title="Profit by Category")
        return fig

    if chart_type == "discount_scatter":
        fig = px.scatter(
            df, x="Discount", y="Profit", color="Category", opacity=0.5,
            title="Discount vs Profit (why margins shrink)",
        )
        return fig

    if chart_type == "year_comparison_bar":
        grouped = df.groupby("Year")["Sales"].sum().reset_index()
        fig = px.bar(grouped, x="Year", y="Sales", title="Sales by Year")
        return fig

    return go.Figure()  # empty figure for "none"
