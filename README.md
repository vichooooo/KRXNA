# KRXNA — Conversational Data Analyst Agent

> Ask business questions in plain English. Get answers, insights and charts instantly.

![Python](https://img.shields.io/badge/Python-3.11-black?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-black?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-black?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-LLM-black?style=flat-square)

---

## What is KRXNA?

KRXNA is an AI-powered data analyst agent that lets anyone upload a CSV and 
ask questions about their data in plain English — no SQL, no Python, no 
technical knowledge needed.

The agent doesn't just retrieve and answer. It **reasons**, **acts**, 
**validates its own output**, and **self-corrects** if the answer is weak. 
That's what makes it different from a basic chatbot.

---

## Features

- **Natural language querying** — ask anything, get data back
- **Auto-generated charts** — dark-themed Plotly visualizations
- **Self-correcting agent loop** — validates answers and retries if needed
- **Multi-dataset support** — drop multiple CSVs and query across all of them
- **Smart routing** — automatically decides whether to query, chart or summarize
- **Persistent chat history** — conversations saved across refreshes
- **Clean minimal UI** — dark theme built to match the KRXNA brand

---

## Tech Stack

| Layer | Tool |
|---|---|
| Agent orchestration | LangGraph |
| LLM + tools | LangChain + Groq (llama-3.3-70b) |
| Data querying | Pandas |
| Visualizations | Plotly |
| Frontend | Streamlit |

---

## How It Works
