from agent.state import AgentState
from agent.tools import query_dataframe, generate_chart, formulate_response, get_llm_response
from utils.loader import get_dataframe_summary


def router_node(state: AgentState) -> AgentState:
    question = state["question"]
    dataset_names = list(state["dataframes"].keys())
    datasets_text = ", ".join(dataset_names)

    prompt = f"""Route this user request. 
Datasets available: {datasets_text}
Question: {question}

You must choose ONE action:
1. 'query' (for general questions, sums, counts, or finding specific data)
2. 'chart' (if the user explicitly asks for a graph, plot, or visualization)

Reply exactly in this format:
ACTION: <query or chart>
DATASET: <dataset_name>"""

    text = get_llm_response(prompt).strip().lower()

    route = "query"
    selected_dataset = dataset_names[0]

    if "chart" in text:
        route = "chart"
    elif "query" in text or "summarize" in text:
        route = "query"

    for name in dataset_names:
        if name.lower() in text:
            selected_dataset = name
            break

    print(f"[Router] Decision -> Route: {route} | Dataset: {selected_dataset}")
    return {**state, "route": route, "selected_dataset": selected_dataset}


def query_node(state: AgentState) -> AgentState:
    print("[Query Node] Running pandas query...")
    raw_result = query_dataframe(
        state["question"],
        state["dataframes"],
        state.get("selected_dataset")
    )
    friendly_answer = formulate_response(state["question"], raw_result, "query")
    return {**state, "query_result": raw_result, "final_answer": friendly_answer}


def chart_node(state: AgentState) -> AgentState:
    print("[Chart Node] Generating visualization...")
    chart_path = generate_chart(
        state["question"],
        state["dataframes"],
        state.get("selected_dataset")
    )
    return {**state, "chart_path": chart_path}


def summary_node(state: AgentState) -> AgentState:
    print("[Summary Node] Generating dataset summary...")
    ds_name = state.get("selected_dataset") or list(state["dataframes"].keys())[0]
    df = state["dataframes"][ds_name]
    summary = get_dataframe_summary({ds_name: df})
    friendly_answer = formulate_response(state["question"], summary, "summary")
    return {**state, "summary": summary, "final_answer": friendly_answer}


def validator_node(state: AgentState) -> AgentState:
    is_valid = bool(state.get("final_answer") or state.get("chart_path"))
    return {**state, "is_valid": is_valid}
