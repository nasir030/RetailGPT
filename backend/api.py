"""
FastAPI backend for RetailGPT.

Run with:
    uvicorn backend.api:app --reload --port 8000

Endpoints:
    GET  /health
    GET  /kpis                 -> executive KPI summary
    POST /chat   {"question": "..."}   -> grounded AI answer + suggested chart type
    GET  /report/executive-summary     -> generates & returns a PDF report
"""

import os
import sys

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.data_service import load_data, kpi_summary, apply_filters
from backend.services.ollama_service import answer_question, is_ollama_available
from agents.report_agent import generate_executive_summary_pdf

app = FastAPI(title="RetailGPT API", version="0.1.0")


class ChatRequest(BaseModel):
    question: str
    region: str | None = None
    category: str | None = None
    segment: str | None = None
    year: int | None = None


@app.get("/health")
def health():
    return {"status": "ok", "ollama_connected": is_ollama_available()}


@app.get("/kpis")
def kpis(region: str | None = None, category: str | None = None, segment: str | None = None, year: int | None = None):
    df = load_data()
    filtered = apply_filters(df, region=region, category=category, segment=segment, year=year)
    return kpi_summary(filtered)


@app.post("/chat")
def chat(req: ChatRequest):
    df = load_data()
    filtered = apply_filters(df, region=req.region, category=req.category, segment=req.segment, year=req.year)
    result = answer_question(req.question, filtered)
    # Figures aren't JSON-serializable directly; the frontend re-derives the chart
    # client-side using chart_suggestion + /kpis, so we drop the raw figure here.
    return {"answer": result["answer"], "intent": result["intent"], "data": result["data"],
             "chart_suggestion": result["chart_suggestion"]}


@app.get("/report/executive-summary")
def executive_summary():
    df = load_data()
    path = generate_executive_summary_pdf(df, os.path.join("reports", "executive_summary.pdf"))
    return FileResponse(path, media_type="application/pdf", filename="executive_summary.pdf")
