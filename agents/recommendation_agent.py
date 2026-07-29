"""
recommendation_agent.py
------------------------
Generates business recommendations from real, computed patterns in the data
(not an LLM - these are rule-based so they're deterministic and auditable,
which matters more for business advice than creative phrasing).
"""

from __future__ import annotations

import pandas as pd


def generate_recommendations(df: pd.DataFrame) -> list[str]:
    recs: list[str] = []

    # 1. Discount impact
    high_disc_profit = df[df["Discount"] > 0.2]["Profit"].mean()
    low_disc_profit = df[df["Discount"] <= 0.2]["Profit"].mean()
    if high_disc_profit < 0 <= low_disc_profit:
        recs.append(
            f"Orders with discounts above 20% average a loss of ${abs(high_disc_profit):,.2f} "
            f"per order, while lower discounts average a ${low_disc_profit:,.2f} profit. "
            "Consider capping discounts near 20% on low-margin categories."
        )

    # 2. Low-margin categories
    category_margin = (
        df.groupby("Category").agg(sales=("Sales", "sum"), profit=("Profit", "sum"))
    )
    category_margin["margin_pct"] = category_margin["profit"] / category_margin["sales"] * 100
    worst_cat = category_margin["margin_pct"].idxmin()
    worst_margin = category_margin["margin_pct"].min()
    if worst_margin < 5:
        recs.append(
            f"{worst_cat} has a thin profit margin of {worst_margin:.1f}%. "
            "Review pricing or supplier costs in this category."
        )

    # 3. Best region to double down on
    region_sales = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
    recs.append(
        f"{region_sales.index[0]} generates the most revenue (${region_sales.iloc[0]:,.2f}). "
        "Prioritize marketing spend and inventory allocation there."
    )

    # 4. High-margin products worth promoting
    product_perf = df.groupby("Product Name").agg(sales=("Sales", "sum"), profit=("Profit", "sum"))
    product_perf["margin_pct"] = product_perf["profit"] / product_perf["sales"] * 100
    strong = product_perf[(product_perf["margin_pct"] > 30) & (product_perf["sales"] > product_perf["sales"].median())]
    if not strong.empty:
        top_pick = strong.sort_values("sales", ascending=False).index[0]
        recs.append(
            f"'{top_pick}' combines high sales volume with a strong margin — "
            "a good candidate for featured promotion or bundling."
        )

    # 5. Slow-moving inventory
    qty_by_product = df.groupby("Product Name")["Quantity"].sum().sort_values()
    low_movers = qty_by_product[qty_by_product <= qty_by_product.quantile(0.1)]
    if len(low_movers) > 0:
        recs.append(
            f"{len(low_movers)} products are in the bottom 10% for units sold. "
            "Consider bundling, discounting clearance, or discontinuing slow movers."
        )

    return recs


if __name__ == "__main__":
    import sys, os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.services.data_service import load_data

    for r in generate_recommendations(load_data()):
        print("-", r)
