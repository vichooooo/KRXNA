import pandas as pd
import plotly.express as px
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_llm_response(prompt: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def query_dataframe(question: str, dataframes: dict, selected_dataset: str = None) -> str:
    context_parts = []
    for name, df in dataframes.items():
        cols = ", ".join(df.columns.tolist())
        note = " ← USE THIS ONE" if name == selected_dataset else ""
        context_parts.append(f"DataFrame: '{name}'{note}\nColumns: {cols}\nShape: {df.shape}")

    context = "\n\n".join(context_parts)

    prompt = f"""You are a pandas expert. Given these dataframes:
{context}

The dataframes are already loaded in memory as a dict called `dataframes`.
Access them like: dataframes['{selected_dataset if selected_dataset else "dataset_name"}']

Write Python pandas code to answer this question: {question}

Rules:
- Store the final result in a variable called `result`
- `result` must be a string, number, DataFrame, or Series
- For name searches use case-insensitive matching
- Write only the code, no explanation, no markdown

Code:"""

    code = get_llm_response(prompt)
    code = code.replace("```python", "").replace("```", "").strip()

    try:
        local_vars = {"dataframes": dataframes, "pd": pd}
        exec(code, {}, local_vars)
        result = local_vars.get("result", "No result returned.")

        if isinstance(result, pd.DataFrame):
            return "No matching records found." if result.empty else result.to_markdown(index=False)
        if isinstance(result, (pd.Series, list)):
            items = result.dropna().tolist() if isinstance(result, pd.Series) else result
            return "\n".join(f"- {item}" for item in items)

        return str(result)
    except Exception as e:
        return f"Query failed: {str(e)}\nCode attempted:\n{code}"


def generate_chart(question: str, dataframes: dict, selected_dataset: str = None) -> str:
    context_parts = []
    for name, df in dataframes.items():
        cols = ", ".join(df.columns.tolist())
        note = " ← USE THIS ONE" if name == selected_dataset else ""
        context_parts.append(f"DataFrame: '{name}'{note}\nColumns: {cols}\nShape: {df.shape}")

    context = "\n\n".join(context_parts)

    prompt = f"""You are a data visualization expert. Write Python code using plotly express (px) to answer: {question}
Datasets: {context}
Access via: dataframes['{selected_dataset if selected_dataset else "name"}']

Rules:
- Store figure in `fig`
- Use dark theme layout (bg: #0e0e0e)
- Do NOT use fig.show()
- Write only code, no markdown.

Code:"""

    code = get_llm_response(prompt)
    code = code.replace("```python", "").replace("```", "").strip()

    try:
        local_vars = {"dataframes": dataframes, "pd": pd, "px": px}
        exec(code, {}, local_vars)
        fig = local_vars.get("fig")

        if fig:
            os.makedirs("charts", exist_ok=True)
            chart_path = "charts/latest_chart.html"
            fig.write_html(chart_path, config={"displayModeBar": False})
            return chart_path
        return None
    except Exception as e:
        print(f"[Chart Error] {str(e)}")
        return None


def formulate_response(question: str, raw_result: str, route: str) -> str:
    truncated = raw_result[:1500] if len(raw_result) > 1500 else raw_result
    prompt = f"User asked: {question}\nData result: {truncated}\n\nSummarize this concisely and add 1 insight."
    return get_llm_response(prompt)
