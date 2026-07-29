"""
ollama_service.py
------------------
Talks to a LOCALLY hosted Ollama server running Mistral (or Llama 3.1 8B).

This is real, runnable code - but it requires Ollama to be installed and
running on the machine that executes it (see README for setup). This
sandbox cannot install/run Ollama itself (no internet access to
ollama.com / model registries), so this file has been written and
syntax/logic-tested, but the actual HTTP round-trip to Ollama has not
been executed here. Test it locally with:

    ollama pull mistral
    ollama serve          # usually auto-starts on install
    python backend/services/ollama_service.py

Design: the LLM is NEVER trusted to invent numbers. Every chat response
is "grounded" - analytics_agent.route_question() computes the real
answer from pandas first, then the LLM is only asked to phrase that
already-computed data in natural language.
"""

from __future__ import annotations

import os
import sys
import json

import requests
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")  # or "llama3.1:8b"
REQUEST_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))


def is_ollama_available() -> bool:
    """Check whether the local Ollama server is reachable."""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False


def call_ollama(prompt: str, model: str | None = None, system: str | None = None) -> str:
    """Send a prompt to the local Ollama model and return the generated text."""
    payload = {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate", json=payload, timeout=REQUEST_TIMEOUT
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


GROUNDED_SYSTEM_PROMPT = """You are RetailGPT, a retail business intelligence assistant.
You will be given a user's question and a JSON object containing numbers that were
already computed correctly from the real dataset with pandas.

Rules:
- Use ONLY the numbers given to you in the JSON. Never invent or estimate a number.
- Answer in 2-4 concise, business-friendly sentences.
- If relevant, offer one short actionable recommendation.
"""


def answer_question(question: str, df) -> dict:
    """Full pipeline: route question -> compute real data -> phrase with Mistral.

    Returns dict with keys: answer (str), intent (str), data (dict), chart_suggestion (str)
    Falls back to a templated answer (no LLM) if Ollama isn't running, so the
    dashboard still works even before you set up Ollama locally.
    """
    from agents.analytics_agent import route_question
    from agents.visualization_agent import suggest_chart

    routed = route_question(question, df)
    intent, data = routed["intent"], routed["data"]
    chart_suggestion = suggest_chart(intent)

    if is_ollama_available():
        prompt = (
            f"User question: {question}\n\n"
            f"Computed data (JSON): {json.dumps(data, default=str)}\n\n"
            "Write the answer now."
        )
        try:
            answer = call_ollama(prompt, system=GROUNDED_SYSTEM_PROMPT)
        except requests.exceptions.RequestException as e:
            answer = _fallback_answer(intent, data) + f"\n\n(LLM phrasing unavailable: {e})"
    else:
        answer = _fallback_answer(intent, data)

    return {
        "answer": answer,
        "intent": intent,
        "data": data,
        "chart_suggestion": chart_suggestion,
    }


def _fallback_answer(intent: str, data: dict) -> str:
    """Plain-English templated answer used when Ollama is not running,
    so the app is still usable without the LLM installed."""
    templates = {
        "highest_sales_month": "The highest sales month was {month} with ${sales:,.2f} in sales.",
        "most_profitable_product": "Top profitable products: "
        + ", ".join([f"{p['product']} (${p['profit']:,.2f})" for p in data]) if isinstance(data, list) else "",
        "best_region": "{region} is the best performing region with ${sales:,.2f} in sales.",
        "lowest_profit_category": "{category} has the lowest profit at ${profit:,.2f}.",
        "profit_decline_analysis": (
            "Discounts above 20% average ${avg_profit_high_discount:,.2f} profit per order vs "
            "${avg_profit_low_discount:,.2f} for lower discounts. {worst_category} in the "
            "{worst_region} region shows the weakest profit."
        ),
    }
    tpl = templates.get(intent)
    if not tpl:
        return f"Here's what I found: {json.dumps(data, default=str)}"
    try:
        return tpl.format(**data) if isinstance(data, dict) else tpl
    except (KeyError, TypeError):
        return json.dumps(data, default=str)


if __name__ == "__main__":
    from backend.services.data_service import load_data

    df = load_data()
    print("Ollama available:", is_ollama_available())
    result = answer_question("Which month had the highest sales?", df)
    print(json.dumps(result, indent=2, default=str))
