import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.services.data_service import load_data, apply_filters
from backend.services.ollama_service import answer_question, is_ollama_available
from agents.visualization_agent import build_chart
from agents.navigation_agent import find_page

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")
st.title("🤖 AI Business Assistant")

df = load_data()
filters = st.session_state.get("filters", {})
filtered = apply_filters(df, **filters) if filters else df

ollama_ok = is_ollama_available()
if ollama_ok:
    st.success("Connected to local Ollama (Mistral) — answers are LLM-phrased and data-grounded.")
else:
    st.warning(
        "Ollama isn't reachable right now, so answers use a plain-English template instead of "
        "the LLM. Run `ollama serve` and `ollama pull mistral` locally, then refresh this page. "
        "See README.md for setup."
    )

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.caption("Try: *Which month had the highest sales?* · *Why did profits decrease?* · "
           "*Show Technology category sales* · *Compare sales between 2016 and 2017* · "
           "*Which customers spend the most?*")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("chart") is not None:
            st.plotly_chart(msg["chart"], use_container_width=True)
        if msg.get("nav"):
            st.info(f"📍 See more detail on the **{msg['nav']}** page (left sidebar).")

question = st.chat_input("Ask a business question about your retail data...")

if question:
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing your data..."):
            result = answer_question(question, filtered)
            chart = None
            if result["chart_suggestion"] != "none":
                chart = build_chart(result["chart_suggestion"], filtered)
            nav = find_page(question)["page"]

        st.write(result["answer"])
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
        st.info(f"📍 See more detail on the **{nav}** page (left sidebar).")

    st.session_state.chat_history.append(
        {"role": "assistant", "content": result["answer"], "chart": chart, "nav": nav}
    )
