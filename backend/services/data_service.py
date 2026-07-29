"""
data_service.py
----------------
Central data access layer for RetailGPT.

Responsibilities:
- Load the raw Superstore CSV
- Clean it (dates, duplicates, nulls, types)
- Feature-engineer business fields (Year, Month, Quarter, Profit Margin, etc.)
- Cache a processed copy to data/processed/
- Provide reusable KPI calculations used by the dashboard, the FastAPI backend,
  and the AI agents (so every part of the app computes numbers the same way).
"""

from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "Sample_-_Superstore.csv")
PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed", "superstore_clean.csv")


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the raw Superstore dataframe and add business features."""
    df = df.copy()

    # Standardize column names (no spaces / dashes -> easier to reference)
    df.columns = [c.strip() for c in df.columns]

    # Parse dates
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="mixed", dayfirst=False)
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="mixed", dayfirst=False)

    # Drop exact duplicate rows
    df = df.drop_duplicates()

    # Handle missing values defensively (this dataset ships clean, but new data may not be)
    numeric_cols = ["Sales", "Quantity", "Discount", "Profit"]
    for col in numeric_cols:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())

    categorical_cols = ["Ship Mode", "Segment", "Region", "Category", "Sub-Category"]
    for col in categorical_cols:
        if df[col].isnull().any():
            df[col] = df[col].fillna("Unknown")

    # Outlier flag (IQR method) on Sales - flagged, not removed (business reality)
    q1, q3 = df["Sales"].quantile([0.25, 0.75])
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr
    df["Is_Sales_Outlier"] = df["Sales"] > upper_bound

    # Feature engineering
    df["Year"] = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.month
    df["Month Name"] = df["Order Date"].dt.strftime("%b")
    df["Quarter"] = df["Order Date"].dt.quarter
    df["Year-Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["Order Processing Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
    df["Profit Margin"] = np.where(df["Sales"] != 0, df["Profit"] / df["Sales"], 0)

    return df


def build_processed_dataset(save: bool = True) -> pd.DataFrame:
    """Load raw CSV, clean it, optionally persist to data/processed/."""
    raw = pd.read_csv(RAW_PATH, encoding="latin1")
    cleaned = clean_data(raw)
    if save:
        os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
        cleaned.to_csv(PROCESSED_PATH, index=False)
    return cleaned


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    """Load the processed dataset, building it from raw data if needed.

    Cached in-process so Streamlit / FastAPI don't reprocess on every call.
    """
    if os.path.exists(PROCESSED_PATH):
        df = pd.read_csv(PROCESSED_PATH, parse_dates=["Order Date", "Ship Date"])
        return df
    return build_processed_dataset(save=True)


# ---------------------------------------------------------------------------
# KPI calculations (shared by dashboard pages, API, and agents)
# ---------------------------------------------------------------------------
def kpi_summary(df: pd.DataFrame) -> dict:
    """Core executive KPIs for a (possibly filtered) dataframe."""
    total_revenue = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["Order ID"].nunique()
    total_customers = df["Customer ID"].nunique()
    avg_order_value = total_revenue / total_orders if total_orders else 0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0

    monthly = df.groupby("Year-Month")["Sales"].sum().sort_index()
    monthly_growth = (
        ((monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2] * 100)
        if len(monthly) >= 2 and monthly.iloc[-2] != 0
        else 0
    )

    best_product = (
        df.groupby("Product Name")["Sales"].sum().idxmax() if not df.empty else None
    )
    best_region = (
        df.groupby("Region")["Sales"].sum().idxmax() if not df.empty else None
    )

    return {
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "total_orders": int(total_orders),
        "total_customers": int(total_customers),
        "avg_order_value": round(avg_order_value, 2),
        "profit_margin_pct": round(profit_margin, 2),
        "monthly_growth_pct": round(monthly_growth, 2),
        "best_selling_product": best_product,
        "best_performing_region": best_region,
    }


def apply_filters(
    df: pd.DataFrame,
    region: str | None = None,
    category: str | None = None,
    segment: str | None = None,
    year: int | None = None,
) -> pd.DataFrame:
    """Apply optional sidebar-style filters. None / 'All' means no filter."""
    out = df
    if region and region != "All":
        out = out[out["Region"] == region]
    if category and category != "All":
        out = out[out["Category"] == category]
    if segment and segment != "All":
        out = out[out["Segment"] == segment]
    if year and year != "All":
        out = out[out["Year"] == int(year)]
    return out


if __name__ == "__main__":
    data = build_processed_dataset(save=True)
    print(f"Processed dataset: {data.shape[0]} rows, {data.shape[1]} columns")
    print(f"Saved to: {PROCESSED_PATH}")
    print(kpi_summary(data))
