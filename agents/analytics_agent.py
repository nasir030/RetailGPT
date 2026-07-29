"""
analytics_agent.py
-------------------
The Analytics Agent computes real answers from the dataset using pandas.

This agent NEVER hardcodes answers - every function below actually
aggregates/filters the dataframe you pass in. The chatbot (ollama_service.py)
calls these functions to get grounded facts, then asks the LLM only to
phrase the answer in natural language - the LLM never invents the numbers.
"""

from __future__ import annotations

import pandas as pd


def highest_sales_month(df: pd.DataFrame) -> dict:
    monthly = df.groupby("Year-Month")["Sales"].sum().sort_values(ascending=False)
    top_month = monthly.index[0]
    return {"month": top_month, "sales": round(float(monthly.iloc[0]), 2)}


def most_profitable_product(df: pd.DataFrame, top_n: int = 5) -> list[dict]:
    grouped = (
        df.groupby("Product Name")["Profit"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
    )
    return [{"product": p, "profit": round(float(v), 2)} for p, v in grouped.items()]


def category_sales(df: pd.DataFrame, category: str) -> dict:
    subset = df[df["Category"].str.lower() == category.lower()]
    if subset.empty:
        return {"category": category, "found": False}
    return {
        "category": category,
        "found": True,
        "total_sales": round(float(subset["Sales"].sum()), 2),
        "total_profit": round(float(subset["Profit"].sum()), 2),
        "orders": int(subset["Order ID"].nunique()),
    }


def compare_years(df: pd.DataFrame, year_a: int, year_b: int) -> dict:
    a = df[df["Year"] == year_a]["Sales"].sum()
    b = df[df["Year"] == year_b]["Sales"].sum()
    change_pct = ((b - a) / a * 100) if a else 0
    return {
        "year_a": year_a,
        "year_b": year_b,
        "sales_a": round(float(a), 2),
        "sales_b": round(float(b), 2),
        "change_pct": round(float(change_pct), 2),
    }


def best_region(df: pd.DataFrame) -> dict:
    grouped = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
    return {"region": grouped.index[0], "sales": round(float(grouped.iloc[0]), 2)}


def profit_decline_analysis(df: pd.DataFrame) -> dict:
    """Analyze WHY profit might be down: discount correlation, category drag, region drag."""
    discount_profit_corr = df["Discount"].corr(df["Profit"])

    category_profit = df.groupby("Category")["Profit"].sum().sort_values()
    worst_category = category_profit.index[0]

    region_profit = df.groupby("Region")["Profit"].sum().sort_values()
    worst_region = region_profit.index[0]

    high_discount_profit = df[df["Discount"] > 0.2]["Profit"].mean()
    low_discount_profit = df[df["Discount"] <= 0.2]["Profit"].mean()

    return {
        "discount_profit_correlation": round(float(discount_profit_corr), 3),
        "worst_category": worst_category,
        "worst_category_profit": round(float(category_profit.iloc[0]), 2),
        "worst_region": worst_region,
        "worst_region_profit": round(float(region_profit.iloc[0]), 2),
        "avg_profit_high_discount": round(float(high_discount_profit), 2),
        "avg_profit_low_discount": round(float(low_discount_profit), 2),
    }


def top_customers(df: pd.DataFrame, top_n: int = 5) -> list[dict]:
    grouped = (
        df.groupby("Customer Name")["Sales"].sum().sort_values(ascending=False).head(top_n)
    )
    return [{"customer": c, "sales": round(float(v), 2)} for c, v in grouped.items()]


def lowest_profit_category(df: pd.DataFrame) -> dict:
    grouped = df.groupby("Category")["Profit"].sum().sort_values()
    return {"category": grouped.index[0], "profit": round(float(grouped.iloc[0]), 2)}


def monthly_sales_trend(df: pd.DataFrame) -> list[dict]:
    grouped = df.groupby("Year-Month")["Sales"].sum().sort_index()
    return [{"period": k, "sales": round(float(v), 2)} for k, v in grouped.items()]


def products_to_promote(df: pd.DataFrame, top_n: int = 5) -> list[dict]:
    """High margin + high volume products worth promoting further."""
    grouped = df.groupby("Product Name").agg(
        sales=("Sales", "sum"), profit=("Profit", "sum"), qty=("Quantity", "sum")
    )
    grouped["margin"] = grouped["profit"] / grouped["sales"]
    candidates = grouped[(grouped["margin"] > 0.2)].sort_values("sales", ascending=False).head(top_n)
    return [
        {
            "product": idx,
            "sales": round(float(row["sales"]), 2),
            "margin_pct": round(float(row["margin"]) * 100, 2),
        }
        for idx, row in candidates.iterrows()
    ]


# ---------------------------------------------------------------------------
# Simple intent router (keyword-based fallback; ollama_service.py can
# override this with an LLM-based router when Ollama is available)
# ---------------------------------------------------------------------------
def route_question(question: str, df: pd.DataFrame) -> dict:
    """Very lightweight keyword router so the chatbot works even without an LLM
    for intent detection. Returns {"intent": ..., "data": ...}."""
    q = question.lower()

    if "highest sales" in q or ("month" in q and "sales" in q):
        return {"intent": "highest_sales_month", "data": highest_sales_month(df)}
    if "profit" in q and "decrease" in q or ("why" in q and "profit" in q):
        return {"intent": "profit_decline_analysis", "data": profit_decline_analysis(df)}
    if "most profitable" in q or ("highest profit" in q):
        return {"intent": "most_profitable_product", "data": most_profitable_product(df)}
    if "region" in q and ("best" in q or "perform" in q):
        return {"intent": "best_region", "data": best_region(df)}
    if "top customer" in q or "spend the most" in q:
        return {"intent": "top_customers", "data": top_customers(df)}
    if "lowest profit" in q or "worst category" in q:
        return {"intent": "lowest_profit_category", "data": lowest_profit_category(df)}
    if "trend" in q or "monthly sales" in q:
        return {"intent": "monthly_sales_trend", "data": monthly_sales_trend(df)}
    if "promote" in q:
        return {"intent": "products_to_promote", "data": products_to_promote(df)}
    if "compare" in q and "20" in q:
        import re

        years = re.findall(r"20\d{2}", question)
        if len(years) >= 2:
            return {
                "intent": "compare_years",
                "data": compare_years(df, int(years[0]), int(years[1])),
            }
    for cat in df["Category"].unique():
        if cat.lower() in q:
            return {"intent": "category_sales", "data": category_sales(df, cat)}

    # default: general KPI summary
    from backend.services.data_service import kpi_summary

    return {"intent": "kpi_summary", "data": kpi_summary(df)}


if __name__ == "__main__":
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.services.data_service import load_data

    df = load_data()
    print(highest_sales_month(df))
    print(profit_decline_analysis(df))
    print(route_question("Which month had the highest sales?", df))
    print(route_question("Why did profits decrease?", df))
