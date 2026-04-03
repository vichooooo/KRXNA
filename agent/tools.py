import pandas as pd
import plotly.express as px
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)


def query_dataframe(question: str, dataframes: dict, selected_dataset: str = None) -> str:
    """
    Takes a natural language question, converts it to pandas code,
    executes it, and returns the result as a string.
    """
    # Build context about available dataframes
    context_parts = []
    for name, df in dataframes.items():
        cols = ", ".join(df.columns.tolist())
        context_parts.append(f"DataFrame name: '{name}'\nColumns: {cols}\nShape: {df.shape}")
    context = "\n\n".join(context_parts)

    prompt = f"""You are a pandas expert. Given these dataframes:

{context}

The dataframes are already loaded in memory as a dict called `dataframes`.
Access them like: dataframes['Sample - Superstore']

Write Python pandas code to answer this question: {question}

Rules:
- Store the final result in a variable called `result`
- `result` must be a string, number, or call str() on it
- Do NOT import anything
- Do NOT use print()
- Write only the code, no explanation, no markdown

Code:"""

    response = llm.invoke(prompt)
    code = response.content.strip()

    # Clean up any markdown the LLM adds
    code = code.replace("```python", "").replace("```", "").strip()

    try:
        local_vars = {"dataframes": dataframes, "pd": pd}
        exec(code, {}, local_vars)
        result = local_vars.get("result", "No result returned.")

        # If result is a DataFrame, format it nicely
        if isinstance(result, pd.DataFrame):
            if result.empty:
                return "No matching records found."
            return result.to_markdown(index=False)

        # If result is a Series, convert to a clean list
        if isinstance(result, pd.Series):
            items = result.dropna().tolist()
            return "\n".join(f"- {item}" for item in items)

        # If result is a plain Python list
        if isinstance(result, list):
            return "\n".join(f"- {item}" for item in result)

        return str(result)

    except Exception as e:
        return f"Query failed: {str(e)}\nCode attempted:\n{code}"


def generate_chart(question: str, dataframes: dict, selected_dataset: str = None) -> str:
    """
    Generates a beautiful dark-themed Plotly chart.
    """
    context_parts = []
    for name, df in dataframes.items():
        cols = ", ".join(df.columns.tolist())
        note = " ← USE THIS ONE" if name == selected_dataset else ""
        context_parts.append(f"DataFrame: '{name}'{note}\nColumns: {cols}\nShape: {df.shape}")
    context = "\n\n".join(context_parts)

    prompt = f"""You are a data visualization expert. Given these dataframes:

{context}

The dataframes are loaded as a dict called `dataframes`.
Access them like: dataframes['Sample - Superstore']

Write Python code using plotly.express to answer: {question}

Rules:
- Store the final figure in a variable called `fig`
- Do NOT import anything
- Do NOT call fig.show()
- plotly.express is available as `px` — always use px.bar(), px.line(), px.pie(), px.scatter() etc
- Always aggregate data before plotting (use groupby) to avoid messy charts
- Apply this dark theme to every chart using fig.update_layout():
    fig.update_layout(
        plot_bgcolor='#0e0e0e',
        paper_bgcolor='#0e0e0e',
        font=dict(color='#e8e8e8', family='Inter'),
        title_font=dict(size=16, color='#e8e8e8'),
        xaxis=dict(gridcolor='#1f1f1f', linecolor='#2a2a2a'),
        yaxis=dict(gridcolor='#1f1f1f', linecolor='#2a2a2a'),
        legend=dict(bgcolor='#161616', bordercolor='#2a2a2a'),
        margin=dict(l=40, r=40, t=60, b=40)
    )
- Use this color sequence for bars/lines: ['#e8e8e8', '#a0a0a0', '#606060', '#303030']
- Write only the code, no explanation, no markdown

Code:"""

    response = llm.invoke(prompt)
    code = response.content.strip()
    code = code.replace("```python", "").replace("```", "").strip()

    try:
        local_vars = {"dataframes": dataframes, "pd": pd, "px": px}
        exec(code, {}, local_vars)
        fig = local_vars.get("fig")

        if fig is None:
            return "Chart generation failed: no figure was created."

        os.makedirs("charts", exist_ok=True)
        chart_path = "charts/latest_chart.html"
        fig.write_html(chart_path, config={"displayModeBar": False})
        return chart_path

    except Exception as e:
        return f"Chart failed: {str(e)}\nCode attempted:\n{code}"
    
def formulate_response(question: str, raw_result: str, route: str) -> str:
    """
    Takes a raw result and turns it into a friendly, insightful analyst response.
    """
    prompt = f"""You are a friendly, insightful data analyst assistant with a confident personality.

The user asked: {question}
The raw data result is: {raw_result}
The type of result is: {route}

Your job:
- Answer the question directly and clearly
- Add 1-2 extra insights or observations beyond just the raw answer
- If it's a number, give it context (is it high? what might be driving it?)
- If the result involves multiple categories or time periods, mention that a chart would show it better
- Keep it conversational and engaging, like a smart colleague
- Use emojis sparingly but effectively
- Keep it under 120 words

Response:"""

    response = llm.invoke(prompt)
    return response.content.strip()