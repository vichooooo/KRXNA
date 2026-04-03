from langchain_groq import ChatGroq
from agent.state import AgentState
from agent.tools import query_dataframe, generate_chart, formulate_response
from utils.loader import get_dataframe_summary
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)


def router_node(state: AgentState) -> AgentState:
    """
    Decides which tool to use AND which dataset is most relevant.
    """
    question = state["question"]

    # Build dataset info
    dataset_info = []
    for name, df in state["dataframes"].items():
        cols = ", ".join(df.columns.tolist())
        dataset_info.append(f"- '{name}': {cols}")
    datasets_text = "\n".join(dataset_info)

    prompt = f"""You are a routing agent for a data analyst assistant.

Available datasets:
{datasets_text}

User question: {question}

Decide:
1. Which ACTION to take: query, chart, or summary
2. Which DATASET is most relevant to the question

Rules:
- query: user wants a specific number, filter, lookup, or calculation
- chart: user wants a graph, plot, visualization, OR asks about trends/comparisons/distributions (these are always better as charts)
- summary: user wants a broad overview or general insight about the data
- Pick the dataset whose columns best match the question
- When in doubt between query and chart, prefer chart — visuals are more insightful

Respond in exactly this format:
ACTION: query
DATASET: name of dataset"""

    response = llm.invoke(prompt)
    text = response.content.strip()

    # Parse response
    route = "query"
    selected_dataset = list(state["dataframes"].keys())[0]

    for line in text.split("\n"):
        if line.startswith("ACTION:"):
            route = line.replace("ACTION:", "").strip().lower()
        if line.startswith("DATASET:"):
            selected_dataset = line.replace("DATASET:", "").strip()

    if route not in ["query", "chart", "summary"]:
        route = "query"

    # Fuzzy match dataset name
    if selected_dataset not in state["dataframes"]:
        for name in state["dataframes"].keys():
            if selected_dataset.lower() in name.lower() or name.lower() in selected_dataset.lower():
                selected_dataset = name
                break
        else:
            selected_dataset = list(state["dataframes"].keys())[0]

    print(f"[Router] Route: {route} | Dataset: {selected_dataset}")

    return {
        **state,
        "route": route,
        "dataframes": state["dataframes"],
        "reasoning": f"Routed to **{route}** using dataset **'{selected_dataset}'**",
        "selected_dataset": selected_dataset
    }
def query_node(state: AgentState) -> AgentState:
    print("[Query Node] Running pandas query...")
    raw_result = query_dataframe(
        state["question"],
        state["dataframes"],
        state.get("selected_dataset")
    )
    friendly_answer = formulate_response(state["question"], raw_result, "query")
    
    # Combine raw data + friendly commentary
    final = f"{friendly_answer}\n\n---\n\n**Full Results:**\n\n{raw_result}"
    
    return {**state, "query_result": raw_result, "final_answer": final}

def chart_node(state: AgentState) -> AgentState:
    """Runs the chart generation tool"""
    print("[Chart Node] Generating chart...")
    chart_path = generate_chart(state["question"], state["dataframes"])
    return {**state, "chart_path": chart_path, "final_answer": f"Chart saved to: {chart_path}"}


def summary_node(state: AgentState) -> AgentState:
    """Generates a natural language summary/insight"""
    print("[Summary Node] Generating summary...")
    data_summary = get_dataframe_summary(state["dataframes"])

    prompt = f"""You are a friendly, insightful data analyst assistant with a confident personality.

Given this dataset information:
{data_summary}

Answer this question in an engaging, insightful way: {state["question"]}

- Be conversational and enthusiastic about the data
- Highlight key numbers and what they mean
- Add observations the user might not have thought to ask
- Use emojis sparingly
- Keep it under 150 words"""

    response = llm.invoke(prompt)
    summary = response.content.strip()
    return {**state, "summary": summary, "final_answer": summary}

def validator_node(state: AgentState) -> AgentState:
    """
    Checks if the answer is good enough.
    If not, increments retry_count so the graph can loop back.
    """
    print("[Validator] Checking answer quality...")
    answer = state.get("final_answer", "")
    retry_count = state.get("retry_count", 0)

    # Hard stop after 2 retries to avoid infinite loops
    if retry_count >= 2:
        print("[Validator] Max retries reached. Accepting answer.")
        return {**state, "is_valid": True}

    prompt = f"""You are a quality checker for an AI data analyst.

User question: {state["question"]}
Agent answer: {answer}

Rules for a VALID answer:
- A number is valid if the question asked for a calculation or total
- A file path like charts/latest_chart.html is valid if the question asked for a chart
- A text summary is valid if the question asked for insights or trends
- Only say no if the answer is clearly an error or completely unrelated

Is this a valid, useful answer to the question?
Reply with only one word: yes or no."""

    response = llm.invoke(prompt)
    verdict = response.content.strip().lower()
    is_valid = verdict == "yes"

    print(f"[Validator] Valid: {is_valid}")

    return {
        **state,
        "is_valid": is_valid,
        "retry_count": retry_count + 1 if not is_valid else retry_count
    }