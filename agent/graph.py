from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import router_node, query_node, chart_node, summary_node, validator_node


def route_decision(state: AgentState) -> str:
    return state["route"]


def validation_decision(state: AgentState) -> str:
    if state.get("is_valid"):
        return "end"
    else:
        return "retry"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("query", query_node)
    graph.add_node("chart", chart_node)
    graph.add_node("summary", summary_node)
    graph.add_node("validator", validator_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "query": "query",
            "chart": "chart",
            "summary": "summary"
        }
    )

    graph.add_edge("query", "validator")
    graph.add_edge("chart", "validator")
    graph.add_edge("summary", "validator")

    graph.add_conditional_edges(
        "validator",
        validation_decision,
        {
            "end": END,
            "retry": "router"
        }
    )

    return graph.compile()
