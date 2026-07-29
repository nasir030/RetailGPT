"""
report_agent.py
-----------------
Generates an Executive Summary PDF report from the real dataset using ReportLab.
"""

from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_executive_summary_pdf(df: pd.DataFrame, output_path: str, period_label: str = "All-Time") -> str:
    """Build a one-page executive summary PDF and save it to output_path."""
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.services.data_service import kpi_summary
    from agents.recommendation_agent import generate_recommendations

    kpis = kpi_summary(df)
    recommendations = generate_recommendations(df)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=20)
    story = []

    story.append(Paragraph("RetailGPT — Executive Summary", title_style))
    story.append(
        Paragraph(
            f"Period: {period_label} &nbsp;|&nbsp; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    kpi_rows = [
        ["Metric", "Value"],
        ["Total Revenue", f"${kpis['total_revenue']:,.2f}"],
        ["Total Profit", f"${kpis['total_profit']:,.2f}"],
        ["Profit Margin", f"{kpis['profit_margin_pct']:.2f}%"],
        ["Total Orders", f"{kpis['total_orders']:,}"],
        ["Total Customers", f"{kpis['total_customers']:,}"],
        ["Avg Order Value", f"${kpis['avg_order_value']:,.2f}"],
        ["Best Selling Product", str(kpis["best_selling_product"])],
        ["Best Performing Region", str(kpis["best_performing_region"])],
    ]
    table = Table(kpi_rows, colWidths=[2.7 * inch, 3.3 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.35 * inch))

    story.append(Paragraph("Key Recommendations", styles["Heading2"]))
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", styles["Normal"]))
        story.append(Spacer(1, 0.08 * inch))

    doc.build(story)
    return output_path


if __name__ == "__main__":
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.services.data_service import load_data

    df = load_data()
    path = generate_executive_summary_pdf(
        df, os.path.join("reports", "executive_summary.pdf")
    )
    print("Report generated at:", path)
