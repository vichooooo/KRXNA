import streamlit as st
import os
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

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0e0e0e;
        color: #e8e8e8;
    }

    .main .block-container {
        padding: 2rem 2.5rem;
        max-width: 860px;
    }

    header[data-testid="stHeader"] {
        background: #0e0e0e;
        border-bottom: 1px solid #1a1a1a;
    }

    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #1a1a1a;
    }
    [data-testid="stSidebar"] * {
        color: #c0c0c0 !important;
    }

    [data-testid="stChatMessage"] {
        background-color: #161616;
        border: 1px solid #202020;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }

    [data-testid="stChatInput"] {
        background-color: #161616 !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 12px !important;
        color: #e8e8e8 !important;
    }

    .stButton > button {
        background-color: #1a1a1a;
        color: #e8e8e8;
        border: 1px solid #2e2e2e;
        border-radius: 6px;
        font-size: 0.82rem;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #252525;
        border-color: #555;
    }

    [data-testid="stExpander"] {
        background-color: #141414;
        border: 1px solid #1f1f1f;
        border-radius: 8px;
    }

    /* Center greeting layout */
    .center-greeting {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
        text-align: center;
    }

    .greeting-text {
        font-size: 2rem;
        font-weight: 500;
        color: #e8e8e8;
        margin-bottom: 0.4rem;
    }

    .greeting-sub {
        font-size: 0.9rem;
        color: #555;
        margin-bottom: 2.5rem;
    }

    hr { border-color: #1f1f1f; }
    footer { display: none; }
    #MainMenu { display: none; }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0e0e0e; }
    ::-webkit-scrollbar-thumb { background: #2e2e2e; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.image("assets/logo.png", width=130)
    st.markdown("<p style='color:#444; font-size:0.72rem; margin-top:-6px;'>Your Personal Data Analysis Assistant</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("**Upload Data**")
    uploaded_files = st.file_uploader(
        "Drop CSV files here",
        type=["csv"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        import pandas as pd
        for file in uploaded_files:
            name = file.name.replace(".csv", "")
            try:
                df = pd.read_csv(file, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file, encoding="latin1")
            st.session_state.dataframes[name] = df
            st.success(f"✓ {file.name} — {df.shape[0]}r × {df.shape[1]}c")

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
        st.rerun()

# ── Main area ────────────────────────────────────────────────
if not st.session_state.dataframes:
    # No data loaded — centered welcome
    st.markdown("""
    <div class="center-greeting">
        <div class="greeting-text">Upload a dataset to get started.</div>
        <div class="greeting-sub">Drop a CSV in the sidebar and start asking questions.</div>
    </div>
    """, unsafe_allow_html=True)

elif len(st.session_state.messages) == 0:
    # Data loaded, no messages yet — centered greeting + input
    greetings = [
        "What's on the agenda today?",
        "What do you want to dig into?",
        "What are we analysing today?",
        "Ask me anything about your data.",
        "What story is your data hiding?",
    ]
    import random
    greeting = random.choice(greetings)

    st.markdown(f"""
    <div class="center-greeting">
        <div class="greeting-text">{greeting}</div>
        <div class="greeting-sub">Your data is loaded and ready.</div>
    </div>
    """, unsafe_allow_html=True)

    question = st.chat_input("Ask anything...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})

        with st.spinner(""):
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

        chart_path = result.get("chart_path")
        if chart_path and os.path.exists(chart_path):
            display_answer = "Chart generated ↑"
        else:
            display_answer = result.get("final_answer", "I couldn't find an answer.")

        st.session_state.messages.append({
            "role": "assistant",
            "content": display_answer,
            "chart_path": chart_path,
            "reasoning": result.get("reasoning")
        })
        st.rerun()

else:
    # Conversation in progress — chat at top, input at bottom
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("reasoning"):
                with st.expander("reasoning"):
                    st.markdown(msg["reasoning"])
            if msg.get("chart_path") and os.path.exists(msg["chart_path"]):
                with open(msg["chart_path"], "r", encoding="utf-8") as f:
                    st.components.v1.html(f.read(), height=480)

    question = st.chat_input("Ask anything...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner(""):
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
            if chart_path and os.path.exists(chart_path):
                st.markdown("Here's your chart:")
                with open(msg["chart_path"], "r", encoding="utf-8") as f:
                    st.components.v1.html(f.read(), height=480)
                display_answer = "Chart generated ↑"
            else:
                display_answer = result.get("final_answer", "I couldn't find an answer.")
                st.markdown(display_answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": display_answer,
                "chart_path": chart_path,
                "reasoning": result.get("reasoning")
            })