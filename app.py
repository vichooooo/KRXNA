import streamlit as st
import os
import json
import base64
import pandas as pd
from streamlit.components.v1 import html

def get_logo():
    try:
        with open("assets/logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

from utils.loader import load_csvs
from agent.graph import build_graph

# ── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title="KRXNA",
    page_icon="assets/logo.png",
    layout="wide"
)

# ── Global styles ────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0e0e0e; color: #e8e8e8; }
    .main .block-container { padding: 2rem 2.5rem; max-width: 860px; }
    header[data-testid="stHeader"] { background: #0e0e0e; border-bottom: 1px solid #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #1a1a1a; }
    [data-testid="stSidebar"] * { color: #c0c0c0 !important; }
    [data-testid="stChatMessage"] { background-color: #161616; border: 1px solid #202020; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; }
    [data-testid="stChatInput"] { background-color: #161616 !important; border: 1px solid #2a2a2a !important; border-radius: 12px !important; color: #e8e8e8 !important; }
    .stButton > button { background-color: #1a1a1a; color: #e8e8e8; border: 1px solid #2e2e2e; border-radius: 6px; font-size: 0.82rem; transition: all 0.2s ease; }
    [data-testid="stExpander"] { background-color: #141414; border: 1px solid #1f1f1f; border-radius: 8px; }
    .center-greeting { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 70vh; text-align: center; margin-top: -2rem; }
    .greeting-text { font-size: 2rem; font-weight: 500; color: #e8e8e8; margin-bottom: 0.4rem; }
    .greeting-sub { font-size: 0.9rem; color: #555; margin-bottom: 2.5rem; }
    hr { border-color: #1f1f1f; }
    footer { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Chat history persistence ─────────────────────────────────
CHAT_HISTORY_FILE = "chat_history.json"

def save_chat_history(messages):
    saveable = []
    for msg in messages:
        saveable.append({
            "role": msg["role"],
            "content": msg["content"],
            "chart_path": msg.get("chart_path"),
            "reasoning": msg.get("reasoning")
        })
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(saveable, f, ensure_ascii=False, indent=2)

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def safe_open_chart(chart_path):
    if chart_path and isinstance(chart_path, str) and os.path.exists(chart_path):
        try:
            with open(chart_path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return None
    return None

# ── Session state ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()
if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    logo_b64 = get_logo()
    if logo_b64:
        st.markdown(f'<img src="data:image/png;base64,{logo_b64}" width="130">', unsafe_allow_html=True)
    else:
        st.markdown("## KRXNA")
    st.markdown("<p style='color:#444; font-size:0.72rem; margin-top:-6px;'>Your Personal Data Analysis Assistant</p>", unsafe_allow_html=True)
    st.divider()

    # ── Groq API Key input ───────────────────────────────────
    st.markdown("**Groq API Key**")
    groq_key = st.text_input("Enter your Groq API key", type="password", label_visibility="collapsed", placeholder="gsk_...")
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
        st.success("✓ Key set")
    st.divider()

    st.markdown("**Upload Data**")
    uploaded_files = st.file_uploader("Drop CSV files here", type=["csv"], accept_multiple_files=True, label_visibility="collapsed")

    if uploaded_files:
        for file in uploaded_files:
            name = file.name.replace(".csv", "")
            try:
                df = pd.read_csv(file, encoding="utf-8")
            except:
                df = pd.read_csv(file, encoding="latin1")
            st.session_state.dataframes[name] = df
            st.success(f"✓ {file.name}")

    if os.path.exists("data"):
        auto_loaded = load_csvs("data")
        for name, df in auto_loaded.items():
            if name not in st.session_state.dataframes:
                st.session_state.dataframes[name] = df

    if st.session_state.dataframes:
        st.divider()
        st.markdown("**Loaded Datasets**")
        for name, df in st.session_state.dataframes.items():
            with st.expander(f"↗ {name}"):
                st.dataframe(df.head(5), use_container_width=True)

    st.divider()
    if st.button("Clear Chat"):
        st.session_state.messages = []
        if os.path.exists(CHAT_HISTORY_FILE):
            os.remove(CHAT_HISTORY_FILE)
        st.rerun()

# ── Main area ────────────────────────────────────────────────
if not st.session_state.dataframes:
    st.markdown('<div class="center-greeting"><div class="greeting-text">Upload a dataset to get started.</div><div class="greeting-sub">Drop a CSV in the sidebar and start asking questions.</div></div>', unsafe_allow_html=True)

else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("reasoning"):
                with st.expander("reasoning"):
                    st.markdown(msg["reasoning"])
            chart_html = safe_open_chart(msg.get("chart_path"))
            if chart_html:
                html(chart_html, height=500, width=700)

    question = st.chat_input("Ask anything...")

    if question:
        if not os.getenv("GROQ_API_KEY"):
            st.warning("Please enter your Groq API key in the sidebar first.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                initial_state = {
                    "question": question,
                    "dataframes": st.session_state.dataframes,
                    "retry_count": 0,
                    "route": None,
                    "query_result": None,
                    "chart_path": None,
                    "summary": None,
                    "final_answer": None,
                    "reasoning": None,
                    "is_valid": None,
                    "selected_dataset": None
                }
                result = st.session_state.graph.invoke(initial_state)

            if result.get("reasoning"):
                with st.expander("reasoning"):
                    st.markdown(result["reasoning"])

            chart_path = result.get("chart_path")
            chart_html = safe_open_chart(chart_path)

            if chart_html:
                st.markdown("Here's your chart:")
                html(chart_html, height=500, width=700)
                display_answer = "Chart generated above."
            else:
                display_answer = result.get("final_answer", "I couldn't find an answer.")
                st.markdown(display_answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": display_answer,
                "chart_path": chart_path,
                "reasoning": result.get("reasoning")
            })
            save_chat_history(st.session_state.messages)
