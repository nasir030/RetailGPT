"""
navigation_agent.py
--------------------
Guides the user to the right dashboard page based on what they ask.
Used by the AI Assistant page to tell the user (and optionally trigger
st.switch_page) where to look for more detail.
"""

from __future__ import annotations

PAGE_MAP = {
    "Executive Dashboard": ["overview", "executive", "summary", "kpi"],
    "Sales Analysis": ["sales", "revenue"],
    "Product Analysis": ["product", "sku", "item"],
    "Customer Analysis": ["customer", "segmentation", "retention", "clv", "lifetime value"],
    "Regional Analysis": ["region", "state", "city", "geographic", "map"],
    "Profit Analysis": ["profit", "margin"],
    "Discount Analysis": ["discount", "promo"],
}

PAGE_FILES = {
    "Executive Dashboard": "dashboard/pages/1_Executive_Dashboard.py",
    "Sales Analysis": "dashboard/pages/2_Sales_Analysis.py",
    "Product Analysis": "dashboard/pages/3_Product_Analysis.py",
    "Customer Analysis": "dashboard/pages/4_Customer_Analysis.py",
    "Regional Analysis": "dashboard/pages/5_Regional_Analysis.py",
    "Profit Analysis": "dashboard/pages/6_Profit_Analysis.py",
    "Discount Analysis": "dashboard/pages/7_Discount_Analysis.py",
}


def find_page(question: str) -> dict:
    """Return the best-matching dashboard page for a natural-language question."""
    q = question.lower()
    for page, keywords in PAGE_MAP.items():
        if any(kw in q for kw in keywords):
            return {"page": page, "file": PAGE_FILES[page]}
    return {"page": "Executive Dashboard", "file": PAGE_FILES["Executive Dashboard"]}


if __name__ == "__main__":
    tests = [
        "Where can I see customer segmentation?",
        "Show me regional sales",
        "How is profit trending?",
    ]
    for t in tests:
        print(t, "->", find_page(t))
